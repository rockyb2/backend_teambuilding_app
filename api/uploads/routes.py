import os
import random
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
import cloudinary
import cloudinary.uploader
from cloudinary import Search
from cloudinary.utils import cloudinary_url

from security import get_current_user, user_can_access_module

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".ppt", ".pptx"}
ALLOWED_DOCUMENT_CONTENT_TYPES = {
    "",
    "application/octet-stream",
    "application/pdf",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_UPLOAD_FOLDER", "ivoirtrips/circuits")
CLOUDINARY_DOCUMENT_FOLDER = os.getenv(
    "CLOUDINARY_DOCUMENT_FOLDER",
    "ivoirtrips/teambuilding/documents",
)
PUBLIC_CLOUDINARY_FOLDERS = {
    folder.strip().strip("/")
    for folder in os.getenv(
        "PUBLIC_CLOUDINARY_FOLDERS",
        "ivoirtrips/teambuilding/msf,ivoirtrips/teambuilding/canal+",
    ).split(",")
    if folder.strip()
}


def require_upload_access(current_user=Depends(get_current_user)):
    if (
        user_can_access_module(current_user, "production")
        or user_can_access_module(current_user, "tourisme")
        or user_can_access_module(current_user, "teambuilding")
    ):
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image trop lourde (max 10MB)")

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


@router.post("/document")
async def upload_document(file: UploadFile = File(...), current_user=Depends(require_upload_access)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier invalide")

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format document non supporte")

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_DOCUMENT_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type de document non supporte")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document trop lourd (max 10MB)")

    ensure_cloudinary_configured()

    public_id = f"{uuid4().hex}{extension}"
    document_stream = BytesIO(content)
    document_stream.name = filename

    try:
        upload_result = cloudinary.uploader.upload(
            document_stream,
            folder=CLOUDINARY_DOCUMENT_FOLDER,
            public_id=public_id,
            resource_type="raw",
            overwrite=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Impossible d envoyer le document vers Cloudinary",
        ) from exc

    secure_url = upload_result.get("secure_url")
    if not secure_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloudinary n a pas retourne d URL document",
        )

    return {
        "filename": filename,
        "url": secure_url,
        "public_id": upload_result.get("public_id"),
        "resource_type": upload_result.get("resource_type"),
        "size": len(content),
        "content_type": content_type,
    }


@router.get("/cloudinary/random")
def get_random_cloudinary_images(
    folder: str = Query("ivoirtrips/teambuilding/msf", min_length=1),
    limit: int = Query(7, ge=1, le=20),
):
    normalized_folder = folder.strip().strip("/")
    if normalized_folder not in PUBLIC_CLOUDINARY_FOLDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dossier Cloudinary non autorise",
        )

    ensure_cloudinary_configured()

    try:
        result = Search().expression(f'asset_folder="{normalized_folder}"').max_results(500).execute()
        resources = result.get("resources", [])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Impossible de recuperer les images Cloudinary",
        ) from exc

    selected_images = random.sample(resources, min(limit, len(resources))) if resources else []
    images = []
    for item in selected_images:
        public_id = item.get("public_id")
        if not public_id:
            continue

        optimized_url, _ = cloudinary_url(
            public_id,
            secure=True,
            fetch_format="auto",
            quality="auto",
            crop="fill",
            width=1800,
            height=1050,
        )
        images.append(
            {
                "public_id": public_id,
                "url": optimized_url,
                "secure_url": item.get("secure_url"),
                "format": item.get("format"),
                "width": item.get("width"),
                "height": item.get("height"),
            }
        )

    return {"folder": normalized_folder, "count": len(images), "images": images}
