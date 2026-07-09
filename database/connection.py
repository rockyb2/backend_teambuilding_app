import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from database.base import Base

# DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

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

OFFRE_STATUSES = (
    "brouillon",
    "envoyee",
    "validee",
    "refusee",
    "expiree",
    "annulee",
)

DEMANDE_TOURISME_STATUSES = (
    "nouvelle",
    "contactee",
    "en_traitement",
    "devis_envoye",
    "en_attente_reponse_client",
    "relance_envoyee",
    "validee",
    "annulee",
    "refusee",
    "terminee",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _synchronize_offre_status_constraint(connection):
    if connection.dialect.name != "postgresql":
        return

    constraint_definition = connection.execute(
        text(
            """
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'public.offre'::regclass
              AND conname = 'ck_offre_statut'
            """
        )
    ).scalar()

    if constraint_definition and all(
        f"'{status}'" in constraint_definition for status in OFFRE_STATUSES
    ):
        return

    # Convertit les anciennes valeurs masculines avant de remplacer la contrainte.
    connection.execute(
        text(
            """
            UPDATE public.offre
            SET statut = CASE statut
                WHEN 'envoye' THEN 'envoyee'
                WHEN 'valide' THEN 'validee'
                WHEN 'refuse' THEN 'refusee'
                WHEN 'expire' THEN 'expiree'
                WHEN 'annule' THEN 'annulee'
                ELSE statut
            END
            WHERE statut IN ('envoye', 'valide', 'refuse', 'expire', 'annule')
            """
        )
    )
    connection.execute(
        text("ALTER TABLE public.offre DROP CONSTRAINT IF EXISTS ck_offre_statut")
    )
    connection.execute(
        text(
            """
            ALTER TABLE public.offre
            ADD CONSTRAINT ck_offre_statut
            CHECK (
                statut IN (
                    'brouillon',
                    'envoyee',
                    'validee',
                    'refusee',
                    'expiree',
                    'annulee'
                )
            )
            """
        )
    )


def _synchronize_demande_tourisme_status_constraints(connection):
    if connection.dialect.name != "postgresql":
        return

    statuses_sql = ", ".join(f"'{status}'" for status in DEMANDE_TOURISME_STATUSES)
    constraints = (
        ("demandes_tourisme", "ck_demandes_tourisme_statut", "statut"),
        ("demandes_tourisme_custom", "ck_demandes_tourisme_custom_statut", "statut"),
        (
            "historique_statut_demandes_tourisme",
            "ck_historique_statut_demande_tourisme_nouveau_statut",
            "nouveau_statut",
        ),
    )

    for table_name, constraint_name, column_name in constraints:
        constraint_definition = connection.execute(
            text(
                """
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = CAST(:table_name AS regclass)
                  AND conname = :constraint_name
                """
            ),
            {
                "table_name": f"public.{table_name}",
                "constraint_name": constraint_name,
            },
        ).scalar()
        if constraint_definition and all(
            f"'{status}'" in constraint_definition
            for status in DEMANDE_TOURISME_STATUSES
        ):
            continue

        connection.execute(
            text(
                f'ALTER TABLE "{table_name}" '
                f'DROP CONSTRAINT IF EXISTS "{constraint_name}"'
            )
        )
        connection.execute(
            text(
                f'ALTER TABLE "{table_name}" '
                f'ADD CONSTRAINT "{constraint_name}" '
                f"CHECK ({column_name} IN ({statuses_sql}))"
            )
        )


def _synchronize_proforma_constraints(connection):
    if connection.dialect.name != "postgresql":
        return

    connection.execute(
        text(
            """
            UPDATE public.proformas
            SET pole = 'teambuilding'
            WHERE pole IS NULL
            """
        )
    )

    constraint_definition = connection.execute(
        text(
            """
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'public.proformas'::regclass
              AND conname = 'ck_proformas_pole'
            """
        )
    ).scalar()
    if constraint_definition and "'teambuilding'" in constraint_definition and "'tourisme'" in constraint_definition:
        return

    connection.execute(text("ALTER TABLE public.proformas DROP CONSTRAINT IF EXISTS ck_proformas_pole"))
    connection.execute(
        text(
            """
            ALTER TABLE public.proformas
            ADD CONSTRAINT ck_proformas_pole
            CHECK (pole IN ('teambuilding', 'tourisme'))
            """
        )
    )


def _synchronize_depense_constraints(connection):
    if connection.dialect.name != "postgresql":
        return

    connection.execute(
        text(
            """
            UPDATE public.depense
            SET pole = 'teambuilding'
            WHERE pole IS NULL
            """
        )
    )
    connection.execute(text("ALTER TABLE public.depense ALTER COLUMN activite_id DROP NOT NULL"))
    connection.execute(text("ALTER TABLE public.depense DROP CONSTRAINT IF EXISTS ck_depense_pole"))
    connection.execute(
        text(
            """
            ALTER TABLE public.depense
            ADD CONSTRAINT ck_depense_pole
            CHECK (pole IN ('teambuilding', 'tourisme', 'production'))
            """
        )
    )
    connection.execute(text("ALTER TABLE public.depense DROP CONSTRAINT IF EXISTS depense_activite_id_fkey"))
    connection.execute(
        text(
            """
            ALTER TABLE public.depense
            ADD CONSTRAINT depense_activite_id_fkey
            FOREIGN KEY (activite_id) REFERENCES public.activite(id) ON DELETE SET NULL
            """
        )
    )
    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_depense_pole ON public.depense (pole)"))
    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_depense_proforma_id ON public.depense (proforma_id)"))
    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_depense_facture_id ON public.depense (facture_id)"))
    connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_depense_demande_team_building_id "
            "ON public.depense (demande_team_building_id)"
        )
    )
    connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_depense_demande_tourisme_id "
            "ON public.depense (demande_tourisme_id)"
        )
    )
    connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_depense_demande_tourisme_custom_id "
            "ON public.depense (demande_tourisme_custom_id)"
        )
    )


def create_tables():
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # This project does not use Alembic yet. Keep existing deployments compatible
    # when small nullable audit columns are introduced.
    required_columns = {
        "utilisateur": {
            "derniere_connexion": "TIMESTAMP WITH TIME ZONE NULL",
        },
        "demandes_team_building": {
            "statut_modifie_le": "TIMESTAMP WITH TIME ZONE NULL",
            "statut_modifie_par_id": (
                "INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL"
            ),
            "created_by_id": (
                "INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL"
            ),
        },
        "demandes_tourisme": {
            "created_by_id": (
                "INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL"
            ),
        },
        "proformas": {
            "pole": "VARCHAR(30) NOT NULL DEFAULT 'teambuilding'",
            "demande_tourisme_id": (
                "INTEGER NULL REFERENCES demandes_tourisme(id) ON DELETE SET NULL"
            ),
            "demande_tourisme_custom_id": (
                "INTEGER NULL REFERENCES demandes_tourisme_custom(id) ON DELETE SET NULL"
            ),
            "offre_tourisme_id": (
                "INTEGER NULL REFERENCES offre_tourisme(id) ON DELETE SET NULL"
            ),
        },
        "materiel": {
            "marque": "VARCHAR(100) NULL",
            "modele": "VARCHAR(150) NULL",
        },
        "depense": {
            "pole": "VARCHAR(30) NOT NULL DEFAULT 'teambuilding'",
            "proforma_id": (
                "INTEGER NULL REFERENCES proformas(id) ON DELETE SET NULL"
            ),
            "facture_id": (
                "INTEGER NULL REFERENCES facture(id) ON DELETE SET NULL"
            ),
            "demande_team_building_id": (
                "INTEGER NULL REFERENCES demandes_team_building(id) ON DELETE SET NULL"
            ),
            "demande_tourisme_id": (
                "INTEGER NULL REFERENCES demandes_tourisme(id) ON DELETE SET NULL"
            ),
            "demande_tourisme_custom_id": (
                "INTEGER NULL REFERENCES demandes_tourisme_custom(id) ON DELETE SET NULL"
            ),
        },
    }

    with engine.begin() as connection:
        inspector = inspect(connection)
        for table_name, columns in required_columns.items():
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, definition in columns.items():
                if column_name in existing_columns:
                    continue
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN {column_name} {definition}"
                    )
                )

        _synchronize_offre_status_constraint(connection)
        _synchronize_demande_tourisme_status_constraints(connection)
        _synchronize_proforma_constraints(connection)
        _synchronize_depense_constraints(connection)
