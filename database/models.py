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
    func,
    text,
)
from sqlalchemy.orm import relationship

from database.base import Base


class Client(Base):
    __tablename__ = "client"

    id_client = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=True)
    entreprise = Column(String(150), nullable=True)
    email = Column(String(150), unique=True, nullable=True)
    telephone = Column(String(20), nullable=True)
    adresse = Column(Text, nullable=True)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    demandes = relationship("Demande", back_populates="client", cascade="all, delete-orphan")


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
    offres = relationship("Offre", back_populates="demande", cascade="all, delete-orphan")


class ContactAkan(Base):
    __tablename__ = "contact_akan"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenoms = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, nullable=True)
    telephone = Column(String(20), nullable=True)
    has_won = Column(Boolean, nullable=True, default=False)
    





class Offre(Base):
    __tablename__ = "offre"
    __table_args__ = (
        CheckConstraint(
            "statut_offre IN ('brouillon','envoyee','validee','refusee')",
            name="ck_offre_statut",
        ),
    )

    id_offre = Column(Integer, primary_key=True, index=True)
    date_creation = Column(Date, nullable=True, server_default=func.current_date())
    montant_propose = Column(Numeric(12, 2), nullable=False)
    statut_offre = Column(
        String(30),
        nullable=False,
        default="brouillon",
        server_default=text("'brouillon'"),
    )
    id_demande = Column(Integer, ForeignKey("demande.id_demande", ondelete="CASCADE"), nullable=False)
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    demande = relationship("Demande", back_populates="offres")
    activite = relationship("Activite", back_populates="offre", uselist=False)


class Site(Base):
    __tablename__ = "site"
    __table_args__ = (CheckConstraint("capacite > 0", name="ck_site_capacite_pos"),)

    id_site = Column(Integer, primary_key=True, index=True)
    nom_site = Column(String(150), nullable=False)
    localisation = Column(String(150), nullable=True)
    capacite = Column(Integer, nullable=True)
    type_site = Column(String(50), nullable=True)
    image_site = Column(String(500), nullable=True)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    activites = relationship("Activite", back_populates="site")


class Activite(Base):
    __tablename__ = "activite"
    __table_args__ = (
        CheckConstraint(
            "statut IN ('planifiee','en_cours','terminee','annulee')",
            name="ck_activite_statut",
        ),
    )

    id_activite = Column(Integer, primary_key=True, index=True)
    nom = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    date_debut = Column(DateTime, nullable=False)
    date_fin = Column(DateTime, nullable=False)
    statut = Column(
        String(30),
        nullable=False,
        default="planifiee",
        server_default=text("'planifiee'"),
    )
    id_offre = Column(
        Integer,
        ForeignKey("offre.id_offre", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    id_site = Column(Integer, ForeignKey("site.id_site"), nullable=False)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    offre = relationship("Offre", back_populates="activite")
    site = relationship("Site", back_populates="activites")
    activite_jeux = relationship("ActiviteJeu", back_populates="activite", cascade="all, delete-orphan")
    affectations = relationship("Affectation", back_populates="activite", cascade="all, delete-orphan")
    depenses = relationship("Depense", back_populates="activite", cascade="all, delete-orphan")


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

    activite_jeux = relationship("ActiviteJeu", back_populates="jeu", cascade="all, delete-orphan")


class ActiviteJeu(Base):
    __tablename__ = "activite_jeu"

    id_activite = Column(
        Integer,
        ForeignKey("activite.id_activite", ondelete="CASCADE"),
        primary_key=True,
    )
    id_jeu = Column(Integer, ForeignKey("jeu.id_jeu", ondelete="CASCADE"), primary_key=True)
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


class Affectation(Base):
    __tablename__ = "affectation"

    id_affectation = Column(Integer, primary_key=True, index=True)
    id_activite = Column(Integer, ForeignKey("activite.id_activite", ondelete="CASCADE"), nullable=False)
    id_personnel = Column(
        Integer,
        ForeignKey("personnel.id_personnel", ondelete="CASCADE"),
        nullable=False,
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


class Depense(Base):
    __tablename__ = "depense"
    __table_args__ = (CheckConstraint("montant >= 0", name="ck_depense_montant_non_neg"),)

    id_depense = Column(Integer, primary_key=True, index=True)
    libelle = Column(String(150), nullable=False)
    montant = Column(Numeric(12, 2), nullable=False)
    date_depense = Column(Date, nullable=True, server_default=func.current_date())
    type_depense = Column(String(100), nullable=True)
    id_activite = Column(Integer, ForeignKey("activite.id_activite", ondelete="CASCADE"), nullable=False)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
    id_utilisateur_create = Column(
        Integer,
        ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"),
        nullable=True,
    )

    activite = relationship("Activite", back_populates="depenses")


class DemandeTourisme(Base):
    __tablename__ = "demandes_tourisme"
    __table_args__ = (
        CheckConstraint("nombre_voyageurs > 0", name="ck_demandes_tourisme_nombre_voyageurs_pos"),
        CheckConstraint(
            "statut IN ('nouvelle', 'contactee', 'devis_envoye', 'confirmee', 'annulee')",
            name="ck_demandes_tourisme_statut",
        ),
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
        String(30),
        nullable=False,
        default="nouvelle",
        server_default=text("'nouvelle'"),
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class DemandeTourismeCustom(Base):
    __tablename__ = "demandes_tourisme_custom"
    __table_args__ = (
        CheckConstraint("nombre_personne > 0", name="ck_demandes_tourisme_custom_nombre_personne_pos"),
        CheckConstraint(
            "statut IN ('nouvelle', 'en_cours_de_traitement', 'traitee', 'annulee')",
            name="ck_demandes_tourisme_custom_statut",
        ),
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
    statut = Column(
        String(50),
        nullable=False,
        default="nouvelle",
        server_default=text("'nouvelle'"),
    )

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
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    cadres = relationship(
        "DemandeTeamBuildingCadre",
        back_populates="demande_team_building",
        cascade="all, delete-orphan",
    )


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
