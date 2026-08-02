# Audit des collections Wikigacha — Document d'implémentation

**Dépôt :** `blinytz/gacha-wikipedia`
**Données :** `data/collections.json` (index) + `data/<slug>.json` (clé `cartes`)
**Version :** v1 — lot 1 (corps célestes, mythologie grecque, dirigeants, monuments, constellations)
**Date :** 2 août 2026

---

## Consignes générales pour Claude Code

1. **Ne rien inventer.** Toutes les cartes à ajouter sont nommées explicitement dans ce document. Si une carte de la liste pose problème (page Wikipédia introuvable, homonymie ambiguë), la signaler au lieu de la remplacer par un choix arbitraire.
2. **Pipeline d'ajout de carte** : résoudre `titrePage` sur fr.wikipedia.org → récupérer `imageUrl` / `thumbUrl` / `description` / `pageviews` / `liensSortants` → générer `tags` (Wikidata, axes Lieu/Temps) → calculer `pv`, `pvCombat`, `role`, `pouvoir` selon les règles existantes.
3. **Renumérotation obligatoire** : après suppressions/ajouts, renuméroter `numero` de 1 à N en continu sur chaque collection touchée. Plusieurs collections ont aujourd'hui des trous.
4. **Raretés** : la rareté est calculée depuis les pageviews. Les surcharges manuelles listées en section « Raretés » sont à appliquer **après** le calcul automatique, en dur.
5. **Homonymes inter-collections** : deux cartes ne doivent jamais porter exactement le même `nom` dans deux collections différentes. Règle de résolution : suffixer avec le type entre parenthèses, ex. `Charon (lune)`.
6. **Mettre à jour `collections.json`** (nom, slug, description, nombre de cartes) pour toute création/scission.

**9. Liens Wikipédia des cartes à ajouter.** Le fichier `annexe_liens_wikipedia.csv` accompagne ce document. Il contient, pour chacune des **1 473 cartes à créer**, quatre colonnes : `collection`, `nom_carte`, `titrePage`, `lienWikipedia`. Ce fichier est la source de vérité pour la résolution des pages : utiliser le `titrePage` fourni plutôt que de deviner depuis le nom de la carte.

- Les lignes dont la colonne `statut` vaut **`à vérifier`** (67 entrées) portent une ambiguïté connue : homonymie, page de redirection possible, ou titre exact incertain. Pour celles-ci, interroger l'API MediaWiki (`https://fr.wikipedia.org/w/api.php?action=query&list=search`) avec le `titrePage` proposé en première hypothèse, et retenir la page réellement pertinente.
- Si une page renvoie une **page d'homonymie**, ne pas la retenir : résoudre vers l'article spécifique.
- Si une page est introuvable, **signaler la carte** au lieu de la remplacer par un choix arbitraire.

**10. Champs à générer pour chaque carte ajoutée.** Le document et son annexe fournissent uniquement `nom`, `titrePage` et `lienWikipedia`. Pour chaque carte créée, Claude Code doit produire en plus :

| Champ | Méthode |
|---|---|
| `imageUrl` / `thumbUrl` | image principale de la page Wikipédia, récupérée à la construction selon le pipeline Python existant (logique par source : TMDB pour les films, art de fandom pour la mythologie, cartes de position Wikimedia pour les lieux) |
| `description` | résumé d'introduction de la page |
| `pageviews` | consultations sur 12 mois, via l'API Wikimedia Pageviews |
| `rarete` | calcul automatique depuis les `pageviews`, **puis** application des surcharges manuelles listées dans les sections « Raretés à forcer » de ce document |
| `pouvoir` | générateur automatique à 3 variables déjà en place : catégorie → `déclencheur`, nombre de liens sortants → `familleId`, rareté + notoriété → `valeur` et `unité` |
| `pv`, `pvCombat`, `role` | selon les règles de combat existantes |
| `tags` | génération Wikidata sur les axes Lieu et Temps uniquement |

Aucune carte ne doit être livrée sans image, sans rareté et sans pouvoir.

---

# 1. CORPS CÉLESTES

**Slug :** `corps-celestes`
**État actuel :** 49 cartes
**Décision :** pas de scission. Extension massive + renommages.
**Cible :** ~97 cartes

## 1.1 Suppressions
Aucune. Les lunes moyennes de Saturne et Uranus sont conservées.

## 1.2 Renommages (résolution d'homonymes)

| Nom actuel | Nouveau nom | Raison |
|---|---|---|
| Charon | `Charon (lune)` | conflit avec Charon (mythologie grecque) |
| Éris | `Éris (planète naine)` | conflit avec Éris (mythologie grecque) |
| Rhéa | `Rhéa (lune)` | conflit avec Rhéa (Titanide, ajoutée en mythologie) |
| Titan | `Titan (lune)` | ambiguïté avec les Titans mythologiques |
| Europe | `Europe (lune)` | ambiguïté avec le continent (tags) |

Ne pas modifier `titrePage` ni `lienWikipedia` : uniquement le champ `nom` affiché.

## 1.3 Ajouts (48 cartes)

### Étoile centrale (1)
- Soleil

### Étoiles remarquables (12)
- Bételgeuse
- Sirius
- Proxima du Centaure
- Alpha Centauri
- Véga
- Rigel
- Antarès
- Aldébaran
- Arcturus
- Deneb
- Altaïr
- Étoile polaire

### Galaxies (8)
- Voie lactée
- Galaxie d'Andromède
- Galaxie du Tourbillon
- Galaxie du Sombrero
- Grand Nuage de Magellan
- Petit Nuage de Magellan
- Galaxie du Triangle
- Centaurus A

### Amas et grandes structures (6)
- Pléiades
- Amas d'Hercule
- Amas de la Vierge
- Ceinture d'astéroïdes
- Ceinture de Kuiper
- Nuage d'Oort

### Comètes et objets transitoires (6)
- Comète de Halley
- Comète Hale-Bopp
- 67P/Tchourioumov-Guérassimenko
- Shoemaker-Levy 9
- C/2020 F3 (NEOWISE)
- ʻOumuamua

### Astéroïdes (5)
- (4) Vesta
- (2) Pallas
- (101955) Bennu
- (99942) Apophis
- (162173) Ryugu

### Objets transneptuniens (1)
- (90377) Sedna

### Exoplanètes et systèmes (5)
- TRAPPIST-1
- Proxima Centauri b
- Kepler-452b
- 51 Pegasi b
- HD 189733 b

### Nébuleuses supplémentaires (5)
- Nébuleuse de la Lagune
- Nébuleuse Trifide
- Nébuleuse de l'Œil de Chat
- Nébuleuse de la Tarentule
- Nébuleuse Oméga

## 1.4 Raretés à forcer

| Carte | Rareté actuelle | Rareté forcée |
|---|---|---|
| Soleil | (nouvelle) | mythique |
| Terre | legendaire | mythique |
| Voie lactée | (nouvelle) | legendaire |
| M87* | commune | epique |
| Sagittarius A* | rare | epique |
| TON 618 | epique | rare |
| Gaia BH1 | commune | commune (inchangé) |
| Comète de Halley | (nouvelle) | epique |
| Bételgeuse | (nouvelle) | rare |

---

# 2. DIEUX ET FIGURES MYTHOLOGIQUES GRECQUES

**Slug :** `dieux-et-figures-mythologiques-grecques`
**État actuel :** 38 cartes, numérotation trouée (26, 30, 40 manquants)
**Décision :** pas de scission. Correction + extension.
**Cible :** ~79 cartes

## 2.1 Correction critique

La carte **« Chronos »** (n°24) pointe vers la page du dieu primordial du Temps, alors qu'elle est censée représenter le Titan père de Zeus.

**Action en deux temps :**
1. Renommer la carte existante en **Cronos**, `titrePage` = `Cronos`, `lienWikipedia` = `https://fr.wikipedia.org/wiki/Cronos`. Régénérer description, image, pageviews.
2. **Créer une nouvelle carte** `Chronos` (divinité primordiale du Temps), `titrePage` = `Chronos`. C'est bien une entité distincte.

## 2.2 Renumérotation
Renuméroter de 1 à N en continu après ajouts.

## 2.3 Suppressions
Aucune.

## 2.4 Ajouts (40 cartes)

### Divinités primordiales et Titans (7)
- Gaïa
- Ouranos
- Rhéa
- Atlas
- Chronos *(voir §2.1)*
- Styx
- Hélios

### Olympiens et divinités manquantes (6)
- Héphaïstos *(le panthéon olympien était incomplet)*
- Éros
- Pan
- Asclépios
- Iris
- Les Muses

### Héros (9)
- Héraclès
- Ulysse
- Persée
- Thésée
- Jason
- Bellérophon
- Icare
- Dédale
- Œdipe

### Cycle troyen (5)
- Hector
- Pâris
- Hélène de Troie
- Agamemnon
- Cassandre

### Figures féminines et mortels (6)
- Pandore
- Narcisse
- Ariane
- Pénélope
- Circé
- Antigone

### Créatures et monstres (11)
- Minotaure
- Pégase
- Hydre de Lerne
- Chimère
- Sirène (mythologie grecque)
- Polyphème
- Sphinx
- Arachné
- Charybde
- Chiron
- Harpie

## 2.5 Raretés à forcer

| Carte | Rareté actuelle | Rareté forcée |
|---|---|---|
| Hadès | rare | epique |
| Poséidon | rare | epique |
| Héraclès | (nouvelle) | legendaire |
| Minotaure | (nouvelle) | epique |
| Cronos | commune | epique |
| Pégase | (nouvelle) | rare |

---

# 3. GRANDS DIRIGEANTS → SCISSION EN 2 COLLECTIONS

**État actuel :** `grands-dirigeants`, 67 cartes
**Décision :** scission chronologique à la Révolution française (1789).

- Collection A : **Souverains et conquérants** — slug `souverains-et-conquerants` — Antiquité → 1789
- Collection B : **Dirigeants de l'ère contemporaine** — slug `dirigeants-contemporains` — 1789 → aujourd'hui

## 3.1 Suppressions préalables (2)
- **Gilgamesh** — figure légendaire/épique, pas un dirigeant historique. À déplacer vers `mythologies-du-monde-hors-grece`.
- **Didon** — fondatrice mythique de Carthage. Idem.

## 3.2 Correction critique

La carte **« Elizabeth Ire »** (n°2) pointe en réalité vers **Élisabeth Ire de Russie** (impératrice, fille de Pierre le Grand). D'où ses tags « Empire russe / Eurasie / XVIIIe siècle » et sa rareté commune.

**Action :**
1. Renommer la carte en **Élisabeth Ire de Russie** (elle reste valide, page correcte).
2. **Créer** la carte **Élisabeth Ire d'Angleterre**, `titrePage` = `Élisabeth Ire (reine d'Angleterre)`, rareté forcée **mythique**.

## 3.3 Correction de tags
- **Simón Bolívar** : tags actuels `['Espagne','Europe','XVIIIe siècle','XIXe siècle']` → doivent être `['Venezuela','Amérique du Sud','XVIIIe siècle','XIXe siècle']`.

## 3.4 Répartition des cartes existantes

### → Souverains et conquérants (57 cartes)
Élisabeth Ire de Russie · Napoléon · Catherine II · Qin Shi Huang · Cléopâtre · Ramsès II · Périclès · Alexandre le Grand · Auguste · Trajan · Tokugawa Ieyasu · Saladin · Darius Ier · Cyrus le Grand · Gengis Khan · Moctezuma Ier · Pachacuti · Pacal le Grand · Askia Mohammed · Christine de Suède · Harald Hardrada · Harald à la Dent bleue · Guillaume d'Orange · Isabelle Ire · Marie Ire · Casimir III · Soliman le Magnifique · Justinien Ier · Théodora · Sejong le Grand · Jayavarman VII · Amanitore · Mvemba a Nzinga · Robert Ier d'Écosse · Tamar de Géorgie · Matthias Corvin · Mansa Moussa · Hannibal Barca · Boadicée · Vercingétorix · Louis XIV · Charlemagne · Frédéric II le Grand · Pierre le Grand · Ivan le Terrible · Marie-Thérèse d'Autriche · Wu Zetian · Kubilai Khan · Ashoka · Akbar · Attila · Harun al-Rashid · Sundiata Keïta · Ana de Sousa Nzinga Mbande · Piye · Kamehameha Ier · Tecumseh

> Note : Napoléon est classé ici (souverain-conquérant). Kamehameha (unification 1810) et Tecumseh (mort 1813) sont classés ici pour cohérence de style de pouvoir.

### → Dirigeants de l'ère contemporaine (8 cartes)
Abraham Lincoln · Otto von Bismarck · Gandhi · Shaka · Haïlé Sélassié · Victoria · Simón Bolívar · Pedro II

## 3.5 Ajouts — Souverains et conquérants (33 cartes)

### Proche-Orient et Égypte antiques (6)
- Hammurabi
- Nabuchodonosor II
- Hatchepsout
- Toutânkhamon
- Akhenaton
- Xerxès Ier

### Grèce et Rome (6)
- Léonidas Ier
- Jules César
- Marc Antoine
- Néron
- Marc Aurèle
- Constantin Ier

### Moyen Âge européen (7)
- Clovis Ier
- Guillaume le Conquérant
- Richard Cœur de Lion
- Frédéric Barberousse
- Philippe Auguste
- Louis IX
- Aliénor d'Aquitaine

### Europe moderne (8)
- Élisabeth Ire d'Angleterre *(voir §3.2)*
- Henri VIII
- François Ier
- Charles Quint
- Philippe II d'Espagne
- Henri IV
- Oliver Cromwell
- Louis XVI

### Asie et monde musulman (6)
- Mehmed II
- Tamerlan
- Oda Nobunaga
- Toyotomi Hideyoshi
- Kangxi
- Shah Jahan

**Total collection A : 57 + 33 = 90 cartes**

## 3.6 Ajouts — Dirigeants de l'ère contemporaine (48 cartes)

> Décision assumée : la collection inclut les dirigeants infâmes au même titre que les autres (Attila et Ivan le Terrible étaient déjà présents dans la collection d'origine). Le critère est l'impact historique, pas le jugement moral.

### Fondateurs et révolutionnaires (5)
- George Washington
- Maximilien de Robespierre
- Toussaint Louverture
- Giuseppe Garibaldi
- Sun Yat-sen

### Europe XIXe – début XXe (6)
- Napoléon III
- Guillaume II
- François-Joseph Ier
- Nicolas II
- Léopold II
- Georges Clemenceau

### Régimes totalitaires et Seconde Guerre mondiale (7)
- Vladimir Lénine
- Joseph Staline
- Adolf Hitler
- Benito Mussolini
- Francisco Franco
- Hirohito
- Winston Churchill

### États-Unis (6)
- Theodore Roosevelt
- Woodrow Wilson
- Franklin Delano Roosevelt
- Harry S. Truman
- Dwight D. Eisenhower
- John Fitzgerald Kennedy

### Asie (6)
- Empereur Meiji
- Cixi
- Mao Zedong
- Tchang Kaï-chek
- Hô Chi Minh
- Deng Xiaoping

### Décolonisation, Afrique, Moyen-Orient (8)
- Mustafa Kemal Atatürk
- Gamal Abdel Nasser
- Kwame Nkrumah
- Patrice Lumumba
- Thomas Sankara
- Nelson Mandela
- Ménélik II
- David Ben Gourion

### Guerre froide et fin de siècle (10)
- Charles de Gaulle
- Fidel Castro
- Jawaharlal Nehru
- Indira Gandhi
- Pol Pot
- Golda Meir
- Margaret Thatcher
- Ronald Reagan
- Mikhaïl Gorbatchev
- Juan Perón

**Total collection B : 8 + 48 = 56 cartes**

## 3.7 Raretés à forcer

| Carte | Collection | Rareté forcée |
|---|---|---|
| Élisabeth Ire d'Angleterre | A | mythique |
| Jules César | A | mythique |
| Marie Ire | A | rare *(actuellement épique, disproportionné)* |
| Élisabeth Ire de Russie | A | commune (inchangé) |
| Adolf Hitler | B | legendaire |
| Winston Churchill | B | epique |
| Nelson Mandela | B | epique |
| Charles de Gaulle | B | epique |

---

# 4. MONUMENTS EMBLÉMATIQUES → SCISSION EN 2 COLLECTIONS

**État actuel :** `monuments-emblematiques`, 50 cartes
**Décision :** scission par nature de l'objet.

- Collection A : **Monuments et architecture** — slug `monuments-emblematiques` (conservé) — édifices bâtis, Moyen Âge → aujourd'hui
- Collection B : **Sites antiques et archéologiques** — slug `sites-antiques` — vestiges, ruines, sites de fouilles

**Contrainte de non-recouvrement :** ne jamais réintroduire les cartes déjà présentes dans `merveilles-du-monde` (Grande Pyramide de Gizeh, Grande Muraille, Pétra, Machu Picchu, Chichén Itzá, Colisée, Taj Mahal, Christ rédempteur). La séparation actuelle est propre, la maintenir.

## 4.1 Suppression (1)
- **Table Mountain** — site naturel, pas un monument. À supprimer de la collection.

## 4.2 Répartition des cartes existantes

### → Sites antiques et archéologiques (11 cartes)
Acropole d'Athènes · Stonehenge · Teotihuacan · Forum romain · Armée de terre cuite de Xi'an · Panthéon de Rome · Temple de Karnak · Vallée des Rois · Abou Simbel · Ruines de Palmyre · Moaïs de l'île de Pâques

### → Monuments et architecture (38 cartes)
Toutes les autres cartes existantes, hors Table Mountain.

## 4.3 Ajouts — Sites antiques et archéologiques (28 cartes)

### Égypte et Nubie (3)
- Sphinx de Gizeh
- Pyramides de Méroé
- Deir el-Bahari

### Proche-Orient et Mésopotamie (6)
- Persépolis
- Ziggourat d'Our
- Porte d'Ishtar
- Baalbek
- Masada
- Éphèse

### Monde gréco-romain (5)
- Pompéi
- Delphes
- Olympie
- Mycènes
- Cnossos

### Afrique du Nord et subsaharienne (3)
- Leptis Magna
- Volubilis
- Grand Zimbabwe

### Europe préhistorique et celtique (4)
- Alignements de Carnac
- Newgrange
- Skara Brae
- Lascaux

### Asie (3)
- Göbekli Tepe
- Mohenjo-daro
- Grottes d'Ajanta

### Amériques (4)
- Tikal
- Palenque
- Lignes de Nazca
- Sacsayhuamán

**Total collection B : 11 + 28 = 39 cartes**

## 4.4 Ajouts — Monuments et architecture (37 cartes)

### France (6)
- Arc de Triomphe
- Sacré-Cœur de Montmartre
- Pyramide du Louvre
- Palais des Papes
- Château de Chenonceau
- Pont du Gard

### Royaume-Uni et Irlande (3)
- Tower Bridge
- Tour de Londres
- Abbaye de Westminster

### Europe continentale (10)
- Mosquée-cathédrale de Cordoue
- Tour de Belém
- Cathédrale Santa Maria del Fiore
- Basilique Saint-Marc
- Fontaine de Trevi
- Cathédrale de Chartres
- Atomium
- Grand-Place de Bruxelles
- Château de Schönbrunn
- Musée Guggenheim (Bilbao)

### Europe de l'Est et Russie (4)
- Palais d'Hiver
- Mur de Berlin
- Château de Bran
- Palais du Parlement (Bucarest)

### Moyen-Orient et monde musulman (4)
- Dôme du Rocher
- Masjid al-Haram
- Krak des Chevaliers
- Mosquée Hassan-II

### Asie (7)
- Borobudur
- Temple d'Or d'Amritsar
- Pagode Shwedagon
- Grand Palais de Bangkok
- Bouddha de Leshan
- Petronas Towers
- Taipei 101

### Amériques (5)
- Maison-Blanche
- Chrysler Building
- Lincoln Memorial
- Hollywood Sign
- Capitole des États-Unis

### Afrique (1)
- Églises de Lalibela

### Océanie (1)
- Harbour Bridge

**Total collection A : 38 + 37 = 75 cartes**

## 4.5 Raretés à forcer

| Carte | Rareté actuelle | Rareté forcée |
|---|---|---|
| Mont Rushmore | epique | rare |
| Sphinx de Gizeh | (nouvelle) | legendaire |
| Arc de Triomphe | (nouvelle) | epique |
| Pompéi | (nouvelle) | epique |
| Mur de Berlin | (nouvelle) | epique |

---

# 5. CONSTELLATIONS

**Slug :** `constellations`
**État actuel :** 85 cartes sur les 88 constellations officielles de l'UAI.
**Décision :** complétion simple.

## 5.1 Ajouts (3)
- Oiseau de paradis *(Apus)*
- Règle *(Norma)*
- Flèche *(Sagitta)*

Aucune suppression, aucune modification par ailleurs.

---

# Récapitulatif du lot 1

| Collection | Avant | Après | Action |
|---|---|---|---|
| Corps célestes | 49 | ~97 | +48, 5 renommages |
| Dieux et figures mythologiques grecques | 38 | ~79 | +41, 1 correction de page |
| Grands dirigeants | 67 | — | scindée, 2 suppressions, 1 correction de page |
| → Souverains et conquérants | — | 90 | nouvelle collection |
| → Dirigeants de l'ère contemporaine | — | 56 | nouvelle collection |
| Monuments emblématiques | 50 | — | scindée, 1 suppression |
| → Monuments et architecture | — | 75 | slug conservé |
| → Sites antiques et archéologiques | — | 39 | nouvelle collection |
| Constellations | 85 | 88 | +3 |

**Collections validées sans modification :** Merveilles du monde · Pilotes F1 champions du monde · Éléments chimiques

**Lot 2 (à traiter) :** Dynasties et empires · Grandes batailles · Grandes guerres · Dinosaures célèbres · Grands explorateurs


---
---

# LOT 2

**Version :** v2 — ajout du lot 2 (empires, batailles, guerres, dinosaures, explorateurs)

---

# 6. DYNASTIES ET EMPIRES → SCISSION EN 2 COLLECTIONS

**État actuel :** `dynasties-et-empires-historiques`, 42 cartes
**Problème :** la collection mélange deux objets de nature différente — des entités politiques territoriales (empires, civilisations) et des familles régnantes (dynasties, maisons).

- Collection A : **Empires et civilisations** — slug `empires-et-civilisations`
- Collection B : **Dynasties et maisons régnantes** — slug `dynasties-regnantes`

## 6.1 Répartition des cartes existantes

### → Empires et civilisations (33 cartes)
Empire romain · Empire byzantin · Empire ottoman · Empire perse achéménide · Empire parthe · Empire sassanide · Empire mongol · Empire moghol · Empire maurya · Empire Gupta · Empire aztèque · Empire inca · Civilisation maya · Ancien Empire égyptien · Moyen Empire égyptien · Nouvel Empire égyptien · Empire assyrien · Empire babylonien · Empire hittite · Royaume de Koush · Empire du Mali · Empire songhaï · Empire du Ghana · Empire zoulou · Empire d'Aksoum · Empire khmer · Empire britannique · Empire espagnol · Empire portugais · Empire colonial français · Empire russe · Saint-Empire romain germanique · Empire austro-hongrois

### → Dynasties et maisons régnantes (9 cartes)
Dynastie Qin · Dynastie Han · Dynastie Tang · Dynastie Song · Dynastie Ming · Dynastie Qing · Shogunat Tokugawa · Califat omeyyade · Califat abbasside

## 6.2 Ajouts — Empires et civilisations (27 cartes)

### Antiquité proche-orientale (5)
- Sumer
- Empire d'Akkad
- Empire mède
- Civilisation de l'Indus
- Carthage

### Monde égéen et hellénistique (4)
- Civilisation minoenne
- Civilisation mycénienne
- Empire d'Alexandre le Grand
- Empire séleucide

### Rome (1)
- République romaine

### Europe médiévale et moderne (5)
- Empire carolingien *(alors que Charlemagne est déjà une carte dirigeant)*
- Rus' de Kiev
- Empire allemand
- Empire colonial néerlandais
- Union soviétique

### Monde musulman (4)
- Califat de Cordoue
- Empire almoravide
- Empire almohade
- Empire safavide

### Asie (4)
- Empire timouride
- Sultanat de Delhi
- Empire japonais
- Empire chola

### Afrique (4)
- Empire éthiopien
- Empire ashanti
- Royaume du Bénin
- Empire du Kanem-Bornou

## 6.3 Ajouts — Dynasties et maisons régnantes (29 cartes)

### Chine, Corée, Japon (7)
- Dynastie Shang
- Dynastie Zhou
- Dynastie Sui
- Dynastie Yuan *(alors que Kubilai Khan est déjà une carte dirigeant)*
- Dynastie Joseon
- Shogunat Kamakura
- Shogunat Ashikaga

### Monde musulman et Méditerranée antique (4)
- Lagides *(alors que Cléopâtre est déjà une carte dirigeant)*
- Dynastie fatimide
- Dynastie ayyoubide
- Mamelouks

### France (5)
- Mérovingiens
- Carolingiens
- Capétiens
- Maison de Valois
- Maison de Bourbon

### Îles Britanniques (4)
- Plantagenêt
- Maison de Tudor
- Maison Stuart
- Maison de Windsor

### Europe continentale (9)
- Maison de Habsbourg
- Hohenstaufen
- Hohenzollern
- Maison de Savoie
- Maison d'Orange-Nassau
- Médicis
- Romanov
- Dynastie Piast
- Jagellons

**Totaux : A = 60 cartes · B = 38 cartes**

## 6.4 Raretés à forcer

| Carte | Collection | Rareté forcée |
|---|---|---|
| Union soviétique | A | legendaire |
| Empire d'Alexandre le Grand | A | epique |
| Carthage | A | epique |
| Maison de Habsbourg | B | epique |
| Médicis | B | epique |

---

# 7. GRANDES BATAILLES HISTORIQUES

**Slug :** `grandes-batailles-historiques`
**État actuel :** 44 cartes
**Décision :** pas de scission, extension massive.
**Cible :** ~87 cartes

## 7.1 Suppressions
Aucune.

## 7.2 Ajouts (43 cartes)

### Antiquité (9)
- Bataille de Qadesh *(alors que Ramsès II est une carte dirigeant)*
- Bataille de Mégiddo
- Bataille de Platées
- Bataille d'Issos
- Bataille du lac Trasimène
- Bataille de Pharsale
- Siège d'Alésia *(alors que Vercingétorix est une carte dirigeant)*
- Bataille de Philippes
- Bataille du pont Milvius

### Moyen Âge (5)
- Bataille de Roncevaux
- Bataille de Bouvines
- Bataille de Kosovo (1389)
- Bataille de Grunwald
- Siège d'Orléans

### Époque moderne (6)
- Bataille de Marignan
- Bataille de Pavie
- Bataille de Mohács
- Siège de Vienne (1683)
- Bataille de Blenheim
- Bataille des plaines d'Abraham

### Épopée napoléonienne (5)
- Bataille des Pyramides
- Bataille d'Iéna
- Bataille de la Moskova
- Bataille de Leipzig
- Bataille de Wagram

### XIXe siècle (3)
- Bataille de Fort Alamo
- Bataille de Little Bighorn
- Bataille de Tsushima

### Première Guerre mondiale (4)
- Bataille des Dardanelles
- Bataille de Tannenberg
- Deuxième bataille d'Ypres
- Bataille du Chemin des Dames

### Seconde Guerre mondiale (9)
- Attaque de Pearl Harbor
- Bataille d'Angleterre
- Seconde bataille d'El-Alamein
- Bataille de Koursk
- Siège de Léningrad
- Campagne de Guadalcanal
- Bataille du Monte Cassino
- Bataille d'Iwo Jima
- Bataille de Berlin

### Conflits contemporains (2)
- Bataille de la baie des Cochons
- Bataille de Mogadiscio

## 7.3 Raretés à forcer

| Carte | Rareté forcée |
|---|---|
| Attaque de Pearl Harbor | legendaire |
| Siège d'Alésia | epique |
| Bataille d'Angleterre | epique |
| Bataille de Koursk | epique |
| Bataille de Little Bighorn | rare |

---

# 8. GRANDES GUERRES

**Slug :** `grandes-guerres`
**État actuel :** 35 cartes
**Cible :** ~59 cartes

## 8.1 Incohérences à corriger en priorité
Deux conflits sont représentés par une bataille mais n'existent pas comme guerre :
- **Guerre de Crimée** — alors que le siège de Sébastopol est une carte bataille.
- **Guerre d'Indochine** — alors que Diên Biên Phu est une carte bataille.

## 8.2 Ajouts (24 cartes)

### Médiéval et moderne (4)
- Reconquista
- Guerres d'Italie
- Guerre de Succession d'Autriche
- Guerre de Vendée

### XIXe siècle (7)
- Guerre d'indépendance grecque
- Guerre de Crimée
- Guerres de l'opium
- Révolte des Taiping
- Unification italienne
- Guerre hispano-américaine
- Révolte des Boxers

### Première moitié du XXe siècle (2)
- Guerres balkaniques
- Guerre d'Indochine

### Seconde moitié du XXe siècle (6)
- Guerre des Six Jours
- Guerre du Biafra
- Guerre du Liban
- Guerre Iran-Irak
- Guerres de Yougoslavie
- Génocide des Tutsi au Rwanda

### XXIe siècle (5)
- Deuxième guerre du Congo
- Guerre d'Afghanistan (2001-2021)
- Guerre civile syrienne
- Guerre civile yéménite
- Guerre russo-ukrainienne

## 8.3 Raretés à forcer

| Carte | Rareté forcée |
|---|---|
| Guerre russo-ukrainienne | epique |
| Guerres de Yougoslavie | rare |
| Révolte des Taiping | rare |

---

# 9. DINOSAURES CÉLÈBRES + NOUVELLE COLLECTION

**Slug :** `dinosaures-celebres`
**État actuel :** 49 cartes, numéro 35 manquant dans la séquence.
**Décision :** épuration + extension, et création d'une collection sœur pour tout ce qui n'est pas un dinosaure au sens strict.

## 9.1 Suppressions (4)
- **Nanotyrannus** — taxon contesté, considéré aujourd'hui comme un jeune *Tyrannosaurus*.
- **Segnosaurus** — notoriété quasi nulle, redondant avec Therizinosaurus.
- **Ouranosaurus** — notoriété quasi nulle, redondant avec Iguanodon.
- **Nodosaurus** — notoriété quasi nulle, redondant avec Ankylosaurus.

## 9.2 Renumérotation
Renuméroter de 1 à N (le trou du n°35 disparaît).

## 9.3 Ajouts — Dinosaures célèbres (17 cartes)
- Megalosaurus *(premier dinosaure jamais décrit scientifiquement)*
- Utahraptor
- Carcharodontosaurus
- Brontosaurus
- Tarbosaurus
- Albertosaurus
- Troodon
- Deinocheirus
- Psittacosaurus
- Cryolophosaurus
- Mamenchisaurus
- Patagotitan
- Pentaceratops
- Euoplocephalus
- Hadrosaurus
- Ornithomimus
- Majungasaurus

**Total : 49 − 4 + 17 = 62 cartes**

## 9.4 NOUVELLE COLLECTION — Créatures préhistoriques

**Slug :** `creatures-prehistoriques`
**Description :** les grandes créatures disparues qui ne sont pas des dinosaures — ptérosaures, reptiles marins, synapsides, mégafaune.
**Total : 40 cartes**

### Ptérosaures (5)
- Pterodactylus
- Pteranodon
- Quetzalcoatlus
- Rhamphorhynchus
- Dimorphodon

### Reptiles marins (7)
- Mosasaurus
- Plesiosaurus
- Elasmosaurus
- Ichthyosaurus
- Liopleurodon
- Kronosaurus
- Shonisaurus

### Reptiles terrestres non-dinosauriens (3)
- Titanoboa
- Sarcosuchus
- Deinosuchus

### Synapsides et proto-mammifères (3)
- Dimetrodon
- Lystrosaurus
- Gorgonops

### Mégafaune mammifère (11)
- Mammouth laineux
- Mastodonte
- Smilodon
- Megatherium
- Glyptodon
- Rhinocéros laineux
- Ours des cavernes
- Lion des cavernes
- Megaloceros
- Paraceratherium
- Andrewsarchus

### Poissons et invertébrés géants (7)
- Mégalodon
- Dunkleosteus
- Helicoprion
- Arthropleura
- Meganeura
- Anomalocaris
- Trilobite

### Oiseaux disparus (4)
- Gastornis
- Phorusrhacos
- Moa
- Aepyornis

### Raretés à forcer
| Carte | Rareté forcée |
|---|---|
| Mégalodon | legendaire |
| Mammouth laineux | epique |
| Smilodon | epique |
| Pteranodon | epique |
| Quetzalcoatlus | rare |

---

# 10. GRANDS EXPLORATEURS → SCISSION EN 2 COLLECTIONS

**État actuel :** `grands-explorateurs`, 50 cartes

- Collection A : **Grands explorateurs** — slug `grands-explorateurs` (conservé) — découverte terrestre et maritime
- Collection B : **Pionniers de l'extrême** — slug `pionniers-de-lextreme` — pôles, sommets, abysses, stratosphère, espace

## 10.1 Répartition des cartes existantes

### → Pionniers de l'extrême (12 cartes)
Roald Amundsen · Robert Falcon Scott · Ernest Shackleton · Fridtjof Nansen · Edmund Hillary · Tenzing Norgay · Youri Gagarine · Neil Armstrong · Buzz Aldrin · Auguste Piccard · Jacques-Yves Cousteau · Thor Heyerdahl

### → Grands explorateurs (38 cartes)
Toutes les autres cartes existantes.

## 10.2 Ajouts — Grands explorateurs (23 cartes)

### Antiquité et Moyen Âge (4)
- Pythéas
- Hannon le Navigateur
- Erik le Rouge *(alors que Leif Erikson est déjà une carte)*
- Ahmad ibn Fadlan

### Grandes découvertes (6)
- Juan Sebastián Elcano *(c'est lui qui a achevé le premier tour du monde, Magellan étant mort en route)*
- Giovanni da Verrazzano
- Diogo Cão
- Francisco de Orellana
- Álvar Núñez Cabeza de Vaca
- Abel Tasman

### Pacifique et XVIIIe siècle (4)
- Willem Janszoon
- Louis Antoine de Bougainville
- Jeanne Baret *(première femme à faire le tour du monde)*
- Jules Dumont d'Urville

### Afrique et Asie XIXe-XXe (5)
- René Caillié
- Heinrich Barth
- Pierre Savorgnan de Brazza
- Alexandra David-Néel
- Isabelle Eberhardt

### Aventuriers et archéologues (4)
- Ella Maillart
- Percy Fawcett
- Hiram Bingham
- Howard Carter

**Total : 38 + 23 = 61 cartes**

## 10.3 Ajouts — Pionniers de l'extrême (23 cartes)

### La famille Piccard (4)
> Auguste Piccard est déjà présent. Ajouter les quatre autres membres notables de la lignée.
- Jean-Félix Piccard *(frère jumeau d'Auguste, aéronaute stratosphérique)*
- Jeannette Piccard *(épouse de Jean-Félix, première femme à atteindre la stratosphère, 1934)*
- Jacques Piccard *(fils d'Auguste, descente dans la fosse des Mariannes à bord du Trieste, 1960)*
- Bertrand Piccard *(fils de Jacques, premier tour du monde en ballon puis Solar Impulse)*

### Abysses (4)
- Don Walsh
- James Cameron
- Sylvia Earle
- Jean-Louis Étienne

### Sommets (4)
- George Mallory
- Maurice Herzog
- Reinhold Messner
- Junko Tabei

### Pôles (5)
- Robert Peary
- Matthew Henson
- Douglas Mawson
- Jean-Baptiste Charcot
- Paul-Émile Victor

### Espace (3)
- Valentina Terechkova
- Alexeï Leonov
- Michael Collins

### Aventure extrême contemporaine (3)
- Félix Baumgartner
- Ranulph Fiennes
- Mike Horn

**Total : 12 + 23 = 35 cartes**

## 10.4 Raretés à forcer

| Carte | Collection | Rareté forcée |
|---|---|---|
| Jacques Piccard | B | rare |
| Bertrand Piccard | B | rare |
| Reinhold Messner | B | epique |
| Félix Baumgartner | B | epique |
| Valentina Terechkova | B | rare |
| Juan Sebastián Elcano | A | rare |

---

# Récapitulatif du lot 2

| Collection | Avant | Après | Action |
|---|---|---|---|
| Dynasties et empires | 42 | — | scindée |
| → Empires et civilisations | — | 60 | nouvelle collection |
| → Dynasties et maisons régnantes | — | 38 | nouvelle collection |
| Grandes batailles historiques | 44 | 87 | +43 |
| Grandes guerres | 35 | 59 | +24 |
| Dinosaures célèbres | 49 | 62 | −4, +17 |
| Créatures préhistoriques | — | 40 | **nouvelle collection** |
| Grands explorateurs | 50 | 61 | scindée, +23 |
| Pionniers de l'extrême | — | 35 | nouvelle collection |

**Lot 3 (à traiter) :** Auteurs célèbres · Scientifiques célèbres · Grands peintres · Tableaux célèbres


---
---

# LOT 3

**Version :** v3 — ajout du lot 3 (auteurs, scientifiques, peintres, tableaux)

---

## Ajout aux consignes générales

**7. Règle de cohérence croisée peintre ↔ tableau.** Toute carte de la collection *Tableaux célèbres* implique la présence de son auteur dans *Grands peintres*. Vérifier cette contrainte après implémentation et signaler tout tableau orphelin.

**8. Cartes doublées entre collections.** Certaines personnalités légitimes dans deux collections différentes sont volontairement dupliquées. Dans ce cas, le champ `nom` **doit** porter le domaine entre parenthèses dans les deux collections, et les deux cartes pointent vers la même page Wikipédia. Liste exhaustive des doublons autorisés :

| Personne | Carte 1 | Carte 2 |
|---|---|---|
| Antoine de Saint-Exupéry | `Antoine de Saint-Exupéry (auteur)` — Auteurs modernes | `Antoine de Saint-Exupéry (aviateur)` — Aviateurs célèbres |
| Léonard de Vinci | `Léonard de Vinci (peintre)` — Grands peintres | `Léonard de Vinci (inventeur)` — Inventeurs et ingénieurs |

> Note : la carte « Léonard de Vinci » actuellement dans *Scientifiques célèbres* est **déplacée** vers *Inventeurs et ingénieurs* et renommée, elle n'est pas dupliquée une troisième fois.

---

## Correction au lot 2 — chevauchement Aviateurs / Pionniers de l'extrême

La collection `aviateurs-celebres` contient six cartes qui ne relèvent pas de l'aviation mais du vol spatial ou du saut extrême. Elles doivent être **déplacées** vers *Pionniers de l'extrême* et non dupliquées :

**Valentina Terechkova · Michael Collins · Sally Ride · Eileen Collins · Chris Hadfield · Felix Baumgartner**

Ces six cartes remplacent donc les entrées correspondantes de la section 10.3 (qui listait Terechkova, Michael Collins et Baumgartner comme des ajouts : ce sont en réalité des transferts). *Pionniers de l'extrême* passe ainsi à **38 cartes** et *Aviateurs célèbres* à **31 cartes** avant traitement du lot 4.

---

# 11. AUTEURS CÉLÈBRES → SCISSION EN 2 COLLECTIONS

**État actuel :** `auteurs-celebres`, 140 cartes, numéro 72 manquant.

- Collection A : **Auteurs classiques** — slug `auteurs-classiques` — Antiquité → fin XIXe siècle
- Collection B : **Auteurs modernes et contemporains** — slug `auteurs-modernes` — XXe et XXIe siècles

**Critère de répartition :** la période de l'œuvre principale, pas la date de naissance.

## 11.1 Répartition des cartes existantes

### → Auteurs classiques (64 cartes)
Homère · Sophocle · Euripide · Virgile · Ovide · Dante Alighieri · Geoffrey Chaucer · François Rabelais · Michel de Montaigne · William Shakespeare · Miguel de Cervantes · Molière · Jean Racine · John Milton · Jonathan Swift · Voltaire · Jean-Jacques Rousseau · Denis Diderot · Johann Wolfgang von Goethe · Friedrich Schiller · Jane Austen · Walter Scott · Alexandre Pouchkine · Victor Hugo · Alexandre Dumas · Honoré de Balzac · Stendhal · Charles Dickens · Charlotte Brontë · Emily Brontë · Nathaniel Hawthorne · Edgar Allan Poe · Herman Melville · Nikolai Gogol · Ivan Tourgueniev · Fiodor Dostoïevski · Léon Tolstoï · Gustave Flaubert · Émile Zola · Guy de Maupassant · Lewis Carroll · Mark Twain · Henry James · Anton Tchekhov · Thomas Hardy · Oscar Wilde · Rudyard Kipling · Jules Verne · H.G. Wells · Mary Shelley · Bram Stoker · Emily Dickinson · Walt Whitman · Charles Baudelaire · Arthur Rimbaud · Paul Verlaine · Stéphane Mallarmé · George Sand · Confucius · Sun Tzu · Cao Xueqin · Ferdowsi · Rûmî · Omar Khayyam

### → Auteurs modernes et contemporains (76 cartes)
Toutes les autres cartes existantes.

## 11.2 Ajouts — Auteurs classiques (50 cartes)

### Antiquité gréco-latine (10)
- Eschyle *(le troisième grand tragique, absent alors que Sophocle et Euripide sont présents)*
- Aristophane
- Hésiode
- Sappho
- Ésope
- Hérodote
- Thucydide
- Cicéron
- Sénèque
- Horace

### Moyen Âge et Renaissance (10)
- Murasaki Shikibu *(autrice du Dit du Genji, souvent tenu pour le premier roman de l'histoire)*
- Chrétien de Troyes
- Pétrarque
- Boccace
- Érasme
- Luís de Camões
- Lope de Vega
- Calderón de la Barca
- John Donne
- Matsuo Bashō

### XVIIe et XVIIIe siècles (10)
- Pierre Corneille
- Jean de La Fontaine
- Charles Perrault
- Madame de La Fayette
- Beaumarchais
- Choderlos de Laclos
- Marquis de Sade
- Daniel Defoe
- Henry Fielding
- Laurence Sterne

### XIXe siècle (20)
- Chateaubriand
- Alphonse de Lamartine
- Alfred de Musset
- Alfred de Vigny
- Théophile Gautier
- Prosper Mérimée
- Lord Byron
- John Keats
- Percy Bysshe Shelley
- William Wordsworth
- George Eliot
- Anne Brontë
- Heinrich Heine
- E.T.A. Hoffmann
- Mikhaïl Lermontov
- Alessandro Manzoni
- Machado de Assis
- Natsume Sōseki
- Joseph Conrad
- Jack London

**Total : 64 + 50 = 114 cartes**

## 11.3 Ajouts — Auteurs modernes et contemporains (67 cartes)

### Littérature française (21)
- Antoine de Saint-Exupéry (auteur) *(carte doublée, voir consigne 8)*
- André Gide
- Louis-Ferdinand Céline
- André Malraux
- François Mauriac
- Jean Giono
- Jean Cocteau
- Samuel Beckett
- Eugène Ionesco
- Jean Genet
- Nathalie Sarraute
- Alain Robbe-Grillet
- Michel Tournier
- J.M.G. Le Clézio
- Patrick Modiano
- Annie Ernaux
- Louis Aragon
- Paul Éluard
- Jacques Prévert
- Georges Simenon
- Marcel Pagnol

### Littérature russe et soviétique (6)
- Mikhaïl Boulgakov
- Alexandre Soljenitsyne
- Boris Pasternak
- Maxime Gorki
- Vladimir Maïakovski
- Anna Akhmatova

### Littérature germanophone (6)
- Bertolt Brecht
- Stefan Zweig
- Günter Grass
- Erich Maria Remarque
- Robert Musil
- Paul Celan

### Littérature anglophone (16)
- J.D. Salinger
- Harper Lee
- Jack Kerouac
- Cormac McCarthy
- Philip Roth
- Saul Bellow
- Truman Capote
- Tennessee Williams
- Arthur Miller
- Eugene O'Neill
- James Baldwin
- Sylvia Plath
- Robert Frost
- Langston Hughes
- Graham Greene
- E.M. Forster

### Littératures ibérique et latino-américaine (7)
- Fernando Pessoa
- José Saramago
- Mario Vargas Llosa
- Juan Rulfo
- Roberto Bolaño
- Jorge Amado
- Miguel de Unamuno

### Littérature italienne (3)
- Luigi Pirandello
- Primo Levi
- Alberto Moravia

### Reste du monde (8)
- Orhan Pamuk
- Ismail Kadaré
- Yasunari Kawabata
- Liu Cixin
- Han Kang
- Amos Oz
- Chimamanda Ngozi Adichie
- Svetlana Alexievitch

**Total : 76 + 67 = 143 cartes**

## 11.4 Raretés à forcer

| Carte | Collection | Rareté forcée |
|---|---|---|
| Eschyle | A | rare |
| Murasaki Shikibu | A | rare |
| Antoine de Saint-Exupéry (auteur) | B | mythique |
| Samuel Beckett | B | epique |
| Annie Ernaux | B | rare |

---

# 12. SCIENTIFIQUES CÉLÈBRES → SCISSION EN 2 COLLECTIONS

**État actuel :** `scientifiques-celebres`, 115 cartes, numéros 56, 57, 84, 85, 86 manquants.

- Collection A : **Scientifiques célèbres** — slug `scientifiques-celebres` (conservé)
- Collection B : **Inventeurs et ingénieurs** — slug `inventeurs-et-ingenieurs`

Cette scission crée une symétrie avec la collection existante *Inventions importantes* : les objets d'un côté, leurs auteurs de l'autre.

## 12.1 Cartes existantes transférées vers Inventeurs et ingénieurs (17)
Alfred Nobel · Nikola Tesla · Thomas Edison · Alexander Graham Bell · Guglielmo Marconi · Karl Benz · Rudolf Diesel · Henry Ford · Nikolaus Otto · Charles Babbage · Gustave Eiffel · Louis Braille · Hedy Lamarr · George Washington Carver · Wernher von Braun · Tim Berners-Lee · Margaret Hamilton

La carte **Léonard de Vinci** est également transférée et renommée **Léonard de Vinci (inventeur)**.

Toutes les autres cartes restent dans *Scientifiques célèbres* (98 cartes).

## 12.2 Ajouts — Scientifiques célèbres (63 cartes)

### Mathématiques — la discipline la plus sous-représentée (16)
- Fibonacci
- Pierre de Fermat
- Leonhard Euler
- Carl Friedrich Gauss
- Pierre-Simon de Laplace
- Joseph-Louis Lagrange
- Joseph Fourier
- Évariste Galois
- Bernhard Riemann
- Georg Cantor
- Henri Poincaré
- David Hilbert
- Kurt Gödel
- John Forbes Nash
- Alexandre Grothendieck
- Grigori Perelman

### Astronomie et cosmologie (9)
- Tycho Brahe
- Christiaan Huygens
- Edmond Halley
- William Herschel
- Caroline Herschel
- Georges Lemaître *(père de la théorie du Big Bang)*
- Arthur Eddington
- Henrietta Leavitt
- Fred Hoyle

### Physique et chimie (16)
- Robert Boyle
- Émilie du Châtelet
- John Dalton
- Amedeo Avogadro
- James Prescott Joule
- Lord Kelvin
- Ludwig Boltzmann
- Heinrich Hertz
- August Kekulé
- Svante Arrhenius
- Fritz Haber
- Louis de Broglie
- Wolfgang Pauli
- Max Born
- Murray Gell-Mann
- Andreï Sakharov

### Sciences du vivant et médecine (14)
- André Vésale
- Ambroise Paré
- William Harvey
- Jean-Baptiste de Lamarck
- Georges Cuvier
- Alfred Russel Wallace
- Ignace Philippe Semmelweis
- Paul Ehrlich
- Jonas Salk
- Frederick Banting
- Frederick Sanger
- Lynn Margulis
- Richard Dawkins
- Edward Osborne Wilson

### Sciences de la Terre (4)
- Alfred Wegener *(dérive des continents)*
- James Hutton
- Charles Lyell
- Marie Tharp

### Informatique théorique (4)
- Claude Shannon *(théorie de l'information)*
- Norbert Wiener
- Donald Knuth
- Vint Cerf

**Total : 98 + 63 = 161 cartes**

## 12.3 Ajouts — Inventeurs et ingénieurs (31 cartes)

### Avant la révolution industrielle (3)
- Léonard de Vinci (inventeur) *(transféré et renommé, voir §12.1)*
- Johannes Gutenberg *(absent de toutes les collections aujourd'hui)*
- Denis Papin

### Révolution industrielle (8)
- Thomas Newcomen
- James Watt
- Frères Montgolfier
- Richard Trevithick
- George Stephenson
- Robert Fulton
- Isambard Kingdom Brunel
- Ferdinand de Lesseps

### XIXe siècle (7)
- Samuel Morse
- Nicéphore Niépce
- Louis Daguerre
- Elisha Otis
- Isaac Singer
- Ferdinand von Zeppelin
- Frères Lumière

### XXe siècle (7)
- Willis Carrier
- John Logie Baird
- Vladimir Zvorykine
- Frank Whittle
- Sergueï Korolev
- Percy Spencer
- Jack Kilby

### Informatique et électronique (6)
- Robert Noyce
- Gordon Moore
- Douglas Engelbart
- Steve Wozniak
- Linus Torvalds
- Shuji Nakamura

**Total : 18 + 31 = 49 cartes**

## 12.4 Raretés à forcer

| Carte | Collection | Rareté forcée |
|---|---|---|
| Leonhard Euler | A | epique |
| Carl Friedrich Gauss | A | epique |
| Georges Lemaître | A | rare |
| Claude Shannon | A | rare |
| Johannes Gutenberg | B | legendaire |
| James Watt | B | epique |
| Frères Lumière | B | epique |

---

# 13. GRANDS PEINTRES

**Slug :** `grands-peintres`
**État actuel :** 69 cartes, numéros 3 et 52 manquants.
**Cible :** ~114 cartes

## 13.1 Correction prioritaire — peintres orphelins
Quatre peintres ont une œuvre dans *Tableaux célèbres* mais aucune carte ici. À ajouter en priorité :
- **Léonard de Vinci (peintre)** — *La Joconde*, *La Cène*
- **Jan van Eyck** — *Les Époux Arnolfini*
- **Théodore Géricault** — *Le Radeau de la Méduse*
- **Grant Wood** — *American Gothic*

## 13.2 Ajouts (45 cartes)

### Renaissance et maniérisme (8)
- Léonard de Vinci (peintre)
- Jan van Eyck
- Albrecht Dürer
- Hans Holbein le Jeune
- Fra Angelico
- Masaccio
- Piero della Francesca
- Andrea Mantegna

### Renaissance vénitienne et baroque (5)
- Giorgione
- Le Tintoret
- Véronèse
- Georges de La Tour
- Jean Siméon Chardin

### XIXe siècle (11)
- Théodore Géricault
- Jean-Auguste-Dominique Ingres
- Camille Corot
- Jean-François Millet
- Alfred Sisley
- Gustave Caillebotte
- Mary Cassatt
- Paul Signac
- Henri Rousseau
- Odilon Redon
- James Abbott McNeill Whistler

### Peinture nationale et académique (5)
- John Singer Sargent
- Winslow Homer
- Ilia Répine
- Ivan Aïvazovski
- Joaquín Sorolla

### Avant-gardes du XXe siècle (9)
- Kazimir Malevitch
- Giorgio de Chirico
- Max Ernst
- Otto Dix
- Fernand Léger
- Robert Delaunay
- Sonia Delaunay
- Hilma af Klint
- Alphonse Mucha

### Après-guerre et contemporain (7)
- Grant Wood
- Nicolas de Staël
- Pierre Soulages
- Yves Klein
- Roy Lichtenstein
- Willem de Kooning
- Jean Dubuffet

### Scène internationale contemporaine et Asie (5)
- Gerhard Richter
- Anselm Kiefer
- Yayoi Kusama
- Takashi Murakami
- Zao Wou-Ki

**Total : 69 + 45 = 114 cartes**

## 13.3 Raretés à forcer

| Carte | Rareté forcée |
|---|---|
| Léonard de Vinci (peintre) | mythique |
| Jan van Eyck | epique |
| Albrecht Dürer | epique |
| Théodore Géricault | rare |
| Kazimir Malevitch | rare |

---

# 14. TABLEAUX CÉLÈBRES

**Slug :** `tableaux-celebres`
**État actuel :** 55 cartes, numéros 13, 50, 54 et 58 manquants.
**Cible :** ~110 cartes

## 14.1 Corrections
- La carte **« Autoportrait »** pointe vers *Autoportrait (Rembrandt, Vienne)*. La renommer **« Autoportrait de Rembrandt »** pour lever l'ambiguïté.
- Renumérotation complète (4 trous).

## 14.2 Ajouts (55 cartes)

### Primitifs, Renaissance, maniérisme (9)
- L'Agneau mystique *(van Eyck)*
- Le Printemps *(Botticelli)*
- La Dame à l'hermine *(Léonard de Vinci)*
- La Vierge aux rochers *(Léonard de Vinci)*
- Melencolia I *(Dürer)*
- Les Ambassadeurs *(Holbein)*
- La Tempête *(Giorgione)*
- Les Noces de Cana *(Véronèse)*
- Le Christ mort *(Mantegna)*

### Baroque et âge d'or (7)
- La Leçon d'anatomie du docteur Tulp *(Rembrandt)*
- La Vénus au miroir *(Vélasquez)*
- La Reddition de Breda *(Vélasquez)*
- Le Tricheur à l'as de carreau *(Georges de La Tour)*
- La Descente de croix *(Rubens)*
- Les Trois Grâces *(Rubens)*
- L'Enlèvement des Sabines *(Poussin)*

### Néoclassicisme et romantisme (8)
- Le Serment des Horaces *(David)*
- La Mort de Marat *(David)*
- Le Sacre de Napoléon *(David)*
- La Grande Odalisque *(Ingres)*
- Le Bain turc *(Ingres)*
- Le Voyageur contemplant une mer de nuages *(Friedrich)*
- Le Cauchemar *(Füssli)*
- Washington traversant le Delaware *(Leutze)*

### Réalisme et académisme (5)
- L'Angélus *(Millet)*
- Des glaneuses *(Millet)*
- Un enterrement à Ornans *(Courbet)*
- Arrangement en gris et noir n°1 *(Whistler)*
- Les Raboteurs de parquet *(Caillebotte)*

### Impressionnisme et postimpressionnisme (10)
- Le Déjeuner des canotiers *(Renoir)*
- Un bar aux Folies Bergère *(Manet)*
- La Classe de danse *(Degas)*
- L'Absinthe *(Degas)*
- La Cathédrale de Rouen *(Monet)*
- Les Joueurs de cartes *(Cézanne)*
- La Montagne Sainte-Victoire *(Cézanne)*
- Les Mangeurs de pommes de terre *(van Gogh)*
- Le Café de nuit *(van Gogh)*
- D'où venons-nous ? Que sommes-nous ? Où allons-nous ? *(Gauguin)*

### Modernité et avant-gardes (9)
- La Danse *(Matisse)*
- Carré noir sur fond blanc *(Malevitch)*
- Nu descendant un escalier n°2 *(Duchamp)*
- La Trahison des images *(Magritte)*
- Golconde *(Magritte)*
- La Femme qui pleure *(Picasso)*
- Les Trois Musiciens *(Picasso)*
- Le Rêve *(Picasso)*
- La Ville qui monte *(Boccioni)*

### Après-guerre et contemporain (7)
- Marilyn Diptych *(Warhol)*
- Whaam! *(Lichtenstein)*
- Drowning Girl *(Lichtenstein)*
- No. 61 (Rust and Blue) *(Rothko)*
- Autoportrait au collier d'épines *(Frida Kahlo)*
- Trois études de figures au pied d'une crucifixion *(Francis Bacon)*
- Un plus grand plongeon *(Hockney)*

**Total : 55 + 55 = 110 cartes**

## 14.3 Raretés à forcer

| Carte | Rareté forcée |
|---|---|
| Le Sacre de Napoléon | epique |
| La Trahison des images | epique |
| Le Voyageur contemplant une mer de nuages | epique |
| L'Agneau mystique | rare |
| Marilyn Diptych | rare |

---

# Récapitulatif du lot 3

| Collection | Avant | Après | Action |
|---|---|---|---|
| Auteurs célèbres | 140 | — | scindée |
| → Auteurs classiques | — | 114 | nouvelle collection |
| → Auteurs modernes et contemporains | — | 143 | nouvelle collection |
| Scientifiques célèbres | 115 | 161 | scindée, +63 |
| → Inventeurs et ingénieurs | — | 49 | **nouvelle collection** |
| Grands peintres | 69 | 114 | +45 |
| Tableaux célèbres | 55 | 110 | +55, 1 renommage |

**Lot 4 (à traiter) :** Inventions importantes · Aviateurs célèbres


---
---

# LOT 4

**Version :** v4 — ajout du lot 4 (inventions, aviateurs)

---

# 15. INVENTIONS IMPORTANTES

**Slug :** `inventions-importantes`
**État actuel :** 68 cartes, numéros 49 et 59 manquants.
**Cible :** ~129 cartes

## 15.1 Corrections de pages Wikipédia — prioritaires
C'est la collection la plus abîmée du jeu.

| N° | Carte | `titrePage` actuel (erroné) | `titrePage` correct |
|---|---|---|---|
| 13 | Télégraphe | `Téléphone` | `Télégraphe électrique` |
| 15 | Téléphone | `Le Téléphone` *(groupe de rock français)* | `Téléphone` |
| 51 | Machine à écrire | `La Machine à écrire` *(pièce de Cocteau)* | `Machine à écrire` |
| 38 | GPS | `GPS (assistant de navigation)` | `Global Positioning System` |
| 69 | Intelligence Artificielle | `Intelligence artificielle générative` | `Intelligence artificielle` |

Régénérer description, image et pageviews pour ces cinq cartes.

## 15.2 Corrections de libellés
- « Péniciline » → **Pénicilline**
- « Ampoule Electrique » → **Ampoule électrique**

## 15.3 Suppressions (2)
- **Tunnel sous la Manche** — ouvrage d'art et non invention. **Transférer** vers *Monuments et architecture* (§4).
- **Machine électrique** — entrée vague ne correspondant à aucune invention identifiable.

## 15.4 Ajouts (63 cartes)

### Préhistoire et Antiquité (10)
- Maîtrise du feu
- Outil de pierre taillée
- Poterie
- Arc (arme)
- Métallurgie du bronze
- Verre
- Monnaie
- Charrue
- Voile (navigation)
- Aqueduc

### Antiquité tardive et Moyen Âge (6)
- Acier
- Horloge mécanique
- Lunettes de vue
- Moulin à eau
- Étrier
- Gouvernail d'étambot

### Époque moderne (6)
- Thermomètre
- Baromètre
- Sextant
- Machine à coudre
- Conserve alimentaire
- Pasteurisation

### Transport et industrie (8)
- Locomotive à vapeur
- Chemin de fer
- Bateau à vapeur
- Sous-marin
- Hélicoptère
- Turboréacteur
- Montgolfière
- Parachute

### Chimie et matériaux (6)
- Dynamite
- Bakélite
- Nylon
- Vulcanisation
- Procédé Haber-Bosch
- Procédé Hall-Héroult

### Énergie (3)
- Réacteur nucléaire
- Bombe atomique
- Réseau électrique

### Médecine (8)
- Antibiotique
- Contraception orale
- Échographie
- Tomodensitométrie
- Défibrillateur
- Transfusion sanguine
- Vaccin à ARN messager
- CRISPR

### Informatique et réseaux (11)
- Microprocesseur
- Disque dur
- Mémoire flash
- Souris (informatique)
- Écran tactile
- Fibre optique
- Wi-Fi
- Courrier électronique
- Moteur de recherche
- Cryptographie asymétrique
- Blockchain

### Hygiène et vie quotidienne (5)
- Toilettes à chasse d'eau
- Réseau d'égouts
- Savon
- Allumette
- Lave-vaisselle

## 15.5 Raretés à forcer

| Carte | Rareté forcée |
|---|---|
| Maîtrise du feu | mythique |
| Monnaie | epique |
| Antibiotique | epique |
| Bombe atomique | epique |
| Microprocesseur | epique |
| Imprimerie | epique *(actuellement rare, disproportionné)* |

---

# 16. AVIATEURS CÉLÈBRES

**Slug :** `aviateurs-celebres`
**État actuel :** 37 cartes, numéros 17, 19, 20 et 36 manquants.
**Après transferts (voir correction lot 2/lot 3) :** 31 cartes
**Cible :** ~67 cartes

## 16.1 Transferts sortants (6)
Vers *Pionniers de l'extrême* : Valentina Terechkova · Michael Collins · Sally Ride · Eileen Collins · Chris Hadfield · Felix Baumgartner

## 16.2 Carte doublée
- **Antoine de Saint-Exupéry** → renommer en `Antoine de Saint-Exupéry (aviateur)`, la carte jumelle étant créée dans *Auteurs modernes et contemporains* (voir consigne 8).

## 16.3 Ajouts (36 cartes)

### Pionniers du vol (6)
- Otto Lilienthal *(le précurseur du vol plané, sans qui les Wright n'auraient pas abouti)*
- Henri Farman
- Gabriel Voisin
- Adolphe Pégoud
- Hubert Latham
- Louis Breguet

### As de guerre (6)
- René Fonck *(l'as des as alliés de 14-18, absent alors que Guynemer et Richthofen sont présents)*
- Eddie Rickenbacker
- Erich Hartmann
- Adolf Galland
- Saburō Sakai
- Pierre Clostermann

### Aéropostale et grands raids (7)
- Henri Guillaumet *(le troisième pilier de l'Aéropostale avec Mermoz et Saint-Exupéry)*
- Didier Daurat
- Pierre-Georges Latécoère
- Dieudonné Costes
- Maurice Bellonte
- Charles Kingsford Smith
- Wiley Post

### Aviatrices (6)
- Raymonde de Laroche *(première femme brevetée pilote au monde, 1910)*
- Hélène Boucher
- Maryse Bastié
- Jacqueline Auriol
- Beryl Markham
- Jean Batten

### Constructeurs et ingénieurs de l'aéronautique (7)
- Marcel Dassault
- Anthony Fokker
- Hugo Junkers
- Andreï Tupolev
- Sergueï Iliouchine
- Donald Douglas
- William Boeing

### Pilotes d'essai et aventuriers (4)
- Bob Hoover
- André Turcat *(premier vol du Concorde)*
- Steve Fossett
- Yves Rossy

## 16.4 Raretés à forcer

| Carte | Rareté actuelle | Rareté forcée |
|---|---|---|
| Wilbur Wright | commune | epique |
| Orville Wright | commune | epique |
| Howard Hughes | legendaire | epique |
| Otto Lilienthal | (nouvelle) | rare |
| Marcel Dassault | (nouvelle) | rare |

---

# Récapitulatif du lot 4

| Collection | Avant | Après | Action |
|---|---|---|---|
| Inventions importantes | 68 | 129 | −2, +63, 5 corrections de page |
| Aviateurs célèbres | 37 | 67 | −6 transferts, +36 |
| Pionniers de l'extrême | 35 | 38 | +3 transferts nets |
| Monuments et architecture | 75 | 76 | +1 (Tunnel sous la Manche) |

**Lot 5 (à traiter) :** Mammifères · Oiseaux · Reptiles et amphibiens · Poissons et vie marine · Insectes · Races de chien


---
---

# LOT 5 — ANIMAUX

**Version :** v5
**Contrainte de volume imposée :** Mammifères ≤ 100 · Oiseaux ≤ 70 · Reptiles et amphibiens ≤ 40 · Poissons et vie marine ≤ 50 · Insectes ≤ 60.
**Conséquence :** pas de scission sur ces collections. Le travail est un **remplacement à volume constant** — on retire les cartes redondantes ou obscures pour faire entrer les espèces incontournables.

---

# 17. MAMMIFÈRES

**Slug :** `mammiferes`
**État actuel :** 105 cartes, numéro 65 manquant.
**Cible :** 100 cartes (−20, +15)

## 17.1 Suppressions (20)
Critère : doublon avec une espèce proche déjà présente, ou notoriété trop faible.

| Carte | Motif |
|---|---|
| Wallaby de Bennett | doublon avec Wallaby |
| Hippopotame nain | doublon avec Hippopotame |
| Rhinocéros de Java | doublon (noir et blanc déjà présents) |
| Zèbre de Grévy | doublon avec Zèbre des plaines |
| Bison européen | doublon avec Bison d'Amérique |
| Hyène rayée | doublon avec Hyène tachetée |
| Loup rouge | notoriété faible |
| Loup à crinière | notoriété faible |
| Chacal | doublon fonctionnel avec Coyote |
| Colobe | notoriété faible |
| Numbat | notoriété faible |
| Rat-taupe nu | notoriété faible |
| Écureuil volant | notoriété faible |
| Civette | notoriété faible |
| Belette | doublon avec Hermine |
| Antilope saïga | notoriété faible |
| Ours à lunettes | notoriété faible |
| Serval | doublon (Caracal et Ocelot conservés) |
| Chat des sables | doublon, et libère la place pour le chat domestique |
| **Roussette** | **résout aussi l'homonyme avec la Roussette des poissons** |

## 17.2 Ajouts (15)

### Mammifères domestiques et familiers — le trou le plus flagrant (9)
- Chat *(l'animal domestique le plus répandu au monde, absent)*
- Vache
- Cochon
- Mouton
- Chèvre
- Cheval *(seul le cheval de Przewalski était présent)*
- Lapin de garenne
- Rat brun
- Souris grise

### Espèces emblématiques manquantes (6)
- Panthère des neiges
- Raton laveur
- Mouffette rayée
- Porc-épic
- Marmotte alpine
- Mandrill

**Total : 105 − 20 + 15 = 100 cartes**

---

# 18. OISEAUX

**Slug :** `oiseaux`
**État actuel :** 71 cartes
**Cible :** 70 cartes (−12, +11)

## 18.1 Corrections de nommage
| Carte | Problème | Action |
|---|---|---|
| Colombe | terme générique, pas une espèce | **supprimer** (voir 18.2) |
| Corbeau | ambigu | renommer **Grand Corbeau**, `titrePage` = `Grand Corbeau` |
| Aigle pêcheur | ambigu | vérifier la page et renommer **Balbuzard pêcheur** ou **Pygargue vocifer** |
| Pigeon voyageur | probable confusion | l'oiseau disparu emblématique est la **Tourte voyageuse** (*Ectopistes migratorius*) ; le pigeon voyageur est une variété domestique. Vérifier `titrePage` et corriger |

## 18.2 Suppressions (12)
Milan noir · Vautour percnoptère · Manchot papou · Oie cendrée · Ara rouge · Aigrette garzette · Corneille noire · Grue cendrée · Colombe · Nandou · Autour des palombes · Chouette hulotte

## 18.3 Ajouts (11)
- Coq domestique *(l'oiseau le plus nombreux de la planète, absent)*
- Bec-en-sabot du Nil
- Harpie féroce
- Gypaète barbu
- Macareux moine
- Calao bicorne
- Paradisier
- Messager sagittaire
- Sterne arctique *(record de migration du règne animal)*
- Rossignol philomèle
- Étourneau sansonnet

**Total : 71 − 12 + 11 = 70 cartes**

---

# 19. REPTILES ET AMPHIBIENS

**Slug :** `reptiles-et-amphibiens`
**État actuel :** 40 cartes, numéros 22, 32, 34, 41 et 42 manquants.
**Cible :** 40 cartes (−11, +11)
**Objectif du remaniement :** les amphibiens passent de 10 à 16 cartes sur 40. Ils étaient réduits à un appendice alors qu'ils constituent la moitié du titre de la collection.

## 19.1 Suppressions (11)
Caïman à lunettes *(doublon Alligator)* · Cobra cracheur *(doublon Cobra royal)* · Vipère heurtante · Caméléon commun *(doublon Caméléon panthère)* · Tortue boîte · Tortue caouanne *(doublon Tortue luth)* · Iguane à queue épineuse · Triton alpestre · Python molure *(doublon Python réticulé)* · Agame barbu · Crapaud buffle

## 19.2 Ajouts (11)

### Amphibiens (6)
- Dendrobate *(la grenouille venimeuse, l'amphibien le plus reconnaissable au monde)*
- Rainette aux yeux rouges
- Grenouille de verre
- Grenouille Goliath *(le plus grand amphibien anoure)*
- Cécilie *(l'ordre des gymnophiones était totalement absent du jeu)*
- Protée anguillard

### Reptiles (5)
- Sphénodon *(seul survivant d'une lignée entière de reptiles)*
- Taïpan du désert *(le serpent le plus venimeux du monde)*
- Vipère du Gabon
- Monstre de Gila
- Tortue verte

**Total : 40 − 11 + 11 = 40 cartes**

---

# 20. POISSONS ET VIE MARINE

**Slug :** `poissons-et-vie-marine`
**État actuel :** 55 cartes
**Cible :** 50 cartes (−11, +6)

## 20.1 Correction de nommage
- **« Poulpe »** → renommer **Pieuvre commune** pour lever l'ambiguïté avec Pieuvre à anneaux bleus.
- **« Roussette »** est conservée ici, l'homonyme mammifère ayant été supprimé (§17.1).

## 20.2 Suppressions (11)
Requin dormeur · Requin-nourrice · Torpille · Baliste · Poisson-ange · Corail corne d'élan · Corail rouge *(doublon Corail cerveau)* · Diable de mer *(doublon Raie manta)* · Langouste *(doublon Homard)* · Crabe royal *(doublon Crabe-araignée géant)* · Truite arc-en-ciel *(doublon Saumon atlantique)*

## 20.3 Ajouts (6)
- Cœlacanthe *(le fossile vivant le plus célèbre de la biologie, absent)*
- Baudroie abyssale
- Requin du Groenland *(le vertébré le plus longévif connu)*
- Requin pèlerin
- Poisson rouge
- Krill

**Total : 55 − 11 + 6 = 50 cartes**

---

# 21. INSECTES

**Slug :** `insectes`
**État actuel :** 56 cartes
**Cible :** 60 cartes (−4, +8)

## 21.1 Suppressions (4)
Cochenille · Chrysope verte · Guêpe des figuiers · Punaise verte

## 21.2 Ajouts (8)
- Drosophile *(l'insecte le plus étudié de l'histoire de la science)*
- Scarabée Hercule
- Fourmi coupe-feuille
- Coléoptère bombardier
- Mante orchidée
- Phasme feuille
- Punaise de lit
- Frelon géant asiatique

**Total : 56 − 4 + 8 = 60 cartes**

---

# 22. RACES DE CHIEN

**Slug :** `races-de-chien`
**État actuel :** 114 cartes, numéros 39, 99 et 114 manquants.
**Cible :** ~130 cartes

## 22.1 Corrections de doublons
| Problème | Action |
|---|---|
| **Papillon** et **Épagneul nain continental** sont la même race | fusionner en une seule carte : **Épagneul nain continental (Papillon)** |
| **Spitz nain** est une variété du **Spitz allemand** | fusionner en une seule carte : **Spitz allemand** |
| **Pitbull** n'est pas une race reconnue par les fédérations canines | renommer **American Pit Bull Terrier** |

## 22.2 Ajouts (20)

### Lévriers (3)
- Greyhound *(absent alors que le Whippet est présent)*
- Saluki
- Barzoï

### Bergers et bouviers (6)
- Welsh Corgi Pembroke
- Bobtail
- Bearded Collie
- Bouvier australien
- Kelpie australien
- Berger des Pyrénées

### Molossoïdes et chiens de garde (3)
- Dogo argentino
- Berger du Caucase
- Dogue du Tibet

### Chiens de chasse et d'eau (5)
- Braque hongrois
- Springer spaniel anglais
- Flat-Coated Retriever
- Griffon Korthals
- Chien d'eau portugais

### Petits chiens (3)
- Chien chinois à crête
- Pinscher nain
- Affenpinscher

**Total : 112 (après fusions) + 20 = 132 cartes**

---

# 23. NOUVELLE COLLECTION — RACES DE CHAT

**Slug :** `races-de-chat`
**Justification :** 114 races de chien et zéro race de chat dans le jeu.
**Total : 45 cartes**

### Races les plus populaires (12)
- Maine coon
- Persan
- Siamois
- Bengal
- Sphynx
- Ragdoll
- British shorthair
- Chartreux
- Norvégien
- Abyssin
- Scottish fold
- Sacré de Birmanie

### Races reconnues classiques (17)
- Bleu russe
- Somali
- Balinais
- Oriental shorthair
- Bombay
- Burmese
- Tonkinois
- Mau égyptien
- Angora turc
- Van turc
- Sibérien
- Ocicat
- American shorthair
- Exotic shorthair
- Himalayen
- Manx
- Korat

### Races à morphologie particulière (9)
- Devon rex
- Cornish rex
- Selkirk rex
- LaPerm
- Munchkin
- American curl
- Highland fold
- Bobtail japonais
- Bobtail des Kouriles

### Races récentes et hybrides (7)
- Savannah
- Chausie
- Peterbald
- Donskoy
- Nebelung
- Ragamuffin
- Snowshoe

---

# Récapitulatif du lot 5

| Collection | Avant | Après | Action |
|---|---|---|---|
| Mammifères | 105 | 100 | −20, +15 |
| Oiseaux | 71 | 70 | −12, +11, 3 corrections de nommage |
| Reptiles et amphibiens | 40 | 40 | −11, +11 |
| Poissons et vie marine | 55 | 50 | −11, +6, 1 renommage |
| Insectes | 56 | 60 | −4, +8 |
| Races de chien | 114 | 132 | 2 fusions, 1 renommage, +20 |
| Races de chat | — | 45 | **nouvelle collection** |

**Lot 6 (à traiter) :** Plus grands joueurs de football · Mythologies du monde


---
---

# LOT 6 — FOOTBALL ET MYTHOLOGIES

**Version :** v6

---

# 24. COUPES DU MONDE FIFA

**Slug :** `coupes-du-monde-fifa`
**État actuel :** 22 cartes, s'arrête à Qatar 2022.

## 24.1 Ajout (1)
- **Coupe du monde 2026** — édition organisée par les États-Unis, le Canada et le Mexique, **remportée par l'Espagne**. Générer la carte depuis la page Wikipédia de l'édition.

**Total : 23 cartes**

---

# 25. PLUS GRANDS JOUEURS DE FOOTBALL → SCISSION EN 2 COLLECTIONS

**État actuel :** `plus-grands-joueurs-de-football`, 147 cartes, **29 numéros manquants** (27, 76, 78, 101, 109, 131-139, 143-144, 149-152, 156-160, 164, 171-175). Renumérotation impérative.

- Collection A : **Légendes du football** — slug `legendes-du-football` — carrière principale avant 1990 — **50 cartes**
- Collection B : **Football, ère moderne** — slug `football-ere-moderne` — carrière principale à partir de 1990 — **100 cartes**

## 25.1 Répartition des cartes existantes vers Légendes (23)
Pelé · Diego Maradona · Johan Cruyff · Franz Beckenbauer · Alfredo Di Stéfano · Ferenc Puskás · Garrincha · Bobby Charlton · Gerd Müller · Michel Platini · Zico · Sócrates · Falcão · Lev Yachine · Raymond Kopa · Just Fontaine · Marco van Basten · Ruud Gullit · Frank Rijkaard · Franco Baresi · Lothar Matthäus · Jürgen Klinsmann · Roger Milla

## 25.2 Ajouts — Légendes du football (27)

### Portugal et Angleterre (7)
- Eusébio
- Stanley Matthews *(tout premier Ballon d'Or de l'histoire, 1956)*
- Bobby Moore
- Gordon Banks
- George Best
- Denis Law
- Jimmy Greaves

### Îles Britanniques, suite (2)
- Kenny Dalglish
- Kevin Keegan *(double Ballon d'Or)*

### Italie (4)
- Dino Zoff
- Giuseppe Meazza
- Gianni Rivera
- Giacinto Facchetti

### Brésil (5)
- Carlos Alberto
- Jairzinho
- Didi
- Nílton Santos
- Rivelino

### Allemagne et Pays-Bas (5)
- Johan Neeskens
- Karl-Heinz Rummenigge
- Uwe Seeler
- Sepp Maier
- Paul Breitner

### Reste du monde (4)
- Oleg Blokhine *(Ballon d'Or 1975)*
- Mario Kempes
- Daniel Passarella
- Larbi Benbarek

**Total collection A : 23 + 27 = 50 cartes**

## 25.3 Football, ère moderne — répartition et coupes
Les 124 cartes restantes basculent dans cette collection, moins les 34 suppressions ci-dessous.

### Suppressions (34)
Kaoru Mitoma · Tim Cahill · Andrés Escobar · Xherdan Shaqiri · Granit Xhaka · Memphis Depay · João Félix · Gavi · Ousmane Dembélé · Nicolas Anelka · Gary Neville · Ashley Cole · John Terry · Emmanuel Petit · Bixente Lizarazu · Youri Djorkaeff · Hugo Lloris · Michael Essien · Hidetoshi Nakata · James Rodríguez · Radamel Falcao · Gonzalo Higuaín · Javier Zanetti · Henrik Larsson · Rio Ferdinand · Frenkie de Jong · Bernardo Silva · Bruno Fernandes · Robin van Persie · Edwin van der Sar · Achraf Hakimi · Fernando Torres · Carles Puyol · Roy Keane

### Ajouts (10)
- Romário *(Ballon d'Or 1994)*
- Gabriel Batistuta
- Andriy Shevchenko *(Ballon d'Or 2004)*
- Jean-Pierre Papin *(Ballon d'Or 1991)*
- Juan Román Riquelme
- Hugo Sánchez
- Clarence Seedorf
- Oliver Kahn
- Xabi Alonso
- Sergio Busquets

**Total collection B : 124 − 34 + 10 = 100 cartes**

---

# 26. MYTHOLOGIES DU MONDE → SCISSION EN 10 COLLECTIONS

**État actuel :** `mythologies-du-monde-hors-grece`, 58 cartes couvrant dix aires culturelles très inégalement.
**Décision :** éclatement en dix collections thématiques, chacune complétée nommément.

## 26.1 Règle de frontière avec *Créatures et légendes*
Toute créature rattachée à un panthéon identifié appartient à sa collection mythologique. *Créatures et légendes* ne conserve que le folklore et les cryptides sans panthéon.

## 26.2 Mythologie nordique — slug `mythologie-nordique` — 35 cartes
**Existantes (12) :** Odin · Thor · Loki · Freyja · Freyr · Baldr · Týr · Heimdall · Frigg · Fenrir · Jörmungandr · Hel
**Ajouts (23) :** Sif · Bragi · Idunn · Njörd · Skadi · Ullr · Vidar · Vali · Forseti · Ymir · Surt · Sleipnir · Huginn et Muninn · Yggdrasil · Valkyrie · Valhalla · Ragnarök · Nornes · Mjöllnir · Sigurd · Fáfnir · Nídhögg · Ratatosk
**Transferts entrants depuis Créatures et légendes :** Troll scandinave

## 26.3 Mythologie égyptienne — slug `mythologie-egyptienne` — 35 cartes
**Existantes (12) :** Rê · Osiris · Isis · Horus · Anubis · Seth · Thot · Hathor · Sekhmet · Bastet · Ptah · Amon
**Ajouts (23) :** Nout · Geb · Shou · Tefnout · Nephthys · Maât · Sobek · Khnoum · Khonsou · Mout · Apophis · Ammit · Bès · Taouret · Nekhbet · Ouadjet · Atoum · Min · Sokar · Hâpy · Serket · Anouket · Benou

## 26.4 Mythologie hindoue — slug `mythologie-hindoue` — 35 cartes
**Existantes (12) :** Brahmā · Vishnu · Shiva · Ganesh · Hanumān · Durga · Kali · Lakshmi · Sarasvati · Indra · Krishna · Rāma
**Ajouts (23) :** Parvati · Kartikeya · Agni · Varuna · Vayu · Surya · Yama · Kubera · Ganga · Nandi · Garuda · Naga · Ravana · Sita · Arjuna · Draupadi · Bhima · Karna · Narasimha · Kurma · Matsya · Vamana · Airavata

## 26.5 Mythologie celtique — slug `mythologie-celtique` — 25 cartes
**Existantes (5) :** Dagda · Morrigan · Lugh · Brigid · Cernunnos
**Ajouts (16) :** Nuada · Ogma · Danu · Boann · Manannán mac Lir · Aengus · Cúchulainn · Fionn mac Cumhaill · Medb · Balor · Epona · Taranis · Teutatès · Belenos · Arawn · Rhiannon
**Transferts entrants depuis Créatures et légendes (4) :** Banshee · Leprechaun · Selkie · Kelpie

## 26.6 Mythologies d'Asie de l'Est — slug `mythologies-asie-est` — 35 cartes
**Existantes (8) :** Amaterasu · Susanoo · Tsukuyomi · Izanagi · Izanami · Inari · Pangu · Nuwa
**Ajouts (23) :** Raijin · Fūjin · Hachiman · Ebisu · Benzaiten · Daikokuten · Kagutsuchi · Ōkuninushi · Ryūjin · Yamata no Orochi · Empereur de Jade · Fuxi · Shennong · Xiwangmu · Chang'e · Sun Wukong · Nezha · Guanyin · Yanluo · Roi-Dragon · Qilin · Fenghuang · Dangun
**Transferts entrants depuis Créatures et légendes (4) :** Kappa · Oni · Tengu · Kitsune

## 26.7 Mythologies mésoaméricaines et andines — slug `mythologies-mesoamericaines` — 30 cartes
**Existantes (5) :** Quetzalcóatl · Huitzilopochtli · Tlaloc · Xochiquetzal · Kukulcan
**Ajouts (25) :** Tezcatlipoca · Xipe Totec · Mictlantecuhtli · Coatlicue · Chalchiuhtlicue · Xolotl · Ehecatl · Coyolxauhqui · Tonatiuh · Itzamna · Ixchel · Chaac · Ah Puch · Hunahpú · Ixbalanqué · Vucub Caquix · Camazotz · Viracocha · Inti · Mama Quilla · Pachamama · Supay · Illapa · Manco Cápac · Ai Apaec

## 26.8 Mythologies du Proche-Orient ancien — slug `mythologies-proche-orient` — 34 cartes
**Existantes : aucune.** Aire culturelle totalement absente du jeu aujourd'hui.

**Mésopotamie (18) :** Marduk · Ishtar · Enki · Enlil · Anu · Tiamat · Ereshkigal · Ninurta · Nergal · Sin · Shamash · Dumuzi · **Gilgamesh** *(transféré depuis Grands dirigeants, voir §3.1)* · Enkidu · Humbaba · Adad · Apsû · Lamashtu
**Perse et zoroastrisme (12) :** Ahura Mazda · Angra Mainyu · Mithra · Anahita · Zurvan · Verethragna · Sraosha · Simurgh · Rostam · Zahhak · Fereydoun · Jamshid
**Levant et Phénicie (4) :** Baal · Astarté · Melqart · **Didon** *(transférée depuis Grands dirigeants, voir §3.1)*

## 26.9 Mythologies slaves et baltes — slug `mythologies-slaves` — 25 cartes
**Existantes (2) :** Péroun · Vélès
**Ajouts (21) :** Svarog · Mokosh · Dazhbog · Stribog · Lada · Jarilo · Marzanna · Tchernobog · Bielobog · Domovoï · Leshy · Vodianoï · Kikimora · Bannik · Koschei · Zmeï Gorynytch · Alkonost · Sirin · Oiseau de feu · Perkūnas · Laima
**Transferts entrants depuis Créatures et légendes (2) :** Baba Yaga · Rusalka

## 26.10 Mythologies africaines — slug `mythologies-africaines` — 25 cartes
**Existantes (1) :** Anansi
**Ajouts (24) :** Olorun · Obatala · Shango · Ogoun · Eshu · Oshun · Yemoja · Oya · Orunmila · Nyame · Asase Ya · Mami Wata · Legba · Damballa · Mbombo · Nyambe · Amma · Nommo · Kalunga · Unkulunkulu · Heitsi-Eibib · Tanit · Anzar · Bumba

## 26.11 Mythologies océaniennes et amérindiennes — slug `mythologies-oceanie-ameriques` — 25 cartes
**Existantes (1) :** Coyote → **renommer `Coyote (mythologie)`** *(homonyme avec le mammifère)*

**Polynésie et Océanie (12) :** Māui · **Pelé (déesse)** *(homonyme avec le footballeur — le suffixe est obligatoire)* · Tāne · Tangaroa · Rangi et Papa · Hina · Kāne · Kanaloa · Lono · Kū · Tāwhirimātea · Hine-nui-te-pō
**Aborigènes d'Australie (2) :** Temps du rêve · Serpent arc-en-ciel
**Amériques autochtones (10) :** Wakan Tanka · Oiseau-tonnerre · Kokopelli · **Sedna (déesse)** *(homonyme avec l'objet transneptunien)* · Nanabozho · Glooscap · Femme-Bison-Blanc · Corbeau (mythologie haïda) · Ictinike · Amaru
**Transfert entrant depuis Créatures et légendes (1) :** Wendigo

## 26.12 Raretés à forcer

| Carte | Collection | Rareté forcée |
|---|---|---|
| Odin | nordique | legendaire |
| Ragnarök | nordique | epique |
| Rê | égyptienne | legendaire |
| Vishnu | hindoue | legendaire |
| Sun Wukong | Asie de l'Est | epique |
| Marduk | Proche-Orient | epique |
| Gilgamesh | Proche-Orient | epique |
| Māui | Océanie-Amériques | rare |

---

# 27. CRÉATURES ET LÉGENDES — RECENTRAGE

**Slug :** `creatures-et-legendes`
**État actuel :** 45 cartes, numéro 12 manquant.
**Cible :** 45 cartes après nettoyage et recomplétion.

## 27.1 Transferts sortants (15)
| Carte | Destination |
|---|---|
| Chimère · Hydre de Lerne · Minotaure · Pégase | déjà présentes dans *Dieux et figures mythologiques grecques* (§2.4) → **supprimer ici** |
| Kappa · Oni · Tengu · Kitsune | Mythologies d'Asie de l'Est |
| Banshee · Leprechaun · Selkie · Kelpie | Mythologie celtique |
| Baba Yaga · Rusalka | Mythologies slaves et baltes |
| Wendigo | Mythologies océaniennes et amérindiennes |
| Troll scandinave | Mythologie nordique |

*(soit 16 transferts au total)*

## 27.2 Corrections d'homonymes
| Carte | Nouveau nom | Conflit |
|---|---|---|
| Sirène | `Sirène (folklore)` | *Sirène (mythologie grecque)* |
| Basilic | `Basilic (créature)` | *Basilic vert* (reptiles) |

## 27.3 Ajouts (16)
Bête du Gévaudan · Tarasque · Manticore · Cockatrice · Hippogriffe · Léviathan · Béhémoth · Djinn · Goule · Bunyip · Jersey Devil · Mokèlé-mbembé · Korrigan · Zombie · Momie · Gnome

**Total : 45 − 16 + 16 = 45 cartes**

---

# Récapitulatif du lot 6

| Collection | Avant | Après | Action |
|---|---|---|---|
| Coupes du monde FIFA | 22 | 23 | +1 (édition 2026, victoire de l'Espagne) |
| Plus grands joueurs de football | 147 | — | scindée |
| → Légendes du football | — | 50 | nouvelle collection |
| → Football, ère moderne | — | 100 | nouvelle collection |
| Mythologies du monde | 58 | — | éclatée en 10 collections |
| → Mythologie nordique | — | 35 | nouvelle collection |
| → Mythologie égyptienne | — | 35 | nouvelle collection |
| → Mythologie hindoue | — | 35 | nouvelle collection |
| → Mythologie celtique | — | 25 | nouvelle collection |
| → Mythologies d'Asie de l'Est | — | 35 | nouvelle collection |
| → Mythologies mésoaméricaines et andines | — | 30 | nouvelle collection |
| → Mythologies du Proche-Orient ancien | — | 34 | nouvelle collection |
| → Mythologies slaves et baltes | — | 25 | nouvelle collection |
| → Mythologies africaines | — | 25 | nouvelle collection |
| → Mythologies océaniennes et amérindiennes | — | 25 | nouvelle collection |
| Créatures et légendes | 45 | 45 | 16 transferts, 2 renommages, +16 |

**Lot 7 (à traiter) :** Personnages de fiction célèbres · Films cultes · Jeux vidéo cultes


---
---

# LOT 7 — PERSONNAGES DE FICTION

**Version :** v7

---

# 28. PERSONNAGES DE FICTION → SCISSION EN 6 COLLECTIONS

**État actuel :** `personnages-de-fiction-celebres`, 170 cartes, numéros 106, 129 et 144 manquants.
**Décision :** éclatement par média, **un personnage n'apparaît que dans une seule collection**.

## 28.1 Règle d'attribution
**Le média de notoriété dominante** — celui par lequel le grand public connaît majoritairement le personnage, pas nécessairement celui de sa création.

**Sous-règle d'arbitrage (pour rendre la décision déterministe) :** lorsque l'œuvre d'origine et son adaptation sont toutes deux majeures et durables, l'œuvre d'origine l'emporte. C'est ce qui maintient Dracula, Sherlock Holmes, Harry Potter et le *Seigneur des Anneaux* en littérature, tandis que James Bond, Hannibal Lecter et Geralt de Riv basculent vers leur média de notoriété.

## 28.2 Suppression (1)
- **Thor** — sort de la collection des personnages de fiction. Il ne subsiste que comme divinité dans *Mythologie nordique*, ce qui supprime l'homonyme.

## 28.3 Renommage (1)
- **Nemo** → `Nemo (Le Monde de Nemo)`, pour lever l'ambiguïté avec *Capitaine Nemo* (littérature).

---

## 28.4 Collection : Personnages de littérature
**Slug :** `personnages-litterature` — **60 cartes**

**Existantes (46) :** Sherlock Holmes · Dracula · Frankenstein · Dr. Jekyll et Mr. Hyde · Dorian Gray · Robinson Crusoé · Gulliver · Don Quichotte · Sancho Pança · D'Artagnan · Jean Valjean · Quasimodo · Comte de Monte-Cristo · Capitaine Nemo · Phileas Fogg · Cyrano de Bergerac · Alice · Chapelier fou · Peter Pan · Capitaine Crochet · Tarzan · Ebenezer Scrooge · Oliver Twist · Long John Silver · Frodon Sacquet · Gandalf · Aragorn · Legolas · Gimli · Sauron · Gollum · Bilbo Sacquet · Harry Potter · Hermione Granger · Ron Weasley · Albus Dumbledore · Voldemort · Severus Rogue · Hagrid · Daenerys Targaryen · Jon Snow · Tyrion Lannister · Aslan · Cthulhu · Conan le Barbare · Elric de Melniboné

**Ajouts (14) :** Le Petit Prince · Arsène Lupin · Hercule Poirot · Jules Maigret · Hamlet · Roméo et Juliette · Faust · Capitaine Achab · Emma Bovary · Anna Karénine · Rodion Raskolnikov · Meursault · Javert · Paul Atréides

---

## 28.5 Collection : Personnages de cinéma et de série
**Slug :** `personnages-cinema-serie` — **55 cartes**

**Existantes (25) :** James Bond · Dark Vador · Luke Skywalker · Han Solo · Princesse Leia · Yoda · Indiana Jones · Rocky Balboa · Terminator · Ellen Ripley · Neo · Forrest Gump · Hannibal Lecter · Norman Bates · Freddy Krueger · Jason Voorhees · Michael Myers · Jack Sparrow · Wednesday Addams · Gomez Addams · Walter White · Tony Soprano · Eleven · Sorcier d'Oz · Dorothy Gale

**Ajouts (30) :** Vito Corleone · Michael Corleone · Tony Montana · King Kong · Godzilla · E.T. · Marty McFly · Doc Brown · John McClane · John Rambo · Willy Wonka · Mary Poppins · Jack Torrance · Maximus · Travis Bickle · Tyler Durden · Alex DeLarge · Amélie Poulain · OSS 117 · Fantômas · Columbo · Docteur Who · Saul Goodman · Gus Fring · Don Draper · Rick Grimes · Omar Little · Jack Bauer · Sheldon Cooper · Dexter Morgan

---

## 28.6 Collection : Personnages de bande dessinée et de comics
**Slug :** `personnages-bd-comics` — **55 cartes**

**Existantes (27) :** Superman · Batman · Wonder Woman · Spider-Man · Iron Man · Captain America · Hulk · Wolverine · Black Panther · Doctor Strange · Deadpool · Joker · Harley Quinn · The Flash · Green Lantern · Aquaman · Catwoman · Punisher · Daredevil · Professeur X · Magnéto · Astérix · Obélix · Tintin · Capitaine Haddock · Lucky Luke · Gaston Lagaffe
*(Thor retiré, voir §28.2)*

**Ajouts (28) :**
*Comics américains (13)* — Thanos · Lex Luthor · Venom · Docteur Fatalis · Robin · Black Widow · Silver Surfer · Galactus · Tornade · Jean Grey · Hellboy · Spawn · Judge Dredd
*Franco-belge (11)* — Spirou · Fantasio · Marsupilami · Blake et Mortimer · Corto Maltese · Thorgal · Largo Winch · XIII · Iznogoud · Rahan · Titeuf
*Comic strips (4)* — Snoopy · Garfield · Calvin et Hobbes · Boule et Bill

---

## 28.7 Collection : Personnages de jeu vidéo
**Slug :** `personnages-jeu-video` — **55 cartes**

**Existantes (33) :** Mario · Luigi · Bowser · Princesse Peach · Link · Zelda · Ganon · Sonic the Hedgehog · Kirby · Pikachu · Master Chief · Lara Croft · Solid Snake · Kratos · Ezio Auditore · Gordon Freeman · Cloud Strife · Séphiroth · Chun-Li · Ryu · Samus Aran · Donkey Kong · Yoshi · Crash Bandicoot · Spyro le Dragon · Agent 47 · Nathan Drake · Aloy · Arthur Morgan · Commander Shepard · Vault Boy · Duke Nukem · **Geralt de Riv** *(reclassé depuis la littérature : notoriété dominante par le jeu)*

**Ajouts (22) :** Pac-Man · Rayman · Mega Man · Sub-Zero · Scorpion · Ellie · Joel · Leon S. Kennedy · Jill Valentine · Nemesis · Pyramid Head · Alucard · Simon Belmont · Bayonetta · Sora · 2B · Big Daddy · Steve (Minecraft) · Creeper · Sackboy · Ratchet et Clank · Cuphead

---

## 28.8 Collection : Personnages d'animation
**Slug :** `personnages-animation` — **50 cartes**

**Existantes (22) :** Mickey Mouse · Donald Duck · Dingo · Blanche-Neige · Cendrillon · Belle au bois dormant · Simba · Aladdin · Génie · Ariel · Elsa · Woody · Buzz l'Éclair · Nemo (Le Monde de Nemo) · Shrek · Âne · Homer Simpson · Bart Simpson · Bugs Bunny · Daffy Duck · Tom et Jerry · Scooby-Doo

**Ajouts (28) :** Pinocchio · Bambi · Dumbo · Baloo · Mulan · Stitch · WALL-E · Rémy · Sulli · Dory · Vaiana · Raiponce · Mérida · Mufasa · Scar · Timon et Pumbaa · Maléfique · Ursula · Jafar · Cruella d'Enfer · Bob l'éponge · Patrick Étoile · Vil Coyote et Bip Bip · Titi et Grosminet · Les Schtroumpfs · Popeye · Betty Boop · Casper

---

## 28.9 Collection : Personnages de manga et d'anime
**Slug :** `personnages-manga-anime` — **45 cartes**

**Existantes (16) :** Son Goku · Naruto Uzumaki · Sasuke Uchiha · Luffy · Zoro · Sangohan · Vegeta · Ichigo Kurosaki · Eren Yeager · Light Yagami · L · Edward Elric · Totoro · Sailor Moon · Doraemon · Astro, le petit robot

**Ajouts (29) :** Kenshiro · Guts · Griffith · Seiya · Kenshin Himura · Spike Spiegel · Lelouch Lamperouge · Levi Ackerman · Mikasa Ackerman · Kakashi Hatake · Itachi Uchiha · Gon Freecss · Killua Zoldyck · Tanjiro Kamado · Nezuko Kamado · Gojo Satoru · Denji · Piccolo · Freezer · Cell · Bulma · Krilin · Nami · Sanji · Portgas D. Ace · Shanks · Lupin III · Motoko Kusanagi · Ryuk

---

## 28.10 Règle de non-collision avec les collections d'œuvres
*Films cultes* et *Jeux vidéo cultes* recensent des **œuvres**. Les six collections ci-dessus recensent des **personnages**. Aucune carte ne doit exister dans les deux registres : pas de carte « Star Wars » dans les personnages, pas de carte « Dark Vador » dans les films. Vérifier cette contrainte après implémentation.

---

# Récapitulatif du lot 7

| Collection | Avant | Après | Action |
|---|---|---|---|
| Personnages de fiction célèbres | 170 | — | éclatée en 6 collections |
| → Personnages de littérature | — | 60 | nouvelle collection |
| → Personnages de cinéma et de série | — | 55 | nouvelle collection |
| → Personnages de bande dessinée et de comics | — | 55 | nouvelle collection |
| → Personnages de jeu vidéo | — | 55 | nouvelle collection |
| → Personnages d'animation | — | 50 | nouvelle collection |
| → Personnages de manga et d'anime | — | 45 | nouvelle collection |

**Lot 8 (à traiter, dernier) :** Films cultes · Jeux vidéo cultes


---
---

# LOT 8 — LES ŒUVRES

**Version :** v8 — dernier lot

---

# 29. RÉSOLUTION DES COLLISIONS PERSONNAGE ↔ ŒUVRE

Six cartes de *Films cultes* portent le même `nom` qu'une carte personnage. Le `titrePage` reste inchangé, seul le champ `nom` est modifié par ajout du suffixe `(film)`.

| Nom actuel | Nouveau nom | `titrePage` (inchangé) |
|---|---|---|
| Batman | `Batman (film)` | `Batman (film, 1989)` |
| King Kong | `King Kong (film)` | `King Kong` |
| Terminator | `Terminator (film)` | `Terminator` |
| E.T., l'extra-terrestre | `E.T., l'extra-terrestre (film)` | `E.T., l'extra-terrestre` |
| Forrest Gump | `Forrest Gump (film)` | `Forrest Gump` |
| Joker | `Joker (film)` | `Joker (film, 2019)` |

---

# 30. FILMS CULTES → SCISSION EN 2 COLLECTIONS

**État actuel :** `films-cultes`, 121 cartes, numérotation continue.

- Collection A : **Classiques du cinéma** — slug `classiques-du-cinema` — sorties avant 1980 — **70 cartes**
- Collection B : **Cinéma moderne** — slug `cinema-moderne` — sorties à partir de 1980 — **110 cartes**

## 30.1 Règle de granularité
**Une carte = un film.** La carte actuelle « Seigneur des Anneaux » pointe vers la série de films : la remplacer par **Le Seigneur des anneaux : La Communauté de l'anneau**. La carte « Star Wars » pointe déjà correctement vers l'épisode IV, conserver ce principe.

## 30.2 Répartition des cartes existantes vers Classiques du cinéma (48)
Voyage dans la Lune · Naissance d'une nation · Nosferatu · Metropolis · Le Cuirassé Potemkine · La Ruée vers l'or · Les Temps modernes · Le Kid · King Kong (film) · Autant en emporte le vent · Le Magicien d'Oz · Citizen Kane · Casablanca · La vie est belle · Sunset Boulevard · Chantons sous la pluie · Fenêtre sur cour · Vertigo · Douze Hommes en colère · Certains l'aiment chaud · À bout de souffle · Psychose · Lawrence d'Arabie · 2001, l'Odyssée de l'espace · Le Bon, la Brute et le Truand · La Grande Vadrouille · Bonnie and Clyde · Le Parrain · Le Parrain 2 · Orange mécanique · L'Exorciste · Les Dents de la mer · Star Wars · Rencontres du troisième type · Apocalypse Now · Rocky · Taxi Driver · Alien · Les 400 coups · Rashōmon · La Dolce vita · 8½ · Amarcord · Solaris · Andreï Roublev · Tokyo Story · Vivre · La Bataille d'Alger

Les **73 cartes restantes** basculent dans *Cinéma moderne*.

## 30.3 Ajouts — Classiques du cinéma (22)
Les Sept Samouraïs *(l'un des films les plus influents de l'histoire, absent)* · Docteur Folamour · La Mort aux trousses · Vol au-dessus d'un nid de coucou · Chinatown · Il était une fois dans l'Ouest · Le Septième Sceau · La Règle du jeu · Le Voleur de bicyclette · Les Enfants du paradis · Le Troisième Homme · Le Pont de la rivière Kwaï · Ben-Hur · Les Lumières de la ville · Le Dictateur · M le maudit · Les Oiseaux · Le Lauréat · Easy Rider · Macadam Cowboy · Le Salaire de la peur · Les Tontons flingueurs

**Total collection A : 48 + 22 = 70 cartes**

## 30.4 Ajouts — Cinéma moderne (37)

### Classiques modernes absents (15)
Les Évadés *(n°1 du classement IMDb, absent)* · Shining · Les Affranchis · Amadeus · Cinema Paradiso · Braveheart · Sixième Sens · Fargo · The Big Lebowski · Reservoir Dogs · Kill Bill · Le Cinquième Élément · Full Metal Jacket · Scarface · Heat

### Cinéma français (6)
Nikita · Le Dîner de cons · Les Visiteurs · La Cité de la peur · Intouchables · Astérix et Obélix : Mission Cléopâtre

### Grands succès populaires et animation (11)
Avatar *(plus gros succès du box-office mondial, absent)* · Toy Story · Le Monde de Nemo · Shrek · La Reine des neiges · Avengers: Endgame · Harry Potter à l'école des sorciers · Les Indestructibles · Ratatouille · Vice-versa · Là-haut

### Asie (5)
Akira *(le film qui a fait connaître l'animation japonaise en Occident, absent)* · Le Tombeau des lucioles · Your Name · In the Mood for Love · Tigre et Dragon

**Total collection B : 73 + 37 = 110 cartes**

## 30.5 Raretés à forcer

| Carte | Collection | Rareté forcée |
|---|---|---|
| Les Sept Samouraïs | A | legendaire |
| Citizen Kane | A | epique |
| Les Évadés | B | epique |
| Avatar | B | epique |
| Akira | B | rare |

---

# 31. JEUX VIDÉO CULTES → SCISSION EN 2 COLLECTIONS

**État actuel :** `jeux-video-cultes`, 95 cartes, numérotation continue.

- Collection A : **Âge d'or du jeu vidéo** — slug `age-dor-du-jeu-video` — sorties de 1972 à 1999 — **61 cartes**
- Collection B : **Jeu vidéo moderne** — slug `jeu-video-moderne` — sorties à partir de 2000 — **89 cartes**

## 31.1 Répartition des cartes existantes vers Âge d'or (48)
Pong · Space Invaders · Pac-Man · Asteroids · Galaga · Donkey Kong · Frogger · Missile Command · Defender · Tetris · Q*bert · Super Mario Bros. · The Legend of Zelda · Metroid · Punch-Out!! · Excitebike · Duck Hunt · Sonic the Hedgehog · Street Fighter II · Mortal Kombat · Super Mario World · Donkey Kong Country · The Legend of Zelda: A Link to the Past · Chrono Trigger · Final Fantasy VI · Prince of Persia · Maniac Mansion · SimCity · Myst · Doom · Wolfenstein 3D · Civilization · Warcraft II · Command & Conquer · Final Fantasy VII · Super Mario 64 · The Legend of Zelda: Ocarina of Time · GoldenEye 007 · Resident Evil · Metal Gear Solid · Half-Life · StarCraft · Diablo · Pokémon Rouge et Bleu · Tomb Raider · Crash Bandicoot · Spyro the Dragon · Age of Empires

Les **47 cartes restantes** basculent dans *Jeu vidéo moderne*.

## 31.2 Ajouts — Âge d'or du jeu vidéo (13)
Super Metroid · Castlevania: Symphony of the Night · Mega Man 2 · Contra · Mario Kart 64 · Super Smash Bros. · Quake · Counter-Strike · Dragon Quest · Gran Turismo · Tony Hawk's Pro Skater · Age of Empires II · Unreal Tournament

**Total collection A : 48 + 13 = 61 cartes**

## 31.3 Ajouts — Jeu vidéo moderne (42)

### Franchises entièrement absentes alors que leurs personnages sont des cartes (6)
- Grand Theft Auto V *(le produit de divertissement le plus rentable de l'histoire, absent)*
- Assassin's Creed II *(Ezio Auditore est une carte personnage)*
- Fallout 3 *(Vault Boy est une carte personnage)*
- Uncharted 2: Among Thieves *(Nathan Drake est une carte personnage)*
- Mass Effect 2 *(Commander Shepard est une carte personnage)*
- Grand Theft Auto III

### Grands absents des années 2000 (11)
Diablo II · Deus Ex · Silent Hill 2 · The Elder Scrolls III: Morrowind · Baldur's Gate II · Metal Gear Solid 3 · Final Fantasy X · Kingdom Hearts · Super Smash Bros. Melee · Team Fortress 2 · Fallout: New Vegas

### Années 2010-2020 (11)
Persona 5 · NieR: Automata · Monster Hunter: World · Sekiro · Ghost of Tsushima · Cyberpunk 2077 · Death Stranding · The Legend of Zelda: Tears of the Kingdom · Mario Kart 8 · Rocket League · Terraria

### Indépendants (6)
Slay the Spire · Papers, Please · Hotline Miami · Limbo · Braid · Vampire Survivors

### Mobile, social et compétitif — segment totalement absent (8)
Wii Sports · Pokémon GO · Angry Birds · Roblox · PUBG: Battlegrounds · Apex Legends · Valorant · Genshin Impact

**Total collection B : 47 + 42 = 89 cartes**

## 31.4 Raretés à forcer

| Carte | Collection | Rareté forcée |
|---|---|---|
| Pong | A | epique |
| Counter-Strike | A | epique |
| Grand Theft Auto V | B | legendaire |
| Pokémon GO | B | rare |

---

# Récapitulatif du lot 8

| Collection | Avant | Après | Action |
|---|---|---|---|
| Films cultes | 121 | — | scindée, 6 renommages, 1 correction de granularité |
| → Classiques du cinéma | — | 70 | nouvelle collection |
| → Cinéma moderne | — | 110 | nouvelle collection |
| Jeux vidéo cultes | 95 | — | scindée |
| → Âge d'or du jeu vidéo | — | 61 | nouvelle collection |
| → Jeu vidéo moderne | — | 89 | nouvelle collection |

---
---

# RÉCAPITULATIF GÉNÉRAL

Le jeu passe de **32 collections / 2 304 cartes** à **57 collections / ~3 690 cartes**.

| # | Collection | Cartes |
|---|---|---|
| 1 | Merveilles du monde | 14 |
| 2 | Pilotes F1 champions du monde | 34 |
| 3 | Éléments chimiques | 118 |
| 4 | Corps célestes | 97 |
| 5 | Constellations | 88 |
| 6 | Dieux et figures mythologiques grecques | 79 |
| 7 | Mythologie nordique | 35 |
| 8 | Mythologie égyptienne | 35 |
| 9 | Mythologie hindoue | 35 |
| 10 | Mythologie celtique | 25 |
| 11 | Mythologies d'Asie de l'Est | 35 |
| 12 | Mythologies mésoaméricaines et andines | 30 |
| 13 | Mythologies du Proche-Orient ancien | 34 |
| 14 | Mythologies slaves et baltes | 25 |
| 15 | Mythologies africaines | 25 |
| 16 | Mythologies océaniennes et amérindiennes | 25 |
| 17 | Créatures et légendes | 45 |
| 18 | Souverains et conquérants | 90 |
| 19 | Dirigeants de l'ère contemporaine | 56 |
| 20 | Empires et civilisations | 60 |
| 21 | Dynasties et maisons régnantes | 38 |
| 22 | Grandes batailles historiques | 87 |
| 23 | Grandes guerres | 59 |
| 24 | Monuments et architecture | 76 |
| 25 | Sites antiques et archéologiques | 39 |
| 26 | Grands explorateurs | 61 |
| 27 | Pionniers de l'extrême | 38 |
| 28 | Aviateurs célèbres | 67 |
| 29 | Scientifiques célèbres | 161 |
| 30 | Inventeurs et ingénieurs | 49 |
| 31 | Inventions importantes | 129 |
| 32 | Auteurs classiques | 114 |
| 33 | Auteurs modernes et contemporains | 143 |
| 34 | Grands peintres | 114 |
| 35 | Tableaux célèbres | 110 |
| 36 | Mammifères | 100 |
| 37 | Oiseaux | 70 |
| 38 | Reptiles et amphibiens | 40 |
| 39 | Poissons et vie marine | 50 |
| 40 | Insectes | 60 |
| 41 | Dinosaures célèbres | 62 |
| 42 | Créatures préhistoriques | 40 |
| 43 | Races de chien | 132 |
| 44 | Races de chat | 45 |
| 45 | Coupes du monde FIFA | 23 |
| 46 | Légendes du football | 50 |
| 47 | Football, ère moderne | 100 |
| 48 | Personnages de littérature | 60 |
| 49 | Personnages de cinéma et de série | 55 |
| 50 | Personnages de bande dessinée et de comics | 55 |
| 51 | Personnages de jeu vidéo | 55 |
| 52 | Personnages d'animation | 50 |
| 53 | Personnages de manga et d'anime | 45 |
| 54 | Classiques du cinéma | 70 |
| 55 | Cinéma moderne | 110 |
| 56 | Âge d'or du jeu vidéo | 61 |
| 57 | Jeu vidéo moderne | 89 |

## Contrôles finaux à effectuer
1. **Vérification des homonymes** — contrôler qu'aucun `nom` n'est dupliqué entre deux collections, et appliquer le suffixe entre parenthèses le cas échéant.
2. **Renumérotation générale** — toutes les collections touchées doivent avoir un `numero` continu de 1 à N.
3. **Complétude des champs** — aucune carte ne doit rester sans `imageUrl`, `rarete` ni `pouvoir` (voir consignes 9 et 10).
