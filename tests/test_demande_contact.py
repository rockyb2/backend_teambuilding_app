import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from crud import demande_contact
from database.models import DemandeContact
from database.schemas import DemandeContactCreate


class DemandeContactTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        DemandeContact.__table__.create(self.engine)
        self.db = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def create(self, name: str, type_demande: str = "autre"):
        return demande_contact.create_demande_contact(
            self.db,
            DemandeContactCreate(
                nom_complet=name,
                email=f"{name.lower()}@example.com",
                telephone="0102030405",
                sujet="Information",
                message="Je souhaite être rappelé.",
                type_demande=type_demande,
                source="site_web",
            ),
        )

    def test_list_filters_and_status_update(self):
        tourism = self.create("Tourisme", "tourisme")
        self.create("Podcast", "podcast")

        demande_contact.update_demande_contact_statut(self.db, tourism, "traitee")

        results = demande_contact.get_demandes_contact(
            self.db,
            statut="traitee",
            type_demande="tourisme",
            source="site_web",
        )
        self.assertEqual([item.id for item in results], [tourism.id])
        self.assertEqual(results[0].statut, "traitee")


if __name__ == "__main__":
    unittest.main()
