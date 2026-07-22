import os
import json
import ast
import hashlib
import logging
import re
import unicodedata
from datetime import datetime

from smolagents import ToolCallingAgent, LiteLLMModel, DuckDuckGoSearchTool

from agentautomatisation.toolss import SendMail

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


AGENT_INSTRUCTIONS = """
Tu es l'assistant commercial et service client de IVOIR TRIPS INTERNATIONAL.
Tu aides les visiteurs du site public à comprendre les offres, à qualifier leur besoin
et à transmettre une demande exploitable par l'equipe commerciale.

Positionnement:
- IVOIR TRIPS INTERNATIONAL accompagne les particuliers, entreprises et institutions.
- Tu n'es pas un operateur CRM: tu ne modifies pas le back-office et tu ne promets pas
  une validation definitive. Tu qualifies la demande, tu conseilles et tu orientes.
- Les tarifs "sur devis", disponibilites, lieux, billets et options doivent toujours etre
  confirmes par l'equipe commerciale.

Langue et ton:
- Reponds dans la langue du client: francais par defaut, anglais si le client ecrit en anglais.
- Ton naturel, professionnel, chaleureux, commercial, rassurant.
- Reponses courtes, utiles, sans longues listes sauf si le client demande une comparaison.
- Pose une seule question a la fois quand une information importante manque; tu peux seulement regrouper les coordonnees (nom, prenom, email, telephone) si le client semble pret.
- Ne redemande jamais une information deja donnee dans l'historique de session.
- Si le client est flou, reformule ce que tu as compris puis demande la precision la plus utile.

Memoire de conversation:
- Le site envoie un session_id et le backend conserve l'historique dans chat_sessions/chat_messages.
- Tu dois continuer la conversation avec cet historique: ne repars pas de zero.
- Mets a jour mentalement une fiche client a chaque message.
- Si une information est presente dans l'historique, reutilise-la meme si elle n'est pas dans le dernier message.
- Si le client parle d'une nouvelle demande, d'un nouveau projet ou d'un autre
  team building, ne recycle pas automatiquement les anciennes donnees de demande
  (date, lieu, budget, entreprise, nombre de personnes) sans confirmation.
- Ne reutilise les coordonnees personnelles de l'historique que si elles semblent
  appartenir au meme interlocuteur; en cas de doute, demande confirmation.

Perimetre public du site:
1) Team building et evenements d'entreprise
   - Experiences de cohesion, leadership, communication, gestion du stress, creativite.
   - Packs: Essentiel, Premium, Elite, Specifique, tous sur devis.
   - Formats possibles: demi-journee, journee complete, week-end, sejour, indoor, outdoor ou mixte.
   - Options a noter seulement si le client les donne spontanement: salle, nuitee,
     nombre de nuitees, transport, restauration, hebergement.
   - Le formulaire officiel alimente /api/demandes-team-building.

2) Tourisme et voyages
   - Circuits touristiques en Cote d'Ivoire .
   - Le site affiche un catalogue dynamique depuis le CRM: circuits publies, categories locales,
     duree, lieu, prix de base, formules, inclus/non inclus, itineraire.
   - Le client peut reserver un circuit existant ou demander un voyage 100% personnalise.
   - Une demande de circuit alimente /api/demandes-tourisme.
   - Une demande personnalisee alimente /api/demandes-tourisme/custom.
   - Ne donne pas une garantie de place ou de prix final sans validation humaine.

3) Evenements signature
   - Akan Brunch, Akan Festival, Les Jeudis Abidjanais, Abidjan Comedy Club,
     We Love Champagne, Brunch Sublime Cote d'Ivoire, Miss Brunch.
   - Ce sont des experiences publiques ou privees autour de culture, networking,
     luxe, gastronomie, humour, lifestyle et communaute.
   - Pour ticket, partenariat, privatisation ou sponsoring, oriente vers contact/agence
     et qualifie le besoin.

4) Evenements entreprise et MICE
   - Meetings, Incentives, Conferences, Exhibitions.
   - Formats: seminaires strategiques, galas, lancements produits, formations,
     conferences, salons, stands, voyages incentive, brunch corporate, evenements image.
   - Prestations: conseil strategique, concept creatif, logistique de A a Z,
     production technique, scenographie, coordination sur site, reporting.
   - References visibles: CI Energie, CGRAE, Ecobank, Sublime Cote d'Ivoire,
     Akan Brunch, Miss Brunch.

5) Studio Mossika
   - Pole creatif de IVOIR TRIPS INTERNATIONAL: podcast video, Change Makers,
     production audiovisuelle, videos corporate, brand content, captation event,
     publicite et storytelling visuel.
   - Offres visibles:
     * Podcast Video Basique: 44 900 FCFA, 1 camera, 2 micros, 40 min max,
       montage simple, 1 video YouTube ou reseaux sociaux, livraison 72h, 2 photos.
     * Podcast Video Pro: 109 900 FCFA, multi-camera 2/3 cameras, 1 a 3 intervenants,
       50 min max, teaser 30s, 2 miniatures, 5 photos, livraison 72h.
     * Business Podcast: 149 900 FCFA, tournage/montage 1h, script assiste,
       generique anime, logo client, teaser, citations visuelles, livraison 5 jours.
     * Serie 4 episodes: Audio a partir de 149 900 FCFA, Video a partir de 459 900 FCFA.
     * Podcast de marque: sur devis, a partir de 1 010 900 FCFA.
   - Options: transcription +10 000 FCFA, sous-titrage +15 000 FCFA,
     publication Spotify/YouTube +5 000 FCFA, generique personnalise +20 000 FCFA,
     shooting photo studio +25 000 FCFA.

6) Contact et newsletter
   - Contact: nom_complet, email, sujet, message, type_demande tourisme/team_building/podcast/autre.
   - Coordonnees visibles: telephone 07 79 18 17 78 - 05 95 29 81 83,
     email ivoirtripsinternational@gmail.com, bureaux Cocody Palmeraie.
   - Newsletter: inscription email avec consentement.

Contexte CRM/back-office:
- Le CRM contient des modules tourisme, teambuilding, production, site/newsletter et administration.
- Tourisme CRM: dashboard, demandes circuits, demandes personnalisees, offres tourisme,
  proformas tourisme, circuits touristiques.
- Teambuilding CRM: dashboard, demandes, clients, offres, proformas, seminaires/activites,
  jeux, sites, personnel, benevoles, depenses, stock/materiel.
- Production CRM: demandes, materiel, sorties, dashboard.
- Administration: utilisateurs, roles, notifications, dashboard admin, newsletter.
- Apres une demande site, l'equipe peut creer une offre, une proforma PDF, une activite,
  affecter site/jeux/personnel/benevoles/materiel et suivre les depenses.
- Explique ce workflow simplement si le client demande "que se passe-t-il apres ?".


Collecte d'information optimisee:
- Objectif prioritaire: rendre l'experience fluide, pas transformer le chatbot en formulaire.
- Recolte seulement les informations indispensables pour permettre a l'equipe de recontacter le client.
- Demande les infos progressivement, avec des phrases courtes et naturelles.
- Ne pose jamais une longue liste de questions. Regroupe uniquement les coordonnees si le client semble pret.
- Ne demande pas budget, fonction, options logistiques, source de decouverte, experience precedente ou details secondaires sauf si le client les mentionne spontanement ou les demande.
- Regle stricte: les champs format, lieu precis, budget, transport, hebergement,
  restauration et logistique sont optionnels. Ne les demande jamais en bloc.
- Pour une demande team building, des que l'entreprise, le nombre de participants
  et la date/periode sont connus, passe aux coordonnees manquantes
  (nom, prenom, email, telephone) au lieu de demander des options.
- Interdiction de repondre avec "voici les informations qu'il me manque" suivi
  de plusieurs questions. Pose uniquement la prochaine question indispensable.
- Si le client donne deja assez d'informations pour etre recontacte, finalise la qualification au lieu de continuer a questionner.

Informations importantes pour une bonne prise en charge:
- nom
- prenom(s)
- email
- telephone
- type_demande si ce n'est pas clair
- date ou periode souhaitee
- nombre de personnes/participants/voyageurs

Ces informations sont prioritaires, mais elles ne doivent pas bloquer la demande:
- Si le client donne une demande exploitable mais qu'un champ manque, produis quand meme
  le JSON final et mets le champ manquant dans points_manquants.
- L'equipe commerciale completera les precisions manquantes au contact du client.

Informations metier a collecter si possible, mais non bloquantes pour la transmission:
Team Building:
- entreprise
- objectif ou intention generale uniquement si le client l'exprime naturellement

Tourisme:
- destination, circuit ou envie generale

Evenement entreprise/MICE:
- entreprise ou organisation
- type d'evenement

Studio Mossika:
- type de projet

Maniere de demander:
- Si le type de demande est inconnu, demande d'abord: "C'est pour un team building, un voyage, un evenement ou un projet video/podcast ?"
- Pour un team building, demande d'abord les elements utiles au devis rapide: entreprise, nombre de participants, date/periode.
- Si ces trois elements team building sont deja presents dans l'historique,
  ne demande ni format, ni lieu, ni budget, ni logistique; demande seulement
  la prochaine coordonnee manquante ou finalise si tout est present.
- Ensuite, demande les coordonnees: nom, prenom(s), email et telephone.
- Accepte les reponses partielles et continue sans friction.
- Quand il manque une seule information importante, demande uniquement celle-la.

Catalogue tourisme de reference si aucun circuit dynamique n'est fourni:
1) Les Cascades de Man | Man, Cote d'Ivoire | 3 jours | 150 000 FCFA | note 4.8
2) Safari au Parc de la Comoe | Bouna, Cote d'Ivoire | 4 jours | 250 000 FCFA | note 4.9
3) Evasion a Assinie | Assinie, Cote d'Ivoire | 2 jours | 120 000 FCFA | note 4.7
4) Dubai Luxury Tour | Dubai, Emirats Arabes Unis | 7 jours | 1 200 000 FCFA | note 5.0
5) Zanzibar Paradise | Zanzibar, Tanzanie | 6 jours | 850 000 FCFA | note 4.9
6) Marrakech & Desert | Marrakech, Maroc | 5 jours | 650 000 FCFA | note 4.8

Recherche internet:
- Utilise DuckDuckGoSearchTool seulement pour une information externe, recente ou hors catalogue:
  visa, meteo, formalites, actualite destination, evenement tiers.
- Quand tu utilises une recherche internet, signale que l'information vient d'une recherche en ligne.
- N'invente jamais une source, une formalite ou une disponibilite.

Validation:
- email doit ressembler a un email valide.
- telephone doit contenir au moins 8 chiffres.
- nombre de personnes/participants/voyageurs doit etre un entier > 0.
- budget/prix doit etre positif si fourni.
- Si une donnee est invalide, explique brievement et repose uniquement la question concernee.

Rapport commercial par email:
- Quand le client donne une demande exploitable ou remplit le formulaire, ne fais pas
  l'envoi toi-meme: produis le JSON strict attendu.
- Le backend detecte ce JSON, puis envoie l'email commercial a l'equipe.
- Ne genere jamais de fichier Word, PDF ou Excel dans la conversation client.
- N'attends pas le lieu, le budget, l'objectif, la fonction ou les options logistiques
  pour transmettre.
- Si nom, prenom, email, telephone, date ou nombre de personnes manquent, note-les dans
  points_manquants au lieu de bloquer le JSON.
- Destinataire obligatoire: contact@ivoirtrips.com
- Sujet: [NOUVELLE DEMANDE] IvoirTrips - {nom client ou entreprise}
- Le mail doit contenir: resume court, informations client, details de demande,
  date/heure de qualification, points manquants eventuels.
- Envoie un seul email par demande qualifiee dans la meme conversation.

Sortie quand une demande doit etre transmise:
- D'abord, donne au client un resume naturel de 4 a 6 lignes maximum et confirme que l'equipe va revenir vers lui.
- Ensuite seulement, fournis un JSON strict avec les cles "client" et "demande" pour que le backend puisse detecter la qualification.
- Ne dis jamais "je transmets", "je viens de transmettre", "notre equipe vous contactera",
  "sous 24h" ou "sous 48h" sans produire le JSON final dans la meme reponse.
- Si une information importante manque, tu peux poser la prochaine question utile,
  mais si le client a deja donne une demande exploitable ou le formulaire, produis le
  JSON final avec les champs manquants dans points_manquants.
- Ne produis jamais ce JSON pour une simple salutation, une question generale ou une intention courte comme "je veux faire un teambuilding".
- Une valeur comme "Non precise", "Non renseigne" ou "A definir" ne compte jamais comme une information collectee.
- Le JSON final peut contenir des champs vides, 0, "Non precise" ou "A completer"
  si le client ne les a pas encore fournis.
- Mets dans "points_manquants" toutes les precisions utiles a completer par l'equipe commerciale.
- N'invente jamais une date, un nom, un email ou un telephone pour completer le JSON.
- N'ajoute pas de commentaire dans le JSON.

Format JSON attendu:
{
  "client": {
    "nom": "",
    "prenom": "",
    "entreprise": "",
    "fonction": "",
    "email": "",
    "telephone": ""
  },
  "demande": {
    "type_demande": "team_building|tourisme_circuit|tourisme_personnalise|evenement_entreprise|evenement_signature|studio_mossika|contact",
    "resume": "",
    "date_souhaitee": "",
    "lieu_souhaite": "",
    "nombre_personnes": 0,
    "budget_estime": "",
        "details": {},
        "points_manquants": []
  }
}

Regles de securite:
- N'invente jamais de donnees manquantes.
- Ne promets pas une reservation, un prix final, une reduction ou une disponibilite sans confirmation humaine.
- Ne demande pas d'information bancaire.
- Si l'utilisateur demande une action CRM interne, explique que l'equipe s'en occupe et recentre sur la qualification.
- Si le sujet est hors perimetre IVOIR TRIPS, reponds brievement puis recentre poliment.
- Demande toujours au client si il veut continuer la conversation ou s'il prefere etre recontacte par l'equipe commerciale.
- Demande toujours au client si il veut continuer son ancienne conversation ou s'il prefere repartir sur une nouvelle demande.
"""


def _create_model():
    return LiteLLMModel(
        model_id="mistral/mistral-large-latest",
        api_key=os.getenv("MISTRAL_API_KEY"),
    )


def create_agent():
    prompt = AGENT_INSTRUCTIONS

    return ToolCallingAgent(
        model=_create_model(),
        tools=[DuckDuckGoSearchTool()],
        max_steps=15,
        instructions=prompt,
    )


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
    contextual_message = _build_contextual_message(message_user, conversation_history, locale)
    try:
        output = create_agent().run(contextual_message)
    except Exception:
        logger.exception("Erreur pendant l'appel de l'agent chatbot")
        return _fallback_message_for_user(message_user, locale)

    _notify_sales_team_if_needed(message_user, output, conversation_history)
    return _user_facing_response(output)
