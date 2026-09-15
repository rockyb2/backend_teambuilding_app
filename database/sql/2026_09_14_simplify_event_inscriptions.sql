-- Simplification validée : conserver les contacts et les noms d'événements.
-- À exécuter dans une transaction. Aucune table Tourisme n'est modifiée.
DO $$
DECLARE
    pair text[];
BEGIN
    IF to_regclass('inscriptions_event') IS NOT NULL THEN
        ALTER TABLE inscriptions_event ADD COLUMN IF NOT EXISTS evenement VARCHAR(255);
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'inscriptions_event' AND column_name = 'event_id') THEN
            UPDATE inscriptions_event AS inscription
            SET evenement = event.titre
            FROM events AS event
            WHERE event.id = inscription.event_id AND inscription.evenement IS NULL;
        END IF;

        FOREACH pair SLICE 1 IN ARRAY ARRAY[
            ['contact_prenom', 'prenom'], ['contact_nom', 'nom'],
            ['contact_telephone', 'telephone'], ['contact_email', 'email'],
            ['created_at', 'date_inscription']
        ] LOOP
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'inscriptions_event' AND column_name = pair[1]) THEN
                EXECUTE format('ALTER TABLE inscriptions_event RENAME COLUMN %I TO %I', pair[1], pair[2]);
            END IF;
        END LOOP;

        DROP TABLE IF EXISTS participants_event;
        ALTER TABLE inscriptions_event
            ALTER COLUMN evenement SET NOT NULL,
            DROP COLUMN IF EXISTS reference,
            DROP COLUMN IF EXISTS empreinte,
            DROP COLUMN IF EXISTS event_id,
            DROP COLUMN IF EXISTS date_evenement,
            DROP COLUMN IF EXISTS prix_unitaire,
            DROP COLUMN IF EXISTS prix_total_estime,
            DROP COLUMN IF EXISTS statut,
            DROP COLUMN IF EXISTS statut_paiement,
            DROP COLUMN IF EXISTS reference_paiement,
            DROP COLUMN IF EXISTS updated_at;
    END IF;

    IF to_regclass('events') IS NOT NULL THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'events' AND column_name = 'date_evenement') THEN
            ALTER TABLE events RENAME COLUMN date_evenement TO date;
        END IF;
        ALTER TABLE events
            DROP COLUMN IF EXISTS slug,
            DROP COLUMN IF EXISTS collection,
            DROP COLUMN IF EXISTS ancien_tarif,
            DROP COLUMN IF EXISTS devise,
            DROP COLUMN IF EXISTS programme,
            DROP COLUMN IF EXISTS informations,
            DROP COLUMN IF EXISTS actif,
            DROP COLUMN IF EXISTS inscriptions_ouvertes,
            DROP COLUMN IF EXISTS created_at,
            DROP COLUMN IF EXISTS updated_at;
    END IF;
END $$;
