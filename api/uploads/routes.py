import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import cloudinary
import cloudinary.uploader

from security import get_current_user, user_can_access_module

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_UPLOAD_FOLDER", "ivoirtrips/circuits")


def require_upload_access(current_user=Depends(get_current_user)):
    if user_can_access_module(current_user, "production") or user_can_access_module(current_user, "tourisme"):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Vous n avez pas les droits pour envoyer une image",
    )


def ensure_cloudinary_configured():
    if not os.getenv("CLOUDINARY_URL"):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True,
        )
    else:
        cloudinary.config(secure=True)

    config = cloudinary.config()
    if not config.cloud_name or not config.api_key or not config.api_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary n est pas configure sur le serveur",
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

    ensure_cloudinary_configured()

    public_id = uuid4().hex
    image_stream = BytesIO(content)
    image_stream.name = file.filename

    try:
        upload_result = cloudinary.uploader.upload(
            image_stream,
            folder=CLOUDINARY_FOLDER,
            public_id=public_id,
            resource_type="image",
            overwrite=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Impossible d envoyer l image vers Cloudinary",
        ) from exc

    secure_url = upload_result.get("secure_url")
    if not secure_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloudinary n a pas retourne d URL image",
        )

    return {
        "filename": Path(file.filename).name,
        "url": secure_url,
        "public_id": upload_result.get("public_id"),
        "size": len(content),
        "content_type": content_type,
    }
