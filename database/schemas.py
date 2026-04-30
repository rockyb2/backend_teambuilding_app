from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover
    ConfigDict = None


class ContactAkanBase(BaseModel):
    nom: str
    prenoms: str
    email: str
    telephone: Optional[str] = None
    has_won: Optional[bool] = False

class ContactAkanCreate(ContactAkanBase):
    pass

class ContactAkanResponse(ContactAkanBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True





class ORMBaseModel(BaseModel):
    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:  # pragma: no cover
        class Config:
            orm_mode = True


DemandeTourismeStatut = Literal[
    "nouvelle",
    "en_traitement",
    "devis_envoye",
    "en_attente_reponse_client",
    "relance_envoyee",
    "validee",
    "annulee",
    "refusee",
    "terminee",
]

STATUTS_DEMANDE_TOURISME: tuple[str, ...] = (
    "nouvelle",
    "en_traitement",
    "devis_envoye",
    "en_attente_reponse_client",
    "relance_envoyee",
    "validee",
    "annulee",
    "refusee",
    "terminee",
)


class ClientBase(ORMBaseModel):
    nom: str
    prenom: Optional[str] = None
    entreprise: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ORMBaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    entreprise: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class ClientRead(ClientBase):
    id_client: int


class DemandeBase(ORMBaseModel):
    date_demande: Optional[date] = None
    description: Optional[str] = None
    nombre_participants: Optional[int] = None
    budget_estime: Optional[Decimal] = None
    statut: Optional[str] = "en_attente"
    id_client: int
    id_utilisateur: Optional[int] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class DemandeCreate(DemandeBase):
    pass


class DemandeRead(DemandeBase):
    id_demande: int


class OffreBase(ORMBaseModel):
    date_creation: Optional[date] = None
    montant_propose: Decimal
    statut_offre: Optional[str] = "brouillon"
    id_demande: int
    id_utilisateur_create: Optional[int] = None


class OffreCreate(OffreBase):
    pass


class OffreRead(OffreBase):
    id_offre: int


class SiteBase(ORMBaseModel):
    nom_site: str
    localisation: Optional[str] = None
    capacite: Optional[int] = None
    type_site: Optional[str] = None
    image_site: Optional[str] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class SiteCreate(SiteBase):
    pass


class SiteRead(SiteBase):
    id_site: int


class ActiviteBase(ORMBaseModel):
    nom: str
    description: Optional[str] = None
    date_debut: datetime
    date_fin: datetime
    statut: Optional[str] = "planifiee"
    id_offre: Optional[int] = None
    id_site: int
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class ActiviteCreate(ActiviteBase):
    pass


class ActiviteRead(ActiviteBase):
    id_activite: int


class JeuBase(ORMBaseModel):
    nom_jeu: str
    description: Optional[str] = None
    duree: Optional[int] = None
    nb_min_participants: Optional[int] = None
    nb_max_participants: Optional[int] = None
    materiel_requis: Optional[str] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class JeuCreate(JeuBase):
    pass


class JeuRead(JeuBase):
    id_jeu: int


class ActiviteJeuBase(ORMBaseModel):
    id_activite: int
    id_jeu: int
    ordre: Optional[int] = None
    duree_prevue: Optional[int] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class ActiviteJeuCreate(ActiviteJeuBase):
    pass


class ActiviteJeuRead(ActiviteJeuBase):
    pass


class PersonnelBase(ORMBaseModel):
    nom: str
    prenom: Optional[str] = None
    fonction: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class PersonnelCreate(PersonnelBase):
    pass


class PersonnelUpdate(ORMBaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    fonction: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class PersonnelRead(PersonnelBase):
    id_personnel: int


class AffectationBase(ORMBaseModel):
    id_activite: int
    id_personnel: int
    role: Optional[str] = None
    heure_debut: Optional[datetime] = None
    heure_fin: Optional[datetime] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class AffectationCreate(AffectationBase):
    pass


class AffectationRead(AffectationBase):
    id_affectation: int


class DepenseBase(ORMBaseModel):
    libelle: str
    montant: Decimal
    date_depense: Optional[date] = None
    type_depense: Optional[str] = None
    id_activite: int
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class DepenseCreate(DepenseBase):
    pass


class DepenseRead(DepenseBase):
    id_depense: int


class DemandeTourismeBase(ORMBaseModel):
    circuit_externe_id: Optional[int] = None
    titre_circuit: str
    lieu_circuit: Optional[str] = None
    duree_circuit: Optional[str] = None
    formule_choisie: Optional[str] = None
    prix_formule: Optional[Decimal] = Decimal("0")
    date_depart_souhaitee: Optional[date] = None
    prenom: str
    nom: str
    telephone: str
    email: str
    nombre_voyageurs: int = 1
    note_client: Optional[str] = None
    prix_total_estime: Optional[Decimal] = Decimal("0")
    source: Optional[str] = "site_web"
    statut: Optional[DemandeTourismeStatut] = "nouvelle"


class DemandeTourismeCreate(DemandeTourismeBase):
    pass


class DemandeTourismeRead(DemandeTourismeBase):
    id: int
    statut_modifie_le: Optional[datetime] = None
    statut_modifie_par_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class DemandeTourismeStatutUpdate(ORMBaseModel):
    statut: DemandeTourismeStatut
    commentaire: Optional[str] = None


class HistoriqueStatutDemandeTourismeRead(ORMBaseModel):
    id: int
    demande_tourisme_id: Optional[int] = None
    demande_tourisme_custom_id: Optional[int] = None
    ancien_statut: Optional[str] = None
    nouveau_statut: str
    commentaire: Optional[str] = None
    modifie_par_id: Optional[int] = None
    modifie_le: datetime


class CircuitTouristiqueBase(ORMBaseModel):
    titre: str
    lieu: Optional[str] = None
    thematique: Optional[str] = None
    description: Optional[str] = None
    details: list[Any] = Field(default_factory=list)
    duree: Optional[str] = None
    prix_base: Decimal = Decimal("0")
    categorie: Literal["local", "international"] = "local"
    type_circuit: Optional[str] = None
    images: list[Any] = Field(default_factory=list)
    itineraire: list[Any] = Field(default_factory=list)
    formules: list[Any] = Field(default_factory=list)
    inclus: list[Any] = Field(default_factory=list)
    non_inclus: list[Any] = Field(default_factory=list)
    conditions_annulation: list[Any] = Field(default_factory=list)
    actif: bool = True
    publie: bool = False


class CircuitTouristiqueCreate(CircuitTouristiqueBase):
    pass


class CircuitTouristiqueUpdate(ORMBaseModel):
    titre: Optional[str] = None
    lieu: Optional[str] = None
    thematique: Optional[str] = None
    description: Optional[str] = None
    details: Optional[list[Any]] = None
    duree: Optional[str] = None
    prix_base: Optional[Decimal] = None
    categorie: Optional[Literal["local", "international"]] = None
    type_circuit: Optional[str] = None
    images: Optional[list[Any]] = None
    itineraire: Optional[list[Any]] = None
    formules: Optional[list[Any]] = None
    inclus: Optional[list[Any]] = None
    non_inclus: Optional[list[Any]] = None
    conditions_annulation: Optional[list[Any]] = None
    actif: Optional[bool] = None
    publie: Optional[bool] = None


class CircuitTouristiqueRead(CircuitTouristiqueBase):
    id: int
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_by_nom_complet: Optional[str] = None
    updated_by_nom_complet: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    title: str
    location: Optional[str] = None
    thematic: Optional[str] = None
    duration: Optional[str] = None
    price: Decimal
    category: str
    type: Optional[str] = None
    itinerary: list[Any] = Field(default_factory=list)
    budget: list[Any] = Field(default_factory=list)
    included: list[Any] = Field(default_factory=list)
    notIncluded: list[Any] = Field(default_factory=list)
    cancellation: list[Any] = Field(default_factory=list)


class DemandeTeamBuildingCadreBase(ORMBaseModel):
    cadre: str


class DemandeTeamBuildingCadreCreate(DemandeTeamBuildingCadreBase):
    pass


class DemandeTeamBuildingCadreRead(DemandeTeamBuildingCadreBase):
    id: int
    demande_team_building_id: int


class DemandeTeamBuildingBase(ORMBaseModel):
    entreprise: str
    nom_contact: str
    fonction_contact: Optional[str] = None
    telephone_contact: str
    email_contact: str
    nombre_participants: int
    objectif: str
    lieu_souhaite: Optional[str] = None
    date_souhaitee: Optional[date] = None
    type_activite: Optional[str] = None
    avec_salle: Optional[bool] = False
    avec_nuitee: Optional[bool] = False
    nombre_nuitees: Optional[int] = 0
    transport_inclus: Optional[bool] = False
    restauration_incluse: Optional[bool] = False
    hebergement_inclus: Optional[bool] = False
    experience_precedente: Optional[str] = None
    source_decouverte: Optional[str] = None
    source: Optional[str] = "site_web"
    statut: Optional[str] = "nouvelle"


class DemandeTeamBuildingCreate(DemandeTeamBuildingBase):
    cadres: list[DemandeTeamBuildingCadreCreate] = []


class DemandeTeamBuildingRead(DemandeTeamBuildingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    cadres: list[DemandeTeamBuildingCadreRead] = []


class DemandeContactBase(ORMBaseModel):
    nom_complet: str
    email: str
    sujet: Optional[str] = None
    message: str
    type_demande: Optional[str] = "autre"
    source: Optional[str] = "site_web"
    statut: Optional[str] = "nouvelle"


class DemandeContactCreate(DemandeContactBase):
    pass




class DemandeContactRead(DemandeContactBase):
    id: int
    created_at: datetime
    updated_at: datetime


class UtilisateurBase(ORMBaseModel):
    nom: str
    prenom: Optional[str] = None
    email: str
    role: Optional[str] = None
    id_role: Optional[int] = None
    actif: Optional[bool] = True
    id_utilisateur_create: Optional[int] = None
    image_utilisateur: Optional[str] = None


class UtilisateurCreate(ORMBaseModel):
    nom: str
    prenom: Optional[str] = None
    email: str
    mot_de_passe: str
    role: Optional[str] = None
    id_role: Optional[int] = None
    actif: Optional[bool] = True
    id_utilisateur_create: Optional[int] = None
    image_utilisateur: Optional[str] = None


class RoleRead(ORMBaseModel):
    id_role: int
    nom_role: str


class RoleCreate(ORMBaseModel):
    nom_role: str


class RoleUpdate(ORMBaseModel):
    nom_role: Optional[str] = None


class UtilisateurRead(UtilisateurBase):
    id_utilisateur: int
    date_creation: datetime


class UtilisateurUpdate(ORMBaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    id_role: Optional[int] = None
    actif: Optional[bool] = None
    id_utilisateur_create: Optional[int] = None
    image_utilisateur: Optional[str] = None


class LoginRequest(ORMBaseModel):
    email: str
    password: str


class RefreshTokenRequest(ORMBaseModel):
    refresh_token: str


class AuthUserResponse(ORMBaseModel):
    id_utilisateur: int
    nom: str
    prenom: Optional[str] = None
    email: str
    role: Optional[str] = None
    id_role: Optional[int] = None
    actif: Optional[bool] = True
    date_creation: Optional[datetime] = None
    image_utilisateur: Optional[str] = None


class LoginResponse(ORMBaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


class RefreshTokenResponse(ORMBaseModel):
    access_token: str
    token_type: str = "bearer"


class DemandeTourismeCustumerBase(ORMBaseModel):
    prenom: str
    nom: str
    email: str
    telephone: Optional[str] = None
    nb_personnes: int = 1
    nb_jours: Optional[int] = None
    lieu_souhaite: Optional[str] = None
    attente_voyage: Optional[str] = None
    statut: Optional[DemandeTourismeStatut] = "nouvelle"


class DemandeTourismeCustom(DemandeTourismeCustumerBase):
    id: int
    statut_modifie_le: Optional[datetime] = None
    statut_modifie_par_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DemandeTourismeCustumerCreate(DemandeTourismeCustumerBase):
    pass
