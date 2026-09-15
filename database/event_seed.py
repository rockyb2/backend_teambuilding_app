from datetime import date
import json
from pathlib import Path

from sqlalchemy import select

from database.event_models import Event, InscriptionEvent

EVENT_TABLES = [Event.__table__, InscriptionEvent.__table__]


def initialize_events(engine):
    """Crée les tables simples et ajoute les événements absents."""
    rows = json.loads((Path(__file__).parent / 'seeds' / 'events_2026.json').read_text(encoding='utf-8'))
    with engine.begin() as connection:
        Event.metadata.create_all(bind=connection, tables=EVENT_TABLES)
        for row in rows:
            row['date'] = date.fromisoformat(row['date']) if row['date'] else None
            exists = connection.scalar(select(Event.id).where(Event.titre == row['titre'], Event.date == row['date']))
            if exists is None:
                connection.execute(Event.__table__.insert().values(**row))