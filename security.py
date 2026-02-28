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
