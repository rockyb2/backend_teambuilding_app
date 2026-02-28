from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from database.connection import create_tables
from database import schemas, models
from api import include_api_routes

app = FastAPI(
    title="Team Building Management API",
    description="API pour la gestion des activités de team building",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://localhost:3000",
]
,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer les tables au démarrage
create_tables()

# Inclure toutes les routes API
include_api_routes(app)

uploads_dir = Path(__file__).resolve().parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")





@app.get("/")
def read_root():
    """Endpoint racine"""
    return {
        "message": "Bienvenue sur l'API du Team Building Management",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health")
def health_check():
    """Vérifier l'état de l'API"""
    return {"status": "ok"}
