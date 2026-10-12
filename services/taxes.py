from decimal import Decimal, ROUND_HALF_UP

MONEY = Decimal("0.01")

def _hotel_base_ht(sections):
    return sum(
        Decimal(str(line.get("montant_ht") or 0))
        for section in sections or []
        for line in section.get("prestations") or []
        if line.get("prestation_hoteliere") is True
    )


def calculate_taxes(db, selections, base_ht, nombre_chambres, nombre_nuitees, sections=None):
    from database.models import Taxe
    total = Decimal("0")
    details = []
    for selection in selections or []:
        code = selection.get("code") if isinstance(selection, dict) else None
        taxe = db.query(Taxe).filter(Taxe.code == code, Taxe.actif.is_(True)).first() if code else None
        if not taxe:
            continue
        if taxe.type_calcul in {"pourcentage", "pourcentage_lignes"}:
            taxable_base = _hotel_base_ht(sections) if taxe.type_calcul == "pourcentage_lignes" else Decimal(str(base_ht))
            montant = (taxable_base * Decimal(str(taxe.taux or 0)) / 100)
            tarif = None
        else:
            tarif = selection.get("tarif") if isinstance(selection, dict) else None
            if tarif is None and taxe.bareme:
                tarif = taxe.bareme[0].get("amount")
            rooms = int(nombre_chambres or 0)
            nights = int(nombre_nuitees or 0)
            if rooms <= 0 or nights <= 0:
                raise ValueError("La taxe de nuitée exige un nombre de chambres et de nuitées supérieur à zéro.")
            montant = Decimal(str(tarif or 0)) * rooms * nights
        montant = montant.quantize(MONEY, rounding=ROUND_HALF_UP)
        detail = {"id": taxe.id, "code": taxe.code, "nom": taxe.nom, "montant": float(montant)}
        if taxe.type_calcul in {"pourcentage", "pourcentage_lignes"}:
            detail.update({"taux": float(taxe.taux or 0), "base_ht": float(taxable_base)})
        else:
            detail.update({"tarif": float(Decimal(str(tarif or 0))), "nombre_chambres": rooms, "nombre_nuitees": nights})
        details.append(detail)
        total += montant
    return details, total.quantize(MONEY, rounding=ROUND_HALF_UP)


def add_persisted_taxes(totals: dict, data: dict) -> dict:
    """Ajoute aux totaux documentaires les montants fiscaux figés à la création."""
    details = data.get("taxes_selectionnees") or []
    normalized = []
    total_taxes = Decimal("0")
    for detail in details:
        if not isinstance(detail, dict):
            continue
        amount = Decimal(str(detail.get("montant") or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)
        normalized.append({**detail, "montant": amount})
        total_taxes += amount
    result = dict(totals)
    result["taxes_selectionnees"] = normalized
    result["total_taxes"] = total_taxes.quantize(MONEY, rounding=ROUND_HALF_UP)
    result["total_ttc"] = Decimal(str(totals.get("total_ttc") or 0)) + result["total_taxes"]
    return result
