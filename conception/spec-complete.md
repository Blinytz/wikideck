# Wikideck : spec complète

Reçue le 03/11/2026. Avancement en fin de document.

Repo : blinytz/gacha-wikipedia (publié sous Blinytz/wikideck). Aucune valeur en dur : tout paramètre passe par
config.js et l'écran Réglages. Les valeurs ci-dessous sont les valeurs par défaut.
Fuseau de référence : Europe/Paris. Le « jour de jeu » commence à 4 h.

## 0. Architecture
- Wikideck rejoint l'écosystème Éclats en ligne, piloté par la Centrale, avec la
  même intégration que Pronos et Cagnottes (solde, mouvements, identification).
- L'état de jeu est stocké dans le Supabase Éclats : cartes possédées, paquets
  (en chargement, prêts, en inventaire), historique, cartes lues, Résonance,
  questions, série, objectifs, boutique. localStorage ne sert plus que de cache.
- Migration unique au premier lancement : cartes possédées et progression des
  paquets envoyées au serveur, éclats locaux transférés sur la Centrale.
- La Station de Recherche est désactivée : vitesse fixe à 1, Station retirée de
  l'interface, code conservé.
- Catalogue des cartes synchronisé dans Supabase par une GitHub Action
  déclenchée à chaque push qui modifie data/.
- Copie des questions Quinytz (voir 3.1).

## 1. Paquets
- Paquet passif : 12 h (dureeBaseSecondes = 43200), 7 cartes (tailleDuPaquet = 7).
  File illimitée, le suivant démarre derrière. Migration : progression et
  paquets prêts conservés.
- Tirage équiprobable sur le pool global (cartes non archivées).
- Paquet standard = 7 cartes du pool global. Tout « paquet » gagné en
  récompense sans autre précision est un paquet standard, ajouté aux paquets prêts.
- Les paquets spéciaux (Collection, Thème, Plancher, Inédit, Sommet, etc.)
  gagnés ou achetés vont dans un inventaire et s'ouvrent quand on veut.

## 2. Ouverture du paquet
- Le paquet arrive fermé, on le déchire d'un geste (glisser).
- Cartes posées face cachée, chacune entourée d'un halo de la couleur de sa rareté.
- Révélation une par une, par rareté croissante, la meilleure en dernier.
- Une animation par rareté, de la plus sobre à la plus excentrique :
  - Commune : retournement simple
  - Rare : retournement avec reflet lumineux qui balaie la carte
  - Épique : pause, halo violet pulsé, particules légères
  - Mythique : la carte tremble, éclat de lumière, son grave
  - Légendaire : écran assombri, faisceau doré, la carte descend du haut,
    pluie d'étincelles
  - Panthéon : séquence complète (paquet figé, écran qui se fissure, fond
    cosmique, vortex, explosion de couleurs, nom gravé lettre par lettre,
    musique dédiée). Jamais passable.
- Tampon « Nouvelle » sur chaque carte jamais possédée.
- Récapitulatif final : nouvelles cartes, collections qui ont progressé,
  jauges de Résonance remplies ou déclenchées.

## 3. Questions

### 3.1 Copie des questions Quinytz
- GitHub Action hebdomadaire, lundi 4 h : lit les questions Quinytz et les
  met à jour dans le Supabase Éclats (upsert, questions retirées désactivées).
  Clés dans les secrets GitHub. Aucune dépendance entre les deux projets à
  l'exécution.

### 3.2 Choix de la question
- 3 propositions tirées totalement au hasard parmi les questions éligibles :
  thème et difficulté visibles, question cachée. Le joueur en choisit une.
- On ne peut pas relancer le tirage. Une fois une question choisie, les deux
  autres sont défaussées (elles restent éligibles).

### 3.3 Validation
- Réponse libre. Normalisation (casse, accents, articles, ponctuation, espaces)
  puis comparaison avec la réponse et ses variantes acceptées, avec une
  tolérance de Levenshtein proportionnelle à la longueur (paramètre).
- Le jeu affiche son verdict et la bonne réponse. Le joueur peut corriger dans
  les deux sens (« en fait j'avais bon » / « en fait j'avais faux »). La
  correction recalcule le gain, la suite et les compteurs.

### 3.4 Gains de temps
- Gain de base : Débutant 6 min, Confirmé 12, Expert 24, Nobel 45, Omniscient 90.
- Suite = bonnes réponses consécutives, réponse en cours comprise.
  Multiplicateur : 1 à 2 → ×1, 3 à 4 → ×1,5, 5 à 9 → ×2, 10 à 19 → ×3, 20+ → ×4.
- Erreur : aucun temps gagné ni perdu, la suite repart à zéro.
- Le gain retire du temps au paquet passif en cours. Le surplus déborde sur
  les paquets suivants (un gain peut rendre plusieurs paquets prêts). Aucun plafond.
- La suite est conservée entre les sessions de jeu, sans limite de durée.

### 3.5 Retour des questions
- Ratée : éligible de nouveau 7 jours après.
- Réussie : 15 jours, puis le délai double à chaque nouvelle réussite
  consécutive (15, 30, 60, 120…).
- Erreur après une ou plusieurs réussites : retour à 7 jours.
- Si moins de 3 questions sont éligibles, on complète avec celles dont le délai
  expire le plus tôt.

### 3.6 Question du jour
- Une question Omniscient par jour de jeu (Nobel si aucune Omniscient éligible).
- Gain fixe 180 min, hors suite (ne la fait ni monter ni casser), ne compte pas
  dans les 10 bonnes réponses quotidiennes. Même règle de retour que les autres.

## 4. Série quotidienne
- Jour validé = 10 bonnes réponses sur le jour de jeu (hors question du jour).
- Paliers et récompenses :
  3 j → 1 paquet ; 7 j → 2 paquets + 1 Gel ; 14 j → paquet Plancher ;
  30 j → paquet Inédit ; 60 j → Grand paquet + 50 000 éclats ;
  100 j → paquet Sommet ; 182 j → 2 paquets Inédit ;
  365 j → une Panthéon manquante garantie (50 000 éclats si toutes possédées).
  Au-delà de 365 j : paquet Sommet tous les 365 jours.
- Gel de série : 1 au palier 7 jours, puis 1 tous les 30 jours de série
  validés (30, 60, 90…). Aucun maximum.
- À 4 h, si le jour écoulé n'est pas validé : un Gel est consommé
  automatiquement et la série continue (le jour gelé compte dans la série sans
  être validé). Sans Gel, la série repart à zéro.
- Écran dédié : série en cours, record, prochain palier, calendrier (validé,
  gelé, manqué), Gels disponibles, bonnes réponses du jour (x/10).

## 5. Collection

### 5.1 Historique d'ouverture
- Chaque ouverture enregistre : date, source (passif, questions, boutique,
  récompense, Résonance), type de paquet, cartes, rareté au moment du tirage,
  statut « Nouvelle ».
- Écran antéchronologique, filtres « nouvelles uniquement » et « non lues ».
- Appui sur une carte : même fiche détaillée que dans les collections.

### 5.2 Cartes lues
- Une carte est marquée lue quand on ouvre son lien Wikipédia depuis sa fiche.
- Indicateur sur la carte, filtre dans les collections et l'historique.

### 5.3 Résonance
- Chaque doublon obtenu, quelle que soit sa source, charge la jauge de sa collection.
- Seuil = arrondi(15 × 1,5^n), n = Résonances déjà déclenchées dans cette collection.
- Jauge pleine : une carte manquante de la collection, tirée au hasard, est
  ajoutée (enregistrée dans l'historique, source Résonance). La jauge repart à zéro.
- Collection complète : jauge en pause.

### 5.4 Valeurs et revente
- Valeur de référence : Commune 500, Rare 1 000, Épique 2 500, Mythique 5 000,
  Légendaire 15 000, Panthéon 50 000.
- Revente d'un doublon = 30 % : 150, 300, 750, 1 500, 4 500, 15 000. Crédit
  sur la Centrale. Le dernier exemplaire n'est jamais vendable.
- Vente groupée : bouton « vendre tous les doublons » (filtrable par rareté),
  avec confirmation et total affiché.

### 5.5 Fins de collection
- Collection terminée : 1 paquet Collection d'une autre collection incomplète
  tirée au hasard (paquet Inédit s'il n'en reste aucune) + 500 éclats par
  carte de la collection terminée.
- Toutes les collections d'un thème terminées : 1 paquet Inédit.

### 5.6 Catalogue évolutif
Ajouts de cartes, collections et thèmes pris en compte sans intervention, par
simple push des données.
- Id de carte figé à la publication, même si la carte change de nom ou de
  collection (table d'alias si besoin).
- Carte retirée jamais supprimée : elle sort du tirage et reste dans la
  collection de ceux qui la possèdent, marquée « archivée ».
- La rareté peut changer à la régénération des données. Valeurs, revente et
  prix suivent la rareté actuelle. L'historique garde la rareté au tirage, la
  fiche affiche « anciennement X ». À la réception d'un nouveau catalogue,
  récapitulatif unique des cartes possédées qui ont changé de rareté.
- Collection complète qui reçoit de nouvelles cartes : récompense déjà
  obtenue acquise, collection repassée incomplète, jauge de Résonance
  réactivée (coût conservé). La recompléter rapporte 1 paquet de cette
  collection, une fois par réouverture.

## 6. Objectifs
Récompense selon le rang du palier dans sa famille : 1er → 1 paquet ;
2e → 2 paquets ; 3e → paquet Plancher ; 4e → paquet Inédit ;
5e et suivants → paquet Inédit + 25 000 éclats ; palier « toutes » → paquet
Sommet. Un palier obtenu reste obtenu. Paliers « toutes » toujours dynamiques.

Questions (comptées après correction éventuelle) :
- Bonnes réponses au total : 10, 100, 500, 1 000, 2 500, 5 000, 10 000
- Bonnes réponses Nobel : 10, 50, 200, 500
- Bonnes réponses Omniscient : 1, 10, 50, 100, 250
- Spécialiste, un objectif par thème Quinytz (généré depuis la copie) : 25, 100, 250
- Record de suite : 5, 10, 20, 30, 50
- Suites de 5 ou plus en Expert ou au-dessus : 1, 10, 50
- Questions du jour réussies : 7, 30, 100, 365

Collection :
- Cartes possédées : 100, 500, 1 000, 2 500, 5 000, 7 500, toutes
- Collections terminées : 1, 5, 10, 25, 50, 100, toutes
- Thèmes terminés : 1, 3, 5, toutes
- Légendaires possédées : 10, 50, 100, toutes
- Panthéon possédées : 1, 5, 10, 25, toutes
- Cartes lues : 10, 100, 500, 1 000, 2 500, 5 000
- Paquets ouverts : 10, 100, 500, 1 000
- Résonances déclenchées : 1, 10, 50

Écran Objectifs : familles, palier suivant, progression, récompense.

## 7. Paquets spéciaux
| Type | Contenu |
|---|---|
| Collection | 7 cartes d'une collection donnée |
| Thème | 7 cartes d'un des thèmes de collections.json |
| Duo | 7 cartes réparties au hasard entre deux collections données |
| Grand paquet | 20 cartes du pool global |
| Initiale | 7 cartes dont le nom commence par une lettre donnée (lettres ayant au moins 30 cartes) |
| Mystère | un des autres types (hors Sommet), révélé à l'ouverture |
| Plancher | 6 cartes du pool global + 1 carte Mythique ou plus (tirée parmi Mythiques, Légendaires, Panthéon, au prorata de leur nombre) |
| Inédit | 5 cartes jamais possédées ; s'il en manque moins de 5, complété par des cartes du pool global ; si aucune ne manque, 5 cartes du pool global + la valeur de référence d'une Légendaire en éclats |
| Sommet | 7 cartes parmi Légendaires et Panthéon, au prorata de leur nombre |

## 8. Boutique
- 3 emplacements. À la première ouverture, 3 offres tirées.
- Chaque offre affiche son contenu précis (« Thème : Religions et
  mythologies », « Duo : Dinosaures célèbres et Volcans », « Initiale : M »).
  Seul le Mystère cache son type.
- Achat unique : une fois achetée, l'offre disparaît. Un emplacement vide
  (achat ou expiration) reçoit une nouvelle offre après 2 à 6 h.
- Le joueur ne choisit jamais le contenu. Paiement par débit sur la Centrale.

| Type | Poids | Durée |
|---|---|---|
| Collection, Thème, Duo | 20 chacun | 24 à 48 h |
| Grand paquet | 10 | 24 h |
| Initiale, Mystère | 8 chacun | 24 h |
| Plancher | 4 | 12 h |
| Inédit | 2 | 12 h |
| Sommet | 0,5 | 6 h |

- Prix = valeur moyenne du contenu possible, calculée sur les cartes réelles
  avec les valeurs de référence (Mystère : prix moyen des types possibles,
  Inédit : valeur × 3). Arrondi à la centaine.
- Remises, appliquées au prix de base :
  - 25 % des offres sortent avec -10 à -30 %
  - 5 % deviennent une offre flash : -40 à -50 %, durée 2 à 6 h
  - 20 % des offres non flash baissent avec le temps : -10 % à mi-durée,
    -25 % dans les 6 dernières heures
- L'offre affiche son prix barré, sa remise et son temps restant.

## 9. Notifications push
- Chrome Android. Web Push (clés VAPID) envoyé par une Edge Function du
  Supabase Éclats, déclenchée par pg_cron. Abonnement via le service worker.
- Notifications (activables une par une dans Réglages) : paquet prêt ;
  nouvelle offre ; offre flash ; offre qui expire dans 2 h ; série en danger
  (21 h sans les 10 bonnes réponses, avec les Gels restants) ; question du
  jour disponible (envoyée à 9 h).

## 10. Écrans
Accueil (paquet en cours, paquets prêts, inventaire, série), Ouverture,
Questions, Collection, Historique, Boutique, Série, Objectifs, Réglages.

---

## Avancement

- **Étape 1, publiée le 03/11/2026** : §1 paquets 12 h / 7 cartes, Station retirée (code conservé, `stationActive`) ; §2 ouverture complète ; §5.1 historique ; §5.2 cartes lues ; §5.3 Résonance ; §5.4 valeurs, revente 30 %, vente groupée.
- **Étape 2, publiée le 03/11/2026** : §10 accueil et navigation ; §7 paquets spéciaux et inventaire ; §5.5 fins de collection ; §5.6 catalogue évolutif (archivage, « anciennement X », récapitulatif) ; §3 moteur de questions complet ; §4 série ; §6 objectifs ; §8 boutique.
- **Étape 3, code publié le 03/11/2026, à activer** : §0 synchronisation de l'état avec le Supabase Éclats et migration unique (`js/synchro.js`), Éclats sur le registre commun (`js/portefeuille.js`), copie Quinytz et catalogue par GitHub Actions (`.github/workflows/`, `build/serveur/`), notifications push (`supabase/functions/wikideck-push`, `sql/02_cron.sql`, `js/notifications.js`). Activation : `sql/01_wikideck.sql`, secrets GitHub et Supabase, déploiement de la fonction (voir `sql/ACTIVATION.md`).
