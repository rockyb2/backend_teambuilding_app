import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.base import Base


DATABASE_URL ="postgresql+psycopg2://postgres:NouveauMotDePasse@localhost:5432/teambuilding"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
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
