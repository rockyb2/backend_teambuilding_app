import unittest
from datetime import date
from types import SimpleNamespace

from core.env_loader import load_local_env

load_local_env()

from crud.dashboard_teambuilding import _activity_readiness, _last_six_months


class TeamBuildingDashboardTests(unittest.TestCase):
    def test_last_six_months_crosses_year_boundary(self):
        months = _last_six_months(date(2026, 2, 10))

        self.assertEqual([item["key"] for item in months], [
            "2025-09",
            "2025-10",
            "2025-11",
            "2025-12",
            "2026-01",
            "2026-02",
        ])

    def test_activity_readiness_lists_missing_resources(self):
        activity = SimpleNamespace(
            responsable_id=None,
            activite_jeux=[],
            activite_materiels=[],
        )

        readiness, missing = _activity_readiness(activity)

        self.assertEqual(readiness, "À compléter")
        self.assertEqual(missing, ["responsable", "jeu", "matériel"])

    def test_activity_is_ready_when_all_resources_are_present(self):
        activity = SimpleNamespace(
            responsable_id=7,
            activite_jeux=[object()],
            activite_materiels=[object()],
        )

        readiness, missing = _activity_readiness(activity)

        self.assertEqual(readiness, "Prête")
        self.assertEqual(missing, [])

    def test_month_labels_are_in_french(self):
        months = _last_six_months(date(2026, 8, 10))

        self.assertEqual(months[-1]["label"], "Août")


if __name__ == "__main__":
    unittest.main()
