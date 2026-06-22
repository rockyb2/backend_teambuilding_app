from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import (
    Activite,
    Benevole,
    CircuitTouristique,
    Client,
    DemandeTeamBuilding,
    DemandeTourisme,
    DemandeTourismeCustom,
    Depense,
    HistoriqueStatutDemandeTourisme,
    Jeu,
    Materiel,
    Offre,
    Personnel,
    Role,
    Site,
    Utilisateur,
)
from database.schemas import UtilisateurCreate, UtilisateurProfileUpdate, UtilisateurUpdate
from security import (
    get_password_hash,
    normalize_role_name,
    user_can_access_module,
    verify_password,
)


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def _resolve_role_id(db: Session, role: Optional[str] = None, id_role: Optional[int] = None) -> int:
    if id_role is not None:
        db_role = db.query(Role).filter(Role.id_role == id_role).first()
        if not db_role:
            raise ValueError("Role introuvable")
        return db_role.id_role

    # We intentionally require an explicit role choice during user creation.
    # It avoids accidentally creating privileged accounts with an implicit default.
    role_name = role
    if not role_name:
        raise ValueError("Un role explicite est obligatoire")

    db_role = db.query(Role).filter(Role.nom_role == role_name).first()
    if not db_role:
        raise ValueError(f"Role '{role_name}' introuvable")
    return db_role.id_role


def get_utilisateur(db: Session, utilisateur_id: int) -> Optional[Utilisateur]:
    return db.query(Utilisateur).filter(Utilisateur.id_utilisateur == utilisateur_id).first()


def get_utilisateur_by_email(db: Session, email: str) -> Optional[Utilisateur]:
    normalized_email = email.strip().lower()
    return db.query(Utilisateur).filter(func.lower(Utilisateur.email) == normalized_email).first()


def get_utilisateurs(db: Session, skip: int = 0, limit: int = 100) -> list[Utilisateur]:
    return db.query(Utilisateur).offset(skip).limit(limit).all()


def get_utilisateurs_actifs(db: Session, skip: int = 0, limit: int = 100) -> list[Utilisateur]:
    return db.query(Utilisateur).filter(Utilisateur.actif == True).offset(skip).limit(limit).all()


def get_utilisateurs_by_role(db: Session, role: str, skip: int = 0, limit: int = 100) -> list[Utilisateur]:
    return (
        db.query(Utilisateur)
        .join(Utilisateur.role_rel)
        .filter(Role.nom_role == role)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_roles(db: Session) -> list[Role]:
    return db.query(Role).order_by(Role.nom_role.asc()).all()


def create_utilisateur(db: Session, payload: UtilisateurCreate) -> Utilisateur:
    data = _model_dump(payload)
    mot_de_passe = data.pop("mot_de_passe")
    role_name = data.pop("role", None)
    role_id = data.pop("id_role", None)
    data["id_role"] = _resolve_role_id(db, role=role_name, id_role=role_id)

    db_utilisateur = Utilisateur(**data)
    db_utilisateur.mot_de_passe = get_password_hash(mot_de_passe)

    db.add(db_utilisateur)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur


def update_utilisateur(db: Session, db_utilisateur: Utilisateur, payload: UtilisateurUpdate) -> Utilisateur:
    updates = _model_dump(payload, exclude_unset=True)

    has_role_name = "role" in updates
    has_role_id = "id_role" in updates
    role_name = updates.pop("role", None)
    role_id = updates.pop("id_role", None)

    if has_role_name or has_role_id:
        db_utilisateur.id_role = _resolve_role_id(db, role=role_name, id_role=role_id)

    for key, value in updates.items():
        setattr(db_utilisateur, key, value)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur


def update_utilisateur_profile(
    db: Session,
    db_utilisateur: Utilisateur,
    payload: UtilisateurProfileUpdate,
) -> Utilisateur:
    updates = _model_dump(payload, exclude_unset=True)

    for key in ("nom", "prenom", "email", "image_utilisateur"):
        if key in updates:
            setattr(db_utilisateur, key, updates[key])

    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur


def change_utilisateur_password(
    db: Session,
    db_utilisateur: Utilisateur,
    current_password: str,
    new_password: str,
) -> bool:
    if not verify_password(current_password, db_utilisateur.mot_de_passe):
        return False

    db_utilisateur.mot_de_passe = get_password_hash(new_password)
    db.commit()
    return True


def record_login(db: Session, db_utilisateur: Utilisateur) -> Utilisateur:
    db_utilisateur.derniere_connexion = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur


def _count_rows(db: Session, model, *criteria) -> int:
    query = db.query(func.count()).select_from(model)
    if criteria:
        query = query.filter(*criteria)
    return int(query.scalar() or 0)


def _tourism_treated_count(db: Session, utilisateur_id: int) -> int:
    rows = (
        db.query(
            HistoriqueStatutDemandeTourisme.demande_tourisme_id,
            HistoriqueStatutDemandeTourisme.demande_tourisme_custom_id,
        )
        .filter(HistoriqueStatutDemandeTourisme.modifie_par_id == utilisateur_id)
        .all()
    )
    treated = set()
    for demande_id, custom_id in rows:
        if demande_id is not None:
            treated.add(("tourisme", demande_id))
        if custom_id is not None:
            treated.add(("tourisme_custom", custom_id))
    return len(treated)


def _creation_metric(key: str, label: str, count: int) -> dict:
    return {"key": key, "label": label, "count": count}


def _tourism_creation_metrics(db: Session, utilisateur_id: int) -> list[dict]:
    return [
        _creation_metric(
            "demandes_circuits",
            "Demandes de circuits creees",
            _count_rows(db, DemandeTourisme, DemandeTourisme.created_by_id == utilisateur_id),
        ),
        _creation_metric(
            "demandes_personnalisees",
            "Demandes personnalisees creees",
            _count_rows(
                db,
                DemandeTourismeCustom,
                DemandeTourismeCustom.created_by_id == utilisateur_id,
            ),
        ),
        _creation_metric(
            "circuits",
            "Circuits / offres touristiques crees",
            _count_rows(
                db,
                CircuitTouristique,
                CircuitTouristique.created_by_id == utilisateur_id,
            ),
        ),
    ]


def _teambuilding_creation_metrics(db: Session, utilisateur_id: int) -> list[dict]:
    tracked_models = (
        ("demandes", "Demandes Team Building creees", DemandeTeamBuilding, DemandeTeamBuilding.created_by_id),
        ("offres", "Offres creees", Offre, Offre.id_utilisateur_cr),
        ("activites", "Activites / seminaires crees", Activite, Activite.id_utilisateur_create),
        ("clients", "Clients crees", Client, Client.id_utilisateur_create),
        ("sites", "Sites crees", Site, Site.id_utilisateur_create),
        ("jeux", "Jeux crees", Jeu, Jeu.id_utilisateur_create),
        ("personnel", "Membres du personnel crees", Personnel, Personnel.id_utilisateur_create),
        ("benevoles", "Benevoles crees", Benevole, Benevole.id_utilisateur_create),
        ("depenses", "Depenses creees", Depense, Depense.id_utilisateur_cr),
        ("materiels", "Materiels crees", Materiel, Materiel.id_utilisateur_create),
    )
    return [
        _creation_metric(
            key,
            label,
            _count_rows(db, model, creator_column == utilisateur_id),
        )
        for key, label, model, creator_column in tracked_models
    ]


def get_utilisateur_activity_summary(db: Session, db_utilisateur: Utilisateur) -> dict:
    utilisateur_id = db_utilisateur.id_utilisateur
    metrics = []

    if user_can_access_module(db_utilisateur, "tourisme"):
        total_tourisme = (
            _count_rows(db, DemandeTourisme)
            + _count_rows(db, DemandeTourismeCustom)
        )
        tourism_creations = _tourism_creation_metrics(db, utilisateur_id)
        metrics.append(
            {
                "module": "tourisme",
                "label": "Tourisme",
                "total_demandes": total_tourisme,
                "demandes_traitees": _tourism_treated_count(db, utilisateur_id),
                "demandes_creees": sum(item["count"] for item in tourism_creations[:2]),
                "offres_creees": tourism_creations[2]["count"],
                "elements_crees": sum(item["count"] for item in tourism_creations),
                "creations": tourism_creations,
            }
        )

    if user_can_access_module(db_utilisateur, "teambuilding"):
        teambuilding_creations = _teambuilding_creation_metrics(db, utilisateur_id)
        metrics.append(
            {
                "module": "teambuilding",
                "label": "Team Building",
                "total_demandes": _count_rows(db, DemandeTeamBuilding),
                "demandes_traitees": _count_rows(
                    db,
                    DemandeTeamBuilding,
                    DemandeTeamBuilding.statut_modifie_par_id == utilisateur_id,
                ),
                "demandes_creees": teambuilding_creations[0]["count"],
                "offres_creees": teambuilding_creations[1]["count"],
                "elements_crees": sum(item["count"] for item in teambuilding_creations),
                "creations": teambuilding_creations,
            }
        )

    if user_can_access_module(db_utilisateur, "production"):
        metrics.append(
            {
                "module": "production",
                "label": "Production",
                "total_demandes": 0,
                "demandes_traitees": 0,
                "demandes_creees": 0,
                "offres_creees": 0,
                "elements_crees": 0,
                "creations": [],
            }
        )

    total_demandes = sum(metric["total_demandes"] for metric in metrics)
    demandes_traitees = sum(metric["demandes_traitees"] for metric in metrics)
    demandes_creees = sum(metric["demandes_creees"] for metric in metrics)
    offres_creees = sum(metric["offres_creees"] for metric in metrics)
    elements_crees = sum(metric["elements_crees"] for metric in metrics)

    return {
        "id_utilisateur": utilisateur_id,
        "role": normalize_role_name(db_utilisateur.role),
        "modules": [metric["module"] for metric in metrics],
        "derniere_connexion": db_utilisateur.derniere_connexion,
        "total_demandes": total_demandes,
        "demandes_traitees": demandes_traitees,
        "demandes_creees": demandes_creees,
        "offres_creees": offres_creees,
        "taux_traitement": round(
            (demandes_traitees / total_demandes) * 100,
            1,
        ) if total_demandes else 0,
        "elements_crees": elements_crees,
        "metrics": metrics,
    }


def delete_utilisateur(db: Session, db_utilisateur: Utilisateur) -> None:
    db.delete(db_utilisateur)
    db.commit()


def authenticate_utilisateur(db: Session, email: str, password: str) -> Optional[Utilisateur]:
    utilisateur = get_utilisateur_by_email(db, email)
    if utilisateur and verify_password(password, utilisateur.mot_de_passe):
        return utilisateur
    return None
