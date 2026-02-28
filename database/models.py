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
import os
import hmac
import hashlib
import binascii


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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

    client = relationship("Client", back_populates="demandes")
    utilisateur = relationship(
        "Utilisateur",
        back_populates="demandes",
        foreign_keys=[id_utilisateur],
    )
    offres = relationship("Offre", back_populates="demande", cascade="all, delete-orphan")


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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)

    activite = relationship("Activite", back_populates="depenses")


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
    id_utilisateur_create = Column(Integer, ForeignKey("utilisateur.id_utilisateur", ondelete="SET NULL"), nullable=True)
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
        self.mot_de_passe = f"pbkdf2_sha256${iterations}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

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
