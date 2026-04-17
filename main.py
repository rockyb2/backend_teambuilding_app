import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.env_loader import load_local_env

load_local_env()

from api import include_api_routes
from database import models, schemas
from database.connection import create_tables


def get_allowed_origins() -> list[str]:
    cors_origins = os.getenv("CORS_ORIGINS", "").strip()
    if cors_origins:
        return [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

    return [
        "*",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://localhost:3000",
    ]


allowed_origins = get_allowed_origins()

app = FastAPI(
    title="Team Building Management API",
    description="API pour la gestion des activites de team building",
    version="1.0.0",
)

# Configure CORS for local development and Render deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials="*" not in allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Creer les tables au demarrage.
create_tables()

# Inclure toutes les routes API.
include_api_routes(app)

uploads_dir = Path(__file__).resolve().parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/")
def read_root():
    """Endpoint racine."""
    return {
        "message": "Bienvenue sur l'API du Team Building Management",
        "version": "1.0.0",
        "documentation": "/docs",
    }


@app.get("/health")
def health_check():
    """Verifier l'etat de l'API."""
    return {"status": "ok"}
