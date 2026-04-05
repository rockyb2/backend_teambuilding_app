from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

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


class LotBase(BaseModel):
    nom: str
    description: Optional[str] = None
    quantite: int = 1
    disponible: bool = True
    

class LotCreate(LotBase):
    pass

class LotResponse(LotBase):
    id: int

    class Config:
        from_attributes = True


class ORMBaseModel(BaseModel):
    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:  # pragma: no cover
        class Config:
            orm_mode = True


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
    statut: Optional[str] = "nouvelle"


class DemandeTourismeCreate(DemandeTourismeBase):
    pass


class DemandeTourismeRead(DemandeTourismeBase):
    id: int
    created_at: datetime
    updated_at: datetime


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


