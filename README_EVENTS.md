# Événements et inscriptions

Deux tables suffisent :

- `events` : `id`, `titre`, `date`, `lieu`, `tarif`, `description`.
- `inscriptions_event` : `id`, `evenement` (nom), `prenom`, `nom`, `telephone`, `email` facultatif, `nombre_participants`, `note`, `date_inscription`.

Une confirmation du formulaire crée une seule inscription avec les informations du contact. Il n’y a ni fiches individuelles, ni table de participants, ni lien obligatoire vers un identifiant d’événement.

Le formulaire utilise le nom déjà disponible sur la page et envoie directement `POST /api/events/inscriptions`. Aucun chargement d’événement n’est nécessaire à l’ouverture. La liste `GET /api/events/inscriptions` reste réservée aux utilisateurs autorisés au module Tourisme.

## Base de données

Le démarrage initialise les deux tables et les événements absents. Pour une installation antérieure avec les tables détaillées, appliquer une fois la simplification validée :

```powershell
.\backendenv\Scripts\python.exe scripts/setup_events.py --simplify
```

Cette migration conserve les contacts existants et le nom de leur événement, puis supprime la table des participants et les colonnes retirées. Elle ne touche pas aux tables des circuits touristiques.

Vérification :

```powershell
.\backendenv\Scripts\python.exe scripts/setup_events.py --check
.\backendenv\Scripts\python.exe -m unittest tests.test_events -v
```

Les tests utilisent une base isolée.