"""Initialisation des événements et migration explicite vers les inscriptions simples."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.env_loader import load_local_env

load_local_env()

from sqlalchemy import inspect, select, func, text
from database.connection import engine
from database.event_seed import EVENT_TABLES, initialize_events

parser = argparse.ArgumentParser()
parser.add_argument('--check', action='store_true', help='Vérifier la cible et les tables sans écrire')
parser.add_argument('--simplify', action='store_true', help='Appliquer la simplification validée des anciennes tables événements')
args = parser.parse_args()
print(f"Database: {engine.url.host or 'local'} / {engine.url.database or 'memory'}")
if not args.check:
    if args.simplify:
        migration = Path(__file__).resolve().parents[1] / 'database/sql/2026_09_14_simplify_event_inscriptions.sql'
        with engine.begin() as connection:
            connection.execute(text(migration.read_text(encoding='utf-8')))
    initialize_events(engine)
inspector = inspect(engine)
with engine.connect() as connection:
    for table in EVENT_TABLES:
        if inspector.has_table(table.name):
            count = connection.scalar(select(func.count()).select_from(table))
            print(f'{table.name}: {count} row(s)')
            print('Columns: ' + ', '.join(column['name'] for column in inspector.get_columns(table.name)))
        else:
            print(f'{table.name}: missing')
    print('participants_event exists: ' + str(inspector.has_table('participants_event')))
