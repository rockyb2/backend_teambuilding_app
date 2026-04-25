import binascii
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db

# Password hashing context (new format)
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

# Bearer token extractor used by protected routes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/utilisateurs/auth/login")

SECRET_KEY = os.environ.get("JWT_SECRET", "change_this_secret_in_production")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Canonical role names used across backend + CRM.
ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_UTILISATEUR = "utilisateur"

# These are the internal modules used in the CRM.
MODULE_TOURISME = "tourisme"
MODULE_TEAMBUILDING = "teambuilding"
MODULE_PRODUCTION = "production"
MODULE_ADMINISTRATION = "administration"


def normalize_role_name(role_name: Optional[str]) -> str:
    if not role_name:
        return ""
    return role_name.strip().lower().replace("-", "_").replace(" ", "_")


def get_user_role_name(user) -> str:
    return normalize_role_name(getattr(user, "role", None))


def is_super_admin(user) -> bool:
    return get_user_role_name(user) == ROLE_SUPER_ADMIN


def is_admin(user) -> bool:
    return get_user_role_name(user) == ROLE_ADMIN


def is_standard_internal_user(user) -> bool:
    return get_user_role_name(user) == ROLE_UTILISATEUR


def _is_module_supervisor(role_name: str, module_name: str) -> bool:
    # The DB already stores dedicated supervisor roles like:
    # - superviseur_tourisme
    # - superviseur_teambuilding
    # - superviseur_production
    # We also keep the checks a bit flexible to tolerate close naming variants.
    if module_name == MODULE_TOURISME:
        return role_name.startswith("superviseur_tour")
    if module_name == MODULE_TEAMBUILDING:
        return role_name.startswith("superviseur_team")
    if module_name == MODULE_PRODUCTION:
        return role_name.startswith("superviseur_prod")
    return False


def user_can_access_module(user, module_name: str) -> bool:
    role_name = get_user_role_name(user)

    # Super admin sees everything, including admin tools and user management.
    if role_name == ROLE_SUPER_ADMIN:
        return True

    # Admin can use every business module and the administration area,
    # but still remains below super_admin for the most sensitive actions.
    if role_name == ROLE_ADMIN:
        return True

    # "utilisateur" is treated as a standard internal collaborator:
    # they can work in business modules but not in the admin area.
    if role_name == ROLE_UTILISATEUR:
        return module_name in {MODULE_TOURISME, MODULE_TEAMBUILDING, MODULE_PRODUCTION}

    if module_name == MODULE_ADMINISTRATION:
        return False

    return _is_module_supervisor(role_name, module_name)


def can_manage_users(user) -> bool:
    return get_user_role_name(user) in {ROLE_SUPER_ADMIN, ROLE_ADMIN}


def can_manage_roles(user) -> bool:
    return is_super_admin(user)


def can_assign_role(user, target_role_name: Optional[str]) -> bool:
    normalized_target = normalize_role_name(target_role_name)
    current_role = get_user_role_name(user)

    if not normalized_target:
        return False

    # Super admin can assign every role stored in the DB.
    if current_role == ROLE_SUPER_ADMIN:
        return True

    # Admin can create/update every role except super_admin.
    if current_role == ROLE_ADMIN:
        return normalized_target != ROLE_SUPER_ADMIN

    return False


def _verify_legacy_pbkdf2_sha256(plain_password: str, legacy_hash: str) -> bool:
    """Compatibility checker for old pbkdf2_sha256$... hashes already stored in DB."""
    try:
        _, iter_str, salt_hex, dk_hex = legacy_hash.split("$")
        iterations = int(iter_str)
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(dk_hex)
        derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(derived, expected)
    except Exception:
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False

    if hashed_password.startswith("pbkdf2_sha256$"):
        return _verify_legacy_pbkdf2_sha256(plain_password, hashed_password)

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"])
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"])
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    from database.models import Utilisateur

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception
        user_id = int(user_id_raw)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = (
        db.query(Utilisateur)
        .options(joinedload(Utilisateur.role_rel))
        .filter(Utilisateur.id_utilisateur == user_id)
        .first()
    )
    if user is None:
        raise credentials_exception
    return user


def require_module_access(module_name: str):
    def dependency(current_user=Depends(get_current_user)):
        if not user_can_access_module(current_user, module_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acces refuse au module {module_name}",
            )
        return current_user

    return dependency


def require_user_management_access(current_user=Depends(get_current_user)):
    if not can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n avez pas les droits pour gerer les utilisateurs",
        )
    return current_user


def require_role_management_access(current_user=Depends(get_current_user)):
    if not can_manage_roles(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n avez pas les droits pour gerer les roles",
        )
    return current_user
