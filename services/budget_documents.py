from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils.cell import quote_sheetname
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from services.agency_fees import resolve_agency_fee_rate


BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "assets" / "proforma"
DEFAULT_OUTPUT_DIR = BASE_DIR / "uploads" / "budgets"


def _decimal(value: Any, field_name: str = "montant") -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    if isinstance(value, str):
        value = (
            value.upper()
            .replace("F CFA", "")
            .replace("FCFA", "")
            .replace("XOF", "")
            .replace("\u202f", "")
            .replace(" ", "")
            .replace(",", ".")
        )
    try:
        amount = Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} doit être un nombre valide.") from exc
    if amount < 0:
        raise ValueError(f"{field_name} ne peut pas être négatif.")
    return amount


def _quantity(value: Any, field_name: str = "quantité") -> Decimal:
    if value in (None, ""):
        return Decimal("1")
    try:
        quantity = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} doit être un nombre valide.") from exc
    if quantity < 0:
        raise ValueError(f"{field_name} ne peut pas être négative.")
    return quantity


def _format_quantity(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        decimal_value = Decimal(str(value))
    except InvalidOperation:
        return str(value)
    return format(decimal_value.normalize(), "f")


def _format_fcfa(value: Any) -> str:
    amount = int(_decimal(value))
    return f"{amount:,}".replace(",", " ") + " F CFA"


def _display_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).strftime("%d/%m/%Y")
        except ValueError:
            return value
    return str(value or "")


def _excel_number(value: Any, default: int | float = 0) -> int | float:
    if value in (None, ""):
        return default
    if isinstance(value, str):
        value = (
            value.upper()
            .replace("F CFA", "")
            .replace("FCFA", "")
            .replace("XOF", "")
            .replace("\u202f", "")
            .replace(" ", "")
            .replace(",", ".")
        )
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return default
    if number == number.to_integral_value():
        return int(number)
    return float(number)


def _safe_sheet_title(value: Any, fallback: str = "Budget estimatif") -> str:
    title = str(value or fallback).strip() or fallback
    for forbidden in ("\\", "/", "?", "*", "[", "]", ":"):
        title = title.replace(forbidden, " ")
    title = " ".join(title.split()).strip("'")
    return title[:31] or fallback[:31]


def _budget_location(data: dict[str, Any]) -> str:
    location = (
        data.get("lieu")
        or data.get("site_localisation")
        or data.get("site_nom")
        or data.get("destination")
        or "-"
    )
    return str(location)


def _budget_nights(data: dict[str, Any]) -> int:
    explicit_value = data.get("nombre_nuitees", data.get("nuits"))
    if explicit_value not in (None, ""):
        return int(_excel_number(explicit_value, 0))
    days = int(_excel_number(data.get("duree_jours"), 1) or 1)
    return max(days - 1, 0)


def _budget_notes(data: dict[str, Any]) -> list[str]:
    notes = str(data.get("notes") or "").strip()
    if notes:
        return [line.strip() for line in notes.splitlines() if line.strip()]
    return [
        "Jus/Sucrerie : 2 canettes par personne",
        "Bière : 2 bouteilles par personne",
        "Vin : 1 bouteille pour 4 personnes",
    ]


def _safe_document_path(reference: str, extension: str, output_dir: str | Path | None = None) -> Path:
    clean_reference = "".join(
        char for char in str(reference or "budget") if char.isalnum() or char in ("-", "_")
    ).strip("-_")
    if not clean_reference:
        clean_reference = "budget"
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return (directory / f"{clean_reference}.{extension.lstrip('.')}").resolve()


def _first_existing_asset(*filenames: str) -> Path | None:
    for filename in filenames:
        path = ASSETS_DIR / filename
        if path.exists():
            return path
    return None


def _image_dimensions(path: Path, max_width: float, max_height: float) -> tuple[float, float]:
    image_width, image_height = ImageReader(str(path)).getSize()
    if not image_width or not image_height:
        return max_width, max_height
    scale = min(max_width / image_width, max_height / image_height)
    return image_width * scale, image_height * scale


def _paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(text or "")), style)


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "normal": ParagraphStyle(
            "NormalBudget",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10.2,
            alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "SmallBudget",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=7.4,
            leading=9,
        ),
        "title": ParagraphStyle(
            "TitleBudget",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            alignment=TA_CENTER,
        ),
        "center": ParagraphStyle(
            "CenterBudget",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "SectionBudget",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=10,
        ),
        "right": ParagraphStyle(
            "RightBudget",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_RIGHT,
        ),
        "right_bold": ParagraphStyle(
            "RightBoldBudget",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=10,
            alignment=TA_RIGHT,
        ),
    }


def normalize_budget_sections(sections: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Decimal]:
    normalized_sections: list[dict[str, Any]] = []
    implementation_total = Decimal("0")

    for section_index, section in enumerate(sections or [], start=1):
        if not isinstance(section, dict):
            raise ValueError(f"La section {section_index} doit être un dictionnaire.")

        section_name = str(section.get("nom") or section.get("name") or "Prestations").strip()
        items = section.get("prestations") or section.get("lignes") or []
        if not isinstance(items, list):
            raise ValueError(f"Les lignes de la section '{section_name}' doivent former une liste.")

        normalized_items: list[dict[str, Any]] = []
        section_total = Decimal("0")
        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"La ligne {item_index} de la section '{section_name}' doit être un dictionnaire."
                )

            designation = str(item.get("designation") or item.get("libelle") or "").strip()
            if not designation:
                continue

            days = _quantity(item.get("nombre_jours", item.get("duree_jours", 1)), "nombre_jours")
            quantity = _quantity(item.get("quantite", 1), "quantite")
            unit_price = _decimal(item.get("prix_unitaire"), "prix_unitaire")
            explicit_amount = item.get("montant_ht")

            if explicit_amount not in (None, ""):
                line_total = _decimal(explicit_amount, "montant_ht")
            else:
                line_total = (days * quantity * unit_price).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

            normalized_items.append(
                {
                    "designation": designation,
                    "nombre_jours": _format_quantity(days),
                    "quantite": _format_quantity(quantity),
                    "prix_unitaire": int(unit_price),
                    "montant_ht": int(line_total),
                    "source": str(item.get("source") or "").strip(),
                }
            )
            section_total += line_total

        if normalized_items:
            normalized_sections.append(
                {
                    "nom": section_name,
                    "prestations": normalized_items,
                    "sous_total": int(section_total),
                }
            )
            implementation_total += section_total

    return normalized_sections, implementation_total


def calculate_budget_totals(
    sections: list[dict[str, Any]],
    frais_agence: Any = 0,
    taux_tva_frais_agence: Any = 0,
    mode_frais_agence: str = "montant",
) -> dict[str, Any]:
    normalized_sections, implementation_total = normalize_budget_sections(sections)
    agency_rate = resolve_agency_fee_rate(mode_frais_agence)
    agency_fees = (
        (implementation_total * agency_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if agency_rate is not None else _decimal(frais_agence, "frais_agence")
    )
    try:
        vat_rate = Decimal(str(taux_tva_frais_agence or 0).replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Le taux de TVA doit être un nombre valide.") from exc
    if vat_rate < 0:
        raise ValueError("Le taux de TVA ne peut pas être négatif.")

    vat = (agency_fees * vat_rate / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    total_ht = implementation_total + agency_fees
    total = total_ht + vat
    return {
        "sections": normalized_sections,
        "sous_total_ht": implementation_total,
        "frais_agence": agency_fees,
        "mode_frais_agence": mode_frais_agence,
        "taux_tva_frais_agence": vat_rate,
        "tva_frais_agence": vat,
        "total_ht": total_ht,
        "total_ttc": total,
    }


def _draw_page(canvas: Any, document: Any) -> None:
    canvas.saveState()
    width, height = landscape(A4)
    logo_path = _first_existing_asset("logo.png")
    if logo_path:
        canvas.drawImage(
            str(logo_path),
            18 * mm,
            height - 25 * mm,
            width=42 * mm,
            height=16 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawCentredString(width / 2, 10 * mm, "Ivoir Trips International - Budget estimatif")
    canvas.restoreState()


def generate_budget_pdf(data: dict[str, Any], output_dir: str | Path | None = None) -> str:
    required_fields = ("reference", "client", "nombre_personnes", "date_budget", "titre")
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValueError(f"Champs obligatoires manquants: {', '.join(missing)}")
    if int(data.get("nombre_personnes") or 0) <= 0:
        raise ValueError("nombre_personnes doit être supérieur à zéro.")

    totals = calculate_budget_totals(
        data.get("sections") or [],
        data.get("frais_agence") or 0,
        data.get("taux_tva_frais_agence") or 0,
        data.get("mode_frais_agence") or "montant",
    )
    sections = totals["sections"]
    if not sections:
        raise ValueError("Le budget doit contenir au moins une ligne.")

    reference = str(data["reference"]).strip()
    output_path = _safe_document_path(reference, "pdf", output_dir)
    styles = _styles()

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=31 * mm,
        bottomMargin=16 * mm,
        title=f"Budget estimatif {reference}",
        author="Ivoir Trips International",
    )
    story: list[Any] = []
    story.append(_paragraph("BUDGET ESTIMATIF", styles["title"]))
    story.append(Spacer(1, 4 * mm))

    header_rows = [
        [
            _paragraph(f"Référence: {reference}", styles["normal"]),
            _paragraph(f"Client: {data['client']}", styles["right_bold"]),
        ],
        [
            _paragraph(f"Objet: {data['titre']}", styles["normal"]),
            _paragraph(f"Date: {_display_date(data['date_budget'])}", styles["right"]),
        ],
        [
            _paragraph(f"Participants: {data['nombre_personnes']}", styles["normal"]),
            _paragraph(f"Événement: {_display_date(data.get('date_evenement')) or '-'}", styles["right"]),
        ],
    ]
    header_table = Table(header_rows, colWidths=[128 * mm, 128 * mm])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    rows: list[list[Any]] = [
        [
            _paragraph("Désignation", styles["center"]),
            _paragraph("Jours", styles["center"]),
            _paragraph("Qté", styles["center"]),
            _paragraph("Prix unitaire", styles["center"]),
            _paragraph("Montant HT", styles["center"]),
        ]
    ]
    table_commands: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF1E6")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]

    for section in sections:
        section_row = len(rows)
        rows.append([_paragraph(section["nom"].upper(), styles["section"]), "", "", "", ""])
        table_commands.append(("SPAN", (0, section_row), (-1, section_row)))
        table_commands.append(("BACKGROUND", (0, section_row), (-1, section_row), colors.HexColor("#ECFDF5")))

        for item in section["prestations"]:
            rows.append(
                [
                    _paragraph(item["designation"], styles["normal"]),
                    _paragraph(_format_quantity(item.get("nombre_jours")), styles["right"]),
                    _paragraph(_format_quantity(item.get("quantite")), styles["right"]),
                    _paragraph(_format_fcfa(item.get("prix_unitaire")), styles["right"]),
                    _paragraph(_format_fcfa(item.get("montant_ht")), styles["right"]),
                ]
            )

        subtotal_row = len(rows)
        rows.append(
            [
                _paragraph(f"Sous-total {section['nom']}", styles["section"]),
                "",
                "",
                "",
                _paragraph(_format_fcfa(section["sous_total"]), styles["right_bold"]),
            ]
        )
        table_commands.extend(
            [
                ("BACKGROUND", (0, subtotal_row), (-1, subtotal_row), colors.HexColor("#F8FAFC")),
                ("SPAN", (0, subtotal_row), (3, subtotal_row)),
            ]
        )

    summary_rows = [
        ("Sous-total prestations", totals["sous_total_ht"]),
        ("Frais d'agence (17,5 %)" if totals["mode_frais_agence"] == "pourcentage" else "Frais d'agence", totals["frais_agence"]),
        (f"TVA frais d'agence {format(totals['taux_tva_frais_agence'].normalize(), 'f')}%", totals["tva_frais_agence"]),
        ("Total estimatif", totals["total_ttc"]),
    ]
    for label, value in summary_rows:
        row_index = len(rows)
        rows.append(["", "", "", _paragraph(label, styles["section"]), _paragraph(_format_fcfa(value), styles["right_bold"])])
        table_commands.append(("SPAN", (0, row_index), (2, row_index)))
        if label == "Total estimatif":
            table_commands.append(("BACKGROUND", (3, row_index), (4, row_index), colors.HexColor("#FFEDD5")))

    budget_table = Table(
        rows,
        colWidths=[153 * mm, 20 * mm, 20 * mm, 33 * mm, 36 * mm],
        repeatRows=1,
        hAlign="CENTER",
    )
    budget_table.setStyle(TableStyle(table_commands))
    story.append(budget_table)

    notes = str(data.get("notes") or "").strip()
    if notes:
        story.append(Spacer(1, 4 * mm))
        story.append(_paragraph(f"Notes: {notes}", styles["small"]))

    document.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return str(output_path)


def _append_budget_sheet(workbook: Workbook, data: dict[str, Any]) -> dict[str, Any]:
    required_fields = ("reference", "client", "nombre_personnes", "date_budget", "titre")
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValueError(f"Champs obligatoires manquants: {', '.join(missing)}")

    totals = calculate_budget_totals(
        data.get("sections") or [],
        data.get("frais_agence") or 0,
        data.get("taux_tva_frais_agence") or 0,
        data.get("mode_frais_agence") or "montant",
    )
    sections = totals["sections"]
    if not sections:
        raise ValueError("Le budget doit contenir au moins une ligne.")

    base_title = _safe_sheet_title(data.get("site_nom") or data.get("titre") or "Budget")
    title = base_title
    suffix = 2
    while title.casefold() in {name.casefold() for name in workbook.sheetnames}:
        marker = f" ({suffix})"
        title = base_title[:31 - len(marker)] + marker
        suffix += 1
    sheet = workbook.create_sheet(title)
    sheet.sheet_view.showGridLines = False

    try:
        workbook.calculation.fullCalcOnLoad = True
        workbook.calculation.forceFullCalc = True
    except AttributeError:
        pass

    font_name = "Agency FB"
    orange_fill = PatternFill("solid", fgColor="FFF1E6")
    green_fill = PatternFill("solid", fgColor="EAF7F0")
    total_fill = PatternFill("solid", fgColor="FFFF00")
    dark_fill = PatternFill("solid", fgColor="0F172A")
    thin_side = Side(style="thin", color="CBD5E1")
    medium_side = Side(style="medium", color="0F172A")
    regular_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    strong_top_border = Border(top=medium_side, bottom=thin_side, left=thin_side, right=thin_side)
    title_font = Font(name=font_name, bold=True, size=18, color="0F172A")
    subtitle_font = Font(name=font_name, bold=True, size=16, color="0F172A")
    header_font = Font(name=font_name, bold=True, size=13, color="0F172A")
    body_font = Font(name=font_name, size=12, color="0F172A")
    body_bold = Font(name=font_name, bold=True, size=12, color="0F172A")
    white_bold = Font(name=font_name, bold=True, size=12, color="FFFFFF")
    money_format = '#,##0 "FCFA"'

    sheet.column_dimensions["A"].width = 3
    sheet.column_dimensions["B"].width = 58
    sheet.column_dimensions["C"].width = 14
    sheet.column_dimensions["D"].width = 17
    sheet.column_dimensions["E"].width = 17
    sheet.column_dimensions["F"].width = 20
    sheet.column_dimensions["G"].width = 3
    for row_index in range(1, 6):
        sheet.row_dimensions[row_index].height = 12
    sheet.row_dimensions[6].height = 42

    logo_path = _first_existing_asset("logo.png")
    if logo_path:
        try:
            logo = ExcelImage(str(logo_path))
            logo.width = 185
            logo.height = 65
            sheet.add_image(logo, "B2")
        except Exception:
            pass

    sheet["D7"] = "BUDGET ESTIMATIF"
    sheet["D8"] = "SÉMINAIRE TEAM BUILDING"
    for cell_ref, font in (("D7", title_font), ("D8", subtitle_font)):
        cell = sheet[cell_ref]
        cell.font = font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    sheet.row_dimensions[7].height = 30
    sheet.row_dimensions[8].height = 26

    days = int(_excel_number(data.get("duree_jours"), 1) or 1)
    participants = int(_excel_number(data.get("nombre_personnes"), 1) or 1)
    header_values = {
        "B9": "DATE :",
        "C9": _display_date(data["date_budget"]),
        "E9": "LIEU :",
        "F9": _budget_location(data),
        "B10": "CLIENT :",
        "C10": str(data["client"]).upper(),
        "D10": "DURÉE",
        "E10": "JOUR(S) :",
        "F10": days,
        "B11": "NOMBRE DE PARTICIPANTS :",
        "C11": participants,
        "E11": "NUIT(S) :",
        "F11": _budget_nights(data),
    }
    for cell_ref, value in header_values.items():
        cell = sheet[cell_ref]
        cell.value = value
        cell.font = body_bold
        cell.alignment = Alignment(
            horizontal="center" if cell_ref[0] in {"C", "F"} else "left",
            vertical="center",
            wrap_text=True,
        )
    sheet["D10"].alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
    for row_index in (9, 10, 11):
        sheet.row_dimensions[row_index].height = 22
    for row_index in (12, 13, 14):
        sheet.row_dimensions[row_index].height = 8

    header_row = 15
    headers = {
        "B": "Désignation",
        "C": "Quantité",
        "D": "Coût unitaire",
        "E": "Nombre de jours",
        "F": "Coût total",
    }
    for column, label in headers.items():
        cell = sheet[f"{column}{header_row}"]
        cell.value = label
        cell.font = header_font
        cell.fill = orange_fill
        cell.border = regular_border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    sheet.row_dimensions[header_row].height = 25

    current_row = header_row + 1
    subtotal_rows: list[int] = []
    for section in sections:
        section_name = str(section["nom"]).upper()
        sheet.cell(row=current_row, column=2, value=section_name)
        for column_index in range(2, 7):
            cell = sheet.cell(row=current_row, column=column_index)
            cell.font = white_bold
            cell.fill = dark_fill
            cell.border = regular_border
            cell.alignment = Alignment(
                horizontal="centerContinuous" if column_index == 2 else "center",
                vertical="center",
                wrap_text=True,
            )
        sheet.row_dimensions[current_row].height = 23
        current_row += 1

        first_line_row = current_row
        for item in section["prestations"]:
            quantity = _excel_number(item.get("quantite"), 1)
            unit_price = _excel_number(item.get("prix_unitaire"), 0)
            item_days = _excel_number(item.get("nombre_jours"), 1)
            line_amount = int(_excel_number(item.get("montant_ht"), 0))

            sheet.cell(row=current_row, column=2, value=item["designation"])
            sheet.cell(row=current_row, column=3, value=quantity)
            sheet.cell(row=current_row, column=4, value=unit_price)
            sheet.cell(row=current_row, column=5, value=item_days)
            calculated_amount = (Decimal(str(quantity)) * Decimal(str(unit_price)) * Decimal(str(item_days))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            if unit_price > 0 and calculated_amount == line_amount:
                sheet.cell(row=current_row, column=6, value=f"=ROUND(C{current_row}*D{current_row}*E{current_row},0)")
            else:
                sheet.cell(row=current_row, column=6, value=line_amount)

            for column_index in range(2, 7):
                cell = sheet.cell(row=current_row, column=column_index)
                cell.font = body_font
                cell.border = regular_border
                cell.alignment = Alignment(
                    horizontal="left" if column_index == 2 else "center",
                    vertical="center",
                    wrap_text=True,
                )
                if column_index in (4, 6):
                    cell.number_format = money_format
            sheet.row_dimensions[current_row].height = 28
            current_row += 1

        last_line_row = current_row - 1
        subtotal_rows.append(current_row)
        sheet.cell(row=current_row, column=3, value=f"SOUS-TOTAL {section_name}")
        sheet.cell(row=current_row, column=6, value=f"=SUM(F{first_line_row}:F{last_line_row})")
        for column_index in range(2, 7):
            cell = sheet.cell(row=current_row, column=column_index)
            cell.font = body_bold
            cell.fill = green_fill
            cell.border = strong_top_border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            if column_index == 6:
                cell.number_format = money_format
        sheet.row_dimensions[current_row].height = 24
        sheet.row_dimensions[current_row + 1].height = 8
        current_row += 2

    implementation_row = current_row
    sheet.cell(row=implementation_row, column=3, value="SOUS-TOTAL MISE EN ŒUVRE")
    sheet.cell(
        row=implementation_row,
        column=6,
        value="=" + "+".join(f"F{row_index}" for row_index in subtotal_rows),
    )
    for column_index in range(2, 7):
        cell = sheet.cell(row=implementation_row, column=column_index)
        cell.font = body_bold
        cell.fill = orange_fill
        cell.border = strong_top_border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        if column_index == 6:
            cell.number_format = money_format
    sheet.row_dimensions[implementation_row].height = 25
    sheet.row_dimensions[current_row + 1].height = 8
    current_row += 2

    agency_title_row = current_row
    sheet.cell(row=agency_title_row, column=2, value="HONORAIRES D'AGENCE")
    for column_index in range(2, 7):
        cell = sheet.cell(row=agency_title_row, column=column_index)
        cell.font = white_bold
        cell.fill = dark_fill
        cell.border = regular_border
        cell.alignment = Alignment(
            horizontal="centerContinuous" if column_index == 2 else "center",
            vertical="center",
            wrap_text=True,
        )
    sheet.row_dimensions[agency_title_row].height = 23
    current_row += 1

    agency_details = (
        "Honoraires de conception, d'organisation, de mise en œuvre opérationnelle et "
        "d'animations d'activités\n"
        "-Matériels et port\n"
        "-Ressources humaines\n"
        "-Transport de l'équipe\n"
        "-Restauration de l'équipe\n"
        "-Hébergement de l'équipe"
    )
    agency_amount_row = current_row
    sheet.cell(row=agency_amount_row, column=2, value=agency_details)
    sheet.cell(row=agency_amount_row, column=6, value=(
        f"=ROUND(F{implementation_row}*17.5%,0)"
        if totals["mode_frais_agence"] == "pourcentage" else int(totals["frais_agence"])
    ))
    if totals["mode_frais_agence"] == "pourcentage":
        sheet.cell(row=agency_title_row, column=2, value="HONORAIRES D'AGENCE - 17,5 %")
    for column_index in range(2, 7):
        cell = sheet.cell(row=agency_amount_row, column=column_index)
        cell.font = body_font
        cell.border = regular_border
        cell.alignment = Alignment(
            horizontal="left" if column_index == 2 else "center",
            vertical="center",
            wrap_text=True,
        )
        if column_index == 6:
            cell.number_format = money_format
            cell.font = body_bold
    sheet.row_dimensions[agency_amount_row].height = 92
    current_row += 1

    total_ht_row = current_row
    sheet.cell(row=total_ht_row, column=4, value="TOTAL HT")
    sheet.cell(row=total_ht_row, column=6, value=f"=F{implementation_row}+F{agency_amount_row}")
    current_row += 1

    vat_rate = format(totals["taux_tva_frais_agence"].normalize(), "f")
    vat_row = current_row
    sheet.cell(row=vat_row, column=4, value=f"TVA {vat_rate}%")
    sheet.cell(row=vat_row, column=6, value=f"=ROUND(F{agency_amount_row}*{vat_rate}/100,0)")
    current_row += 1

    total_ttc_row = current_row
    sheet.cell(row=total_ttc_row, column=4, value="TOTAL TTC")
    sheet.cell(row=total_ttc_row, column=6, value=f"=F{total_ht_row}+F{vat_row}")
    current_row += 1

    total_person_row = current_row
    sheet.cell(row=total_person_row, column=4, value="TOTAL TTC / PERSONNE")
    sheet.cell(row=total_person_row, column=6, value=f"=F{total_ttc_row}/{participants}")

    for row_index in (total_ht_row, vat_row, total_ttc_row, total_person_row):
        for column_index in range(4, 7):
            cell = sheet.cell(row=row_index, column=column_index)
            cell.font = body_bold
            cell.border = regular_border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            if column_index == 6:
                cell.number_format = money_format
        if row_index in (total_ttc_row, total_person_row):
            for column_index in range(4, 7):
                sheet.cell(row=row_index, column=column_index).fill = total_fill
        sheet.row_dimensions[row_index].height = 24

    notes = _budget_notes(data)
    note_start_row = total_ttc_row
    for index, note in enumerate(notes):
        row_index = note_start_row + index
        cell = sheet.cell(row=row_index, column=2, value=note)
        cell.font = body_font
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    for row in sheet.iter_rows(min_row=header_row, max_row=total_person_row, min_col=2, max_col=6):
        for cell in row:
            if cell.value is None:
                cell.border = regular_border

    sheet.freeze_panes = "B16"
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.page_margins.left = 0.35
    sheet.page_margins.right = 0.35
    sheet.page_margins.top = 0.45
    sheet.page_margins.bottom = 0.45
    sheet.print_area = f"B1:F{max(total_person_row, note_start_row + len(notes) - 1)}"

    return {
        "sheet": sheet.title,
        "subtotal": implementation_row,
        "fees": agency_amount_row,
        "vat": vat_row,
        "total": total_ttc_row,
        "per_person": total_person_row,
    }


def generate_budget_excel(data: dict[str, Any], output_dir: str | Path | None = None) -> str:
    workbook = Workbook()
    workbook.remove(workbook.active)
    _append_budget_sheet(workbook, data)
    output_path = _safe_document_path(data["reference"], "xlsx", output_dir)
    workbook.save(output_path)
    return str(output_path)


def generate_multi_site_budget_excel(
    budgets: list[dict[str, Any]], reference: str, output_dir: str | Path | None = None,
) -> str:
    if not budgets or len({data["offre_id"] for data in budgets}) != 1:
        raise ValueError("Le comparatif doit contenir les budgets d'une seule offre.")
    workbook = Workbook()
    summary = workbook.active
    summary.title = "Comparatif"
    summary.sheet_view.showGridLines = False
    summary.append(["Site", "Référence", "Statut", "Prestations HT", "Frais d'agence", "TVA", "Total TTC", "TTC / personne"])
    labels = {"valide": "Validé", "genere": "Généré", "brouillon": "Brouillon", "annule": "Annulé"}
    for data in budgets:
        cells = _append_budget_sheet(workbook, data)
        sheet_name = quote_sheetname(cells["sheet"])
        summary.append([
            data.get("site_nom") or data["titre"], data["reference"], labels.get(data.get("statut"), "Brouillon"),
            *[f"={sheet_name}!F{cells[key]}" for key in ("subtotal", "fees", "vat", "total", "per_person")],
        ])
        row = summary.max_row
        summary.cell(row, 1).hyperlink = f"#{sheet_name}!B9"
        for cell in summary[row]:
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if cell.column >= 4:
                cell.number_format = '#,##0 "FCFA"'
            if data.get("statut") == "valide":
                cell.fill = PatternFill("solid", fgColor="EAF7F0")
        summary.row_dimensions[row].height = 36
    for cell in summary[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="008A50")
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    summary.row_dimensions[1].height = 32
    for column in "ABCDEFGH":
        summary.column_dimensions[column].width = 32 if column == "A" else 22
    summary.freeze_panes = "D2"
    summary.auto_filter.ref = summary.dimensions
    summary.page_setup.orientation = "landscape"
    summary.page_setup.paperSize = summary.PAPERSIZE_A4
    summary.page_setup.fitToWidth = 1
    summary.page_setup.fitToHeight = 0
    output_path = _safe_document_path(reference, "xlsx", output_dir)
    workbook.save(output_path)
    return str(output_path)
