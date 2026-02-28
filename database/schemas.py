from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover
    ConfigDict = None


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
