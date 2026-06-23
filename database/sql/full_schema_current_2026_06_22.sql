-- Schema PostgreSQL complet genere depuis les modeles SQLAlchemy
-- Projet: backend_teambuilding_app
-- Date: 2026-06-22
-- Usage: base neuve ou base de test videe. Pour une prod existante, utiliser plutot render_catchup_2026_06_22.sql.

BEGIN;


CREATE TABLE IF NOT EXISTS categorie_depense (
	id SERIAL NOT NULL, 
	nom VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS contact_akan (
	id SERIAL NOT NULL, 
	nom VARCHAR(100) NOT NULL, 
	prenoms VARCHAR(100), 
	email VARCHAR(150), 
	telephone VARCHAR(20), 
	has_won BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);


CREATE TABLE IF NOT EXISTS demandes_contact (
	id SERIAL NOT NULL, 
	nom_complet VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	sujet VARCHAR(120), 
	message TEXT NOT NULL, 
	type_demande VARCHAR(30) DEFAULT 'autre' NOT NULL, 
	source VARCHAR(30) DEFAULT 'site_web' NOT NULL, 
	statut VARCHAR(30) DEFAULT 'nouvelle' NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_demandes_contact_type_demande CHECK (type_demande IN ('tourisme', 'team_building', 'podcast', 'autre')), 
	CONSTRAINT ck_demandes_contact_statut CHECK (statut IN ('nouvelle', 'traitee', 'fermee'))
);


CREATE TABLE IF NOT EXISTS newsletter_subscribers (
	id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	langue VARCHAR(10), 
	source VARCHAR(50) DEFAULT 'site_web' NOT NULL, 
	consentement BOOLEAN DEFAULT true NOT NULL, 
	actif BOOLEAN DEFAULT true NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS roles (
	id SERIAL NOT NULL, 
	nom_role VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nom_role)
);


CREATE TABLE IF NOT EXISTS utilisateur (
	id_utilisateur SERIAL NOT NULL, 
	nom VARCHAR(100) NOT NULL, 
	prenom VARCHAR(100), 
	email VARCHAR(150) NOT NULL, 
	mot_de_passe VARCHAR(255) NOT NULL, 
	id_role INTEGER NOT NULL, 
	actif BOOLEAN DEFAULT true NOT NULL, 
	date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	derniere_connexion TIMESTAMP WITH TIME ZONE, 
	id_utilisateur_create INTEGER, 
	image_utilisateur VARCHAR(500), 
	PRIMARY KEY (id_utilisateur), 
	UNIQUE (email), 
	FOREIGN KEY(id_role) REFERENCES roles (id) ON DELETE RESTRICT, 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS benevoles (
	id SERIAL NOT NULL, 
	nom VARCHAR(100) NOT NULL, 
	prenoms VARCHAR(150) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	telephone VARCHAR(30), 
	lieu_habitation VARCHAR(255), 
	experience TEXT, 
	actif BOOLEAN DEFAULT true NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS categorie_materiel (
	id SERIAL NOT NULL, 
	nom VARCHAR(100) NOT NULL, 
	description TEXT, 
	date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS circuits_touristiques (
	id SERIAL NOT NULL, 
	titre VARCHAR(255) NOT NULL, 
	lieu VARCHAR(255), 
	thematique VARCHAR(255), 
	description TEXT, 
	details JSONB DEFAULT '[]'::jsonb NOT NULL, 
	duree VARCHAR(120), 
	prix_base NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	categorie VARCHAR(50) DEFAULT 'local' NOT NULL, 
	type_circuit VARCHAR(100), 
	images JSONB DEFAULT '[]'::jsonb NOT NULL, 
	itineraire JSONB DEFAULT '[]'::jsonb NOT NULL, 
	formules JSONB DEFAULT '[]'::jsonb NOT NULL, 
	inclus JSONB DEFAULT '[]'::jsonb NOT NULL, 
	non_inclus JSONB DEFAULT '[]'::jsonb NOT NULL, 
	conditions_annulation JSONB DEFAULT '[]'::jsonb NOT NULL, 
	actif BOOLEAN DEFAULT true NOT NULL, 
	publie BOOLEAN DEFAULT false NOT NULL, 
	created_by_id INTEGER, 
	updated_by_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_circuits_touristiques_prix_base_non_negatif CHECK (prix_base >= 0), 
	CONSTRAINT ck_circuits_touristiques_categorie CHECK (categorie IN ('local', 'international')), 
	FOREIGN KEY(created_by_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL, 
	FOREIGN KEY(updated_by_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS client (
	id_client SERIAL NOT NULL, 
	nom VARCHAR(100) NOT NULL, 
	prenom VARCHAR(100), 
	entreprise VARCHAR(150), 
	role VARCHAR(100), 
	secteur_activite VARCHAR(150), 
	email VARCHAR(150), 
	telephone VARCHAR(20), 
	statut VARCHAR(50), 
	adresse TEXT, 
	date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	PRIMARY KEY (id_client), 
	UNIQUE (email), 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS demandes_team_building (
	id SERIAL NOT NULL, 
	entreprise VARCHAR(255) NOT NULL, 
	nom_contact VARCHAR(255) NOT NULL, 
	fonction_contact VARCHAR(150), 
	telephone_contact VARCHAR(50) NOT NULL, 
	email_contact VARCHAR(255) NOT NULL, 
	nombre_participants INTEGER NOT NULL, 
	objectif TEXT NOT NULL, 
	lieu_souhaite VARCHAR(255), 
	date_souhaitee DATE, 
	type_activite VARCHAR(255), 
	avec_salle BOOLEAN DEFAULT false NOT NULL, 
	avec_nuitee BOOLEAN DEFAULT false NOT NULL, 
	nombre_nuitees INTEGER DEFAULT 0 NOT NULL, 
	transport_inclus BOOLEAN DEFAULT false NOT NULL, 
	restauration_incluse BOOLEAN DEFAULT false NOT NULL, 
	hebergement_inclus BOOLEAN DEFAULT false NOT NULL, 
	experience_precedente TEXT, 
	source_decouverte VARCHAR(255), 
	source VARCHAR(30) DEFAULT 'site_web' NOT NULL, 
	statut VARCHAR(30) DEFAULT 'nouvelle' NOT NULL, 
	statut_modifie_le TIMESTAMP WITH TIME ZONE, 
	statut_modifie_par_id INTEGER, 
	created_by_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_demandes_team_building_nombre_participants_pos CHECK (nombre_participants > 0), 
	CONSTRAINT ck_demandes_team_building_statut CHECK (statut IN ('nouvelle', 'contactee', 'devis_envoye', 'confirmee', 'annulee')), 
	FOREIGN KEY(statut_modifie_par_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS demandes_tourisme (
	id SERIAL NOT NULL, 
	circuit_externe_id INTEGER, 
	titre_circuit VARCHAR(255) NOT NULL, 
	lieu_circuit VARCHAR(255), 
	duree_circuit VARCHAR(120), 
	formule_choisie VARCHAR(100), 
	prix_formule NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	date_depart_souhaitee DATE, 
	prenom VARCHAR(120) NOT NULL, 
	nom VARCHAR(120) NOT NULL, 
	telephone VARCHAR(50) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	nombre_voyageurs INTEGER DEFAULT 1 NOT NULL, 
	note_client TEXT, 
	prix_total_estime NUMERIC(12, 2) DEFAULT 0 NOT NULL, 
	source VARCHAR(30) DEFAULT 'site_web' NOT NULL, 
	statut VARCHAR(50) DEFAULT 'nouvelle' NOT NULL, 
	statut_modifie_le TIMESTAMP WITHOUT TIME ZONE, 
	statut_modifie_par_id INTEGER, 
	created_by_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_demandes_tourisme_nombre_voyageurs_pos CHECK (nombre_voyageurs > 0), 
	CONSTRAINT ck_demandes_tourisme_statut CHECK (statut IN ('nouvelle','contactee','en_traitement','devis_envoye','en_attente_reponse_client','relance_envoyee','validee','annulee','refusee','terminee')), 
	FOREIGN KEY(statut_modifie_par_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS demandes_tourisme_custom (
	id SERIAL NOT NULL, 
	nom_client VARCHAR(255) NOT NULL, 
	prenoms_client VARCHAR(255) NOT NULL, 
	email_client VARCHAR(255) NOT NULL, 
	numero_telephone_client VARCHAR(50) NOT NULL, 
	nombre_personne INTEGER DEFAULT 1 NOT NULL, 
	nombre_jours INTEGER, 
	lieu_souhaite VARCHAR(255), 
	attente_voyage TEXT, 
	source VARCHAR(30) DEFAULT 'site_web' NOT NULL, 
	statut VARCHAR(50) DEFAULT 'nouvelle' NOT NULL, 
	statut_modifie_le TIMESTAMP WITHOUT TIME ZONE, 
	statut_modifie_par_id INTEGER, 
	created_by_id INTEGER, 
	updated_by_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_demandes_tourisme_custom_nombre_personne_pos CHECK (nombre_personne > 0), 
	CONSTRAINT ck_demandes_tourisme_custom_statut CHECK (statut IN ('nouvelle','contactee','en_traitement','devis_envoye','en_attente_reponse_client','relance_envoyee','validee','annulee','refusee','terminee')), 
	FOREIGN KEY(statut_modifie_par_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL, 
	FOREIGN KEY(updated_by_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS jeu (
	id_jeu SERIAL NOT NULL, 
	nom_jeu VARCHAR(150) NOT NULL, 
	description TEXT, 
	duree INTEGER, 
	nb_min_participants INTEGER, 
	nb_max_participants INTEGER, 
	materiel_requis TEXT, 
	image_jeux VARCHAR(255), 
	date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	PRIMARY KEY (id_jeu), 
	CONSTRAINT ck_jeu_duree_pos CHECK (duree > 0), 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS materiel (
	id SERIAL NOT NULL, 
	nom VARCHAR(150) NOT NULL, 
	marque VARCHAR(100), 
	modele VARCHAR(150), 
	description TEXT, 
	quantite_disponible INTEGER DEFAULT 0 NOT NULL, 
	date_ajout TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	statut BOOLEAN DEFAULT true, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS personnel (
	id_personnel SERIAL NOT NULL, 
	nom VARCHAR(100) NOT NULL, 
	prenom VARCHAR(100), 
	fonction VARCHAR(100), 
	telephone VARCHAR(20), 
	email VARCHAR(150), 
	adresse VARCHAR(255), 
	date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	PRIMARY KEY (id_personnel), 
	UNIQUE (email), 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS site (
	id_site SERIAL NOT NULL, 
	nom_site VARCHAR(150) NOT NULL, 
	localisation VARCHAR(150), 
	capacite INTEGER, 
	type_site VARCHAR(50), 
	contact_site VARCHAR(255), 
	email_site VARCHAR(255), 
	images JSONB DEFAULT '[]'::jsonb NOT NULL, 
	a_restauration BOOLEAN DEFAULT false NOT NULL, 
	tarifs_restauration JSONB, 
	a_salle_seminaire BOOLEAN DEFAULT false NOT NULL, 
	tarifs_seminaire JSONB, 
	date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	PRIMARY KEY (id_site), 
	CONSTRAINT ck_site_capacite_pos CHECK (capacite > 0), 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS circuits_touristiques_translations (
	id SERIAL NOT NULL, 
	circuit_id INTEGER NOT NULL, 
	langue VARCHAR(10) NOT NULL, 
	titre VARCHAR(255) NOT NULL, 
	lieu VARCHAR(255), 
	thematique VARCHAR(255), 
	description TEXT, 
	details JSONB DEFAULT '[]'::jsonb NOT NULL, 
	duree VARCHAR(120), 
	type_circuit VARCHAR(100), 
	itineraire JSONB DEFAULT '[]'::jsonb NOT NULL, 
	formules JSONB DEFAULT '[]'::jsonb NOT NULL, 
	inclus JSONB DEFAULT '[]'::jsonb NOT NULL, 
	non_inclus JSONB DEFAULT '[]'::jsonb NOT NULL, 
	conditions_annulation JSONB DEFAULT '[]'::jsonb NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_circuit_langue UNIQUE (circuit_id, langue), 
	CONSTRAINT ck_circuit_translation_langue CHECK (langue IN ('fr', 'en', 'es')), 
	FOREIGN KEY(circuit_id) REFERENCES circuits_touristiques (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS demande (
	id_demande SERIAL NOT NULL, 
	date_demande DATE DEFAULT CURRENT_DATE NOT NULL, 
	description TEXT, 
	nombre_participants INTEGER, 
	budget_estime NUMERIC(12, 2), 
	statut VARCHAR(30) DEFAULT 'en_attente' NOT NULL, 
	source VARCHAR(30) DEFAULT 'client' NOT NULL, 
	id_client INTEGER NOT NULL, 
	id_utilisateur INTEGER, 
	date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	PRIMARY KEY (id_demande), 
	CONSTRAINT ck_demande_nombre_participants_pos CHECK (nombre_participants > 0), 
	CONSTRAINT ck_demande_statut CHECK (statut IN ('en_attente','en_etude','validee','refusee')), 
	CONSTRAINT ck_demande_source CHECK (source IN ('client','interne')), 
	FOREIGN KEY(id_client) REFERENCES client (id_client) ON DELETE CASCADE, 
	FOREIGN KEY(id_utilisateur) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL, 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS demandes_team_building_cadres (
	id SERIAL NOT NULL, 
	demande_team_building_id INTEGER NOT NULL, 
	cadre VARCHAR(30) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_demandes_team_building_cadres_cadre CHECK (cadre IN ('interieur', 'plein_air', 'mixte')), 
	FOREIGN KEY(demande_team_building_id) REFERENCES demandes_team_building (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS historique_statut_demandes_tourisme (
	id SERIAL NOT NULL, 
	demande_tourisme_id INTEGER, 
	demande_tourisme_custom_id INTEGER, 
	ancien_statut VARCHAR(50), 
	nouveau_statut VARCHAR(50) NOT NULL, 
	commentaire TEXT, 
	modifie_par_id INTEGER, 
	modifie_le TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_historique_statut_une_seule_demande_tourisme CHECK ((demande_tourisme_id IS NOT NULL AND demande_tourisme_custom_id IS NULL) OR (demande_tourisme_id IS NULL AND demande_tourisme_custom_id IS NOT NULL)), 
	CONSTRAINT ck_historique_statut_demande_tourisme_nouveau_statut CHECK (nouveau_statut IN ('nouvelle','contactee','en_traitement','devis_envoye','en_attente_reponse_client','relance_envoyee','validee','annulee','refusee','terminee')), 
	FOREIGN KEY(demande_tourisme_id) REFERENCES demandes_tourisme (id) ON DELETE CASCADE, 
	FOREIGN KEY(demande_tourisme_custom_id) REFERENCES demandes_tourisme_custom (id) ON DELETE CASCADE, 
	FOREIGN KEY(modifie_par_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS jeu_materiel (
	id SERIAL NOT NULL, 
	jeu_id INTEGER NOT NULL, 
	materiel_id INTEGER NOT NULL, 
	quantite_requise INTEGER DEFAULT 1 NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_jeu_materiel UNIQUE (jeu_id, materiel_id), 
	CONSTRAINT ck_jeu_materiel_quantite_requise_pos CHECK (quantite_requise > 0), 
	FOREIGN KEY(jeu_id) REFERENCES jeu (id_jeu) ON DELETE CASCADE, 
	FOREIGN KEY(materiel_id) REFERENCES materiel (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS offre (
	id SERIAL NOT NULL, 
	demande_id INTEGER NOT NULL, 
	reference VARCHAR(50), 
	titre VARCHAR(255) NOT NULL, 
	version INTEGER DEFAULT 1 NOT NULL, 
	statut VARCHAR(30) DEFAULT 'brouillon' NOT NULL, 
	montant_total NUMERIC(12, 2) NOT NULL, 
	date_envoi DATE, 
	date_validation DATE, 
	date_expiration DATE, 
	fichier_pptx VARCHAR(500), 
	conditions_paiement TEXT, 
	observations TEXT, 
	id_utilisateur_cr INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_offre_statut CHECK (statut IN ('brouillon','envoyee','validee','refusee','expiree','annulee')), 
	CONSTRAINT ck_offre_montant_total_non_negatif CHECK (montant_total >= 0), 
	FOREIGN KEY(demande_id) REFERENCES demandes_team_building (id) ON DELETE CASCADE, 
	FOREIGN KEY(id_utilisateur_cr) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS offre_tourisme (
	id SERIAL NOT NULL, 
	demande_tourisme_id INTEGER, 
	demande_tourisme_custom_id INTEGER, 
	reference VARCHAR(50) NOT NULL, 
	titre VARCHAR(255) NOT NULL, 
	version INTEGER DEFAULT 1 NOT NULL, 
	statut VARCHAR(30) DEFAULT 'brouillon' NOT NULL, 
	montant_total NUMERIC(12, 2) NOT NULL, 
	date_envoi DATE, 
	date_validation DATE, 
	date_expiration DATE, 
	conditions_paiement TEXT, 
	observations TEXT, 
	created_by_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_offre_tourisme_une_seule_demande CHECK ((demande_tourisme_id IS NOT NULL AND demande_tourisme_custom_id IS NULL) OR (demande_tourisme_id IS NULL AND demande_tourisme_custom_id IS NOT NULL)), 
	CONSTRAINT ck_offre_tourisme_statut CHECK (statut IN ('brouillon','envoyee','validee','refusee','expiree','annulee')), 
	CONSTRAINT ck_offre_tourisme_montant_total_non_negatif CHECK (montant_total >= 0), 
	FOREIGN KEY(demande_tourisme_id) REFERENCES demandes_tourisme (id) ON DELETE CASCADE, 
	FOREIGN KEY(demande_tourisme_custom_id) REFERENCES demandes_tourisme_custom (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS activite (
	id SERIAL NOT NULL, 
	reference VARCHAR(50), 
	titre VARCHAR(150) NOT NULL, 
	description TEXT, 
	client_id INTEGER, 
	demande_id INTEGER, 
	offre_id INTEGER, 
	date_debut TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	date_fin TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	nombre_participants INTEGER, 
	site_id INTEGER NOT NULL, 
	responsable_id INTEGER, 
	budget_previsionnel NUMERIC(12, 2), 
	statut VARCHAR(30) DEFAULT 'planifier' NOT NULL, 
	observations TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_activite_statut CHECK (statut IN ('brouillon','planifier','en_preparation','en_cours','terminer','annuler')), 
	CONSTRAINT ck_activite_nombre_participants_pos CHECK (nombre_participants IS NULL OR nombre_participants > 0), 
	CONSTRAINT ck_activite_budget_previsionnel_non_neg CHECK (budget_previsionnel IS NULL OR budget_previsionnel >= 0), 
	FOREIGN KEY(client_id) REFERENCES client (id_client) ON DELETE SET NULL, 
	FOREIGN KEY(demande_id) REFERENCES demandes_team_building (id) ON DELETE SET NULL, 
	UNIQUE (offre_id), 
	FOREIGN KEY(offre_id) REFERENCES offre (id) ON DELETE SET NULL, 
	FOREIGN KEY(site_id) REFERENCES site (id_site) ON DELETE RESTRICT, 
	FOREIGN KEY(responsable_id) REFERENCES personnel (id_personnel) ON DELETE SET NULL, 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS proformas (
	id SERIAL NOT NULL, 
	reference VARCHAR(50) NOT NULL, 
	pole VARCHAR(30) DEFAULT 'teambuilding' NOT NULL, 
	demande_team_building_id INTEGER, 
	offre_id INTEGER, 
	demande_tourisme_id INTEGER, 
	demande_tourisme_custom_id INTEGER, 
	offre_tourisme_id INTEGER, 
	site_id INTEGER, 
	client VARCHAR(255) NOT NULL, 
	nombre_personnes INTEGER NOT NULL, 
	objet VARCHAR(255) NOT NULL, 
	date_proforma DATE NOT NULL, 
	date_evenement DATE, 
	sections JSONB DEFAULT '[]'::jsonb NOT NULL, 
	frais_agence NUMERIC(14, 2) DEFAULT 0 NOT NULL, 
	details_frais_agence JSONB DEFAULT '[]'::jsonb NOT NULL, 
	taux_tva_frais_agence NUMERIC(5, 2) DEFAULT 18 NOT NULL, 
	sous_total_ht NUMERIC(14, 2) DEFAULT 0 NOT NULL, 
	tva_frais_agence NUMERIC(14, 2) DEFAULT 0 NOT NULL, 
	total_ttc NUMERIC(14, 2) DEFAULT 0 NOT NULL, 
	modalite_paiement TEXT, 
	recommandations JSONB DEFAULT '[]'::jsonb NOT NULL, 
	notes TEXT, 
	statut VARCHAR(30) DEFAULT 'brouillon' NOT NULL, 
	fichier_pdf VARCHAR(500), 
	created_by_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_proformas_pole CHECK (pole IN ('teambuilding','tourisme')), 
	CONSTRAINT ck_proformas_statut CHECK (statut IN ('brouillon','validee','pdf_genere','annulee')), 
	CONSTRAINT ck_proformas_nombre_personnes_pos CHECK (nombre_personnes > 0), 
	CONSTRAINT ck_proformas_sous_total_ht_non_negatif CHECK (sous_total_ht >= 0), 
	CONSTRAINT ck_proformas_frais_agence_non_negatif CHECK (frais_agence >= 0), 
	CONSTRAINT ck_proformas_tva_non_negatif CHECK (tva_frais_agence >= 0), 
	CONSTRAINT ck_proformas_total_ttc_non_negatif CHECK (total_ttc >= 0), 
	FOREIGN KEY(demande_team_building_id) REFERENCES demandes_team_building (id) ON DELETE SET NULL, 
	FOREIGN KEY(offre_id) REFERENCES offre (id) ON DELETE SET NULL, 
	FOREIGN KEY(demande_tourisme_id) REFERENCES demandes_tourisme (id) ON DELETE SET NULL, 
	FOREIGN KEY(demande_tourisme_custom_id) REFERENCES demandes_tourisme_custom (id) ON DELETE SET NULL, 
	FOREIGN KEY(offre_tourisme_id) REFERENCES offre_tourisme (id) ON DELETE SET NULL, 
	FOREIGN KEY(site_id) REFERENCES site (id_site) ON DELETE SET NULL, 
	FOREIGN KEY(created_by_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS activite_benevole (
	id SERIAL NOT NULL, 
	activite_id INTEGER NOT NULL, 
	benevole_id INTEGER NOT NULL, 
	role VARCHAR(100), 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_activite_benevole UNIQUE (activite_id, benevole_id), 
	FOREIGN KEY(activite_id) REFERENCES activite (id) ON DELETE CASCADE, 
	FOREIGN KEY(benevole_id) REFERENCES benevoles (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS activite_jeu (
	activite_id INTEGER NOT NULL, 
	jeu_id INTEGER NOT NULL, 
	ordre INTEGER, 
	duree_prevue INTEGER, 
	date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	PRIMARY KEY (activite_id, jeu_id), 
	FOREIGN KEY(activite_id) REFERENCES activite (id) ON DELETE CASCADE, 
	FOREIGN KEY(jeu_id) REFERENCES jeu (id_jeu) ON DELETE CASCADE, 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS activite_materiel (
	id SERIAL NOT NULL, 
	activite_id INTEGER NOT NULL, 
	materiel_id INTEGER NOT NULL, 
	quantite_prevue INTEGER DEFAULT 1 NOT NULL, 
	quantite_utilisee INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_activite_materiel UNIQUE (activite_id, materiel_id), 
	CONSTRAINT ck_activite_materiel_quantite_prevue_pos CHECK (quantite_prevue > 0), 
	CONSTRAINT ck_activite_materiel_quantite_utilisee_non_neg CHECK (quantite_utilisee IS NULL OR quantite_utilisee >= 0), 
	FOREIGN KEY(activite_id) REFERENCES activite (id) ON DELETE CASCADE, 
	FOREIGN KEY(materiel_id) REFERENCES materiel (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS affectation (
	id_affectation SERIAL NOT NULL, 
	activite_id INTEGER NOT NULL, 
	personnel_id INTEGER NOT NULL, 
	role VARCHAR(100), 
	heure_debut TIMESTAMP WITHOUT TIME ZONE, 
	heure_fin TIMESTAMP WITHOUT TIME ZONE, 
	date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	id_utilisateur_create INTEGER, 
	PRIMARY KEY (id_affectation), 
	CONSTRAINT uq_affectation_activite_personnel UNIQUE (activite_id, personnel_id), 
	FOREIGN KEY(activite_id) REFERENCES activite (id) ON DELETE CASCADE, 
	FOREIGN KEY(personnel_id) REFERENCES personnel (id_personnel) ON DELETE CASCADE, 
	FOREIGN KEY(id_utilisateur_create) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS depense (
	id SERIAL NOT NULL, 
	reference VARCHAR(50), 
	titre VARCHAR(150) NOT NULL, 
	description TEXT, 
	montant NUMERIC(12, 2) NOT NULL, 
	date_depense DATE DEFAULT CURRENT_DATE, 
	categorie_depense_id INTEGER, 
	offre_id INTEGER, 
	activite_id INTEGER NOT NULL, 
	fournisseur VARCHAR(255), 
	mode_paiement VARCHAR(50), 
	type_depense VARCHAR(100), 
	justificatif VARCHAR(500), 
	id_utilisateur_cr INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_depense_montant_non_neg CHECK (montant >= 0), 
	CONSTRAINT ck_depense_mode_paiement CHECK (mode_paiement IS NULL OR mode_paiement IN ('ESPECES','WAVE','ORANGE_MONEY','MTN_MONEY','VIREMENT','CHEQUE','CARTE_BANCAIRE')), 
	FOREIGN KEY(categorie_depense_id) REFERENCES categorie_depense (id) ON DELETE SET NULL, 
	FOREIGN KEY(offre_id) REFERENCES offre (id) ON DELETE SET NULL, 
	FOREIGN KEY(activite_id) REFERENCES activite (id) ON DELETE CASCADE, 
	FOREIGN KEY(id_utilisateur_cr) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_categorie_depense_id ON categorie_depense (id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_categorie_depense_nom ON categorie_depense (nom);

CREATE INDEX IF NOT EXISTS ix_contact_akan_id ON contact_akan (id);

CREATE INDEX IF NOT EXISTS ix_demandes_contact_email ON demandes_contact (email);
CREATE INDEX IF NOT EXISTS ix_demandes_contact_id ON demandes_contact (id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_newsletter_subscribers_email ON newsletter_subscribers (email);
CREATE INDEX IF NOT EXISTS ix_newsletter_subscribers_id ON newsletter_subscribers (id);

CREATE INDEX IF NOT EXISTS ix_roles_id ON roles (id);

CREATE INDEX IF NOT EXISTS ix_utilisateur_id_utilisateur ON utilisateur (id_utilisateur);

CREATE UNIQUE INDEX IF NOT EXISTS ix_benevoles_email ON benevoles (email);
CREATE INDEX IF NOT EXISTS ix_benevoles_id ON benevoles (id);

CREATE INDEX IF NOT EXISTS ix_categorie_materiel_id ON categorie_materiel (id);

CREATE INDEX IF NOT EXISTS ix_circuits_touristiques_id ON circuits_touristiques (id);

CREATE INDEX IF NOT EXISTS ix_client_id_client ON client (id_client);

CREATE INDEX IF NOT EXISTS ix_demandes_team_building_email_contact ON demandes_team_building (email_contact);
CREATE INDEX IF NOT EXISTS ix_demandes_team_building_id ON demandes_team_building (id);

CREATE INDEX IF NOT EXISTS ix_demandes_tourisme_email ON demandes_tourisme (email);
CREATE INDEX IF NOT EXISTS ix_demandes_tourisme_id ON demandes_tourisme (id);

CREATE INDEX IF NOT EXISTS ix_demandes_tourisme_custom_email_client ON demandes_tourisme_custom (email_client);
CREATE INDEX IF NOT EXISTS ix_demandes_tourisme_custom_id ON demandes_tourisme_custom (id);

CREATE INDEX IF NOT EXISTS ix_jeu_id_jeu ON jeu (id_jeu);

CREATE INDEX IF NOT EXISTS ix_materiel_id ON materiel (id);
CREATE INDEX IF NOT EXISTS ix_materiel_marque ON materiel (marque);
CREATE INDEX IF NOT EXISTS ix_materiel_modele ON materiel (modele);

CREATE INDEX IF NOT EXISTS ix_personnel_id_personnel ON personnel (id_personnel);

CREATE INDEX IF NOT EXISTS ix_site_id_site ON site (id_site);

CREATE INDEX IF NOT EXISTS ix_circuits_touristiques_translations_circuit_id ON circuits_touristiques_translations (circuit_id);
CREATE INDEX IF NOT EXISTS ix_circuits_touristiques_translations_id ON circuits_touristiques_translations (id);
CREATE INDEX IF NOT EXISTS ix_circuits_touristiques_translations_langue ON circuits_touristiques_translations (langue);

CREATE INDEX IF NOT EXISTS ix_demande_id_demande ON demande (id_demande);

CREATE INDEX IF NOT EXISTS ix_demandes_team_building_cadres_id ON demandes_team_building_cadres (id);

CREATE INDEX IF NOT EXISTS ix_historique_statut_demandes_tourisme_id ON historique_statut_demandes_tourisme (id);

CREATE INDEX IF NOT EXISTS ix_jeu_materiel_id ON jeu_materiel (id);
CREATE INDEX IF NOT EXISTS ix_jeu_materiel_jeu_id ON jeu_materiel (jeu_id);
CREATE INDEX IF NOT EXISTS ix_jeu_materiel_materiel_id ON jeu_materiel (materiel_id);

CREATE INDEX IF NOT EXISTS ix_offre_demande_id ON offre (demande_id);
CREATE INDEX IF NOT EXISTS ix_offre_id ON offre (id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_offre_reference ON offre (reference);

CREATE INDEX IF NOT EXISTS ix_offre_tourisme_demande_tourisme_custom_id ON offre_tourisme (demande_tourisme_custom_id);
CREATE INDEX IF NOT EXISTS ix_offre_tourisme_demande_tourisme_id ON offre_tourisme (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_offre_tourisme_id ON offre_tourisme (id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_offre_tourisme_reference ON offre_tourisme (reference);

CREATE INDEX IF NOT EXISTS ix_activite_client_id ON activite (client_id);
CREATE INDEX IF NOT EXISTS ix_activite_demande_id ON activite (demande_id);
CREATE INDEX IF NOT EXISTS ix_activite_id ON activite (id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_activite_reference ON activite (reference);
CREATE INDEX IF NOT EXISTS ix_activite_responsable_id ON activite (responsable_id);
CREATE INDEX IF NOT EXISTS ix_activite_site_id ON activite (site_id);

CREATE INDEX IF NOT EXISTS ix_proformas_demande_team_building_id ON proformas (demande_team_building_id);
CREATE INDEX IF NOT EXISTS ix_proformas_demande_tourisme_custom_id ON proformas (demande_tourisme_custom_id);
CREATE INDEX IF NOT EXISTS ix_proformas_demande_tourisme_id ON proformas (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_proformas_id ON proformas (id);
CREATE INDEX IF NOT EXISTS ix_proformas_offre_id ON proformas (offre_id);
CREATE INDEX IF NOT EXISTS ix_proformas_offre_tourisme_id ON proformas (offre_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_proformas_pole ON proformas (pole);
CREATE UNIQUE INDEX IF NOT EXISTS ix_proformas_reference ON proformas (reference);
CREATE INDEX IF NOT EXISTS ix_proformas_site_id ON proformas (site_id);

CREATE INDEX IF NOT EXISTS ix_activite_benevole_activite_id ON activite_benevole (activite_id);
CREATE INDEX IF NOT EXISTS ix_activite_benevole_benevole_id ON activite_benevole (benevole_id);
CREATE INDEX IF NOT EXISTS ix_activite_benevole_id ON activite_benevole (id);

CREATE INDEX IF NOT EXISTS ix_activite_materiel_activite_id ON activite_materiel (activite_id);
CREATE INDEX IF NOT EXISTS ix_activite_materiel_id ON activite_materiel (id);
CREATE INDEX IF NOT EXISTS ix_activite_materiel_materiel_id ON activite_materiel (materiel_id);

CREATE INDEX IF NOT EXISTS ix_affectation_activite_id ON affectation (activite_id);
CREATE INDEX IF NOT EXISTS ix_affectation_id_affectation ON affectation (id_affectation);
CREATE INDEX IF NOT EXISTS ix_affectation_personnel_id ON affectation (personnel_id);

CREATE INDEX IF NOT EXISTS ix_depense_activite_id ON depense (activite_id);
CREATE INDEX IF NOT EXISTS ix_depense_categorie_depense_id ON depense (categorie_depense_id);
CREATE INDEX IF NOT EXISTS ix_depense_id ON depense (id);
CREATE INDEX IF NOT EXISTS ix_depense_offre_id ON depense (offre_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_depense_reference ON depense (reference);

-- Index supplementaires presents dans les migrations SQL manuelles.
CREATE INDEX IF NOT EXISTS idx_benevoles_actif ON benevoles (actif);
CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_created_by ON circuits_touristiques (created_by_id);
CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_actif ON circuits_touristiques (actif);
CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_publie ON circuits_touristiques (publie);
CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_categorie ON circuits_touristiques (categorie);
CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_type ON circuits_touristiques (type_circuit);
CREATE INDEX IF NOT EXISTS idx_demandes_tourisme_custom_created_by ON demandes_tourisme_custom (created_by_id);
CREATE INDEX IF NOT EXISTS idx_demandes_tourisme_custom_updated_by ON demandes_tourisme_custom (updated_by_id);
CREATE INDEX IF NOT EXISTS idx_historique_statut_demandes_tourisme_demande_tourisme_id ON historique_statut_demandes_tourisme (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS idx_historique_statut_demandes_tourisme_demande_tourisme_custom_id ON historique_statut_demandes_tourisme (demande_tourisme_custom_id);
CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_actif ON newsletter_subscribers (actif);
CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_created_at ON newsletter_subscribers (created_at);
CREATE INDEX IF NOT EXISTS idx_site_a_restauration ON site (a_restauration);
CREATE INDEX IF NOT EXISTS idx_site_a_salle_seminaire ON site (a_salle_seminaire);

-- Donnees minimales attendues par les regles d'acces backend + CRM.
INSERT INTO roles (nom_role)
VALUES
	('super_admin'),
	('admin'),
	('utilisateur'),
	('superviseur_tourisme'),
	('superviseur_teambuilding'),
	('superviseur_production')
ON CONFLICT (nom_role) DO NOTHING;

COMMIT;

