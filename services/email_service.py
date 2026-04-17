import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from core.env_loader import load_local_env

load_local_env()


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_email_enabled() -> bool:
    return _get_bool_env("SMTP_ENABLED", False)


def _get_smtp_settings(profile: str | None = None) -> dict[str, str | int | bool]:
    prefix = f"SMTP_{profile.upper()}_" if profile else "SMTP_"

    smtp_host = os.getenv(f"{prefix}HOST") or os.getenv("SMTP_HOST", "mail.ivoirtrips.com")
    smtp_port = int(os.getenv(f"{prefix}PORT") or os.getenv("SMTP_PORT", "465"))
    smtp_username = os.getenv(f"{prefix}USERNAME") or os.getenv("SMTP_USERNAME", "")
    smtp_password = os.getenv(f"{prefix}PASSWORD") or os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv(f"{prefix}FROM_EMAIL") or os.getenv("SMTP_FROM_EMAIL", smtp_username)
    notification_email = os.getenv(f"{prefix}NOTIFICATION_EMAIL") or os.getenv(
        "SMTP_NOTIFICATION_EMAIL", smtp_username
    )
    use_ssl_raw = os.getenv(f"{prefix}USE_SSL")
    smtp_use_ssl = _get_bool_env("SMTP_USE_SSL", True) if use_ssl_raw is None else use_ssl_raw.strip().lower() in {"1", "true", "yes", "on"}

    return {
        "host": smtp_host.strip(),
        "port": smtp_port,
        "username": smtp_username.strip(),
        "password": smtp_password.strip(),
        "use_ssl": smtp_use_ssl,
        "from_email": from_email.strip(),
        "notification_email": notification_email.strip(),
    }


def send_email(
    subject: str,
    body: str,
    to_emails: list[str],
    html_body: str | None = None,
    profile: str | None = None,
) -> None:
    settings = _get_smtp_settings(profile)
    smtp_host = settings["host"]
    smtp_port = settings["port"]
    smtp_username = settings["username"]
    smtp_password = settings["password"]
    smtp_use_ssl = settings["use_ssl"]
    from_email = settings["from_email"]

    recipients = [email.strip() for email in to_emails if email and email.strip()]
    if not recipients:
        raise ValueError("Aucun destinataire email valide n'a ete fourni")

    if not smtp_host or not smtp_username or not smtp_password or not from_email:
        raise ValueError("Configuration SMTP incomplete")

    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))
    if html_body:
        message.attach(MIMEText(html_body, "html", "utf-8"))

    if smtp_use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, recipients, message.as_string())
        return

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, recipients, message.as_string())


def send_notification_email(
    subject: str,
    body: str,
    html_body: str | None = None,
    profile: str | None = None,
) -> None:
    if not is_email_enabled():
        return

    settings = _get_smtp_settings(profile)
    recipient = settings["notification_email"] or settings["username"]
    if not recipient:
        return

    print(
        f"SMTP notification profile={profile or 'DEFAULT'} "
        f"from={settings['from_email']} to={recipient}"
    )

    send_email(subject=subject, body=body, html_body=html_body, to_emails=[recipient], profile=profile)


def _normalize_value(value) -> str:
    if value is None:
        return "Non precise"
    text = str(value).strip()
    return text or "Non precise"


def _render_email_html(title: str, subtitle: str, badge: str, rows: list[tuple[str, str]], accent: str = "#f27d26") -> str:
    safe_title = escape(title)
    safe_subtitle = escape(subtitle)
    safe_badge = escape(badge)

    row_html = "".join(
        (
            "<tr>"
            f"<td style=\"padding:12px 0;color:#64748b;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;width:220px;vertical-align:top;\">{escape(label)}</td>"
            f"<td style=\"padding:12px 0;color:#0f172a;font-size:15px;line-height:1.6;vertical-align:top;\">{escape(_normalize_value(value))}</td>"
            "</tr>"
        )
        for label, value in rows
    )

    return f"""\
<!doctype html>
<html lang="fr">
  <body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
    <div style="padding:32px 16px;">
      <div style="max-width:760px;margin:0 auto;background:#ffffff;border-radius:24px;overflow:hidden;box-shadow:0 18px 50px rgba(15,23,42,0.08);border:1px solid #e2e8f0;">
        <div style="background:linear-gradient(135deg,{accent},#0f172a);padding:36px 40px;color:#ffffff;">
          <div style="display:inline-block;background:rgba(255,255,255,0.16);border:1px solid rgba(255,255,255,0.18);padding:8px 14px;border-radius:999px;font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">{safe_badge}</div>
          <h1 style="margin:18px 0 10px;font-size:30px;line-height:1.2;">{safe_title}</h1>
          <p style="margin:0;font-size:15px;line-height:1.7;color:rgba(255,255,255,0.88);">{safe_subtitle}</p>
        </div>
        <div style="padding:32px 40px;">
          <table style="width:100%;border-collapse:collapse;">
            {row_html}
          </table>
        </div>
        <div style="padding:20px 40px 32px;color:#94a3b8;font-size:12px;line-height:1.6;border-top:1px solid #e2e8f0;background:#f8fafc;">
          Message genere automatiquement depuis le site IVOIR TRIPS.
        </div>
      </div>
    </div>
  </body>
</html>
"""


def build_tourism_booking_email(db_demande) -> tuple[str, str, str]:
    subject = f"Nouvelle demande tourisme - {db_demande.titre_circuit}"
    rows = [
        ("Circuit", db_demande.titre_circuit),
        ("Lieu", db_demande.lieu_circuit),
        ("Duree", db_demande.duree_circuit),
        ("Formule", db_demande.formule_choisie),
        ("Prix formule", db_demande.prix_formule),
        ("Date souhaitee", db_demande.date_depart_souhaitee),
        ("Prenom", db_demande.prenom),
        ("Nom", db_demande.nom),
        ("Telephone", db_demande.telephone),
        ("Email", db_demande.email),
        ("Nombre de voyageurs", db_demande.nombre_voyageurs),
        ("Prix total estime", db_demande.prix_total_estime),
        ("Statut", db_demande.statut),
        ("Note client", db_demande.note_client or "Aucune precision complementaire"),
    ]
    body = "Nouvelle demande tourisme\n\n" + "\n".join(f"{label} : {_normalize_value(value)}" for label, value in rows)
    html_body = _render_email_html(
        title="Nouvelle demande tourisme",
        subtitle="Une reservation circuit vient d'etre enregistree depuis le site.",
        badge="Tourisme",
        rows=rows,
    )
    return subject, body, html_body


def build_custom_tourism_email(db_demande) -> tuple[str, str, str]:
    subject = f"Nouvelle demande tourisme personnalisee - {db_demande.nom_client} {db_demande.prenoms_client}"
    rows = [
        ("Nom", db_demande.nom_client),
        ("Prenoms", db_demande.prenoms_client),
        ("Email", db_demande.email_client),
        ("Telephone", db_demande.numero_telephone_client),
        ("Nombre de personnes", db_demande.nombre_personne),
        ("Nombre de jours", db_demande.nombre_jours),
        ("Lieu souhaite", db_demande.lieu_souhaite),
        ("Statut", db_demande.statut),
        ("Attente voyage", db_demande.attente_voyage or "Aucune precision complementaire"),
    ]
    body = "Nouvelle demande tourisme personnalisee\n\n" + "\n".join(
        f"{label} : {_normalize_value(value)}" for label, value in rows
    )
    html_body = _render_email_html(
        title="Nouvelle demande tourisme personnalisee",
        subtitle="Un voyage sur mesure a ete demande depuis le site.",
        badge="Sur mesure",
        rows=rows,
        accent="#0f766e",
    )
    return subject, body, html_body


def build_team_building_email(db_demande) -> tuple[str, str, str]:
    cadres = ", ".join(c.cadre for c in getattr(db_demande, "cadres", []) if getattr(c, "cadre", None)) or "Non precise"
    rows = [
        ("Entreprise", db_demande.entreprise),
        ("Contact", db_demande.nom_contact),
        ("Fonction", db_demande.fonction_contact),
        ("Telephone", db_demande.telephone_contact),
        ("Email", db_demande.email_contact),
        ("Participants", db_demande.nombre_participants),
        ("Objectif", db_demande.objectif),
        ("Lieu souhaite", db_demande.lieu_souhaite),
        ("Date souhaitee", db_demande.date_souhaitee),
        ("Type d'activite", db_demande.type_activite),
        ("Cadres", cadres),
        ("Avec salle", "Oui" if db_demande.avec_salle else "Non"),
        ("Avec nuitee", "Oui" if db_demande.avec_nuitee else "Non"),
        ("Nombre de nuitees", db_demande.nombre_nuitees),
        ("Transport", "Inclus" if db_demande.transport_inclus else "Non"),
        ("Restauration", "Incluse" if db_demande.restauration_incluse else "Non"),
        ("Hebergement", "Inclus" if db_demande.hebergement_inclus else "Non"),
        ("Experience precedente", db_demande.experience_precedente),
        ("Source de decouverte", db_demande.source_decouverte),
        ("Statut", db_demande.statut),
    ]
    subject = f"Nouvelle demande team building - {db_demande.entreprise}"
    body = "Nouvelle demande team building\n\n" + "\n".join(f"{label} : {_normalize_value(value)}" for label, value in rows)
    html_body = _render_email_html(
        title="Nouvelle demande team building",
        subtitle="Une entreprise vient de soumettre un besoin d'activite ou de sejour d'equipe.",
        badge="Team Building",
        rows=rows,
        accent="#ea580c",
    )
    return subject, body, html_body


def build_contact_email(db_demande) -> tuple[str, str, str]:
    rows = [
        ("Nom complet", db_demande.nom_complet),
        ("Email", db_demande.email),
        ("Sujet", db_demande.sujet),
        ("Type de demande", db_demande.type_demande),
        ("Statut", db_demande.statut),
        ("Message", db_demande.message),
    ]
    subject = f"Nouvelle demande contact - {db_demande.nom_complet}"
    body = "Nouvelle demande contact\n\n" + "\n".join(f"{label} : {_normalize_value(value)}" for label, value in rows)
    html_body = _render_email_html(
        title="Nouvelle demande contact",
        subtitle="Un message a ete envoye depuis le formulaire de contact du site.",
        badge="Contact",
        rows=rows,
        accent="#2563eb",
    )
    return subject, body, html_body
