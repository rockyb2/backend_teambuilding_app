import unittest

from sqlalchemy.dialects.postgresql import dialect

from core.env_loader import load_local_env

load_local_env()

from database.models import Site


class SiteJsonbTests(unittest.TestCase):
    def test_nullable_tarifs_bind_none_as_sql_null(self):
        postgres_dialect = dialect()

        for column_name in ("tarifs_restauration", "tarifs_seminaire"):
            column_type = Site.__table__.c[column_name].type
            processor = column_type.bind_processor(postgres_dialect)
            bound_value = processor(None) if processor else None

            self.assertIsNone(bound_value)


if __name__ == "__main__":
    unittest.main()
