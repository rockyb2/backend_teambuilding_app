import unittest
from datetime import date, datetime
from types import SimpleNamespace

from core.env_loader import load_local_env

load_local_env()

from crud.dashboard_admin import _as_datetime, _count_in_month, _offer_month


class AdminDashboardTests(unittest.TestCase):
    def test_offer_month_accepts_plain_created_at_date(self):
        offer = SimpleNamespace(
            date_validation=None,
            created_at=date(2026, 6, 12),
        )

        self.assertEqual(_offer_month(offer), date(2026, 6, 12))

    def test_offer_month_prefers_validation_date(self):
        offer = SimpleNamespace(
            date_validation=date(2026, 6, 20),
            created_at=datetime(2026, 6, 12, 9, 30),
        )

        self.assertEqual(_offer_month(offer), date(2026, 6, 20))

    def test_count_in_month_accepts_date_and_datetime_values(self):
        bucket = {
            "start": date(2026, 6, 1),
            "end": date(2026, 7, 1),
        }

        self.assertEqual(
            _count_in_month(
                [
                    date(2026, 6, 1),
                    datetime(2026, 6, 30, 23, 59),
                    date(2026, 7, 1),
                    None,
                ],
                bucket,
            ),
            2,
        )

    def test_recent_activity_sort_key_accepts_date_and_datetime_values(self):
        values = [
            {"date": date(2026, 6, 10)},
            {"date": datetime(2026, 6, 12, 9, 30)},
            {"date": None},
        ]

        values.sort(key=lambda item: _as_datetime(item["date"]), reverse=True)

        self.assertEqual(values[0]["date"], datetime(2026, 6, 12, 9, 30))
        self.assertEqual(values[1]["date"], date(2026, 6, 10))
        self.assertIsNone(values[2]["date"])


if __name__ == "__main__":
    unittest.main()
