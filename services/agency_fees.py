from decimal import Decimal
from typing import Any


AGENCY_FEE_RATE = Decimal("0.175")


def resolve_agency_fee_rate(mode: str | None, legacy_rate: Any = None) -> Any:
    if mode == "pourcentage":
        return legacy_rate if legacy_rate is not None else AGENCY_FEE_RATE
    if mode == "montant":
        return None
    if mode is None:
        return legacy_rate
    raise ValueError("Le mode de frais d'agence doit être 'pourcentage' ou 'montant'.")
