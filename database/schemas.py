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
    "contactee",
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
    "contactee",
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
    role: Optional[str] = None
    secteur_activite: Optional[str] = None
    statut: Optional[str] = None
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
    role: Optional[str] = None
    secteur_activite: Optional[str] = None
    statut: Optional[str] = None
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


OffreStatut = Literal["brouillon", "envoyee", "validee", "refusee", "expiree", "annulee"]
DemandeTeamBuildingStatut = Literal["nouvelle", "contactee", "devis_envoye", "confirmee", "annulee"]


class OffreBase(ORMBaseModel):
    demande_id: int
    titre: str
    montant_total: Decimal
    version: int = 1
    statut: OffreStatut = "brouillon"
    date_envoi: Optional[date] = None
    date_validation: Optional[date] = None
    date_expiration: Optional[date] = None
    fichier_pptx: Optional[str] = None
    conditions_paiement: Optional[str] = None
    observations: Optional[str] = None
    id_utilisateur_cr: Optional[int] = None


class OffreCreate(OffreBase):
    pass


class OffreUpdate(ORMBaseModel):
    demande_id: Optional[int] = None
    titre: Optional[str] = None
    montant_total: Optional[Decimal] = None
    version: Optional[int] = None
    statut: Optional[OffreStatut] = None
    date_envoi: Optional[date] = None
    date_validation: Optional[date] = None
    date_expiration: Optional[date] = None
    fichier_pptx: Optional[str] = None
    conditions_paiement: Optional[str] = None
    observations: Optional[str] = None
    id_utilisateur_cr: Optional[int] = None


class OffreRead(OffreBase):
    id: int
    reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime


ProformaStatut = Literal["brouillon", "validee", "pdf_genere", "annulee"]
ProformaPole = Literal["teambuilding", "tourisme"]


class ProformaBase(ORMBaseModel):
    pole: ProformaPole = "teambuilding"
    demande_team_building_id: Optional[int] = None
    offre_id: Optional[int] = None
    demande_tourisme_id: Optional[int] = None
    demande_tourisme_custom_id: Optional[int] = None
    offre_tourisme_id: Optional[int] = None
    site_id: Optional[int] = None
    client: str
    nombre_personnes: int
    objet: str
    date_proforma: date
    date_evenement: Optional[date] = None
    sections: list[dict[str, Any]] = Field(default_factory=list)
    frais_agence: Decimal = Decimal("0")
    details_frais_agence: list[str] = Field(default_factory=list)
    taux_tva_frais_agence: Decimal = Decimal("18")
    modalite_paiement: Optional[str] = None
    recommandations: list[dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None
    statut: ProformaStatut = "validee"


class ProformaCreate(ProformaBase):
    pass


class ProformaUpdate(ORMBaseModel):
    pole: Optional[ProformaPole] = None
    demande_team_building_id: Optional[int] = None
    offre_id: Optional[int] = None
    demande_tourisme_id: Optional[int] = None
    demande_tourisme_custom_id: Optional[int] = None
    offre_tourisme_id: Optional[int] = None
    site_id: Optional[int] = None
    client: Optional[str] = None
    nombre_personnes: Optional[int] = None
    objet: Optional[str] = None
    date_proforma: Optional[date] = None
    date_evenement: Optional[date] = None
    sections: Optional[list[dict[str, Any]]] = None
    frais_agence: Optional[Decimal] = None
    details_frais_agence: Optional[list[str]] = None
    taux_tva_frais_agence: Optional[Decimal] = None
    modalite_paiement: Optional[str] = None
    recommandations: Optional[list[dict[str, Any]]] = None
    notes: Optional[str] = None
    statut: Optional[ProformaStatut] = None


class ProformaRead(ProformaBase):
    id: int
    reference: str
    sous_total_ht: Decimal
    tva_frais_agence: Decimal
    total_ttc: Decimal
    fichier_pdf: Optional[str] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ProformaAssistantSessionCreate(ORMBaseModel):
    demande_id: Optional[int] = None
    offre_id: Optional[int] = None


class ProformaAssistantMessageCreate(ORMBaseModel):
    message: str


class ProformaAssistantResponse(ORMBaseModel):
    session_id: str
    response: str
    collected_fields: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    draft: Optional[dict[str, Any]] = None


class OffreTourismeBase(ORMBaseModel):
    demande_tourisme_id: Optional[int] = None
    demande_tourisme_custom_id: Optional[int] = None
    titre: str
    montant_total: Decimal
    version: int = 1
    statut: OffreStatut = "brouillon"
    date_envoi: Optional[date] = None
    date_validation: Optional[date] = None
    date_expiration: Optional[date] = None
    conditions_paiement: Optional[str] = None
    observations: Optional[str] = None


class OffreTourismeCreate(OffreTourismeBase):
    pass


class OffreTourismeUpdate(ORMBaseModel):
    demande_tourisme_id: Optional[int] = None
    demande_tourisme_custom_id: Optional[int] = None
    titre: Optional[str] = None
    montant_total: Optional[Decimal] = None
    version: Optional[int] = None
    statut: Optional[OffreStatut] = None
    date_envoi: Optional[date] = None
    date_validation: Optional[date] = None
    date_expiration: Optional[date] = None
    conditions_paiement: Optional[str] = None
    observations: Optional[str] = None


class OffreTourismeRead(OffreTourismeBase):
    id: int
    reference: str
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class SiteBase(ORMBaseModel):
    nom_site: str
    localisation: Optional[str] = None
    capacite: Optional[int] = None
    type_site: Optional[str] = None
    date_creation: Optional[datetime] = None
    contact_site: Optional[str] = None
    email_site: Optional[str] = None
    id_utilisateur_create: Optional[int] = None
    images: list[Any] = Field(default_factory=list)
    a_restauration: bool = False
    tarifs_restauration: Optional[dict[str, Any]] = None
    a_salle_seminaire: bool = False
    tarifs_seminaire: Optional[dict[str, Any]] = None


class SiteCreate(SiteBase):
    pass


class SiteRead(SiteBase):
    id_site: int
    images: list[Any] = Field(default_factory=list)


ActiviteStatut = Literal["brouillon", "planifier", "en_preparation", "en_cours", "terminer", "annuler"]


class ActiviteBase(ORMBaseModel):
    titre: str
    description: Optional[str] = None
    client_id: Optional[int] = None
    demande_id: Optional[int] = None
    offre_id: Optional[int] = None
    date_debut: datetime
    date_fin: datetime
    nombre_participants: Optional[int] = None
    site_id: int
    responsable_id: Optional[int] = None
    budget_previsionnel: Optional[Decimal] = None
    statut: ActiviteStatut = "planifier"
    observations: Optional[str] = None
    id_utilisateur_create: Optional[int] = None


class ActiviteCreate(ActiviteBase):
    pass


class ActiviteUpdate(ORMBaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[int] = None
    demande_id: Optional[int] = None
    offre_id: Optional[int] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    nombre_participants: Optional[int] = None
    site_id: Optional[int] = None
    responsable_id: Optional[int] = None
    budget_previsionnel: Optional[Decimal] = None
    statut: Optional[ActiviteStatut] = None
    observations: Optional[str] = None
    id_utilisateur_create: Optional[int] = None


class ActiviteRead(ActiviteBase):
    id: int
    reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JeuMaterielInput(ORMBaseModel):
    materiel_id: int
    quantite_requise: int = Field(default=1, gt=0)


class JeuMaterielRead(JeuMaterielInput):
    id: int
    jeu_id: int
    created_at: datetime


class JeuBase(ORMBaseModel):
    nom_jeu: str
    description: Optional[str] = None
    duree: Optional[int] = None
    nb_min_participants: Optional[int] = None
    nb_max_participants: Optional[int] = None
    nb_participant_max: Optional[int] = None
    materiel_requis: Optional[str] = None
    image_jeux: Optional[str] = None
    materiels: list[JeuMaterielRead] = Field(default_factory=list)
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class JeuCreate(JeuBase):
    materiels: list[JeuMaterielInput] = Field(default_factory=list)


class JeuUpdate(ORMBaseModel):
    nom_jeu: Optional[str] = None
    description: Optional[str] = None
    duree: Optional[int] = None
    nb_min_participants: Optional[int] = None
    nb_max_participants: Optional[int] = None
    nb_participant_max: Optional[int] = None
    materiel_requis: Optional[str] = None
    image_jeux: Optional[str] = None
    materiels: Optional[list[JeuMaterielInput]] = None


class JeuRead(JeuBase):
    id_jeu: int


class ActiviteJeuBase(ORMBaseModel):
    activite_id: int
    jeu_id: int
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


class BenevoleBase(ORMBaseModel):
    nom: str
    prenoms: str
    email: str
    telephone: Optional[str] = None
    lieu_habitation: Optional[str] = None
    experience: Optional[str] = None
    actif: Optional[bool] = True
    id_utilisateur_create: Optional[int] = None


class BenevoleCreate(BenevoleBase):
    pass


class BenevoleUpdate(ORMBaseModel):
    nom: Optional[str] = None
    prenoms: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    lieu_habitation: Optional[str] = None
    experience: Optional[str] = None
    actif: Optional[bool] = None
    id_utilisateur_create: Optional[int] = None


class BenevoleRead(BenevoleBase):
    id: int
    created_at: datetime
    updated_at: datetime


class AffectationBase(ORMBaseModel):
    activite_id: int
    personnel_id: int
    role: Optional[str] = None
    heure_debut: Optional[datetime] = None
    heure_fin: Optional[datetime] = None
    date_creation: Optional[datetime] = None
    id_utilisateur_create: Optional[int] = None


class AffectationCreate(AffectationBase):
    pass


class AffectationRead(AffectationBase):
    id_affectation: int


class ActiviteBenevoleBase(ORMBaseModel):
    activite_id: int
    benevole_id: int
    role: Optional[str] = None


class ActiviteBenevoleCreate(ActiviteBenevoleBase):
    pass


class ActiviteBenevoleUpdate(ORMBaseModel):
    role: Optional[str] = None


class ActiviteBenevoleRead(ActiviteBenevoleBase):
    id: int
    created_at: datetime


class MaterielBase(ORMBaseModel):
    nom: str
    marque: Optional[str] = None
    modele: Optional[str] = None
    description: Optional[str] = None
    quantite_disponible: int = Field(default=0, ge=0)
    statut: Optional[bool] = True
    id_utilisateur_create: Optional[int] = None


class MaterielCreate(MaterielBase):
    pass


class MaterielUpdate(ORMBaseModel):
    nom: Optional[str] = None
    marque: Optional[str] = None
    modele: Optional[str] = None
    description: Optional[str] = None
    quantite_disponible: Optional[int] = Field(default=None, ge=0)
    statut: Optional[bool] = None
    id_utilisateur_create: Optional[int] = None


class MaterielRead(MaterielBase):
    id: int
    date_ajout: datetime


class MaterielProductionBase(ORMBaseModel):
    marque: str = Field(min_length=1, max_length=100)
    modele: str = Field(min_length=1, max_length=150)
    quantite: int = Field(default=0, ge=0)


class MaterielProductionCreate(MaterielProductionBase):
    pass


class MaterielProductionUpdate(ORMBaseModel):
    marque: Optional[str] = Field(default=None, min_length=1, max_length=100)
    modele: Optional[str] = Field(default=None, min_length=1, max_length=150)
    quantite: Optional[int] = Field(default=None, ge=0)


class MaterielProductionRead(MaterielProductionBase):
    id: int
    date_ajout: datetime


class ActiviteMaterielBase(ORMBaseModel):
    activite_id: int
    materiel_id: int
    quantite_prevue: int = Field(default=1, gt=0)
    quantite_utilisee: Optional[int] = Field(default=None, ge=0)


class ActiviteMaterielCreate(ActiviteMaterielBase):
    pass


class ActiviteMaterielUpdate(ORMBaseModel):
    quantite_prevue: Optional[int] = Field(default=None, gt=0)
    quantite_utilisee: Optional[int] = Field(default=None, ge=0)


class ActiviteMaterielRead(ActiviteMaterielBase):
    id: int
    created_at: datetime


class MaterielDisponibiliteRead(ORMBaseModel):
    materiel_id: int
    quantite_totale: int
    quantite_reservee: int
    quantite_disponible: int


ModePaiementDepense = Literal[
    "ESPECES",
    "WAVE",
    "ORANGE_MONEY",
    "MTN_MONEY",
    "VIREMENT",
    "CHEQUE",
    "CARTE_BANCAIRE",
]


class CategorieDepenseBase(ORMBaseModel):
    nom: str


class CategorieDepenseCreate(CategorieDepenseBase):
    pass


class CategorieDepenseUpdate(ORMBaseModel):
    nom: Optional[str] = None


class CategorieDepenseRead(CategorieDepenseBase):
    id: int


class DepenseBase(ORMBaseModel):
    titre: str
    montant: Decimal
    description: Optional[str] = None
    date_depense: Optional[date] = None
    categorie_depense_id: Optional[int] = None
    offre_id: Optional[int] = None
    activite_id: int
    fournisseur: Optional[str] = None
    mode_paiement: Optional[ModePaiementDepense] = None
    type_depense: Optional[str] = None
    justificatif: Optional[str] = None
    id_utilisateur_cr: Optional[int] = None


class DepenseCreate(DepenseBase):
    pass


class DepenseUpdate(ORMBaseModel):
    titre: Optional[str] = None
    montant: Optional[Decimal] = None
    description: Optional[str] = None
    date_depense: Optional[date] = None
    categorie_depense_id: Optional[int] = None
    offre_id: Optional[int] = None
    activite_id: Optional[int] = None
    fournisseur: Optional[str] = None
    mode_paiement: Optional[ModePaiementDepense] = None
    type_depense: Optional[str] = None
    justificatif: Optional[str] = None
    id_utilisateur_cr: Optional[int] = None


class DepenseRead(DepenseBase):
    id: int
    reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime


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
    created_by_id: Optional[int] = None
    created_by_nom_complet: Optional[str] = None
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
    statut: Optional[DemandeTeamBuildingStatut] = "nouvelle"


class DemandeTeamBuildingCreate(DemandeTeamBuildingBase):
    cadres: list[DemandeTeamBuildingCadreCreate] = []


class DemandeTeamBuildingStatutUpdate(ORMBaseModel):
    statut: DemandeTeamBuildingStatut


class DemandeTeamBuildingRead(DemandeTeamBuildingBase):
    id: int
    statut_modifie_le: Optional[datetime] = None
    statut_modifie_par_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_by_nom_complet: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    cadres: list[DemandeTeamBuildingCadreRead] = []


class DemandeContactBase(ORMBaseModel):
    nom_complet: str
    email: str
    telephone: Optional[str] = None
    sujet: Optional[str] = None
    message: str
    type_demande: Optional[str] = "autre"
    source: Optional[str] = "site_web"
    statut: Optional[str] = "nouvelle"


class DemandeContactCreate(DemandeContactBase):
    telephone: str




class DemandeContactRead(DemandeContactBase):
    id: int
    created_at: datetime
    updated_at: datetime


class NewsletterSubscriptionBase(ORMBaseModel):
    email: str
    langue: Optional[str] = None
    source: Optional[str] = "site_web"
    consentement: bool = True


class NewsletterSubscriptionCreate(NewsletterSubscriptionBase):
    pass


class NewsletterSubscriptionUpdate(ORMBaseModel):
    email: Optional[str] = None
    langue: Optional[str] = None
    source: Optional[str] = None
    consentement: Optional[bool] = None
    actif: Optional[bool] = None


class NewsletterSubscriptionRead(NewsletterSubscriptionBase):
    id: int
    actif: bool
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
    derniere_connexion: Optional[datetime] = None


class UtilisateurActivityCreation(ORMBaseModel):
    key: str
    label: str
    count: int


class UtilisateurActivityMetric(ORMBaseModel):
    module: str
    label: str
    total_demandes: int
    demandes_traitees: int
    demandes_creees: int = 0
    offres_creees: int = 0
    elements_crees: int
    creations: list[UtilisateurActivityCreation] = Field(default_factory=list)


class UtilisateurActivitySummary(ORMBaseModel):
    id_utilisateur: int
    role: Optional[str] = None
    modules: list[str] = Field(default_factory=list)
    derniere_connexion: Optional[datetime] = None
    total_demandes: int = 0
    demandes_traitees: int = 0
    demandes_creees: int = 0
    offres_creees: int = 0
    taux_traitement: float = 0
    elements_crees: int = 0
    metrics: list[UtilisateurActivityMetric] = Field(default_factory=list)


class UtilisateurUpdate(ORMBaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    id_role: Optional[int] = None
    actif: Optional[bool] = None
    id_utilisateur_create: Optional[int] = None
    image_utilisateur: Optional[str] = None


class UtilisateurProfileUpdate(ORMBaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, min_length=3, max_length=150)
    image_utilisateur: Optional[str] = Field(default=None, max_length=500)

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True, extra="forbid")
    else:  # pragma: no cover
        class Config:
            orm_mode = True
            extra = "forbid"


class UtilisateurPasswordChange(ORMBaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True, extra="forbid")
    else:  # pragma: no cover
        class Config:
            orm_mode = True
            extra = "forbid"


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
    derniere_connexion: Optional[datetime] = None
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
    source: Optional[str] = "site_web"
    statut: Optional[DemandeTourismeStatut] = "nouvelle"


class DemandeTourismeCustom(DemandeTourismeCustumerBase):
    id: int
    statut_modifie_le: Optional[datetime] = None
    statut_modifie_par_id: Optional[int] = None
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_by_nom_complet: Optional[str] = None
    updated_by_nom_complet: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DemandeTourismeCustumerCreate(DemandeTourismeCustumerBase):
    pass
