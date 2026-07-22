-- Seed des circuits du site public vers PostgreSQL.
-- Table cible: circuits_touristiques
-- Le script evite les doublons en n'inserant pas un circuit si son titre existe deja.
-- Les images locales Tai/Azagny sont mises sous /uploads/... : il faut uploader/copy ces fichiers cote backend ou les remplacer par des URLs Cloudinary.

BEGIN;

WITH seed AS (
  SELECT *
  FROM jsonb_to_recordset($ivoirtrips$
[
  {
    "titre": "Escapade plage à Assinie",
    "lieu": "Assinie, Côte d'Ivoire",
    "thematique": "Plage, Détente, Lagune",
    "description": "Offrez-vous une parenthèse d'évasion à Assinie, destination balnéaire incontournable réputée pour ses plages de sable fin, sa lagune paisible et son ambiance chic et décontractée.\nEntre détente en bord de mer, balades en bateau sur la lagune et moments conviviaux dans des cadres exclusifs, Assinie est l'endroit idéal pour se ressourcer loin de l'agitation d'Abidjan.",
    "details": ["Départ depuis Abidjan", "3 jours / 2 nuits", "Week-end complet", "Formules Standard, Premium et VIP", "Hébergement et pension inclus"],
    "duree": "3 jour(s) / 2 nuit(s)",
    "prix_base": 57500,
    "categorie": "local",
    "type_circuit": "plage",
    "images": [
      "https://commons.wikimedia.org/wiki/Special:Redirect/file/Plage%20Assinie.jpg",
      "https://commons.wikimedia.org/wiki/Special:Redirect/file/Assinie%20%2C%20Par%20Nabil%20ZORKOT.jpg"
    ],
    "itineraire": [
      {
        "day": 1,
        "title": "Départ & Installation",
        "content": "Départ en matinée depuis Abidjan en direction d'Assinie. Arrivée et installation dans votre hébergement (villa, hôtel ou resort). Visite de Bassam. Après-midi détente entre plage et bord de lagune avec accès piscine et activités libres.",
        "extra": "Dîner inclus (libre ou organisé selon formule) avec ambiance chill ou festive"
      },
      {
        "day": 2,
        "title": "Expériences & Loisirs",
        "content": "Petit-déjeuner. Balade en bateau sur la lagune et visite d'Assinie embouchure. Activités nautiques optionnelles (jet-ski, paddle, kayak). Temps libre plage & relaxation. Déjeuner en bord de mer. Après-midi libre pour photos et détente.",
        "extra": "Dîner et soirée ambiance inclus"
      },
      {
        "day": 3,
        "title": "Détente & Retour",
        "content": "Petit-déjeuner. Matinée libre (plage, piscine, repos). Check-out. Déjeuner libre ou léger. Départ en début d'après-midi pour Abidjan. Arrivée en fin de journée."
      }
    ],
    "formules": [
      {
        "name": "Standard",
        "price": 57500,
        "color": "bg-slate-100",
        "features": [
          { "name": "Guide / assistance", "included": true },
          { "name": "Hébergement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": false }
        ]
      },
      {
        "name": "Premium",
        "price": 75000,
        "color": "bg-orange-50",
        "features": [
          { "name": "Guide / assistance", "included": true },
          { "name": "Hébergement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Accompagnateur IvoirTrips", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" }
        ]
      },
      {
        "name": "VIP",
        "price": 92500,
        "color": "bg-amber-50",
        "features": [
          { "name": "Guide / assistance", "included": true },
          { "name": "Hébergement premium", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Accompagnateur IvoirTrips", "included": true },
          { "name": "Transport", "included": true, "note": "Transport inclus" }
        ]
      }
    ],
    "inclus": ["Transport aller-retour Abidjan - Assinie", "Hébergement (2 nuits / 3 jours)", "Petits-déjeuners", "1 déjeuner selon programme", "Balade en bateau sur la lagune", "Accès plage & piscine", "Encadrement et organisation"],
    "non_inclus": ["Autres repas", "Dépenses personnelles", "Boissons", "Activités nautiques optionnelles (jet-ski, paddle, kayak)", "Visites supplémentaires"],
    "conditions_annulation": [
      { "title": "Remboursement intégral", "detail": "Jusqu'à 7 jours avant le départ" },
      { "title": "Remboursement partiel", "detail": "50% jusqu'à 3 jours avant le départ" }
    ],
    "actif": true,
    "publie": true
  },
  {
    "titre": "Grand-Bassam historique",
    "lieu": "Grand-Bassam, Côte d'Ivoire",
    "thematique": "Patrimoine, Histoire, Détente",
    "description": "Partez à la découverte de Grand-Bassam, ancienne capitale coloniale classée au patrimoine mondial de l'UNESCO, et vivez une excursion mêlant histoire, culture et détente en bord de mer.",
    "details": ["Départ depuis Abidjan", "1 jour complet", "Trajet court (45 min à 1h)", "Incluant repas et visite musée", "Ambiance culturelle et balnéaire"],
    "duree": "1 jour(s)",
    "prix_base": 100000,
    "categorie": "local",
    "type_circuit": "excursion",
    "images": ["https://commons.wikimedia.org/wiki/Special:Redirect/file/800px-Grand-Bassam.jpg"],
    "itineraire": [
      { "day": 1, "title": "Départ d'Abidjan", "content": "Départ en matinée depuis Abidjan en direction de Grand-Bassam. Trajet court et confortable (environ 45 min à 1h)." },
      { "day": 2, "title": "Découverte du quartier historique", "content": "Immersion dans le patrimoine colonial classé UNESCO : balade dans les rues historiques, découverte de l'architecture coloniale, visite du Musée National du Costume.", "extra": "Accompagnement par un guide local expert en histoire" },
      { "day": 3, "title": "Temps plage & détente", "content": "Installation en bord de mer avec accès plage, moments de détente et photos dans l'ambiance balnéaire." },
      { "day": 4, "title": "Déjeuner en bord de mer", "content": "Déjeuner dans un restaurant en bord de mer avec spécialités ivoiriennes et fruits de mer dans un cadre agréable et convivial." },
      { "day": 5, "title": "Activités & temps libre", "content": "Balade artisanale pour souvenirs et objets locaux, activités plage (jeux, relaxation), option animations ou team building." },
      { "day": 6, "title": "Retour sur Abidjan", "content": "Départ dans l'après-midi. Arrivée en fin de journée à Abidjan." }
    ],
    "formules": [
      {
        "name": "Standard",
        "price": 100000,
        "color": "bg-slate-100",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Restauration", "included": false },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": false }
        ]
      },
      {
        "name": "Premium",
        "price": 150000,
        "color": "bg-orange-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      },
      {
        "name": "VIP",
        "price": 220000,
        "color": "bg-amber-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": true, "note": "Transport inclus" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      }
    ],
    "inclus": ["Transport climatisé", "Accès plage", "Visites culturelles (musée et secteur historique)", "Déjeuner en bord de mer", "Encadrement et organisation", "Guide local"],
    "non_inclus": ["Dépenses personnelles", "Boissons", "Activités optionnelles (team building spécifique)", "Souvenirs et achats artisanaux"],
    "conditions_annulation": [
      { "title": "Remboursement intégral", "detail": "Jusqu'à 5 jours avant le départ" },
      { "title": "Remboursement partiel", "detail": "50% jusqu'à 48h avant le départ" }
    ],
    "actif": true,
    "publie": true
  },
  {
    "titre": "Yamoussoukro, basilique et capitale politique",
    "lieu": "Yamoussoukro, Côte d'Ivoire",
    "thematique": "Culture, Architecture, Découverte",
    "description": "Découvrez Yamoussoukro, capitale politique de la Côte d'Ivoire, à travers une excursion culturelle riche en histoire, en architecture et en découvertes uniques. Cette destination emblématique séduit par son cadre paisible et ses sites impressionnants qui témoignent du patrimoine ivoirien.",
    "details": ["Départ depuis Abidjan", "1 jour complet", "Culturel, patrimoine et architecture", "Visite basilique et sites emblématiques", "Repas inclus"],
    "duree": "1 jour(s)",
    "prix_base": 160000,
    "categorie": "local",
    "type_circuit": "excursion",
    "images": ["https://commons.wikimedia.org/wiki/Special:Redirect/file/Yakro%20basilique05.jpg"],
    "itineraire": [
      { "day": 1, "title": "Étape 1 : Départ d'Abidjan", "content": "Départ matinal en véhicule climatisé depuis Abidjan en direction de Yamoussoukro. Trajet confortable avec pause en cours de route." },
      { "day": 2, "title": "Étape 2 : Découverte de la Basilique", "content": "Visite guidée de la majestueuse Basilique Notre-Dame de la Paix, l'un des plus grands édifices religieux au monde. Temps dédié aux photos et à l'exploration de ce site emblématique.", "extra": "Accompagnement par un guide expert en architecture et histoire religieuse" },
      { "day": 3, "title": "Étape 3 : Tour de ville & sites emblématiques", "content": "Découverte de LA FONDATION FHB, visite de l'école INPHB, passage aux lacs aux crocodiles. Découverte de la maison Félix Houphouët-Boigny en option." },
      { "day": 4, "title": "Étape 4 : Déjeuner", "content": "Pause déjeuner dans un restaurant local (BOLIKRO). Moment de détente et d'échanges avec l'accompagnateur." },
      { "day": 5, "title": "Étape 5 : Temps libre & photos", "content": "Temps libre pour profiter de la ville, faire des photos ou visiter des sites complémentaires. Option Bomizambo disponible." },
      { "day": 6, "title": "Étape 6 : Retour sur Abidjan", "content": "Départ le soir pour Abidjan. Arrivée en soirée." }
    ],
    "formules": [
      {
        "name": "Standard",
        "price": 160000,
        "color": "bg-slate-100",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Restauration", "included": false },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": false }
        ]
      },
      {
        "name": "Premium",
        "price": 220000,
        "color": "bg-orange-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      },
      {
        "name": "VIP",
        "price": 350000,
        "color": "bg-amber-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": true, "note": "Transport inclus" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      }
    ],
    "inclus": ["Transport climatisé", "Visites mentionnées (basilique, FHB, INPHB, lacs aux crocodiles)", "Encadrement et organisation", "Déjeuner dans restaurant local", "Guide expert"],
    "non_inclus": ["Dépenses personnelles", "Boissons", "Visites optionnelles (maison Félix Houphouët-Boigny, Bomizambo)", "Achats personnels"],
    "conditions_annulation": [
      { "title": "Remboursement intégral", "detail": "Jusqu'à 5 jours avant le départ" },
      { "title": "Remboursement partiel", "detail": "50% jusqu'à 48h avant le départ" }
    ],
    "actif": true,
    "publie": true
  },
  {
    "titre": "Nature et cascades à Man",
    "lieu": "Man, Côte d'Ivoire",
    "thematique": "Nature, Randonnée, Fraîcheur",
    "description": "Un circuit nature à Man pour découvrir les cascades, l'ambiance des montagnes de l'Ouest et une Côte d'Ivoire plus verte.",
    "details": ["Circuit nature de plusieurs jours", "Parfait pour amateurs de randonnée", "Hébergement inclus selon formule"],
    "duree": "3 jour(s) / 2 nuit(s)",
    "prix_base": 119000,
    "categorie": "local",
    "type_circuit": "circuit long",
    "images": [
      "https://commons.wikimedia.org/wiki/Special:Redirect/file/Les%20cascades%20de%20Man.jpg",
      "https://commons.wikimedia.org/wiki/Special:Redirect/file/La%20Cascade%20de%20Man%201990.jpg"
    ],
    "itineraire": [
      { "day": 1, "title": "Arrivée à Man", "content": "Départ depuis Abidjan, arrivée à Man, installation et découverte de l'ambiance locale." },
      { "day": 2, "title": "Cascades et exploration", "content": "Journée consacrée à la découverte des cascades et à l'exploration naturelle de la région.", "extra": "Guide local prévu selon formule." },
      { "day": 3, "title": "Temps libre et retour", "content": "Matinée libre puis retour vers Abidjan." }
    ],
    "formules": [
      {
        "name": "Standard",
        "price": 119000,
        "color": "bg-slate-100",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Hébergement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": false }
        ]
      },
      {
        "name": "Premium",
        "price": 169000,
        "color": "bg-orange-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Hébergement", "included": true },
          { "name": "Restauration partielle", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      },
      {
        "name": "VIP",
        "price": 269000,
        "color": "bg-amber-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Hébergement premium", "included": true },
          { "name": "Restauration partielle", "included": true },
          { "name": "Transport", "included": true, "note": "Transport inclus" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      }
    ],
    "inclus": ["Guide local", "Hébergement selon formule", "Visites mentionnées", "Assistance locale"],
    "non_inclus": ["Boissons", "Dépenses personnelles", "Activités non mentionnées"],
    "conditions_annulation": [
      { "title": "Remboursement intégral", "detail": "Jusqu'à 10 jours avant le départ" },
      { "title": "Remboursement partiel", "detail": "50% jusqu'à 5 jours avant le départ" }
    ],
    "actif": true,
    "publie": true
  },
  {
    "titre": "Abidjan City Tour",
    "lieu": "Abidjan, Côte d'Ivoire",
    "thematique": "Ville, Lagune, Découverte",
    "description": "Un city tour pour découvrir Abidjan, son Plateau, sa lagune et son énergie urbaine. Parfait pour visiteurs, expatriés ou découverte rapide.",
    "details": ["Excursion urbaine", "Idéal pour demi-journée ou journée complète", "Circuit adaptable aux groupes"],
    "duree": "1 jour(s)",
    "prix_base": 25000,
    "categorie": "local",
    "type_circuit": "excursion",
    "images": [
      "https://commons.wikimedia.org/wiki/Special:Redirect/file/Abidjan%20Plateau.png",
      "https://commons.wikimedia.org/wiki/Special:Redirect/file/Abidjan-Plateau1.JPG"
    ],
    "itineraire": [
      { "day": 1, "title": "Découverte d'Abidjan", "content": "Visite du Plateau et des principaux points de vue sur la lagune avec arrêts photos et présentation générale de la ville." }
    ],
    "formules": [
      {
        "name": "Standard",
        "price": 25000,
        "color": "bg-slate-100",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Restauration", "included": false },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": false }
        ]
      },
      {
        "name": "Premium",
        "price": 45000,
        "color": "bg-orange-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      },
      {
        "name": "VIP",
        "price": 75000,
        "color": "bg-amber-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": true, "note": "Transport inclus" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      }
    ],
    "inclus": ["Guide local", "Assistance", "Visite selon programme"],
    "non_inclus": ["Dépenses personnelles", "Achats personnels"],
    "conditions_annulation": [
      { "title": "Remboursement intégral", "detail": "Jusqu'à 72h avant le départ" },
      { "title": "Remboursement partiel", "detail": "50% jusqu'à 24h avant le départ" }
    ],
    "actif": true,
    "publie": true
  },
  {
    "titre": "Road trip à Sassandra",
    "lieu": "Sassandra, Côte d'Ivoire",
    "thematique": "Plage, Route, Découverte",
    "description": "Un circuit sur la côte ouest pour découvrir Sassandra, son atmosphère maritime et son charme balnéaire plus calme.",
    "details": ["Circuit de plusieurs jours", "Cadre côtier", "Bonne option pour couples ou petits groupes"],
    "duree": "3 jour(s) / 2 nuit(s)",
    "prix_base": 189000,
    "categorie": "local",
    "type_circuit": "circuit long",
    "images": ["https://commons.wikimedia.org/wiki/Special:Redirect/file/Sassandra1.jpg"],
    "itineraire": [
      { "day": 1, "title": "Départ et installation", "content": "Départ depuis Abidjan, trajet vers Sassandra, installation et temps libre." },
      { "day": 2, "title": "Découverte de Sassandra", "content": "Journée d'exploration, détente et découverte du littoral local." },
      { "day": 3, "title": "Retour vers Abidjan", "content": "Petit déjeuner puis retour." }
    ],
    "formules": [
      {
        "name": "Standard",
        "price": 189000,
        "color": "bg-slate-100",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Hébergement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": false }
        ]
      },
      {
        "name": "Premium",
        "price": 239000,
        "color": "bg-orange-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Hébergement", "included": true },
          { "name": "Restauration partielle", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      },
      {
        "name": "VIP",
        "price": 349000,
        "color": "bg-amber-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Hébergement premium", "included": true },
          { "name": "Restauration partielle", "included": true },
          { "name": "Transport", "included": true, "note": "Transport inclus" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      }
    ],
    "inclus": ["Guide local", "Hébergement selon formule", "Assistance locale", "Activités prévues au programme"],
    "non_inclus": ["Boissons", "Dépenses personnelles", "Options hors programme"],
    "conditions_annulation": [
      { "title": "Remboursement intégral", "detail": "Jusqu'à 10 jours avant le départ" },
      { "title": "Remboursement partiel", "detail": "50% jusqu'à 5 jours avant le départ" }
    ],
    "actif": true,
    "publie": true
  },
  {
    "titre": "Immersion culturelle à Korhogo",
    "lieu": "Korhogo, Côte d'Ivoire",
    "thematique": "Culture, Nord, Artisanat",
    "description": "Une immersion dans le nord ivoirien à Korhogo, idéale pour mettre en avant la culture, les savoir-faire et une autre facette du pays.",
    "details": ["Circuit culturel", "Convient aux voyageurs en quête d'authenticité", "Peut être vendu en formule groupe ou premium"],
    "duree": "4 jour(s) / 3 nuit(s)",
    "prix_base": 249000,
    "categorie": "local",
    "type_circuit": "circuit long",
    "images": [
      "https://commons.wikimedia.org/wiki/Special:Redirect/file/Korhogo.jpg",
      "https://commons.wikimedia.org/wiki/Special:Redirect/file/Korhogo%208110.jpg"
    ],
    "itineraire": [
      { "day": 1, "title": "Voyage vers Korhogo", "content": "Départ, arrivée et installation." },
      { "day": 2, "title": "Découverte culturelle", "content": "Visite de la ville et immersion dans l'ambiance locale." },
      { "day": 3, "title": "Temps d'exploration", "content": "Journée souple selon formule choisie : visites, rencontres, détente." },
      { "day": 4, "title": "Retour", "content": "Retour vers Abidjan." }
    ],
    "formules": [
      {
        "name": "Standard",
        "price": 249000,
        "color": "bg-slate-100",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Hébergement", "included": true },
          { "name": "Restauration", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": false }
        ]
      },
      {
        "name": "Premium",
        "price": 329000,
        "color": "bg-orange-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Hébergement", "included": true },
          { "name": "Restauration partielle", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      },
      {
        "name": "VIP",
        "price": 469000,
        "color": "bg-amber-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Hébergement premium", "included": true },
          { "name": "Restauration partielle", "included": true },
          { "name": "Transport", "included": true, "note": "Transport inclus" },
          { "name": "Accompagnateur IvoirTrips", "included": true }
        ]
      }
    ],
    "inclus": ["Guide local", "Hébergement selon formule", "Assistance locale", "Visites prévues au programme"],
    "non_inclus": ["Boissons", "Dépenses personnelles", "Activités non prévues"],
    "conditions_annulation": [
      { "title": "Remboursement intégral", "detail": "Jusqu'à 14 jours avant le départ" },
      { "title": "Remboursement partiel", "detail": "50% jusqu'à 7 jours avant le départ" }
    ],
    "actif": true,
    "publie": true
  },
  {
    "titre": "Aventure en terre sauvage : au coeur du Parc national de Taï",
    "lieu": "Taï, Côte d'Ivoire",
    "thematique": "Eco-tourisme, Aventure, Randonnée",
    "description": "Préparez-vous pour une expédition hors du commun, une aventure immersive au coeur de l'une des dernières grandes forêts primaires d'Afrique de l'Ouest. Le Parc national de Taï, classé au patrimoine mondial de l'UNESCO, est un sanctuaire naturel où règnent une biodiversité exceptionnelle et une nature encore indomptée. Ici, pas de routes goudronnées, pas de signal téléphonique : seulement vous, la jungle et son incroyable faune. Ce circuit vous plonge au plus profond de la forêt tropicale, là où seuls quelques privilégiés osent s'aventurer. Vous suivrez les traces des chimpanzés casseurs de noix, pisterez des singes insaisissables, dormirez en pleine nature et vivrez une expérience unique, entre exploration et survie douce. Si vous aimez l'exploration, si vous rêvez d'expériences authentiques et si vous êtes prêt à sortir de votre zone de confort, alors cette expédition est faite pour vous. Osez l'aventure. Osez Taï.",
    "details": ["Circuit éco-touristique en groupe", "4 jours / 3 nuits", "Pension complète - hébergement inclus", "Randonnée et immersion en forêt", "Observation de la faune"],
    "duree": "4 jour(s) / 3 nuit(s)",
    "prix_base": 241000,
    "categorie": "local",
    "type_circuit": "circuit",
    "images": [
      "/uploads/tai-2-4d0zuzs0eab.jpg",
      "/uploads/tai-2-2ymcvyyppsr.jpg",
      "/uploads/tai-3-wff8e6y3vdl.jpg",
      "/uploads/tai-4-5blkj7fc7lj.webp"
    ],
    "itineraire": [
      { "day": 1, "title": "Cap sur Taï - Aux portes d'une forêt légendaire", "content": "L'aventure commence dès votre arrivée à Taï, dernière halte avant la grande traversée. Déjà, l'atmosphère change : l'air est plus humide, les bruits de la forêt résonnent au loin et l'excitation monte. Vous passerez votre première nuit dans un village traditionnel à Daobly, en mode explorateur, en partageant le quotidien des habitants pour une première immersion authentique.", "extra": "Dîner sous les étoiles, derniers préparatifs et nuit paisible. Pension complète - hébergement inclus." },
      { "day": 2, "title": "Plongée dans l'inconnu - Marche vers le coeur de la jungle", "content": "La grande immersion commence avec une marche vers le coeur de la jungle. Ici, plus de repères habituels : seulement la forêt tropicale, sa densité, ses sons et la sensation grisante d'entrer dans un territoire préservé.", "extra": "Journée d'aventure, de randonnée et de déconnexion totale." },
      { "day": 3, "title": "Pister les primates - L'ultime mission avant le retour", "content": "La journée est consacrée à l'observation de la faune et au pistage des primates. Vous suivrez les traces des chimpanzés et d'autres espèces emblématiques du parc, dans une ambiance de véritable expédition.", "extra": "Un moment fort du circuit pour les amoureux de nature sauvage." },
      { "day": 4, "title": "Derniers instants dans la forêt et retour à la civilisation", "content": "Vous profitez des derniers instants dans la forêt avant de reprendre la route. Le retour laisse en mémoire une aventure intense, rare et profondément dépaysante." }
    ],
    "formules": [
      {
        "name": "Standard",
        "price": 241000,
        "color": "bg-slate-100",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Nourriture", "included": false },
          { "name": "Accompagnateur IVOIR TRIPS", "included": false },
          { "name": "Transport", "included": false, "note": "Véhicule requis" }
        ]
      },
      {
        "name": "Premium",
        "price": 271000,
        "color": "bg-orange-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Nourriture", "included": true },
          { "name": "Accompagnateur IVOIR TRIPS", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" }
        ]
      },
      {
        "name": "VIP",
        "price": 431000,
        "color": "bg-amber-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Nourriture", "included": true },
          { "name": "Accompagnateur IVOIR TRIPS", "included": true },
          { "name": "Transport", "included": true, "note": "Transport inclus" }
        ]
      }
    ],
    "inclus": ["Accompagnement par un guide local francophone ou anglophone", "Véhicule à disposition avec chauffeur et carburant (tarif VIP uniquement)", "Les petits-déjeuners, déjeuners et dîners sauf ceux indiqués comme libres", "Assistance de l'équipe IVOIR TRIPS durant le voyage", "Les repas indiqués au programme", "Les visites, les entrées de sites ou parcs et les activités indiquées au programme", "L'hébergement en chambre double"],
    "non_inclus": ["Assurance voyage", "Excursions optionnelles", "Pourboires et dépenses d'ordre personnel", "Les boissons pendant les repas", "Les repas indiqués comme libres dans le programme"],
    "conditions_annulation": [
      { "title": "Remboursement intégral", "detail": "100% jusqu'à 30 jours avant le voyage" },
      { "title": "Remboursement partiel", "detail": "60% jusqu'à 10 jours avant le voyage" },
      { "title": "Aucun remboursement", "detail": "0% jusqu'à 5 jours avant le voyage" }
    ],
    "actif": true,
    "publie": true
  },
  {
    "titre": "Découverte du Parc National d'Azagny",
    "lieu": "Azagny, Côte d'Ivoire",
    "thematique": "Eco-tourisme, Randonnée, Nature",
    "description": "Partez pour une escapade nature au coeur du Parc National d'Azagny, un espace préservé idéal pour les amoureux d'éco-tourisme. Cette excursion en groupe vous plonge dans un environnement naturel riche, entre randonnée, observation et déconnexion au plus près de la biodiversité ivoirienne.",
    "details": ["Excursion éco-touristique en groupe", "8 heures", "Idéal pour une journée nature", "Observation et balade guidée", "Formules Standard, Premium et VIP"],
    "duree": "8 heure(s)",
    "prix_base": 32500,
    "categorie": "local",
    "type_circuit": "excursion",
    "images": [
      "/uploads/azagny1.jpg",
      "/uploads/azagny2.jpg",
      "/uploads/azagny3.webp",
      "/uploads/azagny4.webp"
    ],
    "itineraire": [
      { "day": 1, "title": "Immersion nature au Parc National d'Azagny", "content": "Départ pour le parc, accueil par le guide local puis découverte de cet espace naturel préservé à travers une excursion orientée nature, randonnée et observation. La journée vous permet de profiter des visites et activités prévues au programme dans une ambiance d'évasion et de groupe.", "extra": "Rafraîchissements inclus et repas selon la formule choisie." }
    ],
    "formules": [
      {
        "name": "Standard",
        "price": 32500,
        "color": "bg-slate-100",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Nourriture", "included": false },
          { "name": "Accompagnateur IVOIR TRIPS", "included": false },
          { "name": "Transport", "included": false, "note": "Véhicule requis" }
        ]
      },
      {
        "name": "Premium",
        "price": 69000,
        "color": "bg-orange-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Nourriture", "included": true },
          { "name": "Accompagnateur IVOIR TRIPS", "included": true },
          { "name": "Transport", "included": false, "note": "Véhicule requis" }
        ]
      },
      {
        "name": "VIP",
        "price": 145000,
        "color": "bg-amber-50",
        "features": [
          { "name": "Guide", "included": true },
          { "name": "Rafraîchissement", "included": true },
          { "name": "Nourriture", "included": true },
          { "name": "Accompagnateur IVOIR TRIPS", "included": true },
          { "name": "Transport", "included": true, "note": "Transport inclus" }
        ]
      }
    ],
    "inclus": ["Accompagnement par un guide local francophone ou anglophone", "Véhicule à disposition avec chauffeur et carburant (tarif VIP uniquement)", "Visites, entrées de sites ou parcs et activités indiquées dans le programme", "Assistance de l'équipe IVOIR TRIPS durant le voyage", "Repas indiqués au programme", "Boissons pendant les repas"],
    "non_inclus": ["Repas indiqués comme libres dans le programme", "Pourboires et dépenses d'ordre personnel", "Excursions optionnelles", "Assurance voyage"],
    "conditions_annulation": [
      { "title": "Remboursement intégral", "detail": "100% jusqu'à 7 jours avant le voyage" },
      { "title": "Remboursement partiel", "detail": "50% jusqu'à 5 jours avant le voyage" },
      { "title": "Aucun remboursement", "detail": "0% jusqu'à 3 jours avant le voyage" }
    ],
    "actif": true,
    "publie": true
  }
]
$ivoirtrips$::jsonb) AS circuit(
    titre text,
    lieu text,
    thematique text,
    description text,
    details jsonb,
    duree text,
    prix_base numeric,
    categorie text,
    type_circuit text,
    images jsonb,
    itineraire jsonb,
    formules jsonb,
    inclus jsonb,
    non_inclus jsonb,
    conditions_annulation jsonb,
    actif boolean,
    publie boolean
  )
)
INSERT INTO circuits_touristiques (
  titre,
  lieu,
  thematique,
  description,
  details,
  duree,
  prix_base,
  categorie,
  type_circuit,
  images,
  itineraire,
  formules,
  inclus,
  non_inclus,
  conditions_annulation,
  actif,
  publie
)
SELECT
  titre,
  lieu,
  thematique,
  description,
  COALESCE(details, '[]'::jsonb),
  duree,
  COALESCE(prix_base, 0),
  COALESCE(categorie, 'local'),
  type_circuit,
  COALESCE(images, '[]'::jsonb),
  COALESCE(itineraire, '[]'::jsonb),
  COALESCE(formules, '[]'::jsonb),
  COALESCE(inclus, '[]'::jsonb),
  COALESCE(non_inclus, '[]'::jsonb),
  COALESCE(conditions_annulation, '[]'::jsonb),
  COALESCE(actif, true),
  COALESCE(publie, true)
FROM seed
WHERE NOT EXISTS (
  SELECT 1
  FROM circuits_touristiques existing
  WHERE lower(existing.titre) = lower(seed.titre)
);

COMMIT;
