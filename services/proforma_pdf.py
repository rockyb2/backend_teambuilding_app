from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from num2words import num2words
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    PageBreak,
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
TEAMBUILDING_AGENCY_FEE_RATE = Decimal("0.175")

IVT_ORANGE_DARK = colors.HexColor("#EA580C")
IVT_ORANGE_SOFT = colors.HexColor("#FFF1E7")
IVT_ORANGE_FAINT = colors.HexColor("#FFF7ED")
IVT_INK = colors.HexColor("#101828")
IVT_MUTED = colors.HexColor("#667085")
LETTER_PAGE_SIZE = (612, 792)


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


def _quantity(value: Any, field_name: str = "quantite") -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        quantity = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} doit être un nombre valide.") from exc
    if quantity < 0:
        raise ValueError(f"{field_name} ne peut pas être négatif.")
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


def _rate(value: Any, field_name: str = "taux") -> Decimal | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        value = value.replace("%", "").replace(",", ".").strip()
    try:
        rate = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} doit être un nombre valide.") from exc
    if rate < 0:
        raise ValueError(f"{field_name} ne peut pas être négatif.")
    return rate / Decimal("100") if rate > 1 else rate


def _format_rate_percent(value: Decimal | None) -> str:
    if value is None:
        return ""
    percent = (value * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return format(percent.normalize(), "f").replace(".", ",")


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
            textColor=IVT_INK,
        ),
        "small": ParagraphStyle(
            "SmallProforma",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=7.4,
            leading=8.8,
            textColor=IVT_MUTED,
        ),
        "small_italic": ParagraphStyle(
            "SmallItalicProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.8,
            leading=12.8,
            textColor=IVT_MUTED,
        ),
        "center": ParagraphStyle(
            "CenterProforma",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=IVT_INK,
        ),
        "title": ParagraphStyle(
            "TitleProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            alignment=TA_CENTER,
            textColor=IVT_INK,
        ),
        "financial_title": ParagraphStyle(
            "FinancialTitleProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=16,
            textColor=IVT_ORANGE_DARK,
        ),
        "conditions_title": ParagraphStyle(
            "ConditionsTitleProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            alignment=TA_CENTER,
            textColor=IVT_ORANGE_DARK,
        ),
        "box_title": ParagraphStyle(
            "BoxTitleProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=IVT_ORANGE_DARK,
        ),
        "section": ParagraphStyle(
            "SectionProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.3,
            leading=10,
            leftIndent=5,
            textColor=IVT_ORANGE_DARK,
        ),
        "right": ParagraphStyle(
            "RightProforma",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10,
            alignment=TA_RIGHT,
            textColor=IVT_INK,
        ),
        "right_bold": ParagraphStyle(
            "RightBoldProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.4,
            leading=12.8,
            alignment=TA_RIGHT,
            textColor=IVT_INK,
        ),
        "right_white_bold": ParagraphStyle(
            "RightWhiteBoldProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.2,
            leading=12,
            alignment=TA_RIGHT,
            textColor=colors.white,
        ),
        "summary_label": ParagraphStyle(
            "SummaryLabelProforma",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.5,
            textColor=IVT_INK,
        ),
        "summary_label_bold": ParagraphStyle(
            "SummaryLabelBoldProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.2,
            leading=12.5,
            textColor=IVT_INK,
        ),
        "summary_amount": ParagraphStyle(
            "SummaryAmountProforma",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.5,
            alignment=TA_RIGHT,
            textColor=IVT_INK,
        ),
        "summary_amount_bold": ParagraphStyle(
            "SummaryAmountBoldProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.8,
            leading=12.5,
            alignment=TA_RIGHT,
            textColor=IVT_ORANGE_DARK,
        ),
        "bold": ParagraphStyle(
            "BoldProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.3,
            leading=10,
            textColor=IVT_INK,
        ),
        "bold_white": ParagraphStyle(
            "BoldWhiteProforma",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.6,
            leading=11,
            textColor=colors.white,
        ),
    }


def _draw_page(canvas: Any, document: Any) -> None:
    canvas.saveState()
    width, height = LETTER_PAGE_SIZE

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

    canvas.setFillColor(colors.black)
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

    canvas.setFillColor(IVT_ORANGE_DARK)
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
            raise ValueError(f"La section {section_index} doit être un dictionnaire.")

        section_name = str(section.get("nom") or section.get("name") or "").strip()
        if not section_name:
            section_name = "Prestations"

        items = section.get("prestations") or section.get("lignes") or []
        if not isinstance(items, list):
            raise ValueError(f"Les prestations de la section '{section_name}' doivent former une liste.")

        normalized_items: list[dict[str, Any]] = []
        section_total = Decimal("0")
        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"La prestation {item_index} de la section '{section_name}' doit être un dictionnaire."
                )

            designation = str(item.get("designation") or "").strip()
            if not designation:
                continue

            days = _quantity(item.get("nombre_jours", item.get("duree_jours", 1)), "nombre_jours")
            quantity = _quantity(item.get("quantite", 1), "quantite")
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
                    "unite": str(item.get("unite") or "").strip(),
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
    agency_fee_rate: Any | None = None,
) -> dict[str, Any]:
    normalized_sections, implementation_total = normalize_sections(sections)
    agency_rate = _rate(agency_fee_rate, "taux_frais_agence")
    if agency_rate is None:
        agency_fees = _decimal(frais_agence, "frais_agence")
    else:
        agency_fees = (implementation_total * agency_rate).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
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
        "taux_frais_agence": agency_rate,
        "taux_tva_frais_agence": vat_rate,
        "tva_frais_agence": vat,
        "total_ht": total_ht,
        "total_ttc": total,
    }


def generate_proforma_pdf(data: dict[str, Any], output_dir: str | Path | None = None) -> str:
    required_fields = ("reference", "client", "nombre_personnes", "date_proforma", "objet")
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValueError(f"Champs obligatoires manquants: {', '.join(missing)}")
    if int(data.get("nombre_personnes") or 0) <= 0:
        raise ValueError("nombre_personnes doit être supérieur à zéro.")

    agency_fee_rate = data.get("taux_frais_agence")
    if agency_fee_rate in (None, "") and str(data.get("pole") or "").lower() == "teambuilding":
        agency_fee_rate = TEAMBUILDING_AGENCY_FEE_RATE

    totals = calculate_totals(
        data.get("sections") or [],
        data.get("frais_agence") or 0,
        data.get("taux_tva_frais_agence") or 18,
        agency_fee_rate=agency_fee_rate,
    )
    sections = totals["sections"]
    if not sections:
        raise ValueError("La proforma doit contenir au moins une prestation.")

    reference = str(data["reference"]).strip()
    output_path = _safe_pdf_path(reference, output_dir)
    styles = _styles()
    vat_rate = totals["taux_tva_frais_agence"]
    agency_rate_label = _format_rate_percent(totals.get("taux_frais_agence"))

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER_PAGE_SIZE,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=35 * mm,
        bottomMargin=18 * mm,
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

    rows: list[list[Any]] = []
    table_commands: list[tuple[Any, ...]] = [
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    for section in sections:
        section_row = len(rows)
        rows.append([_paragraph(section["nom"].upper(), styles["bold_white"]), "", "", "", "", ""])
        table_commands.append(("SPAN", (0, section_row), (-1, section_row)))
        table_commands.append(
            ("BACKGROUND", (0, section_row), (-1, section_row), IVT_ORANGE_DARK)
        )

        for item in section["prestations"]:
            item_row = len(rows)
            rows.append(
                [
                    _paragraph(item["designation"], styles["normal"]),
                    _paragraph(_format_quantity(item.get("nombre_jours")), styles["right"]),
                    _paragraph(_format_quantity(item.get("quantite")), styles["right"]),
                    _paragraph(item.get("unite") or "", styles["right"]),
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
            table_commands.append(("BACKGROUND", (0, item_row), (-1, item_row), colors.white))

        subtotal_row = len(rows)
        rows.append(
            [
                _paragraph(f"TOTAL {section['nom'].upper()}", styles["section"]),
                "",
                "",
                "",
                "",
                _paragraph(_format_fcfa(section["sous_total"]), styles["right_bold"]),
            ]
        )
        table_commands.append(
            ("BACKGROUND", (0, subtotal_row), (-1, subtotal_row), IVT_ORANGE_SOFT)
        )
        table_commands.append(("SPAN", (0, subtotal_row), (4, subtotal_row)))
        table_commands.append(("TOPPADDING", (0, subtotal_row), (-1, subtotal_row), 6))
        table_commands.append(("BOTTOMPADDING", (0, subtotal_row), (-1, subtotal_row), 6))

    services_table = Table(
        rows,
        colWidths=[79 * mm, 14 * mm, 14 * mm, 18 * mm, 25 * mm, 26 * mm],
        hAlign="CENTER",
    )
    services_table.setStyle(TableStyle(table_commands))
    story.append(services_table)
    story.append(Spacer(1, 5 * mm))

    amount_in_words = _format_amount_words_fcfa(totals["total_ttc"])
    payment_terms = str(data.get("modalite_paiement") or "100 % à la commande").strip()
    payment_terms_text = payment_terms or "100 % à la commande"
    payment_terms_body = escape(payment_terms_text.rstrip(".") + ".")
    agency_fee_label = (
        f"Frais d’agence = {agency_rate_label} % du sous-total mise en œuvre"
        if agency_rate_label
        else "Frais d’agence"
    )

    financial_rows = [
        [
            _paragraph("RÉCAPITULATIF FINANCIER", styles["financial_title"]),
            _paragraph("Sous-total mise en œuvre", styles["summary_label"]),
            _paragraph(_format_fcfa(totals["sous_total_ht"]), styles["summary_amount"]),
        ],
        [
            "",
            _paragraph(agency_fee_label, styles["summary_label"]),
            _paragraph(_format_fcfa(totals["frais_agence"]), styles["summary_amount"]),
        ],
        [
            "",
            _paragraph("TOTAL HT", styles["summary_label_bold"]),
            _paragraph(_format_fcfa(totals["total_ht"]), styles["summary_amount_bold"]),
        ],
        [
            "",
            _paragraph(f"TVA {format(vat_rate.normalize(), 'f')} % sur frais d’agence", styles["summary_label_bold"]),
            _paragraph(_format_fcfa(totals["tva_frais_agence"]), styles["summary_amount_bold"]),
        ],
        [
            "",
            _paragraph("TOTAL TTC", styles["bold_white"]),
            _paragraph(_format_fcfa(totals["total_ttc"]), styles["right_white_bold"]),
        ],
    ]
    financial_table = Table(
        financial_rows,
        colWidths=[75 * mm, 67 * mm, 34 * mm],
        hAlign="CENTER",
    )
    financial_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (0, 0), "TOP"),
                ("BACKGROUND", (1, 2), (2, 3), IVT_ORANGE_SOFT),
                ("BACKGROUND", (1, 4), (2, 4), IVT_ORANGE_DARK),
            ]
        )
    )
    story.append(financial_table)
    story.append(PageBreak())
    story.append(_paragraph("CONDITIONS COMMERCIALES & VALIDATION", styles["conditions_title"]))
    story.append(Spacer(1, 3 * mm))
    story.append(
        _markup_paragraph(
            "<b>Montant arrêté à la somme de :</b> "
            f"<font color=\"#EA580C\"><b>{escape(amount_in_words)}</b></font>",
            styles["normal"],
        )
    )

    def append_info_box(title: str, body_markup: str) -> None:
        story.append(Spacer(1, 3 * mm))
        box = Table(
            [
                [
                    [
                        _paragraph(title, styles["box_title"]),
                        Spacer(1, 2 * mm),
                        _markup_paragraph(body_markup, styles["normal"]),
                    ]
                ]
            ],
            colWidths=[176 * mm],
            hAlign="CENTER",
        )
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), IVT_ORANGE_FAINT),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(box)

    append_info_box(
        "VALIDATION DE LA COMMANDE",
        "Merci de retourner la présente Proforma signée avec la mention "
        "<b>« Bon pour Accord »</b>, ou de transmettre votre Bon de Commande (BC).",
    )
    append_info_box("MODALITÉS DE PAIEMENT", payment_terms_body)
    append_info_box("PAIEMENT PAR CHÈQUE", "À l’ordre de : IVOIR TRIPS INTERNATIONAL")
    append_info_box(
        "PAIEMENT PAR VIREMENT",
        "Bénéficiaire : IVOIR TRIPS INTERNATIONAL<br/>"
        "IBAN : CI93 CI008 01129 0129 467 319 90 22<br/>"
        "CODE SWIFT : SGCI CIAB",
    )

    signature_path = _first_existing_asset("signature1.png", "signature.png")
    signature: Image | Spacer
    if signature_path:
        signature_width, signature_height = _image_dimensions(
            signature_path,
            max_width=62 * mm,
            max_height=28 * mm,
        )
        signature = Image(
            str(signature_path),
            width=signature_width,
            height=signature_height,
            mask=SIGNATURE_BACKGROUND_MASK,
        )
        signature.hAlign = "CENTER"
    else:
        signature = Spacer(62 * mm, 28 * mm)

    story.append(Spacer(1, 6 * mm))

    signature_table = Table(
        [
            [
                [
                    _paragraph("POUR LE CLIENT", styles["center"]),
                    Spacer(1, 2 * mm),
                    _paragraph("Nom, signature et cachet", styles["center"]),
                    Spacer(1, 2 * mm),
                    _paragraph("Mention « Bon pour Accord »", styles["center"]),
                ],
                [
                    _paragraph("POUR IVOIR TRIPS INTERNATIONAL", styles["center"]),
                    Spacer(1, 2 * mm),
                    _paragraph("Direction Générale", styles["center"]),
                    Spacer(1, 2 * mm),
                    _paragraph("Signature et cachet", styles["center"]),
                    Spacer(1, 5 * mm),
                    signature,
                ],
            ]
        ],
        colWidths=[88 * mm, 88 * mm],
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
    story.append(Spacer(1, 12 * mm))

    control_line = (
        f"Contrôle des calculs : sous-total mise en œuvre = {_format_fcfa(totals['sous_total_ht'])} ; "
        f"{agency_fee_label} = {_format_fcfa(totals['frais_agence'])} ; "
        f"total HT = {_format_fcfa(totals['total_ht'])} ; "
        f"TVA {format(vat_rate.normalize(), 'f')} % sur frais d’agence = {_format_fcfa(totals['tva_frais_agence'])} ; "
        f"total TTC = {_format_fcfa(totals['total_ttc'])}."
    )
    story.append(_paragraph(control_line, styles["center"]))

    document.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return str(output_path)
