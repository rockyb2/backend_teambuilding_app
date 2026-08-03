from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from num2words import num2words
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "assets" / "proforma"
DEFAULT_OUTPUT_DIR = BASE_DIR / "uploads" / "proformas"
SIGNATURE_BACKGROUND_MASK = [245, 255, 245, 255, 245, 255]


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
        raise ValueError(f"{field_name} doit etre un nombre valide.") from exc
    if amount < 0:
        raise ValueError(f"{field_name} ne peut pas etre negatif.")
    return amount


def _quantity(value: Any, field_name: str = "quantite") -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        quantity = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} doit etre un nombre valide.") from exc
    if quantity < 0:
        raise ValueError(f"{field_name} ne peut pas etre negatif.")
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


def _format_amount_words_fcfa(value: Any) -> str:
    amount = int(_decimal(value))
    words = num2words(amount, lang="fr").strip()
    if words:
        words = words[0].upper() + words[1:]
    return f"{words} FCFA"


def _paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(text or "")), style)


def _markup_paragraph(markup: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(markup, style)


def _safe_pdf_path(reference: str, output_dir: str | Path | None = None) -> Path:
    clean_reference = "".join(
        char for char in str(reference or "proforma") if char.isalnum() or char in ("-", "_")
    ).strip("-_")
    if not clean_reference:
        clean_reference = "proforma"
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return (directory / f"{clean_reference}.pdf").resolve()


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


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "normal": ParagraphStyle(
            "NormalProforma",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8.4,
            leading=10.2,
            alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "SmallProforma",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=7.4,
            leading=8.8,
        ),
        "small_italic": ParagraphStyle(
            "SmallItalicProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.8,
            leading=12.8,
        ),
        "center": ParagraphStyle(
            "CenterProforma",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
        ),
        "title": ParagraphStyle(
            "TitleProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "SectionProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.3,
            leading=10,
            leftIndent=5,
        ),
        "right": ParagraphStyle(
            "RightProforma",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10,
            alignment=TA_RIGHT,
        ),
        "right_bold": ParagraphStyle(
            "RightBoldProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.4,
            leading=12.8,
            alignment=TA_RIGHT,
        ),
        "bold": ParagraphStyle(
            "BoldProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.3,
            leading=10,
        ),
    }


def _draw_page(canvas: Any, document: Any) -> None:
    canvas.saveState()
    width, height = A4

    watermark_path = ASSETS_DIR / "watermark.png"
    if watermark_path.exists():
        canvas.drawImage(
            str(watermark_path),
            59 * mm,
            80 * mm,
            width=90 * mm,
            height=95 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )

    logo_path = ASSETS_DIR / "logo.png"
    if logo_path.exists():
        canvas.drawImage(
            str(logo_path),
            25 * mm,
            height - 32 * mm,
            width=50 * mm,
            height=18 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )

    canvas.setFont("Helvetica", 6.8)
    canvas.drawCentredString(
        width / 2,
        15 * mm,
        "Sarl au capital de 1.000.000 FCFA - Siège social : Cocody Angré 7è tranche - 06 BP 914 ABIDJAN 06 RCC CI-ABJ-03-2021-",
    )
    canvas.setFont("Helvetica", 6.8)
    canvas.drawCentredString(
        width / 2,
        11 * mm,
        "B13-02976 / NCC : 2148693 F",
    )
    email_line = "teambuilding@ivoirtrips.com / voyage@ivoirtrips.com"
    phone_line = " Tel : 07 79 181 778 / 05 95 298 183"
    email_width = canvas.stringWidth(email_line, "Helvetica", 6.8)
    phone_width = canvas.stringWidth(phone_line, "Helvetica", 6.8)
    footer_start_x = (width - email_width - phone_width) / 2
    footer_y = 7 * mm

    canvas.setFillColor(colors.HexColor("#1F5FBF"))
    canvas.setFont("Helvetica", 6.8)
    canvas.drawString(footer_start_x, footer_y, email_line)
    canvas.setFillColor(colors.black)
    canvas.drawString(footer_start_x + email_width, footer_y, phone_line)
    canvas.restoreState()


def normalize_sections(sections: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Decimal]:
    normalized_sections: list[dict[str, Any]] = []
    implementation_total = Decimal("0")

    for section_index, section in enumerate(sections or [], start=1):
        if not isinstance(section, dict):
            raise ValueError(f"La section {section_index} doit etre un dictionnaire.")

        section_name = str(section.get("nom") or section.get("name") or "").strip()
        if not section_name:
            section_name = "Prestations"

        items = section.get("prestations") or []
        if not isinstance(items, list):
            raise ValueError(f"Les prestations de la section '{section_name}' doivent former une liste.")

        normalized_items: list[dict[str, Any]] = []
        section_total = Decimal("0")
        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"La prestation {item_index} de la section '{section_name}' doit etre un dictionnaire."
                )

            designation = str(item.get("designation") or "").strip()
            if not designation:
                continue

            days = _quantity(item.get("nombre_jours"), "nombre_jours")
            quantity = _quantity(item.get("quantite"), "quantite")
            unit_price = _decimal(item.get("prix_unitaire"), "prix_unitaire")
            explicit_amount = item.get("montant_ht")

            if explicit_amount not in (None, ""):
                line_total = _decimal(explicit_amount, "montant_ht")
            elif unit_price:
                days_value = days if days is not None else Decimal("1")
                quantity_value = quantity if quantity is not None else Decimal("1")
                line_total = (days_value * quantity_value * unit_price).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            else:
                line_total = Decimal("0")

            normalized_items.append(
                {
                    "designation": designation,
                    "nombre_jours": _format_quantity(days),
                    "quantite": _format_quantity(quantity),
                    "prix_unitaire": int(unit_price),
                    "montant_ht": int(line_total),
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


def calculate_totals(
    sections: list[dict[str, Any]],
    frais_agence: Any = 0,
    taux_tva_frais_agence: Any = 18,
) -> dict[str, Any]:
    normalized_sections, implementation_total = normalize_sections(sections)
    agency_fees = _decimal(frais_agence, "frais_agence")
    try:
        vat_rate = Decimal(str(taux_tva_frais_agence or 0).replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Le taux de TVA doit etre un nombre valide.") from exc
    if vat_rate < 0:
        raise ValueError("Le taux de TVA ne peut pas etre negatif.")

    vat = (agency_fees * vat_rate / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    total = implementation_total + agency_fees + vat
    return {
        "sections": normalized_sections,
        "sous_total_ht": implementation_total,
        "frais_agence": agency_fees,
        "tva_frais_agence": vat,
        "total_ttc": total,
    }


def generate_proforma_pdf(data: dict[str, Any], output_dir: str | Path | None = None) -> str:
    required_fields = ("reference", "client", "nombre_personnes", "date_proforma", "objet")
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValueError(f"Champs obligatoires manquants: {', '.join(missing)}")
    if int(data.get("nombre_personnes") or 0) <= 0:
        raise ValueError("nombre_personnes doit etre superieur a zero.")

    totals = calculate_totals(
        data.get("sections") or [],
        data.get("frais_agence") or 0,
        data.get("taux_tva_frais_agence") or 18,
    )
    sections = totals["sections"]
    if not sections:
        raise ValueError("La proforma doit contenir au moins une prestation.")

    reference = str(data["reference"]).strip()
    output_path = _safe_pdf_path(reference, output_dir)
    styles = _styles()
    vat_rate = Decimal(str(data.get("taux_tva_frais_agence") or 18).replace(",", "."))

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=38 * mm,
        bottomMargin=22 * mm,
        title=f"Facture proforma {reference}",
        author="Ivoir Trips International",
    )
    story: list[Any] = []

    story.append(
        _markup_paragraph(
            f"PROFORMA&nbsp;&nbsp;N°<b>{escape(reference)}</b>",
            styles["center"],
        )
    )
    story.append(Spacer(1, 6 * mm))

    header_info = Table(
        [
            [
                [
                    _markup_paragraph("<i>Centre des impôts : Cocody deux plateaux 3</i>", styles["small_italic"]),
                    Spacer(1, 4 * mm),
                    _markup_paragraph("<i>Régime d'imposition : RSI</i>", styles["small_italic"]),
                ],
                [
                    _markup_paragraph(f"CLIENT : <b>{escape(str(data['client']))}</b>", styles["right_bold"]),
                    Spacer(1, 4 * mm),
                    _markup_paragraph(
                        f"DATE : <b>{escape(_display_date(data['date_proforma']))}</b>",
                        styles["right"],
                    ),
                ],
            ],
        ],
        colWidths=[99 * mm, 77 * mm],
        hAlign="CENTER",
    )
    header_info.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header_info)
    story.append(Spacer(1, 6 * mm))
    story.append(_markup_paragraph(f"<u>{escape(str(data['objet']).upper())}</u>", styles["title"]))
    story.append(Spacer(1, 5 * mm))

    rows: list[list[Any]] = [
        [
            _paragraph("Designation", styles["center"]),
            Paragraph("Nbre de<br/>jour(s)", styles["center"]),
            _paragraph("Qte", styles["center"]),
            Paragraph("Prix<br/>Unitaire", styles["center"]),
            _paragraph("Montant HT", styles["center"]),
        ]
    ]
    table_commands: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#444444")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.3),
    ]

    for section in sections:
        section_row = len(rows)
        rows.append([_paragraph(section["nom"].upper(), styles["section"]), "", "", "", ""])
        table_commands.append(("SPAN", (0, section_row), (-1, section_row)))
        table_commands.append(
            ("BACKGROUND", (0, section_row), (-1, section_row), colors.HexColor("#F5F5F5"))
        )

        for item in section["prestations"]:
            rows.append(
                [
                    _paragraph(item["designation"], styles["normal"]),
                    _paragraph(_format_quantity(item.get("nombre_jours")), styles["right"]),
                    _paragraph(_format_quantity(item.get("quantite")), styles["right"]),
                    _paragraph(
                        _format_fcfa(item.get("prix_unitaire")) if item.get("prix_unitaire") else "",
                        styles["right"],
                    ),
                    _paragraph(
                        _format_fcfa(item.get("montant_ht")) if item.get("montant_ht") else "F CFA",
                        styles["right"],
                    ),
                ]
            )

        subtotal_row = len(rows)
        rows.append(
            [
                _paragraph(f"SOUS-TOTAL {section['nom'].upper()}", styles["normal"]),
                "",
                "",
                "",
                _paragraph(_format_fcfa(section["sous_total"]), styles["right"]),
            ]
        )
        table_commands.append(
            ("BACKGROUND", (0, subtotal_row), (-1, subtotal_row), colors.HexColor("#B7B7B7"))
        )
        table_commands.append(("SPAN", (0, subtotal_row), (3, subtotal_row)))

    implementation_row = len(rows)
    rows.append(
        [
            _paragraph("SOUS-TOTAL MISE EN OEUVRE", styles["bold"]),
            "",
            "",
            "",
            _paragraph(_format_fcfa(totals["sous_total_ht"]), styles["right"]),
        ]
    )
    table_commands.extend(
        [
            ("BACKGROUND", (0, implementation_row), (-1, implementation_row), colors.HexColor("#7DDA86")),
            ("SPAN", (0, implementation_row), (3, implementation_row)),
        ]
    )

    agency_row = len(rows)
    rows.append(
        [
            _paragraph("FRAIS D'AGENCE", styles["section"]),
            "",
            "",
            "",
            _paragraph(_format_fcfa(totals["frais_agence"]), styles["right"]),
        ]
    )
    table_commands.extend(
        [
            ("BACKGROUND", (0, agency_row), (-1, agency_row), colors.HexColor("#D8F0D0")),
            ("SPAN", (0, agency_row), (3, agency_row)),
        ]
    )

    for detail in data.get("details_frais_agence") or []:
        detail_row = len(rows)
        rows.append([_paragraph(detail, styles["normal"]), "", "", "", ""])
        table_commands.append(("SPAN", (0, detail_row), (4, detail_row)))

    total_rows = [
        ("TOTAL HT :", totals["sous_total_ht"] + totals["frais_agence"], colors.white),
        (f"TVA SUR FRAIS D'AGENCE {format(vat_rate.normalize(), 'f')}% :", totals["tva_frais_agence"], colors.white),
        ("TOTAL TTC :", totals["total_ttc"], colors.yellow),
    ]
    for label, value, background in total_rows:
        row_index = len(rows)
        rows.append(
            [
                "",
                "",
                "",
                _paragraph(label, styles["bold"]),
                _paragraph(_format_fcfa(value), styles["right"]),
            ]
        )
        table_commands.extend(
            [
                ("SPAN", (0, row_index), (2, row_index)),
                ("BACKGROUND", (3, row_index), (4, row_index), background),
            ]
        )

    services_table = Table(
        rows,
        colWidths=[91 * mm, 14 * mm, 14 * mm, 27 * mm, 30 * mm],
        repeatRows=1,
        hAlign="CENTER",
    )
    services_table.setStyle(TableStyle(table_commands))
    story.append(services_table)
    story.append(Spacer(1, 5 * mm))

    signature_path = _first_existing_asset("signature1.png", "signature.png")
    signature: Image | Spacer
    if signature_path:
        signature_width, signature_height = _image_dimensions(
            signature_path,
            max_width=70 * mm,
            max_height=30 * mm,
        )
        signature = Image(
            str(signature_path),
            width=signature_width,
            height=signature_height,
            mask=SIGNATURE_BACKGROUND_MASK,
        )
        signature.hAlign = "RIGHT"
    else:
        signature = Spacer(70 * mm, 30 * mm)

    amount_in_words = _format_amount_words_fcfa(totals["total_ttc"])
    validation_block = [
        _markup_paragraph(
            "Arrêter cette présente Proforma à la somme de : "
            f"<font backColor=\"yellow\"><b>{escape(amount_in_words)}</b></font>",
            styles["normal"],
        ),
        Spacer(1, 6 * mm),
        _markup_paragraph(
            "Pour validation de la commande, merci de retourner soit la présente Proforma "
            "signée avec la mention<br/><b>« Bon pour Accord »</b>, soit votre Bon de Commande (BC).",
            styles["normal"],
        ),
    ]
    signature_table = Table(
        [[validation_block, signature]],
        colWidths=[104 * mm, 72 * mm],
        hAlign="CENTER",
    )
    signature_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(signature_table)

    document.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return str(output_path)
