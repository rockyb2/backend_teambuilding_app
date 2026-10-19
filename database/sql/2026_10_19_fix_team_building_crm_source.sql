-- Repair CRM-created requests whose source was reset by a full update.
UPDATE demandes_team_building
SET source = 'crm'
WHERE created_by_id IS NOT NULL
  AND source <> 'crm';
