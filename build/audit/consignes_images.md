# Choisir les images du grand complement

Ces consignes viennent de l'étude des 5 015 cartes que l'utilisateur a recadrées ou remplacées dans l'atelier. Il faut choisir comme lui.

## Règles communes

- **Le sujet d'abord.** L'image montre la carte elle-même, reconnaissable au premier coup d'œil, et non un sujet voisin (la ville au lieu du chat, l'acteur au lieu du personnage, un produit dérivé, un jouet).
- **La qualité ensuite.** Image nette, ni pixellisée ni surcompressée. Petit côté d'au moins 450 px ; au-dessus de 800 px de préférence.
- **Refuser** :
  - les filigranes (Alamy, Getty, Shutterstock, Dreamstime, 123RF, iStock : même discrets) et le texte incrusté ;
  - les collages, mèmes et captures d'écran d'interface ;
  - les montages de plusieurs images ;
  - les timbres, les affiches pleines de texte, les photos de produits emballés ;
  - les croquis naïfs, les diagrammes et les cartes géographiques.
- **Le cadrage.** La carte finale est en 4:3 (800 × 600), recadrée au centre. Le sujet doit y tenir : un sujet collé au bord d'une image très large sera coupé.
- **L'homogénéité.** Regarder la planche de la collection existante : même registre d'image, même tonalité. Entre deux bonnes images, prendre celle qui ressemble le plus aux cartes voisines.
- **Les images sous droits sont admises.** L'usage est strictement personnel. Prendre la meilleure, pas la plus libre.

## Par famille

- **Personnes réelles** : auteurs, compositeurs, philosophes, scientifiques, inventeurs, figures religieuses, figures de l'émancipation, dirigeants, souverains, explorateurs, pionniers, architectes, couturiers, astronautes, peintres, réalisateurs, acteurs.
  - Le portrait canonique, tête et épaules ou buste, net.
  - Le noir et blanc convient pour les figures historiques.
  - Avant la photographie : un portrait peint.
  - Pas de photo de groupe, pas de statue si un portrait existe.
  - Pour un acteur, un portrait (tapis rouge ou studio) plutôt qu'une scène de film.
- **Musiciens populaires** : la photo iconique, sur scène ou en portrait. Pour un groupe, le groupe réuni.
- **Sportifs** : photo d'action ou portrait en tenue, dans le maillot qui les a rendus célèbres (club ou sélection), visage visible.
- **Personnages de fiction** :
  - Ce que l'on retient, c'est l'illustration officielle ou une image de scène du personnage lui-même, colorée, en plein cadre.
  - Comics : art dynamique de bande dessinée.
  - Animation : le rendu officiel.
  - Manga : un visuel de style anime.
  - Pour un personnage de film ou de série : l'image du film, pas l'acteur en interview.
  - Pas de cosplay, de figurine ni de produit dérivé.
- **Films** : une scène emblématique ou l'illustration de l'affiche sans titre. Format paysage.
- **Séries** : photo promotionnelle de la distribution ou visuel clé.
- **Jeux vidéo** : capture de jeu ou visuel officiel, paysage ; pas de boîte de jeu couverte de logos.
- **Mythologies, créatures, lieux, événements, objets, véhicules mythiques, croyances** :
  - Illustration peinte, riche en couleur, dans le style « fantasy numérique » des cartes voisines.
  - À défaut, un tableau classique.
  - Pas de photo de petite statuette de musée sur fond blanc si une illustration existe.
- **Plats et fromages** : photographie culinaire professionnelle, lumière chaude, fond rustique ou sombre, appétissante. Pas d'emballage, pas de texte.
- **Villes** : panorama de carte postale, coucher de soleil ou heure dorée, ligne d'horizon reconnaissable.
- **Nature** (animaux, plantes, arbres, fleurs, champignons, minéraux) :
  - le sujet entier, net, dans son milieu ou sur un fond propre ;
  - pas de dessin ni de planche naturaliste.
- **Lieux** (montagnes, fleuves, îles, monuments, sites) : la vue emblématique, belle lumière, format paysage.
- **Tableaux** : l'œuvre elle-même, entière, en haute définition, sans cadre ni mur de musée.
- **Sculptures** : la sculpture photographiée, bien détachée du fond.
- **Photographies célèbres** : la photographie elle-même.
- **Objets** (inventions, instruments, véhicules, engins spatiaux) : l'objet lui-même, photo nette ; fond neutre bienvenu pour les instruments.
- **Monnaies du monde** : le billet ou la pièce à plat, entier.
- **Monnaies historiques** : la pièce en gros plan.
- **Œuvres littéraires** : une illustration célèbre de l'histoire, ou la couverture de la première édition. De préférence une illustration.
- **Jeux de société** : le jeu en cours de partie (plateau et pions), vue de dessus ou de trois quarts.
- **Disciplines sportives** : une photo d'action dynamique.
- **Empires, dynasties, batailles, guerres, traités** : un tableau qui les représente, ou leur monument ou objet emblématique.
- **Langues anciennes** : une inscription ou une tablette dans l'écriture même.

## Le fichier de choix

Écrire `build/audit/choix_grand/<slug>.json` :

```json
{ "<id de la carte>": {"k": 3},
  "<id>": {"k": 5, "cy": 0.35},
  "<id>": {"k": -1, "note": "aucune candidate valable"} }
```

- `k` est le numéro de la candidate sur la planche.
- `cx`, `cy` et `w` sont facultatifs. Ils imposent le cadre 4:3 : `w` est la fraction de la largeur de l'image, `cx` et `cy` le centre en fractions. On ne les donne que si le recadrage automatique couperait le sujet.
- Le recadrage automatique prend toute la largeur (portraits) ou toute la hauteur (images larges). Il centre, ou suit le visage détecté.
- Si aucune candidate ne convient, relancer une recherche ciblée :
  `python build/audit/candidats_images.py <slug> --seul <id> --requete "<requête>"`
  La planche `<slug>_reprise_000.png` montre alors les nouvelles candidates. Si rien ne va toujours, écrire `k: -1` avec une note.
