from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from security import get_current_user, user_can_access_module

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def require_upload_access(current_user=Depends(get_current_user)):
    if user_can_access_module(current_user, "production") or user_can_access_module(current_user, "tourisme"):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Vous n avez pas les droits pour envoyer une image",
    )


@router.post("/image")
async def upload_image(file: UploadFile = File(...), current_user=Depends(require_upload_access)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier invalide")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format image non supporte")

    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le fichier doit etre une image")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image trop lourde (max 5MB)")

    filename = f"{uuid4().hex}{extension}"
    destination = UPLOADS_DIR / filename

    with open(destination, "wb") as buffer:
        buffer.write(content)

    return {
        "filename": filename,
        "url": f"/uploads/{filename}",
        "size": len(content),
        "content_type": content_type,
    }
