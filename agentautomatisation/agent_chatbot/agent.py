import os
import json
import ast
import hashlib
import logging
import re
import unicodedata
from datetime import datetime

from smolagents import ToolCallingAgent, LiteLLMModel
from agentautomatisation.agent_chatbot.prompt import AGENT_INSTRUCTIONS

from agentautomatisation.agent_chatbot.tools import SendMail, build_chatbot_tools

SALES_EMAIL = os.getenv("SALES_EMAIL", "contact@ivoirtrips.com")
_sent_email_signatures = set()
logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


CHAT_AGENT_HISTORY_SUMMARY_MAX_CHARS = max(
    300,
    _env_int("CHAT_AGENT_HISTORY_SUMMARY_MAX_CHARS", 1200),
)
CHAT_AGENT_FALLBACK_MESSAGE = os.getenv(
    "CHAT_AGENT_FALLBACK_MESSAGE",
    (
        "Je rencontre une difficulte technique momentanee. "
        "Merci de reessayer dans quelques secondes ou d'utiliser le formulaire de contact."
    ),
)
CHAT_AGENT_FALLBACK_MESSAGE_EN = os.getenv(
    "CHAT_AGENT_FALLBACK_MESSAGE_EN",
    (
        "I am experiencing a temporary technical issue. "
        "Please try again in a few seconds or use the contact form."
    ),
)



def _create_model():
    return LiteLLMModel(
        model_id="mistral/mistral-large-latest",
        api_key=os.getenv("MISTRAL_API_KEY"),
    )


def create_agent_chatbot():
    prompt = AGENT_INSTRUCTIONS

    return ToolCallingAgent(
        model=_create_model(),
        tools=build_chatbot_tools(),
        max_steps=15,
        name="agent_chatbot",
        instructions=prompt,
    )


def create_agent():
    return create_agent_chatbot()


def _output_content(raw_output) -> str:
    if isinstance(raw_output, dict):
        content = raw_output.get("content")
        if content is not None:
            return str(content)
    return str(raw_output)


def _is_structured_payload(value) -> bool:
    return isinstance(value, dict) and "client" in value and "demande" in value


def _nested_structured_payload(value) -> dict | None:
    if _is_structured_payload(value):
        return value
    if not isinstance(value, dict):
        return None

    for key in ("answer", "content", "output", "final_answer"):
        nested = value.get(key)
        if _is_structured_payload(nested):
            return nested
        if isinstance(nested, dict):
            found = _nested_structured_payload(nested)
            if found:
                return found
    return None


def _find_structured_payload_span(content: str) -> tuple[int, int, dict] | None:
    decoder = json.JSONDecoder()
    for start, char in enumerate(content):
        if char != "{":
            continue
        try:
            parsed, offset = decoder.raw_decode(content[start:])
        except json.JSONDecodeError:
            continue
        if _is_structured_payload(parsed):
            return start, start + offset, parsed
    return None


def _extract_python_literal_payload(content: str) -> dict | None:
    starts = [match.start() for match in re.finditer(r"\{", content)]
    ends = [match.end() for match in re.finditer(r"\}", content)]

    for start in starts:
        for end in reversed(ends):
            if end <= start:
                continue
            snippet = content[start:end]
            try:
                parsed = ast.literal_eval(snippet)
            except (SyntaxError, ValueError):
                continue
            nested_payload = _nested_structured_payload(parsed)
            if nested_payload:
                return nested_payload
    return None


def _extract_structured_payload(raw_output) -> dict | None:
    if isinstance(raw_output, dict):
        nested_payload = _nested_structured_payload(raw_output)
        if nested_payload:
            return nested_payload
        content = raw_output.get("content")
    else:
        content = _output_content(raw_output)

    if not isinstance(content, str):
        return None

    span = _find_structured_payload_span(content)
    if span:
        return span[2]
    return _extract_python_literal_payload(content)


_MISSING_TEXT_VALUES = {
    "non precise",
    "non precisee",
    "non renseigne",
    "non renseignee",
    "a definir",
    "pas encore",
    "n/a",
    "na",
    "aucun",
    "aucune",
    "none",
    "null",
    "0",
}


def _normalise_text(value) -> str:
    text = str(value or "").strip().lower()
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def _has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0

    text = _normalise_text(value)
    return bool(text) and text not in _MISSING_TEXT_VALUES


def _payload_declared_missing_points(payload: dict) -> list[str]:
    demande = payload.get("demande", {}) or {}
    details = demande.get("details", {}) or {}
    raw_points = demande.get("points_manquants") or details.get("points_manquants") or []

    if isinstance(raw_points, str):
        raw_points = [raw_points]
    if not isinstance(raw_points, list):
        return ["points manquants"]

    points = []
    for point in raw_points:
        if _has_value(point):
            points.append(str(point).strip())
    return points


def _date_value_is_uncertain_or_past(value) -> bool:
    if not _has_value(value):
        return True

    normalized = _normalise_text(value)
    if any(
        marker in normalized
        for marker in [
            "a preciser",
            "a confirmer",
            "date a definir",
            "ou une date",
            "pas encore",
            "non precise",
        ]
    ):
        return True

    current_year = datetime.utcnow().year
    explicit_years = [int(match) for match in re.findall(r"\b(20\d{2}|19\d{2})\b", str(value))]
    return any(year < current_year for year in explicit_years)


def _payload_missing_required_fields(payload: dict) -> list[str]:
    client = payload.get("client", {}) or {}
    demande = payload.get("demande", {}) or {}
    details = demande.get("details", {}) or {}

    missing = []
    if not _has_value(client.get("nom")):
        missing.append("nom")
    if not _has_value(client.get("prenom")):
        missing.append("prenom")
    if not _has_value(client.get("email")):
        missing.append("email")
    if not _has_value(client.get("telephone")):
        missing.append("telephone")

    type_demande = _normalise_text(demande.get("type_demande"))
    if not _has_value(type_demande):
        missing.append("type de demande")
    elif type_demande != "contact":
        number_value = (
            demande.get("nombre_personnes")
            or details.get("nombre_participants")
            or details.get("nombre_personnes")
            or details.get("nombre_voyageurs")
            or details.get("participants")
        )
        date_value = (
            demande.get("date_souhaitee")
            or details.get("date_souhaitee")
            or details.get("date")
            or details.get("periode")
        )

        if not _has_value(number_value):
            missing.append("nombre de personnes")
        if not _has_value(date_value):
            missing.append("date ou periode")
        elif _date_value_is_uncertain_or_past(date_value):
            missing.append("date ou periode future confirmee")

    return missing


def _append_missing_points(payload: dict) -> None:
    demande = payload.setdefault("demande", {})
    raw_points = demande.get("points_manquants") or []
    if isinstance(raw_points, str):
        raw_points = [raw_points]
    if not isinstance(raw_points, list):
        raw_points = []

    existing = {_normalise_text(point) for point in raw_points}
    for field in _payload_missing_required_fields(payload):
        point = f"{field} a completer"
        normalized_point = _normalise_text(point)
        if normalized_point not in existing:
            raw_points.append(point)
            existing.add(normalized_point)

    demande["points_manquants"] = raw_points


def _clean_response_text(content: str) -> str:
    cleaned = content.replace("```json", "").replace("```", "").strip()
    return "\n".join(line.rstrip() for line in cleaned.splitlines()).strip()


def _remove_structured_payload_from_text(content: str) -> tuple[str, dict | None]:
    span = _find_structured_payload_span(content)
    if not span:
        return _clean_response_text(content), None

    start, end, payload = span
    cleaned = _clean_response_text(f"{content[:start]}{content[end:]}")
    return cleaned, payload


def _question_for_missing_field(field: str) -> str:
    field_key = _normalise_text(field)
    if field_key.startswith("point manquant:"):
        label = field.split(":", 1)[1].strip() if ":" in field else "cette information"
        return f"Il me manque encore une precision : {label}. Pouvez-vous me la confirmer ?"
    if field_key == "type de demande":
        return "C'est pour un team building, un voyage, un evenement ou un projet video/podcast ?"
    if field_key in {"nom", "prenom"}:
        return "Pouvez-vous me donner votre nom et prenom ?"
    if field_key == "email":
        return "Quel email pouvons-nous utiliser pour vous recontacter ?"
    if field_key == "telephone":
        return "Quel numero de telephone pouvons-nous utiliser pour vous recontacter ?"
    if field_key == "entreprise":
        return "Quel est le nom de votre entreprise ?"
    if "nombre" in field_key or "participant" in field_key:
        return "Combien de personnes sont prevues ?"
    if "date" in field_key or "periode" in field_key:
        return "Vous avez une date ou une periode souhaitee ?"
    if "destination" in field_key or "voyage" in field_key:
        return "Quelle destination ou quelle envie de voyage avez-vous en tete ?"
    if "evenement" in field_key:
        return "Quel type d'evenement souhaitez-vous organiser ?"
    if "projet" in field_key:
        return "Quel type de projet souhaitez-vous realiser ?"
    return f"Pouvez-vous me preciser {field} ?"


def _fallback_response_from_payload(payload: dict) -> str:
    client = payload.get("client", {}) or {}
    prenom = client.get("prenom")
    salutation = f" {prenom}" if _has_value(prenom) else ""
    return (
        f"Merci{salutation}, c'est bien note. "
        "Je transmets votre demande a l'equipe commerciale, qui reviendra vers vous rapidement."
    )


def _user_facing_response(raw_output):
    if _is_structured_payload(raw_output):
        return {"content": _fallback_response_from_payload(raw_output)}

    content = _output_content(raw_output)
    cleaned, payload = _remove_structured_payload_from_text(content)
    if not cleaned and payload:
        cleaned = _fallback_response_from_payload(payload)

    if isinstance(raw_output, dict):
        response = dict(raw_output)
        response["content"] = cleaned
        return response
    return cleaned


def _split_full_name(value: str) -> tuple[str, str]:
    parts = str(value or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return "", parts[0]
    return " ".join(parts[1:]), parts[0]


def _field_lines_from_text(text: str) -> list[tuple[str, str]]:
    fields = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        value = value.strip()
        if value:
            fields.append((label.strip(), value))
    return fields


def _detect_type_from_text(text: str) -> str:
    normalized = _normalise_text(text)
    if any(term in normalized for term in ["team building", "teambuilding", "team-building"]):
        return "team_building"
    if any(term in normalized for term in ["tourisme", "voyage", "circuit"]):
        return "tourisme_personnalise"
    if any(term in normalized for term in ["podcast", "video", "mossika", "studio"]):
        return "studio_mossika"
    if any(term in normalized for term in ["evenement", "mice", "conference", "gala"]):
        return "evenement_entreprise"
    return ""


def _extract_regex_group(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" .,;:-")
    return ""


def _extract_natural_fields(text: str) -> dict:
    normalized = _normalise_text(text)
    email = _extract_regex_group(
        text,
        [r"\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b"],
    )
    phone = _extract_regex_group(
        normalized,
        [
            r"(?:telephone|tel|numero|num)\s*(?:est|c'est|:)?\s*([+0-9][0-9\s().-]{7,})",
            r"\b(\+?\d[\d\s().-]{7,}\d)\b",
        ],
    )
    full_name = _extract_regex_group(
        normalized,
        [
            r"(?:mon nom complet|nom complet|nom et prenom|mon nom)\s*(?:est|c'est|:)?\s*([a-z][a-z' -]{1,80}?)(?=,|\.|\n|\s+(?:et|mon|ma|email|mail|telephone|tel|numero|fonction|poste|nombre|participant|date|budget|on|nous)\b|$)",
        ],
    )
    first_name = _extract_regex_group(
        normalized,
        [
            r"(?:mon prenom|prenom)\s*(?:est|c'est|:)?\s*([a-z][a-z' -]{1,50}?)(?=,|\.|\n|\s+(?:et|mon|ma|email|mail|telephone|tel|numero|fonction|poste|nombre|participant|date|budget|on|nous)\b|$)",
        ],
    )
    company = _extract_regex_group(
        normalized,
        [
            r"(?:l'entreprise|entreprise|societe|organisation)\s*(?:est|c'est|:)?\s*([a-z0-9&' -]{2,70}?)(?=,|\.|\n|\s+(?:mon|ma|email|mail|telephone|tel|numero|fonction|poste|nombre|participant|date|budget|on|nous|pour|avec)\b|$)",
        ],
    )
    role = _extract_regex_group(
        normalized,
        [
            r"(?:ma fonction|fonction|poste)\s*(?:est|c'est|:)?\s*([a-z][a-z' -]{1,60}?)(?=,|\.|\n|\s+(?:mon|ma|email|mail|telephone|tel|numero|nombre|participant|date|budget|on|nous)\b|$)",
        ],
    )
    participants = _extract_regex_group(
        normalized,
        [
            r"\b(\d{1,6})\s*(?:personnes|participants|voyageurs|invites?)\b",
            r"(?:nombre de participants|participants|personnes|nous sommes|on est|nous serons|on sera)\D{0,25}(\d{1,6})",
        ],
    )
    date = _extract_regex_group(
        normalized,
        [
            r"\b(\d{1,2}\s+(?:janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\s+\d{4})\b",
            r"\b(\d{1,2}\s+(?:janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre))\b",
            r"(?:date|periode)\D{0,25}([0-3]?\d[/-][01]?\d[/-](?:20)?\d{2})",
        ],
    )
    location = _extract_regex_group(
        normalized,
        [
            r"(?:lieu|aller a|sejour a)\s*(?:est|c'est|:)?\s*([a-z][a-z' -]{2,60}?)(?=,|\.|\n|\s+(?:pour la date|date|budget|nombre|participant|personnes|avec|on|nous)\b|$)",
        ],
    )
    budget = _extract_regex_group(
        normalized,
        [
            r"(?:budget|budjet)\D{0,25}([0-9][0-9\s.,]*\s*(?:fcfa|xof|f)?)",
        ],
    )

    return {
        "email": email,
        "telephone": phone,
        "full_name": full_name,
        "first_name": first_name,
        "entreprise": company,
        "fonction": role,
        "participants": participants,
        "date": date,
        "lieu": location,
        "budget": budget,
    }


def _payload_has_transmission_signal(payload: dict, text: str) -> bool:
    normalized = _normalise_text(text)
    client = payload.get("client", {}) or {}
    demande = payload.get("demande", {}) or {}

    has_form_signal = (
        "informations renseignees via le formulaire" in normalized
        or "type de demande" in normalized
    )
    has_contact_signal = any(
        _has_value(client.get(field))
        for field in ("nom", "prenom", "email", "telephone", "entreprise")
    )
    has_request_signal = any(
        [
            _normalise_text(demande.get("type_demande")) not in {"", "contact"},
            _has_value(demande.get("date_souhaitee")),
            _has_value(demande.get("nombre_personnes")),
            _has_value(demande.get("lieu_souhaite")),
            _has_value(demande.get("budget_estime")),
        ]
    )
    return has_form_signal or (has_contact_signal and has_request_signal)


def _payload_from_conversation(
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> dict | None:
    messages = [*(conversation_history or []), {"role": "user", "content": user_message}]
    combined_text = "\n".join(str(message.get("content", "")) for message in messages)
    user_text = "\n".join(
        str(message.get("content", ""))
        for message in messages
        if str(message.get("role", "user")).lower() == "user"
    )

    client = {
        "nom": "",
        "prenom": "",
        "entreprise": "",
        "fonction": "",
        "email": "",
        "telephone": "",
    }
    demande = {
        "type_demande": _detect_type_from_text(user_text or combined_text),
        "resume": "",
        "date_souhaitee": "",
        "lieu_souhaite": "",
        "nombre_personnes": 0,
        "budget_estime": "",
        "details": {},
        "points_manquants": [],
    }

    for label, value in _field_lines_from_text(user_text):
        normalized_label = _normalise_text(label)

        if normalized_label == "type de demande":
            detected_type = _detect_type_from_text(value)
            if detected_type:
                demande["type_demande"] = detected_type
            continue

        if any(term in normalized_label for term in ["nom et prenom", "nom complet", "full name"]):
            nom, prenom = _split_full_name(value)
            client["nom"] = client["nom"] or nom
            client["prenom"] = client["prenom"] or prenom
        elif "email" in normalized_label or "mail" in normalized_label:
            client["email"] = _extract_regex_group(
                value,
                [r"\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b"],
            ) or value
        elif any(term in normalized_label for term in ["telephone", "tel", "phone"]):
            client["telephone"] = _extract_regex_group(
                _normalise_text(value),
                [
                    r"(?:telephone|tel|numero|num)\s*(?:est|c'est|:)?\s*([+0-9][0-9\s().-]{7,})",
                    r"\b(\+?\d[\d\s().-]{7,}\d)\b",
                ],
            ) or value
        elif any(term in normalized_label for term in ["entreprise", "organisation", "societe"]):
            client["entreprise"] = value
        elif "participant" in normalized_label or "nombre de personnes" in normalized_label:
            demande["nombre_personnes"] = _extract_positive_int(value)
        elif any(term in normalized_label for term in ["date", "periode"]):
            demande["date_souhaitee"] = value
        elif "lieu" in normalized_label or "location" in normalized_label:
            demande["lieu_souhaite"] = value
        elif "budget" in normalized_label:
            demande["budget_estime"] = value
        elif "objectif" in normalized_label:
            demande["details"]["objectif"] = value

    natural_fields = _extract_natural_fields(user_text)
    extracted_email = _extract_regex_group(
        client.get("email", ""),
        [r"\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b"],
    )
    if extracted_email:
        client["email"] = extracted_email
    if not _has_value(client.get("email")) and _has_value(natural_fields.get("email")):
        client["email"] = natural_fields["email"]
    if not _has_value(client.get("telephone")) and _has_value(natural_fields.get("telephone")):
        client["telephone"] = natural_fields["telephone"]
    if not _has_value(client.get("nom")) and not _has_value(client.get("prenom")):
        nom, prenom = _split_full_name(natural_fields.get("full_name", ""))
        client["nom"] = nom
        client["prenom"] = prenom
    if not _has_value(client.get("prenom")) and _has_value(natural_fields.get("first_name")):
        client["prenom"] = natural_fields["first_name"]
    if not _has_value(client.get("entreprise")) and _has_value(natural_fields.get("entreprise")):
        client["entreprise"] = natural_fields["entreprise"]
    if not _has_value(client.get("fonction")) and _has_value(natural_fields.get("fonction")):
        client["fonction"] = natural_fields["fonction"]
    if not _has_value(demande.get("nombre_personnes")):
        demande["nombre_personnes"] = _extract_positive_int(natural_fields.get("participants"))
    if not _has_value(demande.get("date_souhaitee")) and _has_value(natural_fields.get("date")):
        demande["date_souhaitee"] = natural_fields["date"]
    if not _has_value(demande.get("lieu_souhaite")) and _has_value(natural_fields.get("lieu")):
        demande["lieu_souhaite"] = natural_fields["lieu"]
    if not _has_value(demande.get("budget_estime")) and _has_value(natural_fields.get("budget")):
        demande["budget_estime"] = natural_fields["budget"]

    if not demande["type_demande"]:
        demande["type_demande"] = "contact"

    demande["resume"] = (
        f"Demande {demande['type_demande']} issue du chat"
        f" pour {client.get('entreprise') or client.get('prenom') or 'un client'}."
    )

    optional_fields = [
        ("lieu_souhaite", "lieu a completer"),
        ("budget_estime", "budget a completer"),
    ]
    for field_name, missing_label in optional_fields:
        if not _has_value(demande.get(field_name)):
            demande["points_manquants"].append(missing_label)

    payload = {"client": client, "demande": demande}
    if not _payload_has_transmission_signal(payload, user_text or combined_text):
        return None
    _append_missing_points(payload)
    return payload


def _extract_positive_int(*values) -> int:
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and value > 0:
            return int(value)
        match = re.search(r"\d+", str(value or "").replace(" ", ""))
        if match:
            number = int(match.group(0))
            if number > 0:
                return number
    return 0


def _format_email_value(value, fallback: str = "A completer") -> str:
    return str(value).strip() if _has_value(value) else fallback


def _format_sales_email_message(user_message: str, payload: dict) -> str:
    client = payload.get("client", {}) or {}
    demande = payload.get("demande", {}) or {}
    details = demande.get("details", {}) or {}
    points = demande.get("points_manquants") or []
    if isinstance(points, str):
        points = [points]
    if not isinstance(points, list):
        points = []

    lines = [
        "Nouvelle demande qualifiee via le chatbot IvoirTrips.",
        "",
        f"Date qualification: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"Message utilisateur: {user_message}",
        "",
        "CLIENT",
        f"- Nom: {_format_email_value(client.get('nom'))}",
        f"- Prenom: {_format_email_value(client.get('prenom'))}",
        f"- Entreprise: {_format_email_value(client.get('entreprise'))}",
        f"- Email: {_format_email_value(client.get('email'))}",
        f"- Telephone: {_format_email_value(client.get('telephone'))}",
        "",
        "DEMANDE",
        f"- Type: {_format_email_value(demande.get('type_demande'))}",
        f"- Resume: {_format_email_value(demande.get('resume'))}",
        f"- Date/periode: {_format_email_value(demande.get('date_souhaitee') or details.get('date') or details.get('periode'))}",
        f"- Nombre de personnes: {_format_email_value(demande.get('nombre_personnes') or details.get('nombre_participants') or details.get('nombre_personnes'))}",
        f"- Lieu souhaite: {_format_email_value(demande.get('lieu_souhaite'))}",
        f"- Budget estime: {_format_email_value(demande.get('budget_estime'))}",
    ]

    if details:
        lines.extend(["", "DETAILS"])
        for key, value in details.items():
            lines.append(f"- {key}: {_format_email_value(value)}")

    clean_points = [str(point).strip() for point in points if _has_value(point)]
    if clean_points:
        lines.extend(["", "POINTS A COMPLETER"])
        lines.extend(f"- {point}" for point in clean_points)

    return "\n".join(lines)


def _shorten_history_text(text: str, max_chars: int) -> str:
    compact_text = " ".join(str(text or "").split())
    if len(compact_text) <= max_chars:
        return compact_text
    return compact_text[:max_chars].rstrip() + "..."


def _summary_line(label: str, value) -> str:
    if not _has_value(value):
        return ""
    return f"- {label}: {value}"


def _compact_session_summary(conversation_history: list[dict] | None = None) -> str:
    messages = conversation_history or []
    if not messages:
        return ""

    user_messages = [
        str(message.get("content", "")).strip()
        for message in messages
        if str(message.get("role", "")).lower() == "user" and message.get("content")
    ]
    assistant_messages = [
        str(message.get("content", "")).strip()
        for message in messages
        if str(message.get("role", "")).lower() == "assistant" and message.get("content")
    ]
    user_text = "\n".join(user_messages)
    natural_fields = _extract_natural_fields(user_text)
    payload = _payload_from_conversation("", messages)
    client = (payload or {}).get("client", {}) or {}
    demande = (payload or {}).get("demande", {}) or {}
    request_type = demande.get("type_demande") or _detect_type_from_text(user_text)

    client_name = " ".join(
        part
        for part in [client.get("prenom"), client.get("nom")]
        if _has_value(part)
    ).strip()
    lines = [
        "Resume compact de la session precedente:",
        _summary_line("type de demande", request_type),
        _summary_line("client", client_name),
        _summary_line("entreprise", client.get("entreprise") or natural_fields.get("entreprise")),
        _summary_line("email", client.get("email") or natural_fields.get("email")),
        _summary_line("telephone", client.get("telephone") or natural_fields.get("telephone")),
        _summary_line("date/periode", demande.get("date_souhaitee") or natural_fields.get("date")),
        _summary_line(
            "nombre de personnes",
            demande.get("nombre_personnes") or natural_fields.get("participants"),
        ),
        _summary_line("lieu/destination", demande.get("lieu_souhaite") or natural_fields.get("lieu")),
        _summary_line("budget", demande.get("budget_estime") or natural_fields.get("budget")),
    ]

    recent_client_messages = [
        _shorten_history_text(message, 180)
        for message in user_messages[-3:]
        if message
    ]
    if recent_client_messages:
        lines.append("- derniers messages client: " + " | ".join(recent_client_messages))

    if assistant_messages:
        cleaned_assistant, payload = _remove_structured_payload_from_text(assistant_messages[-1])
        if not cleaned_assistant and payload:
            resume = (payload.get("demande", {}) or {}).get("resume")
            cleaned_assistant = f"Demande deja capturee: {resume}" if _has_value(resume) else ""
        if cleaned_assistant:
            lines.append(
                "- derniere reponse assistant: "
                + _shorten_history_text(cleaned_assistant, 240)
            )

    summary = "\n".join(line for line in lines if line)
    return _shorten_history_text(summary, CHAT_AGENT_HISTORY_SUMMARY_MAX_CHARS)


def _should_reply_in_english(message_user: str, locale: str | None = None) -> bool:
    locale_code = str(locale or "").strip().lower()
    if locale_code.startswith("en"):
        return True

    text = f" {str(message_user or '').strip().lower()} "
    if not text.strip():
        return False

    strong_phrases = [
        "speak english",
        "tour guide",
        "tour guides",
        "do you",
        "does any",
        "can you",
        "how can",
        "what are",
        "i want",
        "i would",
    ]
    if any(phrase in text for phrase in strong_phrases):
        return True

    english_markers = [
        r"\bhello\b",
        r"\bhi\b",
        r"\bplease\b",
        r"\bthanks?\b",
        r"\benglish\b",
        r"\btour\b",
        r"\bguides?\b",
        r"\bspeak\b",
        r"\bbook\b",
        r"\breserve\b",
        r"\btravel\b",
    ]
    return sum(1 for marker in english_markers if re.search(marker, text)) >= 2


def _language_instruction(message_user: str, locale: str | None = None) -> str:
    if not _should_reply_in_english(message_user, locale):
        return ""
    return (
        "The client's latest message is in English. "
        "Reply only in English unless the client switches language."
    )


def _fallback_message_for_user(message_user: str, locale: str | None = None) -> str:
    if _should_reply_in_english(message_user, locale):
        return CHAT_AGENT_FALLBACK_MESSAGE_EN
    return CHAT_AGENT_FALLBACK_MESSAGE


def _notify_sales_team_if_needed(
    user_message: str,
    agent_output,
    conversation_history: list[dict] | None = None,
) -> None:
    payload = _extract_structured_payload(agent_output) or _payload_from_conversation(
        user_message,
        conversation_history,
    )
    if not payload:
        return
    _append_missing_points(payload)

    signature = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    if signature in _sent_email_signatures:
        return

    client = payload.get("client", {}) or {}
    client_name = client.get("nom") or client.get("entreprise") or "Client"
    subject = f"[NOUVELLE DEMANDE] IvoirTrips - {client_name}"
    message = _format_sales_email_message(user_message, payload)

    send_result = SendMail().forward(
        recipient_email=SALES_EMAIL,
        subject=subject,
        message=message,
        is_html=False,
    )

    if isinstance(send_result, str) and not send_result.lower().startswith("erreur"):
        _sent_email_signatures.add(signature)


def _quick_intent_response(message_user: str, locale: str | None = None) -> dict | None:
    normalized = _normalise_text(message_user)
    if not normalized:
        return None

    english = _should_reply_in_english(message_user, locale)

    if any(term in normalized for term in ["i have a question", "j'ai une question", "jai une question"]):
        return {
            "content": (
                "Of course. What would you like to know?"
                if english
                else "Bien sûr. Quelle est votre question ?"
            )
        }

    if "team building" in normalized or "teambuilding" in normalized or "team-building" in normalized:
        return {
            "content": (
                "Perfect. Let us start simply: which company or organization is this team building for?"
                if english
                else "Parfait. On commence simplement : c'est pour quelle entreprise ou organisation ?"
            )
        }

    if any(term in normalized for term in ["tourism", "travel request", "tourisme", "voyage"]):
        return {
            "content": (
                "Great. Do you already have a destination or travel idea in mind?"
                if english
                else "Super. Vous avez déjà une destination ou une envie de voyage en tête ?"
            )
        }

    if "akan" in normalized or "brunch" in normalized or "ticket" in normalized or "billet" in normalized:
        return {
            "content": (
                "Great. Is it for tickets, partnership, private booking or sponsoring?"
                if english
                else "Très bien. C'est pour des billets, un partenariat, une privatisation ou du sponsoring ?"
            )
        }

    if any(term in normalized for term in ["organize an event", "plan an event", "organiser un evenement", "evenement"]):
        return {
            "content": (
                "Perfect. What type of event would you like to organize?"
                if english
                else "Parfait. Quel type d'événement souhaitez-vous organiser ?"
            )
        }

    if any(term in normalized for term in ["studio mossika", "podcast", "video", "creative project"]):
        return {
            "content": (
                "Perfect. What type of creative project do you have in mind: video, podcast, event coverage or brand content?"
                if english
                else "Parfait. Quel type de projet avez-vous en tête : vidéo, podcast, captation événementielle ou brand content ?"
            )
        }

    if any(term in normalized for term in ["another request", "other request", "autre demande"]):
        return {
            "content": (
                "Of course. Tell me what you need and I will guide you."
                if english
                else "Bien sûr. Dites-moi ce dont vous avez besoin et je vous guide."
            )
        }

    return None


def _build_contextual_message(
    message_user: str,
    conversation_history: list[dict] | None = None,
    locale: str | None = None,
) -> str:
    language_instruction = _language_instruction(message_user, locale)
    if not conversation_history:
        if language_instruction:
            return "\n\n".join([language_instruction, "Nouveau message du client:", message_user])
        return message_user

    lines = []
    if language_instruction:
        lines.extend([language_instruction, ""])

    lines.extend([
        "Tu dois continuer la conversation ci-dessous sans repartir de zero.",
        "Ne redemande pas une information deja donnee dans le resume.",
        "",
        _compact_session_summary(conversation_history),
    ])

    lines.extend(["", "Nouveau message du client:", message_user])
    return "\n".join(lines)


def chat_with_agent(
    message_user: str,
    conversation_history: list[dict] | None = None,
    locale: str | None = None,
) -> str | dict:
    form_payload = _payload_from_conversation(message_user, conversation_history)
    if form_payload:
        _append_missing_points(form_payload)
        _notify_sales_team_if_needed(message_user, form_payload, conversation_history)
        return _user_facing_response(form_payload)

    quick_response = _quick_intent_response(message_user, locale)
    if quick_response:
        return quick_response

    contextual_message = _build_contextual_message(message_user, conversation_history, locale)
    try:
        output = create_agent_chatbot().run(contextual_message)
    except Exception:
        logger.exception("Erreur pendant l'appel de l'agent chatbot")
        return _fallback_message_for_user(message_user, locale)

    _notify_sales_team_if_needed(message_user, output, conversation_history)
    return _user_facing_response(output)
