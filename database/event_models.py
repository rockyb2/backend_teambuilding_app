from sqlalchemy import CheckConstraint, Column, Date, DateTime, Integer, Numeric, String, Text, func

from database.base import Base


class Event(Base):
    __tablename__ = 'events'
    __table_args__ = (CheckConstraint('tarif IS NULL OR tarif >= 0', name='ck_events_tarif'),)

    id = Column(Integer, primary_key=True)
    titre = Column(String(255), nullable=False)
    date = Column(Date, nullable=True)
    lieu = Column(String(500), nullable=True)
    tarif = Column(Numeric(12, 2), nullable=True)
    description = Column(Text, nullable=True)


class InscriptionEvent(Base):
    __tablename__ = 'inscriptions_event'
    __table_args__ = (CheckConstraint('nombre_participants > 0', name='ck_inscriptions_event_count'),)

    id = Column(Integer, primary_key=True)
    evenement = Column(String(255), nullable=False)
    prenom = Column(String(120), nullable=False)
    nom = Column(String(120), nullable=False)
    telephone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=True)
    nombre_participants = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
    date_inscription = Column(DateTime, nullable=False, server_default=func.now())