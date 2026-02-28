"""
Dépendances communes pour les routes API
"""

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from database.connection import SessionLocal


def get_db():
    """Dépendance pour obtenir une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
