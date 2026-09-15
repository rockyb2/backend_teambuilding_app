import os
import unittest

os.environ.setdefault('DATABASE_URL', 'sqlite://')

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.events.routes import router, get_db
from database.event_models import Event, InscriptionEvent
from database.event_seed import EVENT_TABLES, initialize_events


class EventRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Event.metadata.create_all(self.engine, tables=EVENT_TABLES)
        self.sessions = sessionmaker(bind=self.engine)

        def isolated_db():
            with self.sessions() as db:
                yield db

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = isolated_db
        self.client = TestClient(app)
        self.payload = {
            'evenement': 'Ajoupa Green Lodge', 'prenom': 'Marie', 'nom': 'Kouassi',
            'telephone': '+225 07 00 00 00 00', 'nombre_participants': 2, 'note': 'Départ à préciser',
        }

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_simple_contact_saved_without_event_lookup_or_email(self):
        response = self.client.post('/api/events/inscriptions', json=self.payload)
        self.assertEqual(response.status_code, 201, response.text)
        with self.sessions() as db:
            self.assertEqual(db.query(Event).count(), 0)
            row = db.get(InscriptionEvent, response.json()['id'])
            self.assertEqual(row.evenement, 'Ajoupa Green Lodge')
            self.assertEqual(row.prenom, 'Marie')
            self.assertEqual(row.nombre_participants, 2)
            self.assertIsNone(row.email)
            self.assertIsNotNone(row.date_inscription)
            self.assertEqual(db.query(InscriptionEvent).count(), 1)

    def test_email_is_optional_but_checked_when_present(self):
        for email, status in [('', 201), ('   ', 201), (None, 201), ('marie@example.com', 201), ('invalide', 422)]:
            with self.subTest(email=email):
                response = self.client.post('/api/events/inscriptions', json={**self.payload, 'email': email})
                self.assertEqual(response.status_code, status, response.text)

    def test_incomplete_contact_or_invalid_count_cannot_be_saved(self):
        for key, value in [('prenom', '  '), ('nom', ''), ('telephone', '123'), ('nombre_participants', 0), ('nombre_participants', 1.5), ('evenement', '')]:
            with self.subTest(field=key, value=value):
                response = self.client.post('/api/events/inscriptions', json={**self.payload, key: value})
                self.assertEqual(response.status_code, 422)
        with self.sessions() as db:
            self.assertEqual(db.query(InscriptionEvent).count(), 0)

    def test_schema_has_only_approved_columns_and_no_foreign_key(self):
        inspector = inspect(self.engine)
        self.assertEqual(set(inspector.get_table_names()), {'events', 'inscriptions_event'})
        self.assertEqual(set(Event.__table__.columns.keys()), {'id', 'titre', 'date', 'lieu', 'tarif', 'description'})
        self.assertEqual(set(InscriptionEvent.__table__.columns.keys()), {'id', 'evenement', 'prenom', 'nom', 'telephone', 'email', 'nombre_participants', 'note', 'date_inscription'})
        self.assertEqual(inspector.get_foreign_keys('inscriptions_event'), [])

    def test_contact_list_remains_private(self):
        self.client.post('/api/events/inscriptions', json=self.payload)
        self.assertIn(self.client.get('/api/events/inscriptions').status_code, [401, 403])
        self.assertEqual(self.client.get('/api/events/public').json(), [])

    def test_initialization_does_not_duplicate_or_overwrite_events(self):
        initialize_events(self.engine)
        with self.sessions() as db:
            db.query(Event).filter_by(titre='Ajoupa Green Lodge').one().tarif = 42000
            db.commit()
        initialize_events(self.engine)
        with self.sessions() as db:
            self.assertEqual(db.query(Event).count(), 7)
            self.assertEqual(db.query(Event).filter_by(titre='Ajoupa Green Lodge').one().tarif, 42000)


if __name__ == '__main__':
    unittest.main()