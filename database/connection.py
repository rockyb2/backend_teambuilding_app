import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.base import Base

# DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL ="postgresql+psycopg2://postgres:NouveauMotDePasse@localhost:5432/teambuilding"

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Configuration SSL conditionnelle
connect_args = {}
if "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL:
    # Pour les connexions locales, désactiver SSL
    connect_args = {"sslmode": "disable"}
else:
    # Pour les environnements de production (comme Render), garder SSL
    connect_args = {"sslmode": "require"}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
