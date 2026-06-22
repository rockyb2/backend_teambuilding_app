import binascii
import hashlib
import hmac
import os

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database.base import Base


DEMANDE_TOURISME_STATUT_CHECK = (
    "statut IN ("
    "'nouvelle',"
    "'contactee',"
    "'en_traitement',"
    "'devis_envoye',"
    "'en_attente_reponse_client',"
    "'relance_envoyee',"
    "'validee',"
    "'annulee',"
    "'refusee',"
    "'terminee'"
    ")"
)


class Client(Base):
    __tablename__ = "client"

    id_client = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=True)
    entreprise = Column(String(150), nullable=True)
    role = Column(String(100), nullable=True)
    secteur_activite = Column(String(150), nullable=True)
    email = Column(String(150), unique=True, nullable=True)
    telephone = Column(String(20), nullable=True)
    statut = Column(String(50), nullable=True)
    adresse = Column(Text, nullable=True)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    demandes = relationship("Demande", back_populates="client", cascade="all, delete-orphan")
    activites = relationship("Activite", back_populates="client")


class Demande(Base):
    __tablename__ = "demande"
    __table_args__ = (
        CheckConstraint("nombre_participants > 0", name="ck_demande_nombre_participants_pos"),
        CheckConstraint(
            "statut IN ('en_attente','en_etude','validee','refusee')",
            name="ck_demande_statut",
        ),
        CheckConstraint(
            "source IN ('client','interne')",
            name="ck_demande_source",
        ),
    )

    id_demande = Column(Integer, primary_key=True, index=True)
    date_demande = Column(Date, nullable=False, server_default=func.current_date())
    description = Column(Text, nullable=True)
    nombre_participants = Column(Integer, nullable=True)
    budget_estime = Column(Numeric(12, 2), nullable=True)
    statut = Column(
        String(30),
        nullable=False,
        default="en_attente",
        server_default=text("'en_attente'"),
    )
    source = Column(
        String(30),
        nullable=False,
        default="client",
        server_default=text("'client'"),
    )
    id_client = Column(
        Integer,
        ForeignKey("client.id_client", ondelete="CASCADE"),
        nullable=False,
    )
    id_utilisateur = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    client = relationship("Client", back_populates="demandes")
    utilisateur = relationship(
        "Utilisateur",
        back_populates="demandes",
        foreign_keys=[id_utilisateur],
    )
class ContactAkan(Base):
    __tablename__ = "contact_akan"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenoms = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, nullable=True)
    telephone = Column(String(20), nullable=True)
    has_won = Column(Boolean, nullable=True, default=False)
    


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    langue = Column(String(10), nullable=True)
    source = Column(String(50), nullable=False, default="site_web", server_default=text("'site_web'"))
    consentement = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    actif = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

# Modèles pour les teambuildings debut

class Offre(Base):
    __tablename__ = "offre"
    __table_args__ = (
        CheckConstraint(
            "statut IN ('brouillon','envoyee','validee','refusee','expiree','annulee')",
            name="ck_offre_statut",
        ),
        CheckConstraint("montant_total >= 0", name="ck_offre_montant_total_non_negatif"),
    )

    id = Column(Integer, primary_key=True, index=True)
    demande_id = Column(
        Integer,
        ForeignKey("demandes_team_building.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reference = Column(String(50), nullable=True, unique=True, index=True)
    titre = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=1, server_default=text("1"))
    statut = Column(
        String(30),
        nullable=False,
        default="brouillon",
        server_default=text("'brouillon'"),
    )
    montant_total = Column(Numeric(12, 2), nullable=False)
    date_envoi = Column(Date, nullable=True)
    date_validation = Column(Date, nullable=True)
    date_expiration = Column(Date, nullable=True)
    fichier_pptx = Column(String(500), nullable=True)
    conditions_paiement = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    id_utilisateur_cr = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    demande = relationship("DemandeTeamBuilding", back_populates="offres")
    activite = relationship("Activite", back_populates="offre", uselist=False)
    depenses = relationship("Depense", back_populates="offre")
    proformas = relationship("Proforma", back_populates="offre")


class OffreTourisme(Base):
    __tablename__ = "offre_tourisme"
    __table_args__ = (
        CheckConstraint(
            (
                "(demande_tourisme_id IS NOT NULL AND demande_tourisme_custom_id IS NULL) "
                "OR "
                "(demande_tourisme_id IS NULL AND demande_tourisme_custom_id IS NOT NULL)"
            ),
            name="ck_offre_tourisme_une_seule_demande",
        ),
        CheckConstraint(
            "statut IN ('brouillon','envoyee','validee','refusee','expiree','annulee')",
            name="ck_offre_tourisme_statut",
        ),
        CheckConstraint(
            "montant_total >= 0",
            name="ck_offre_tourisme_montant_total_non_negatif",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    demande_tourisme_id = Column(
        Integer,
        ForeignKey("demandes_tourisme.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    demande_tourisme_custom_id = Column(
        Integer,
        ForeignKey("demandes_tourisme_custom.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    reference = Column(String(50), nullable=False, unique=True, index=True)
    titre = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=1, server_default=text("1"))
    statut = Column(
        String(30),
        nullable=False,
        default="brouillon",
        server_default=text("'brouillon'"),
    )
    montant_total = Column(Numeric(12, 2), nullable=False)
    date_envoi = Column(Date, nullable=True)
    date_validation = Column(Date, nullable=True)
    date_expiration = Column(Date, nullable=True)
    conditions_paiement = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    created_by_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    demande_tourisme = relationship("DemandeTourisme", back_populates="offres")
    demande_tourisme_custom = relationship("DemandeTourismeCustom", back_populates="offres")
    created_by = relationship("Utilisateur", foreign_keys=[created_by_id])
    proformas = relationship("Proforma", back_populates="offre_tourisme")


class Site(Base):
    __tablename__ = "site"
    __table_args__ = (CheckConstraint("capacite > 0", name="ck_site_capacite_pos"),)

    id_site = Column(Integer, primary_key=True, index=True)
    nom_site = Column(String(150), nullable=False)
    localisation = Column(String(150), nullable=True)
    capacite = Column(Integer, nullable=True)
    type_site = Column(String(50), nullable=True)
    contact_site = Column(String(255), nullable=True)
    email_site = Column(String(255), nullable=True)
    images = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    a_restauration = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    tarifs_restauration = Column(JSONB(none_as_null=True), nullable=True)
    a_salle_seminaire = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    tarifs_seminaire = Column(JSONB(none_as_null=True), nullable=True)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    activites = relationship("Activite", back_populates="site")
    proformas = relationship("Proforma", back_populates="site")


class Activite(Base):
    __tablename__ = "activite"
    __table_args__ = (
        CheckConstraint(
            "statut IN ('brouillon','planifier','en_preparation','en_cours','terminer','annuler')",
            name="ck_activite_statut",
        ),
        CheckConstraint(
            "nombre_participants IS NULL OR nombre_participants > 0",
            name="ck_activite_nombre_participants_pos",
        ),
        CheckConstraint(
            "budget_previsionnel IS NULL OR budget_previsionnel >= 0",
            name="ck_activite_budget_previsionnel_non_neg",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), nullable=True, unique=True, index=True)
    titre = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    client_id = Column(Integer, ForeignKey("client.id_client", ondelete="SET NULL"), nullable=True, index=True)
    demande_id = Column(Integer, ForeignKey("demandes_team_building.id", ondelete="SET NULL"), nullable=True, index=True)
    offre_id = Column(
        Integer,
        ForeignKey("offre.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    date_debut = Column(DateTime, nullable=False)
    date_fin = Column(DateTime, nullable=False)
    nombre_participants = Column(Integer, nullable=True)
    site_id = Column(Integer, ForeignKey("site.id_site", ondelete="RESTRICT"), nullable=False, index=True)
    responsable_id = Column(
        Integer,
        ForeignKey("personnel.id_personnel", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    budget_previsionnel = Column(Numeric(12, 2), nullable=True)
    statut = Column(
        String(30),
        nullable=False,
        default="planifier",
        server_default=text("'planifier'"),
    )
    observations = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    client = relationship("Client", back_populates="activites")
    demande = relationship("DemandeTeamBuilding", back_populates="activites")
    offre = relationship("Offre", back_populates="activite")
    site = relationship("Site", back_populates="activites")
    responsable = relationship("Personnel", foreign_keys=[responsable_id], back_populates="activites_responsable")
    activite_jeux = relationship("ActiviteJeu", back_populates="activite", cascade="all, delete-orphan")
    affectations = relationship("Affectation", back_populates="activite", cascade="all, delete-orphan")
    activite_benevoles = relationship(
        "ActiviteBenevole",
        back_populates="activite",
        cascade="all, delete-orphan",
    )
    activite_materiels = relationship(
        "ActiviteMateriel",
        back_populates="activite",
        cascade="all, delete-orphan",
    )
    depenses = relationship("Depense", back_populates="activite")


class Jeu(Base):
    __tablename__ = "jeu"
    __table_args__ = (CheckConstraint("duree > 0", name="ck_jeu_duree_pos"),)

    id_jeu = Column(Integer, primary_key=True, index=True)
    nom_jeu = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    duree = Column(Integer, nullable=True)
    nb_min_participants = Column(Integer, nullable=True)
    nb_max_participants = Column(Integer, nullable=True)
    materiel_requis = Column(Text, nullable=True)
    image_jeux = Column(String(255), nullable=True)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    @property
    def nb_participant_max(self):
        return self.nb_max_participants

    @nb_participant_max.setter
    def nb_participant_max(self, value):
        self.nb_max_participants = value

    activite_jeux = relationship("ActiviteJeu", back_populates="jeu", cascade="all, delete-orphan")
    materiels = relationship(
        "JeuMateriel",
        back_populates="jeu",
        cascade="all, delete-orphan",
    )


class ActiviteJeu(Base):
    __tablename__ = "activite_jeu"

    activite_id = Column(
        Integer,
        ForeignKey("activite.id", ondelete="CASCADE"),
        primary_key=True,
    )
    jeu_id = Column(Integer, ForeignKey("jeu.id_jeu", ondelete="CASCADE"), primary_key=True)
    ordre = Column(Integer, nullable=True)
    duree_prevue = Column(Integer, nullable=True)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    activite = relationship("Activite", back_populates="activite_jeux")
    jeu = relationship("Jeu", back_populates="activite_jeux")


class Personnel(Base):
    __tablename__ = "personnel"

    id_personnel = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=True)
    fonction = Column(String(100), nullable=True)
    telephone = Column(String(20), nullable=True)
    email = Column(String(150), unique=True, nullable=True)
    adresse = Column(String(255), nullable=True)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    affectations = relationship("Affectation", back_populates="personnel", cascade="all, delete-orphan")
    activites_responsable = relationship("Activite", back_populates="responsable", foreign_keys="Activite.responsable_id")


class Benevole(Base):
    __tablename__ = "benevoles"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenoms = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    telephone = Column(String(30), nullable=True)
    lieu_habitation = Column(String(255), nullable=True)
    experience = Column(Text, nullable=True)
    actif = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    activite_benevoles = relationship(
        "ActiviteBenevole",
        back_populates="benevole",
        cascade="all, delete-orphan",
    )


class Affectation(Base):
    __tablename__ = "affectation"
    __table_args__ = (
        UniqueConstraint("activite_id", "personnel_id", name="uq_affectation_activite_personnel"),
    )

    id_affectation = Column(Integer, primary_key=True, index=True)
    activite_id = Column(Integer, ForeignKey("activite.id", ondelete="CASCADE"), nullable=False, index=True)
    personnel_id = Column(
        Integer,
        ForeignKey("personnel.id_personnel", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(100), nullable=True)
    heure_debut = Column(DateTime, nullable=True)
    heure_fin = Column(DateTime, nullable=True)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    activite = relationship("Activite", back_populates="affectations")
    personnel = relationship("Personnel", back_populates="affectations")


class ActiviteBenevole(Base):
    __tablename__ = "activite_benevole"
    __table_args__ = (
        UniqueConstraint("activite_id", "benevole_id", name="uq_activite_benevole"),
    )

    id = Column(Integer, primary_key=True, index=True)
    activite_id = Column(
        Integer,
        ForeignKey("activite.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    benevole_id = Column(
        Integer,
        ForeignKey("benevoles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    activite = relationship("Activite", back_populates="activite_benevoles")
    benevole = relationship("Benevole", back_populates="activite_benevoles")


class CategorieDepense(Base):
    __tablename__ = "categorie_depense"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False, unique=True, index=True)

    depenses = relationship("Depense", back_populates="categorie")


class Depense(Base):
    __tablename__ = "depense"
    __table_args__ = (
        CheckConstraint("montant >= 0", name="ck_depense_montant_non_neg"),
        CheckConstraint(
            "mode_paiement IS NULL OR mode_paiement IN ("
            "'ESPECES',"
            "'WAVE',"
            "'ORANGE_MONEY',"
            "'MTN_MONEY',"
            "'VIREMENT',"
            "'CHEQUE',"
            "'CARTE_BANCAIRE'"
            ")",
            name="ck_depense_mode_paiement",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), nullable=True, unique=True, index=True)
    titre = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    montant = Column(Numeric(12, 2), nullable=False)
    date_depense = Column(Date, nullable=True, server_default=func.current_date())
    categorie_depense_id = Column(
        Integer,
        ForeignKey("categorie_depense.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    offre_id = Column(Integer, ForeignKey("offre.id", ondelete="SET NULL"), nullable=True, index=True)
    activite_id = Column(Integer, ForeignKey("activite.id", ondelete="CASCADE"), nullable=False, index=True)
    fournisseur = Column(String(255), nullable=True)
    mode_paiement = Column(String(50), nullable=True)
    type_depense = Column(String(100), nullable=True)
    justificatif = Column(String(500), nullable=True)
    id_utilisateur_cr = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    categorie = relationship("CategorieDepense", back_populates="depenses")
    offre = relationship("Offre", back_populates="depenses")
    activite = relationship("Activite", back_populates="depenses")



class DemandeTeamBuilding(Base):
    __tablename__ = "demandes_team_building"
    __table_args__ = (
        CheckConstraint(
            "nombre_participants > 0",
            name="ck_demandes_team_building_nombre_participants_pos",
        ),
        CheckConstraint(
            "statut IN ('nouvelle', 'contactee', 'devis_envoye', 'confirmee', 'annulee')",
            name="ck_demandes_team_building_statut",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    entreprise = Column(String(255), nullable=False)
    nom_contact = Column(String(255), nullable=False)
    fonction_contact = Column(String(150), nullable=True)
    telephone_contact = Column(String(50), nullable=False)
    email_contact = Column(String(255), nullable=False, index=True)
    nombre_participants = Column(Integer, nullable=False)
    objectif = Column(Text, nullable=False)
    lieu_souhaite = Column(String(255), nullable=True)
    date_souhaitee = Column(Date, nullable=True)
    type_activite = Column(String(255), nullable=True)
    avec_salle = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    avec_nuitee = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    nombre_nuitees = Column(Integer, nullable=False, default=0, server_default=text("0"))
    transport_inclus = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    restauration_incluse = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    hebergement_inclus = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    experience_precedente = Column(Text, nullable=True)
    source_decouverte = Column(String(255), nullable=True)
    source = Column(String(30), nullable=False, default="site_web", server_default=text("'site_web'"))
    statut = Column(
        String(30),
        nullable=False,
        default="nouvelle",
        server_default=text("'nouvelle'"),
    )
    statut_modifie_le = Column(DateTime(timezone=True), nullable=True)
    statut_modifie_par_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    statut_modifie_par = relationship("Utilisateur", foreign_keys=[statut_modifie_par_id])
    created_by = relationship("Utilisateur", foreign_keys=[created_by_id])
    cadres = relationship(
        "DemandeTeamBuildingCadre",
        back_populates="demande_team_building",
        cascade="all, delete-orphan",
    )
    offres = relationship("Offre", back_populates="demande", cascade="all, delete-orphan")
    activites = relationship("Activite", back_populates="demande")
    proformas = relationship("Proforma", back_populates="demande")

    @property
    def created_by_nom_complet(self) -> str | None:
        if not self.created_by:
            return None
        return " ".join(
            value.strip()
            for value in (self.created_by.prenom, self.created_by.nom)
            if value and value.strip()
        ) or self.created_by.email


class DemandeTeamBuildingCadre(Base):
    __tablename__ = "demandes_team_building_cadres"
    __table_args__ = (
        CheckConstraint(
            "cadre IN ('interieur', 'plein_air', 'mixte')",
            name="ck_demandes_team_building_cadres_cadre",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    demande_team_building_id = Column(
        Integer,
        ForeignKey("demandes_team_building.id", ondelete="CASCADE"),
        nullable=False,
    )
    cadre = Column(String(30), nullable=False)

    demande_team_building = relationship("DemandeTeamBuilding", back_populates="cadres")


class Materiel(Base):
    __tablename__ = "materiel"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(150), nullable=False)
    marque = Column(String(100), nullable=True, index=True)
    modele = Column(String(150), nullable=True, index=True)
    description = Column(Text, nullable=True)
    quantite_disponible = Column(Integer, nullable=False, default=0, server_default=text("0"))
    date_ajout = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    statut = Column(Boolean, nullable=True, default=True, server_default=text("true"))

    activite_materiels = relationship(
        "ActiviteMateriel",
        back_populates="materiel",
        cascade="all, delete-orphan",
    )

    @property
    def quantite(self) -> int:
        return self.quantite_disponible

    @quantite.setter
    def quantite(self, value: int) -> None:
        self.quantite_disponible = value
    jeu_materiels = relationship(
        "JeuMateriel",
        back_populates="materiel",
        cascade="all, delete-orphan",
    )


class Proforma(Base):
    __tablename__ = "proformas"
    __table_args__ = (
        CheckConstraint(
            "pole IN ('teambuilding','tourisme')",
            name="ck_proformas_pole",
        ),
        CheckConstraint(
            "statut IN ('brouillon','validee','pdf_genere','annulee')",
            name="ck_proformas_statut",
        ),
        CheckConstraint("nombre_personnes > 0", name="ck_proformas_nombre_personnes_pos"),
        CheckConstraint("sous_total_ht >= 0", name="ck_proformas_sous_total_ht_non_negatif"),
        CheckConstraint("frais_agence >= 0", name="ck_proformas_frais_agence_non_negatif"),
        CheckConstraint("tva_frais_agence >= 0", name="ck_proformas_tva_non_negatif"),
        CheckConstraint("total_ttc >= 0", name="ck_proformas_total_ttc_non_negatif"),
    )

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), nullable=False, unique=True, index=True)
    pole = Column(
        String(30),
        nullable=False,
        default="teambuilding",
        server_default=text("'teambuilding'"),
        index=True,
    )
    demande_team_building_id = Column(
        Integer,
        ForeignKey("demandes_team_building.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    offre_id = Column(
        Integer,
        ForeignKey("offre.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    demande_tourisme_id = Column(
        Integer,
        ForeignKey("demandes_tourisme.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    demande_tourisme_custom_id = Column(
        Integer,
        ForeignKey("demandes_tourisme_custom.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    offre_tourisme_id = Column(
        Integer,
        ForeignKey("offre_tourisme.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    site_id = Column(
        Integer,
        ForeignKey("site.id_site", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    client = Column(String(255), nullable=False)
    nombre_personnes = Column(Integer, nullable=False)
    objet = Column(String(255), nullable=False)
    date_proforma = Column(Date, nullable=False)
    date_evenement = Column(Date, nullable=True)
    sections = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    frais_agence = Column(Numeric(14, 2), nullable=False, default=0, server_default=text("0"))
    details_frais_agence = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    taux_tva_frais_agence = Column(Numeric(5, 2), nullable=False, default=18, server_default=text("18"))
    sous_total_ht = Column(Numeric(14, 2), nullable=False, default=0, server_default=text("0"))
    tva_frais_agence = Column(Numeric(14, 2), nullable=False, default=0, server_default=text("0"))
    total_ttc = Column(Numeric(14, 2), nullable=False, default=0, server_default=text("0"))
    modalite_paiement = Column(Text, nullable=True)
    recommandations = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    notes = Column(Text, nullable=True)
    statut = Column(
        String(30),
        nullable=False,
        default="brouillon",
        server_default=text("'brouillon'"),
    )
    fichier_pdf = Column(String(500), nullable=True)
    created_by_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    demande = relationship("DemandeTeamBuilding", back_populates="proformas")
    offre = relationship("Offre", back_populates="proformas")
    demande_tourisme = relationship("DemandeTourisme", back_populates="proformas")
    demande_tourisme_custom = relationship("DemandeTourismeCustom", back_populates="proformas")
    offre_tourisme = relationship("OffreTourisme", back_populates="proformas")
    site = relationship("Site", back_populates="proformas")
    created_by = relationship("Utilisateur", foreign_keys=[created_by_id], back_populates="proformas_creees")


class ActiviteMateriel(Base):
    __tablename__ = "activite_materiel"
    __table_args__ = (
        UniqueConstraint("activite_id", "materiel_id", name="uq_activite_materiel"),
        CheckConstraint("quantite_prevue > 0", name="ck_activite_materiel_quantite_prevue_pos"),
        CheckConstraint("quantite_utilisee IS NULL OR quantite_utilisee >= 0", name="ck_activite_materiel_quantite_utilisee_non_neg"),
    )

    id = Column(Integer, primary_key=True, index=True)
    activite_id = Column(
        Integer,
        ForeignKey("activite.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    materiel_id = Column(
        Integer,
        ForeignKey("materiel.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantite_prevue = Column(Integer, nullable=False, default=1, server_default=text("1"))
    quantite_utilisee = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    activite = relationship("Activite", back_populates="activite_materiels")
    materiel = relationship("Materiel", back_populates="activite_materiels")


class JeuMateriel(Base):
    __tablename__ = "jeu_materiel"
    __table_args__ = (
        UniqueConstraint("jeu_id", "materiel_id", name="uq_jeu_materiel"),
        CheckConstraint("quantite_requise > 0", name="ck_jeu_materiel_quantite_requise_pos"),
    )

    id = Column(Integer, primary_key=True, index=True)
    jeu_id = Column(
        Integer,
        ForeignKey("jeu.id_jeu", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    materiel_id = Column(
        Integer,
        ForeignKey("materiel.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantite_requise = Column(Integer, nullable=False, default=1, server_default=text("1"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    jeu = relationship("Jeu", back_populates="materiels")
    materiel = relationship("Materiel", back_populates="jeu_materiels")


class categorie_materiel(Base):
    __tablename__ = "categorie_materiel"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
# Modèles pour les teambuildings  Fin

# Modèles pouir les demandes de tourisme debut

class DemandeTourisme(Base):
    __tablename__ = "demandes_tourisme"
    __table_args__ = (
        CheckConstraint("nombre_voyageurs > 0", name="ck_demandes_tourisme_nombre_voyageurs_pos"),
        CheckConstraint(DEMANDE_TOURISME_STATUT_CHECK, name="ck_demandes_tourisme_statut"),
    )

    id = Column(Integer, primary_key=True, index=True)
    circuit_externe_id = Column(Integer, nullable=True)
    titre_circuit = Column(String(255), nullable=False)
    lieu_circuit = Column(String(255), nullable=True)
    duree_circuit = Column(String(120), nullable=True)
    formule_choisie = Column(String(100), nullable=True)
    prix_formule = Column(Numeric(12, 2), nullable=False, default=0, server_default=text("0"))
    date_depart_souhaitee = Column(Date, nullable=True)
    prenom = Column(String(120), nullable=False)
    nom = Column(String(120), nullable=False)
    telephone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    nombre_voyageurs = Column(Integer, nullable=False, default=1, server_default=text("1"))
    note_client = Column(Text, nullable=True)
    prix_total_estime = Column(Numeric(12, 2), nullable=False, default=0, server_default=text("0"))
    source = Column(String(30), nullable=False, default="site_web", server_default=text("'site_web'"))
    statut = Column(
        String(50),
        nullable=False,
        default="nouvelle",
        server_default=text("'nouvelle'"),
    )
    statut_modifie_le = Column(DateTime, nullable=True)
    statut_modifie_par_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    statut_modifie_par = relationship("Utilisateur", foreign_keys=[statut_modifie_par_id])
    created_by = relationship("Utilisateur", foreign_keys=[created_by_id])
    offres = relationship("OffreTourisme", back_populates="demande_tourisme", cascade="all, delete-orphan")
    proformas = relationship("Proforma", back_populates="demande_tourisme")

    @property
    def created_by_nom_complet(self) -> str | None:
        if not self.created_by:
            return None
        return " ".join(
            value.strip()
            for value in (self.created_by.prenom, self.created_by.nom)
            if value and value.strip()
        ) or self.created_by.email


class DemandeTourismeCustom(Base):
    __tablename__ = "demandes_tourisme_custom"
    __table_args__ = (
        CheckConstraint("nombre_personne > 0", name="ck_demandes_tourisme_custom_nombre_personne_pos"),
        CheckConstraint(DEMANDE_TOURISME_STATUT_CHECK, name="ck_demandes_tourisme_custom_statut"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nom_client = Column(String(255), nullable=False)
    prenoms_client = Column(String(255), nullable=False)
    email_client = Column(String(255), nullable=False, index=True)
    numero_telephone_client = Column(String(50), nullable=False)
    nombre_personne = Column(Integer, nullable=False, default=1, server_default=text("1"))
    nombre_jours = Column(Integer, nullable=True)
    lieu_souhaite = Column(String(255), nullable=True)
    attente_voyage = Column(Text, nullable=True)
    source = Column(String(30), nullable=False, default="site_web", server_default=text("'site_web'"))
    statut = Column(
        String(50),
        nullable=False,
        default="nouvelle",
        server_default=text("'nouvelle'"),
    )
    statut_modifie_le = Column(DateTime, nullable=True)
    statut_modifie_par_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    statut_modifie_par = relationship("Utilisateur", foreign_keys=[statut_modifie_par_id])
    created_by = relationship("Utilisateur", foreign_keys=[created_by_id])
    updated_by = relationship("Utilisateur", foreign_keys=[updated_by_id])
    offres = relationship("OffreTourisme", back_populates="demande_tourisme_custom", cascade="all, delete-orphan")
    proformas = relationship("Proforma", back_populates="demande_tourisme_custom")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    @property
    def nom(self) -> str:
        return self.nom_client

    @property
    def prenom(self) -> str:
        return self.prenoms_client

    @property
    def email(self) -> str:
        return self.email_client

    @property
    def telephone(self) -> str:
        return self.numero_telephone_client

    @property
    def nb_personnes(self) -> int:
        return self.nombre_personne

    @property
    def nb_jours(self) -> int | None:
        return self.nombre_jours

    @staticmethod
    def _utilisateur_nom_complet(utilisateur) -> str | None:
        if not utilisateur:
            return None
        return " ".join(
            value.strip()
            for value in (utilisateur.prenom, utilisateur.nom)
            if value and value.strip()
        ) or utilisateur.email

    @property
    def created_by_nom_complet(self) -> str | None:
        return self._utilisateur_nom_complet(self.created_by)

    @property
    def updated_by_nom_complet(self) -> str | None:
        return self._utilisateur_nom_complet(self.updated_by)


class HistoriqueStatutDemandeTourisme(Base):
    __tablename__ = "historique_statut_demandes_tourisme"
    __table_args__ = (
        CheckConstraint(
            (
                "(demande_tourisme_id IS NOT NULL AND demande_tourisme_custom_id IS NULL) "
                "OR "
                "(demande_tourisme_id IS NULL AND demande_tourisme_custom_id IS NOT NULL)"
            ),
            name="ck_historique_statut_une_seule_demande_tourisme",
        ),
        CheckConstraint(
            "nouveau_statut IN ("
            "'nouvelle',"
            "'contactee',"
            "'en_traitement',"
            "'devis_envoye',"
            "'en_attente_reponse_client',"
            "'relance_envoyee',"
            "'validee',"
            "'annulee',"
            "'refusee',"
            "'terminee'"
            ")",
            name="ck_historique_statut_demande_tourisme_nouveau_statut",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    demande_tourisme_id = Column(
        Integer,
        ForeignKey("demandes_tourisme.id", ondelete="CASCADE"),
        nullable=True,
    )
    demande_tourisme_custom_id = Column(
        Integer,
        ForeignKey("demandes_tourisme_custom.id", ondelete="CASCADE"),
        nullable=True,
    )
    ancien_statut = Column(String(50), nullable=True)
    nouveau_statut = Column(String(50), nullable=False)
    commentaire = Column(Text, nullable=True)
    modifie_par_id = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    modifie_le = Column(DateTime, nullable=False, server_default=func.now())

    demande_tourisme = relationship("DemandeTourisme")
    demande_tourisme_custom = relationship("DemandeTourismeCustom")
    modifie_par = relationship("Utilisateur", foreign_keys=[modifie_par_id])


class CircuitTouristique(Base):
    __tablename__ = "circuits_touristiques"
    __table_args__ = (
        CheckConstraint("prix_base >= 0", name="ck_circuits_touristiques_prix_base_non_negatif"),
        CheckConstraint("categorie IN ('local', 'international')", name="ck_circuits_touristiques_categorie"),
    )

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(255), nullable=False)
    lieu = Column(String(255), nullable=True)
    thematique = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    details = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    duree = Column(String(120), nullable=True)
    prix_base = Column(Numeric(12, 2), nullable=False, default=0, server_default=text("0"))
    categorie = Column(String(50), nullable=False, default="local", server_default=text("'local'"))
    type_circuit = Column(String(100), nullable=True)
    images = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    itineraire = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    formules = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    inclus = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    non_inclus = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    conditions_annulation = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    actif = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    publie = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_by_id = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    created_by = relationship("Utilisateur", foreign_keys=[created_by_id])
    updated_by = relationship("Utilisateur", foreign_keys=[updated_by_id])
    translations = relationship(
        "CircuitTouristiqueTranslation",
        back_populates="circuit",
        cascade="all, delete-orphan",
    )

    @property
    def title(self) -> str:
        return self.titre

    @property
    def location(self) -> str | None:
        return self.lieu

    @property
    def thematic(self) -> str | None:
        return self.thematique

    @property
    def duration(self) -> str | None:
        return self.duree

    @property
    def price(self):
        return self.prix_base

    @property
    def category(self) -> str:
        return self.categorie

    @property
    def type(self) -> str | None:
        return self.type_circuit

    @property
    def itinerary(self):
        return self.itineraire

    @property
    def budget(self):
        return self.formules

    @property
    def included(self):
        return self.inclus

    @property
    def notIncluded(self):
        return self.non_inclus

    @property
    def cancellation(self):
        return self.conditions_annulation


class CircuitTouristiqueTranslation(Base):
    __tablename__ = "circuits_touristiques_translations"
    __table_args__ = (
        UniqueConstraint("circuit_id", "langue", name="uq_circuit_langue"),
        CheckConstraint("langue IN ('fr', 'en', 'es')", name="ck_circuit_translation_langue"),
    )

    id = Column(Integer, primary_key=True, index=True)
    circuit_id = Column(
        Integer,
        ForeignKey("circuits_touristiques.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    langue = Column(String(10), nullable=False, index=True)
    titre = Column(String(255), nullable=False)
    lieu = Column(String(255), nullable=True)
    thematique = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    details = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    duree = Column(String(120), nullable=True)
    type_circuit = Column(String(100), nullable=True)
    itineraire = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    formules = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    inclus = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    non_inclus = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    conditions_annulation = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    circuit = relationship("CircuitTouristique", back_populates="translations")

# Modèles pour les demandes de tourisme fin


# Modèles pour les demandes de contact debut

class DemandeContact(Base):
    __tablename__ = "demandes_contact"
    __table_args__ = (
        CheckConstraint(
            "type_demande IN ('tourisme', 'team_building', 'podcast', 'autre')",
            name="ck_demandes_contact_type_demande",
        ),
        CheckConstraint(
            "statut IN ('nouvelle', 'traitee', 'fermee')",
            name="ck_demandes_contact_statut",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    nom_complet = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    sujet = Column(String(120), nullable=True)
    message = Column(Text, nullable=False)
    type_demande = Column(
        String(30),
        nullable=False,
        default="autre",
        server_default=text("'autre'"),
    )
    source = Column(String(30), nullable=False, default="site_web", server_default=text("'site_web'"))
    statut = Column(
        String(30),
        nullable=False,
        default="nouvelle",
        server_default=text("'nouvelle'"),
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Role(Base):
    __tablename__ = "roles"

    id_role = Column("id", Integer, primary_key=True, index=True)
    nom_role = Column(String(50), unique=True, nullable=False)

    utilisateurs = relationship("Utilisateur", back_populates="role_rel")


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id_utilisateur = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, nullable=False)
    mot_de_passe = Column(String(255), nullable=False)
    id_role = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    actif = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    derniere_connexion = Column(DateTime(timezone=True), nullable=True)
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )
    image_utilisateur = Column(String(500), nullable=True)

    role_rel = relationship("Role", back_populates="utilisateurs")
    demandes = relationship(
        "Demande",
        back_populates="utilisateur",
        foreign_keys="Demande.id_utilisateur",
    )
    proformas_creees = relationship("Proforma", back_populates="created_by")

    @property
    def role(self) -> str | None:
        return self.role_rel.nom_role if self.role_rel else None

    def set_password(self, password: str) -> None:
        salt = os.urandom(16)
        iterations = 100_000
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        self.mot_de_passe = (
            f"pbkdf2_sha256${iterations}$"
            f"{binascii.hexlify(salt).decode()}$"
            f"{binascii.hexlify(dk).decode()}"
        )

    def check_password(self, password: str) -> bool:
        try:
            _, iter_str, salt_hex, dk_hex = self.mot_de_passe.split("$")
            iterations = int(iter_str)
            salt = binascii.unhexlify(salt_hex)
            expected = binascii.unhexlify(dk_hex)
            derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(derived, expected)
        except Exception:
            return False

# Modèles pour les demandes de contact fin
#Modèles pour
