-- Additive event registration schema. Existing rows are never modified.
BEGIN;

CREATE TABLE IF NOT EXISTS events (
	id SERIAL NOT NULL,
	titre VARCHAR(255) NOT NULL,
	date DATE,
	lieu VARCHAR(500),
	tarif NUMERIC(12, 2),
	description TEXT,
	PRIMARY KEY (id),
	CONSTRAINT ck_events_tarif CHECK (tarif IS NULL OR tarif >= 0)
);

CREATE TABLE IF NOT EXISTS inscriptions_event (
	id SERIAL NOT NULL,
	evenement VARCHAR(255) NOT NULL,
	prenom VARCHAR(120) NOT NULL,
	nom VARCHAR(120) NOT NULL,
	telephone VARCHAR(50) NOT NULL,
	email VARCHAR(255),
	nombre_participants INTEGER NOT NULL,
	note TEXT,
	date_inscription TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_inscriptions_event_count CHECK (nombre_participants > 0)
);

COMMIT;
