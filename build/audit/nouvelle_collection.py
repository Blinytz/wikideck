#!/usr/bin/env python3
"""Crée une collection à partir de transferts et d'ajouts.

Troisième fois que l'opération se répète — Lieux légendaires, puis les
Événements et les Objets mythiques —, donc elle est écrite une fois pour
toutes ici. Elle fait ce que ces trois cas ont en commun :

  - déménage des cartes existantes, avec leurs fichiers image, leur cadrage et
    leur entrée de sources : l'`id` porte le slug de la collection, et
    l'atelier en déduit tous ces chemins ;
  - crée les cartes neuves depuis le cache de `resoudre_pages`, et va chercher
    leurs pageviews ;
  - recalcule rareté et numérotation des collections touchées, index compris.

Le rôle de combat et le déclencheur sont posés dans `build/combat_config.py` :
ce module ne touche qu'aux données.

Usage : python nouvelle_collection.py <cle> [--essai]
        cles : evenements-mythiques | objets-mythiques
"""
import sys, json, re, time, pickle, unicodedata, urllib.parse, urllib.request
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE / 'build'))
import rarete_pv
import resoudre_pages as R

UA = 'wikideck-build/1.0 (projet perso; contact: claude.elk041@passmail.net)'
CACHE_PV = RACINE / 'build' / '.cache_pageviews.pkl'
_pv = pickle.loads(CACHE_PV.read_bytes()) if CACHE_PV.exists() else {}


# ------------------------------------------------------------------ les plans

PLANS = {
    'evenements-mythiques': dict(
        nom='Événements mythiques',
        # Ragnarök n'était ni un personnage ni un lieu : il n'avait pas sa
        # place chez les divinités nordiques. C'est le point de départ.
        transferts=[('mythologie-nordique', 'Ragnarök')],
        ajouts=[
            ('Déluge', 'Déluge'),
            ('Armageddon', 'Armageddon'),
            ('Jugement dernier', 'Jugement dernier'),
            ('Guerre de Troie', 'Guerre de Troie'),
            ('Titanomachie', 'Titanomachie'),
            ('Gigantomachie', 'Gigantomachie'),
            ("Travaux d'Héraclès", "Travaux d'Héraclès"),
            ('Jugement de Pâris', 'Jugement de Pâris'),
            ('Barattage de la Mer de lait', 'Barattage de la Mer de lait'),
            ('Bataille de Kurukshetra', 'Bataille de Kurukshetra'),
        ],
        # Écartés : « Apocalypse » et « Épopée de Gilgamesh », dont les articles
        # traitent d'un LIVRE et non de l'événement ; « Fin du monde » et
        # « Cataclysme », qui sont des notions générales et non des récits.
    ),
    'croyances-et-notions-sacrees': dict(
        nom='Croyances et notions sacrées',
        # Le Temps du reve n'etait ni un personnage, ni un lieu, ni un objet,
        # ni un evenement : c'est un CADRE de croyance. Il fonde la collection.
        transferts=[('mythologies-oceanie-ameriques', 'Temps du rêve')],
        ajouts=[
            ('Karma', 'Karma'),
            ('Saṃsāra', 'Saṃsāra'),
            ('Réincarnation', 'Réincarnation'),
            ('Métempsycose', 'Métempsycose'),
            ('Yin et yang', 'Yin et yang'),
            ('Au-delà', 'Séjour des morts'),
            ('Enfer', 'Enfer'),
            ('Paradis', 'Paradis'),
            ('Purgatoire', 'Purgatoire'),
            ('Âme', 'Âme'),
            ('Destin', 'Destin'),
            ('Axis mundi', 'Axis mundi'),
            ('Arbre de vie', 'Arbre de vie'),
            ('Chamanisme', 'Chamanisme'),
            ('Animisme', 'Animisme'),
            ('Tabou', 'Tabou'),
        ],
        # Ecartes : Nirvana, Tao, Totem et Mana, qui sont des pages
        # d'homonymie ; la Pesee du coeur, qui n'a pas d'article.
    ),
    'grands-compositeurs': dict(
        nom='Grands compositeurs',
        # La musique etait le plus gros trou du jeu : 119 peintres, 107
        # tableaux, et pas un seul compositeur.
        transferts=[],
        ajouts=[
            ('Claudio Monteverdi', 'Claudio Monteverdi'),
            ('Antonio Vivaldi', 'Antonio Vivaldi'),
            ('Jean-Sébastien Bach', 'Jean-Sébastien Bach'),
            ('Georg Friedrich Haendel', 'Georg Friedrich Haendel'),
            ('Joseph Haydn', 'Joseph Haydn'),
            ('Wolfgang Amadeus Mozart', 'Wolfgang Amadeus Mozart'),
            ('Ludwig van Beethoven', 'Ludwig van Beethoven'),
            ('Franz Schubert', 'Franz Schubert'),
            ('Hector Berlioz', 'Hector Berlioz'),
            ('Frédéric Chopin', 'Frédéric Chopin'),
            ('Robert Schumann', 'Robert Schumann'),
            ('Franz Liszt', 'Franz Liszt'),
            ('Richard Wagner', 'Richard Wagner'),
            ('Giuseppe Verdi', 'Giuseppe Verdi'),
            ('Johannes Brahms', 'Johannes Brahms'),
            ('Piotr Ilitch Tchaïkovski', 'Piotr Ilitch Tchaïkovski'),
            ('Antonín Dvořák', 'Antonín Dvořák'),
            ('Gustav Mahler', 'Gustav Mahler'),
            ('Claude Debussy', 'Claude Debussy'),
            ('Maurice Ravel', 'Maurice Ravel'),
            ('Erik Satie', 'Erik Satie'),
            ('Igor Stravinsky', 'Igor Stravinsky'),
            ('Sergueï Rachmaninov', 'Sergueï Rachmaninov'),
            ('Dmitri Chostakovitch', 'Dmitri Chostakovitch'),
            ('Serge Prokofiev', 'Serge Prokofiev'),
            ('Béla Bartók', 'Béla Bartók'),
            ('Arnold Schönberg', 'Arnold Schönberg'),
            ('George Gershwin', 'George Gershwin'),
            ('Aaron Copland', 'Aaron Copland'),
            ('Olivier Messiaen', 'Olivier Messiaen'),
            ('John Cage', 'John Cage'),
            ('Philip Glass', 'Philip Glass'),
            ('Steve Reich', 'Steve Reich'),
            ('Arvo Pärt', 'Arvo Pärt'),
            ('Ennio Morricone', 'Ennio Morricone'),
            ('Hans Zimmer', 'Hans Zimmer'),
            ('Nino Rota', 'Nino Rota'),
            ('Jean-Philippe Rameau', 'Jean-Philippe Rameau'),
            ('Henry Purcell', 'Henry Purcell'),
            ('Domenico Scarlatti', 'Domenico Scarlatti'),
            ('Christoph Willibald Gluck', 'Christoph Willibald Gluck'),
            ('Camille Saint-Saëns', 'Camille Saint-Saëns'),
            ('Gabriel Fauré', 'Gabriel Fauré'),
            ('César Franck', 'César Franck'),
            ('Modeste Moussorgski', 'Modeste Moussorgski'),
            ('Nikolaï Rimski-Korsakov', 'Nikolaï Rimski-Korsakov'),
            ('Jean Sibelius', 'Jean Sibelius'),
            ('Edvard Grieg', 'Edvard Grieg'),
            ('Giacomo Puccini', 'Giacomo Puccini'),
            ('Gioachino Rossini', 'Gioachino Rossini'),
            ('Georges Bizet', 'Georges Bizet'),
            ('Jacques Offenbach', 'Jacques Offenbach'),
            ('Anton Bruckner', 'Anton Bruckner'),
            ('Félix Mendelssohn', 'Félix Mendelssohn'),
            ('Carl Orff', 'Carl Orff'),
            ('Toru Takemitsu', 'Toru Takemitsu'),
            ('Astor Piazzolla', 'Astor Piazzolla'),
            ('Duke Ellington', 'Duke Ellington'),
            ('Scott Joplin', 'Scott Joplin'),
            ('John Williams', 'John Williams (compositeur)'),
        ],
    ),
    'oeuvres-musicales': dict(
        nom='Œuvres musicales majeures',
        transferts=[],
        ajouts=[
            ('Symphonie nº 9 de Beethoven', 'Symphonie nº 9 de Beethoven'),
            ('Le Sacre du printemps', 'Le Sacre du printemps'),
            ('Les Quatre Saisons', 'Les Quatre Saisons'),
            ('Rhapsody in Blue', 'Rhapsody in Blue'),
            ('Boléro (Ravel)', 'Boléro (Ravel)'),
            ('Symphonie nº 5 de Beethoven', 'Symphonie nº 5 de Beethoven'),
            ('Requiem de Mozart', 'Requiem de Mozart'),
            ('La Flûte enchantée', 'La Flûte enchantée'),
            ('Les Noces de Figaro', 'Les Noces de Figaro'),
            ('Don Giovanni', 'Don Giovanni'),
            ('Carmen (opéra)', 'Carmen (opéra)'),
            ('La Traviata', 'La Traviata'),
            ('Aida', 'Aida (opéra)'),
            ('Nabucco', 'Nabucco'),
            ('Le Barbier de Séville (Rossini)', 'Le Barbier de Séville (Rossini)'),
            ('Tosca', 'Tosca'),
            ('La Bohème', 'La Bohème'),
            ("L'Anneau du Nibelung", "L'Anneau du Nibelung"),
            ('Tristan et Isolde', 'Tristan et Isolde (Wagner)'),
            ('Casse-Noisette', 'Casse-Noisette'),
            ('Le Lac des cygnes', 'Le Lac des cygnes'),
            ('La Belle au bois dormant (ballet)', 'La Belle au bois dormant (ballet)'),
            ('Concertos brandebourgeois', 'Concertos brandebourgeois'),
            ('Variations Goldberg', 'Variations Goldberg'),
            ("L'Art de la fugue", "L'Art de la fugue"),
            ('Le Messie', 'Le Messie (Haendel)'),
            ('Water Music', 'Water Music'),
            ('Symphonie du Nouveau Monde', 'Symphonie nº 9 de Dvořák'),
            ('Clair de lune (Debussy)', 'Clair de lune (Debussy)'),
            ("Prélude à l'après-midi d'un faune", "Prélude à l'après-midi d'un faune"),
            ('Gymnopédies', 'Gymnopédies'),
            ('Pierre et le Loup', 'Pierre et le Loup'),
            ('Le Beau Danube bleu', 'Le Beau Danube bleu'),
            ('Ave Maria (Schubert)', 'Ave Maria (Schubert)'),
            ('Carmina Burana', 'Carmina Burana'),
            ('Symphonie fantastique', 'Symphonie fantastique'),
            ('Roméo et Juliette (Prokofiev)', 'Roméo et Juliette (Prokofiev)'),
            ('Rhapsodie hongroise', 'Rhapsodie hongroise'),
            ('Ainsi parlait Zarathoustra (Strauss)', 'Ainsi parlait Zarathoustra (Strauss)'),
            ('Adagio pour cordes', 'Adagio pour cordes'),
            ('Le Carnaval des animaux', 'Le Carnaval des animaux'),
            ('Nocturnes de Chopin', 'Nocturnes de Chopin'),
            ('Symphonie nº 40 de Mozart', 'Symphonie nº 40 de Mozart'),
            ('Toccata et fugue en ré mineur', 'Toccata et fugue en ré mineur'),
            ('Messe en si mineur', 'Messe en si mineur'),
        ],
    ),
    'musique-populaire': dict(
        nom='Musique populaire',
        transferts=[],
        ajouts=[
            ('The Beatles', 'The Beatles'),
            ('Bob Dylan', 'Bob Dylan'),
            ('Elvis Presley', 'Elvis Presley'),
            ('Michael Jackson', 'Michael Jackson'),
            ('David Bowie', 'David Bowie'),
            ('Queen', 'Queen (groupe)'),
            ('Pink Floyd', 'Pink Floyd'),
            ('Led Zeppelin', 'Led Zeppelin'),
            ('The Rolling Stones', 'The Rolling Stones'),
            ('Jimi Hendrix', 'Jimi Hendrix'),
            ('Aretha Franklin', 'Aretha Franklin'),
            ('Nina Simone', 'Nina Simone'),
            ('Ray Charles', 'Ray Charles'),
            ('James Brown', 'James Brown'),
            ('Stevie Wonder', 'Stevie Wonder'),
            ('Bob Marley', 'Bob Marley'),
            ('Miles Davis', 'Miles Davis'),
            ('John Coltrane', 'John Coltrane'),
            ('Louis Armstrong', 'Louis Armstrong'),
            ('Ella Fitzgerald', 'Ella Fitzgerald'),
            ('Billie Holiday', 'Billie Holiday'),
            ('Frank Sinatra', 'Frank Sinatra'),
            ('Édith Piaf', 'Édith Piaf'),
            ('Jacques Brel', 'Jacques Brel'),
            ('Georges Brassens', 'Georges Brassens'),
            ('Serge Gainsbourg', 'Serge Gainsbourg'),
            ('Charles Aznavour', 'Charles Aznavour'),
            ('Barbara', 'Barbara (chanteuse)'),
            ('Léo Ferré', 'Léo Ferré'),
            ('Johnny Hallyday', 'Johnny Hallyday'),
            ('Daft Punk', 'Daft Punk'),
            ('Nirvana', 'Nirvana (groupe)'),
            ('Radiohead', 'Radiohead'),
            ('U2', 'U2'),
            ('Prince', 'Prince (musicien)'),
            ('Madonna', 'Madonna'),
            ('Whitney Houston', 'Whitney Houston'),
            ('Beyoncé', 'Beyoncé'),
            ('Amy Winehouse', 'Amy Winehouse'),
            ('Bruce Springsteen', 'Bruce Springsteen'),
            ('Johnny Cash', 'Johnny Cash'),
            ('The Doors', 'The Doors'),
            ('The Who', 'The Who'),
            ('AC/DC', 'AC/DC'),
            ('Metallica', 'Metallica'),
            ('Fela Kuti', 'Fela Kuti'),
            ('Cesária Évora', 'Cesária Évora'),
            ('Ravi Shankar', 'Ravi Shankar'),
            ('Björk', 'Björk'),
            ('Kraftwerk', 'Kraftwerk'),
            ('Chuck Berry', 'Chuck Berry'),
            ('Muddy Waters', 'Muddy Waters'),
            ('B.B. King', 'B.B. King'),
            ('Tupac Shakur', 'Tupac Shakur'),
            ('The Velvet Underground', 'The Velvet Underground'),
            ('Joni Mitchell', 'Joni Mitchell'),
            ('Leonard Cohen', 'Leonard Cohen'),
            ('Kate Bush', 'Kate Bush'),
            ('Talking Heads', 'Talking Heads'),
            ('Public Enemy', 'Public Enemy'),
        ],
    ),
    'sculptures-celebres': dict(
        nom='Sculptures célèbres',
        # La peinture avait deux collections, la sculpture aucune.
        transferts=[],
        ajouts=[
            ('Vénus de Milo', 'Vénus de Milo'),
            ('Victoire de Samothrace', 'Victoire de Samothrace'),
            ('David de Michel-Ange', 'David (Michel-Ange)'),
            ('Pietà', 'La Pietà (Michel-Ange)'),
            ('Le Penseur', 'Le Penseur'),
            ('Le Baiser de Rodin', 'Le Baiser (Rodin)'),
            ('Les Bourgeois de Calais', 'Les Bourgeois de Calais'),
            ('Discobole', 'Discobole'),
            ('Laocoon', 'Laocoon'),
            ('Colonne sans fin', 'Colonne sans fin'),
            ('Le Baiser de Brancusi', 'Le Baiser (Brancusi)'),
            ('Homme qui marche I', "L'Homme qui marche I"),
            ('Bronzes de Riace', 'Bronzes de Riace'),
            ('Buste de Néfertiti', 'Buste de Néfertiti'),
            ('Cariatides', 'Cariatides'),
            ('La Petite Danseuse de quatorze ans', 'La Petite Danseuse de quatorze ans'),
            ('Fontaine de Duchamp', 'Fontaine (Duchamp)'),
            ('Maman', 'Maman (sculpture)'),
            ('Cloud Gate', 'Cloud Gate'),
            ('Apollon et Daphné', 'Apollon et Daphné (Le Bernin)'),
            ("L'Extase de sainte Thérèse", "L'Extase de sainte Thérèse"),
            ('Christ des Abysses', 'Christ des Abysses'),
        ],
    ),
    'architectes': dict(
        nom='Architectes',
        # 79 monuments, et personne pour les avoir dessines.
        transferts=[],
        ajouts=[
            ('Antoni Gaudí', 'Antoni Gaudí'),
            ('Le Corbusier', 'Le Corbusier'),
            ('Frank Lloyd Wright', 'Frank Lloyd Wright'),
            ('Zaha Hadid', 'Zaha Hadid'),
            ('Oscar Niemeyer', 'Oscar Niemeyer'),
            ('Tadao Ando', 'Tadao Ando'),
            ('Mies van der Rohe', 'Ludwig Mies van der Rohe'),
            ('Walter Gropius', 'Walter Gropius'),
            ('Frank Gehry', 'Frank Gehry'),
            ('Renzo Piano', 'Renzo Piano'),
            ('Norman Foster', 'Norman Foster (architecte)'),
            ('Jean Nouvel', 'Jean Nouvel'),
            ('Rem Koolhaas', 'Rem Koolhaas'),
            ('Ieoh Ming Pei', 'I. M. Pei'),
            ('Alvar Aalto', 'Alvar Aalto'),
            ('Louis Kahn', 'Louis Kahn (architecte)'),
            ('Filippo Brunelleschi', 'Filippo Brunelleschi'),
            ('Andrea Palladio', 'Andrea Palladio'),
            ('Christopher Wren', 'Christopher Wren'),
            ('Viollet-le-Duc', 'Eugène Viollet-le-Duc'),
            ('Hector Guimard', 'Hector Guimard'),
            ('Auguste Perret', 'Auguste Perret'),
            ('Kenzo Tange', 'Kenzo Tange'),
            ('Santiago Calatrava', 'Santiago Calatrava'),
            ('Bjarke Ingels', 'Bjarke Ingels'),
            ('Sinan', 'Sinan'),
            ('Imhotep', 'Imhotep'),
            ('Louis Le Vau', 'Louis Le Vau'),
            ('Le Bernin', 'Le Bernin'),
        ],
    ),
    'champignons': dict(
        nom='Champignons',
        # Six collections animales, et pas un seul champignon.
        transferts=[],
        ajouts=[
            ('Amanite tue-mouches', 'Amanite tue-mouches'),
            ('Amanite phalloïde', 'Amanite phalloïde'),
            ('Cèpe de Bordeaux', 'Cèpe de Bordeaux'),
            ('Truffe', 'Truffe (champignon)'),
            ('Morille', 'Morille (champignon)'),
            ('Girolle', 'Girolle'),
            ('Coprin chevelu', 'Coprin chevelu'),
            ('Psilocybe', 'Psilocybe'),
            ('Pénicillium', 'Pénicillium'),
            ('Levure de boulanger', 'Levure de boulanger'),
            ('Champignon de Paris', 'Champignon de Paris'),
            ('Shiitake', 'Shiitake'),
            ('Pleurote en huître', 'Pleurote en huître'),
            ('Bolet Satan', 'Bolet Satan'),
            ('Vesse-de-loup', 'Vesse-de-loup'),
            ('Amadouvier', 'Amadouvier'),
            ('Polypore soufré', 'Polypore soufré'),
            ('Chanterelle', 'Chanterelle'),
            ('Trompette de la mort', 'Craterellus cornucopioides'),
            ('Russule charbonnière', 'Russule charbonnière'),
            ('Lactaire délicieux', 'Lactaire délicieux'),
            ('Rosé des prés', 'Rosé des prés'),
            ('Clitocybe', 'Clitocybe'),
            ('Phallus impudicus', 'Phallus impudicus'),
            ('Hydne hérisson', 'Hydne hérisson'),
            ('Reishi', 'Reishi'),
            ('Cordyceps', 'Cordyceps'),
            ('Armillaire', 'Armillaire'),
            ('Mycène', 'Mycène'),
            ('Scléroderme', 'Scleroderma'),
            ('Bolet bai', 'Bolet bai'),
            ('Enoki', 'Flammulina velutipes'),
            ('Aspergillus', 'Aspergillus'),
            ('Ergot du seigle', 'Claviceps purpurea'),
            ('Tricholome de la Saint-Georges', 'Tricholome de la Saint-Georges'),
        ],
    ),
    'arbres': dict(
        nom='Arbres',
        # 599 cartes d'animaux, zero plante : le regne vegetal commence ici.
        transferts=[],
        ajouts=[
            ('Chêne', 'Chêne'),
            ('Séquoia géant', 'Séquoia géant'),
            ('Baobab', 'Baobab'),
            ('Olivier', 'Olivier'),
            ('Hêtre', 'Fagus sylvatica'),
            ('Bouleau', 'Bouleau'),
            ('Pin sylvestre', 'Pin sylvestre'),
            ('Cèdre du Liban', 'Cèdre du Liban'),
            ('Ginkgo biloba', 'Ginkgo biloba'),
            ('Érable', 'Érable'),
            ('Saule pleureur', 'Saule pleureur'),
            ('Peuplier', 'Peuplier'),
            ('Frêne', 'Frêne'),
            ('Tilleul', 'Tilleul'),
            ('Châtaignier', 'Châtaignier'),
            ('Platane', 'Platane'),
            ('Cyprès', 'Cyprès'),
            ('If commun', 'If commun'),
            ('Épicéa commun', 'Épicéa commun'),
            ('Mélèze', 'Mélèze'),
            ('Eucalyptus', 'Eucalyptus'),
            ('Palmier dattier', 'Palmier dattier'),
            ('Cocotier', 'Cocotier'),
            ('Bambou', 'Bambou'),
            ('Acacia', 'Acacia (genre)'),
            ('Marronnier', 'Marronnier'),
            ('Noyer', 'Noyer'),
            ('Orme', 'Orme'),
            ('Aulne', 'Aulne'),
            ('Charme commun', 'Charme commun'),
            ('Sapin', 'Sapin'),
            ('Pin parasol', 'Pin parasol'),
            ('Araucaria', 'Araucaria'),
            ("Séquoia à feuilles d'if", "Séquoia à feuilles d'if"),
            ('Dragonnier', 'Dragonnier'),
            ('Manguier', 'Manguier'),
            ('Figuier des banians', 'Ficus benghalensis'),
            ('Cacaoyer', 'Cacaoyer'),
            ('Caféier', 'Caféier'),
            ('Hévéa', 'Hévéa'),
        ],
    ),
    'fleurs': dict(
        nom='Fleurs',
        # Suite du regne vegetal, apres les arbres.
        transferts=[],
        ajouts=[
            ('Rose', 'Rose (fleur)'),
            ('Tulipe', 'Tulipe'),
            ('Tournesol', 'Tournesol'),
            ('Orchidée', 'Orchidée'),
            ('Lys', 'Lys'),
            ('Pivoine', 'Pivoine'),
            ('Marguerite', 'Leucanthemum vulgare'),
            ('Coquelicot', 'Coquelicot'),
            ('Lavande', 'Lavande'),
            ('Jasmin', 'Jasmin'),
            ('Iris', 'Iris (genre végétal)'),
            ('Muguet', 'Muguet de mai'),
            ('Violette', 'Violette'),
            ('Œillet', 'Œillet'),
            ('Chrysanthème', 'Chrysanthème'),
            ('Dahlia', 'Dahlia'),
            ('Hortensia', 'Hortensia'),
            ('Camélia', 'Camélia'),
            ('Magnolia', 'Magnolia'),
            ('Glycine', 'Wisteria'),
            ('Bougainvillier', 'Bougainvillier'),
            ('Hibiscus', 'Hibiscus'),
            ('Nénuphar', 'Nénuphar'),
            ('Lotus sacré', 'Lotus sacré'),
            ('Edelweiss', 'Edelweiss'),
            ('Bleuet', 'Centaurea cyanus'),
            ('Pensée', 'Pensée (fleur)'),
            ('Jonquille', 'Jonquille'),
            ('Crocus', 'Crocus'),
            ('Bruyère', 'Bruyère'),
            ('Mimosa', 'Acacia dealbata'),
            ('Cerisier du Japon', 'Cerisier du Japon'),
            ('Frangipanier', 'Plumeria'),
            ('Rafflesia', 'Rafflesia'),
            ('Arum', 'Arum'),
            ('Gentiane', 'Gentiane'),
            ('Digitale pourpre', 'Digitale pourpre'),
            ("Bouton-d'or", "Bouton-d'or"),
            ('Pissenlit', 'Pissenlit'),
            ('Chardon', 'Chardon'),
        ],
    ),
    'plantes-cultivees': dict(
        nom='Plantes cultivées',
        # Ce que l'humanite mange et cultive : le pendant agricole des arbres.
        transferts=[],
        ajouts=[
            ('Blé', 'Blé'),
            ('Riz', 'Riz'),
            ('Maïs', 'Maïs'),
            ('Pomme de terre', 'Pomme de terre'),
            ('Tomate', 'Tomate'),
            ('Vigne', 'Vigne'),
            ('Canne à sucre', 'Canne à sucre'),
            ('Soja', 'Soja'),
            ('Coton', 'Coton'),
            ('Lin', 'Lin cultivé'),
            ('Café', 'Café'),
            ('Cacao', 'Cacao'),
            ('Thé', 'Thé'),
            ('Tabac', 'Tabac'),
            ('Poivre noir', 'Poivre noir'),
            ('Vanille', 'Vanille'),
            ('Safran', 'Safran (épice)'),
            ('Cannelle', 'Cannelle'),
            ('Piment', 'Piment'),
            ('Ail', 'Allium sativum'),
            ('Oignon', 'Oignon'),
            ('Carotte', 'Carotte'),
            ('Chou', 'Brassica oleracea'),
            ('Haricot', 'Haricot'),
            ('Pois', 'Pois'),
            ('Lentille', 'Lentille cultivée'),
            ('Banane', 'Banane'),
            ('Pomme', 'Pomme'),
            ('Orange', 'Orange (fruit)'),
            ('Citron', 'Citron'),
            ('Fraise', 'Fraise'),
            ('Raisin', 'Raisin'),
            ('Melon', 'Melon (plante)'),
            ('Courge', 'Courge'),
            ('Aubergine', 'Aubergine'),
            ('Concombre', 'Concombre'),
            ('Betterave', 'Betterave'),
            ('Colza', 'Colza'),
            ('Orge', 'Orge commune'),
        ],
    ),
    'fromages': dict(
        nom='Fromages',
        # La gastronomie n'avait aucune carte.
        transferts=[],
        ajouts=[
            ('Camembert', 'Camembert (fromage)'),
            ('Roquefort', 'Roquefort (fromage)'),
            ('Brie de Meaux', 'Brie de Meaux'),
            ('Comté', 'Comté (fromage)'),
            ('Beaufort', 'Beaufort (fromage)'),
            ('Reblochon', 'Reblochon'),
            ('Munster', 'Munster (fromage)'),
            ('Époisses', 'Époisses'),
            ('Maroilles', 'Maroilles (fromage)'),
            ('Cantal', 'Cantal (fromage)'),
            ('Saint-Nectaire', 'Saint-Nectaire'),
            ("Bleu d'Auvergne", "Bleu d'Auvergne"),
            ("Fourme d'Ambert", "Fourme d'Ambert"),
            ('Crottin de Chavignol', 'Crottin de Chavignol'),
            ('Mimolette', 'Mimolette'),
            ('Tomme de Savoie', 'Tomme de Savoie'),
            ('Morbier', 'Morbier (fromage)'),
            ('Livarot', 'Livarot (fromage)'),
            ('Parmigiano Reggiano', 'Parmigiano Reggiano'),
            ('Mozzarella', 'Mozzarella'),
            ('Gorgonzola', 'Gorgonzola (fromage)'),
            ('Pecorino romano', 'Pecorino romano'),
            ('Ricotta', 'Ricotta'),
            ('Cheddar', 'Cheddar'),
            ('Stilton', 'Stilton (fromage)'),
            ('Gouda', 'Gouda (fromage)'),
            ('Édam', 'Edam (fromage)'),
            ('Emmental', 'Emmental'),
            ('Gruyère', 'Gruyère (fromage)'),
            ('Feta', 'Feta'),
            ('Manchego', 'Manchego'),
            ('Halloumi', 'Halloumi'),
            ('Mascarpone', 'Mascarpone'),
            ('Burrata', 'Burrata'),
            ('Raclette', 'Raclette (fromage)'),
            ('Bleu de Gex', 'Bleu de Gex'),
            ('Ossau-Iraty', 'Ossau-Iraty'),
            ('Vacherin', 'Vacherin (fromage)'),
        ],
    ),
    'plats-francais': dict(
        nom='Plats français',
        # La table francaise, absente jusqu'ici.
        transferts=[],
        ajouts=[
            ('Pot-au-feu', 'Pot-au-feu'),
            ('Bœuf bourguignon', 'Bœuf bourguignon'),
            ('Blanquette de veau', 'Blanquette de veau'),
            ('Coq au vin', 'Coq au vin'),
            ('Cassoulet', 'Cassoulet'),
            ('Choucroute garnie', 'Choucroute garnie'),
            ('Bouillabaisse', 'Bouillabaisse'),
            ('Ratatouille (plat)', 'Ratatouille'),
            ('Quiche lorraine', 'Quiche lorraine'),
            ('Croque-monsieur', 'Croque-monsieur'),
            ('Steak frites', 'Steak frites'),
            ('Gratin dauphinois', 'Gratin dauphinois'),
            ("Soupe à l'oignon", "Soupe à l'oignon"),
            ('Escargots de Bourgogne', 'Escargots de Bourgogne'),
            ('Foie gras', 'Foie gras'),
            ('Confit de canard', 'Confit de canard'),
            ('Andouillette', 'Andouillette'),
            ('Cuisses de grenouille', 'Cuisses de grenouille'),
            ('Aligot', 'Aligot'),
            ('Tartiflette', 'Tartiflette'),
            ('Fondue savoyarde', 'Fondue savoyarde'),
            ('Crêpe', 'Crêpe'),
            ('Galette de sarrasin', 'Galette de sarrasin'),
            ('Baguette', 'Baguette (pain)'),
            ('Croissant', 'Croissant (viennoiserie)'),
            ('Pain au chocolat', 'Pain au chocolat'),
            ('Macaron', 'Macaron'),
            ('Éclair', 'Éclair (pâtisserie)'),
            ('Mille-feuille', 'Mille-feuille'),
            ('Paris-brest', 'Paris-brest'),
            ('Tarte Tatin', 'Tarte Tatin'),
            ('Crème brûlée', 'Crème brûlée'),
            ('Profiterole', 'Profiterole'),
            ('Clafoutis', 'Clafoutis'),
            ('Madeleine', 'Madeleine (pâtisserie)'),
            ('Canelé', 'Canelé'),
            ('Baba au rhum', 'Baba au rhum'),
            ('Salade niçoise', 'Salade niçoise'),
            ('Rillettes', 'Rillettes'),
            ('Pâté en croûte', 'Pâté en croûte'),
            ('Cervelle de canut', 'Cervelle de canut'),
            ('Piperade', 'Piperade'),
            ('Garbure', 'Garbure'),
            ('Brandade de morue', 'Brandade de morue'),
            ('Bouchée à la reine', 'Bouchée à la reine'),
            ('Œufs en meurette', 'Œufs en meurette'),
            ('Sole meunière', 'Sole meunière'),
            ('Steak tartare', 'Steak tartare'),
            ('Hachis parmentier', 'Hachis parmentier'),
            ('Soufflé', 'Soufflé'),
            ('Galette des Rois', 'Galette des Rois'),
            ('Bûche de Noël', 'Bûche de Noël'),
            ('Kouign-amann', 'Kouign-amann'),
            ('Far breton', 'Far breton'),
            ('Tarte flambée', 'Tarte flambée'),
            ('Socca', 'Socca'),
            ('Pissaladière', 'Pissaladière'),
            ('Pieds paquets', 'Pieds paquets'),
            ('Poule au pot', 'Poule au pot'),
        ],
    ),
    'cuisines-du-monde': dict(
        nom='Cuisines du monde',
        # Le pendant international des plats francais.
        transferts=[],
        ajouts=[
            ('Pizza', 'Pizza'),
            ('Sushi', 'Sushi'),
            ('Ramen', 'Ramen'),
            ('Paella', 'Paella'),
            ('Couscous', 'Couscous'),
            ('Curry', 'Curry'),
            ('Tacos', 'Tacos'),
            ('Ceviche', 'Ceviche'),
            ('Falafel', 'Falafel'),
            ('Houmous', 'Houmous'),
            ('Kebab', 'Kebab'),
            ('Tajine', 'Tajine'),
            ('Pho', 'Pho'),
            ('Pad thaï', 'Pad thaï'),
            ('Dim sum', 'Dim sum'),
            ('Canard laqué de Pékin', 'Canard laqué de Pékin'),
            ('Bibimbap', 'Bibimbap'),
            ('Kimchi', 'Kimchi'),
            ('Tempura', 'Tempura'),
            ('Sashimi', 'Sashimi'),
            ('Risotto', 'Risotto'),
            ('Lasagnes', 'Lasagnes'),
            ('Gnocchi', 'Gnocchi'),
            ('Osso buco', 'Osso buco'),
            ('Tiramisu', 'Tiramisu'),
            ('Crème glacée', 'Crème glacée'),
            ('Fish and chips', 'Fish and chips'),
            ('Hamburger', 'Hamburger'),
            ('Hot-dog', 'Hot-dog'),
            ('Barbecue', 'Barbecue'),
            ('Chili con carne', 'Chili con carne'),
            ('Guacamole', 'Guacamole'),
            ('Burrito', 'Burrito'),
            ('Empanada', 'Empanada'),
            ('Feijoada', 'Feijoada'),
            ('Asado', 'Asado'),
            ('Arepa', 'Arepa'),
            ('Moussaka', 'Moussaka'),
            ('Souvlaki', 'Souvlaki'),
            ('Tzatziki', 'Tzatziki'),
            ('Baklava', 'Baklava'),
            ('Chachlik', 'Chachlik'),
            ('Bortsch', 'Bortsch'),
            ('Pierogi', 'Pierogi'),
            ('Goulash', 'Goulash'),
            ('Escalope à la viennoise', 'Escalope viennoise'),
            ('Bretzel', 'Bretzel'),
            ('Poutine', 'Poutine (plat)'),
            ('Injera', 'Injera'),
            ('Bunny chow', 'Bunny chow'),
            ('Biryani', 'Biryani'),
            ('Naan', 'Naan'),
            ('Samoussa', 'Samoussa'),
            ('Tandoori', 'Tandoori'),
            ('Nasi goreng', 'Nasi goreng'),
            ('Satay', 'Satay'),
            ('Laksa', 'Laksa'),
            ('Mole poblano', 'Mole poblano'),
            ('Congee', 'Congee'),
            ('Mochi', 'Mochi'),
            ('Okonomiyaki', 'Okonomiyaki'),
            ('Baozi', 'Baozi'),
            ('Wonton', 'Wonton'),
            ('Katsudon', 'Katsudon'),
        ],
    ),
    'objets-mythiques': dict(
        nom='Objets mythiques',
        transferts=[('mythologie-nordique', 'Mjöllnir')],
        ajouts=[
            ('Arche de Noé', 'Arche de Noé'),
            ("Arche d'alliance", "Arche d'alliance"),
            ('Excalibur', 'Excalibur'),
            ('Graal', 'Graal'),
            ('Table ronde', 'Table ronde'),
            ('Durandal', 'Durandal'),
            ('Joyeuse', 'Joyeuse (épée)'),
            ("Toison d'or", "Toison d'or"),
            ('Cheval de Troie', 'Cheval de Troie'),
            ('Boîte de Pandore', 'Boîte de Pandore'),
            ('Égide', 'Égide'),
            ('Caducée', 'Caducée'),
            ("Corne d'abondance", "Corne d'abondance"),
            ('Gungnir', 'Gungnir'),
            ('Draupnir', 'Draupnir'),
            ('Vajra', 'Vajra'),
            ('Sampo', 'Sampo'),
            ('Bâton de Moïse', 'Bâton de Moïse'),
            ('Pierre philosophale', 'Pierre philosophale'),
        ],
        # Écartés : Kusanagi, dont le titre mène à « Tsurugi », le type d'arme ;
        # la lampe merveilleuse, qui mène au conte ; l'épée de Damoclès, qui
        # mène au personnage.
    ),
}


# ------------------------------------------------------------------- outillage

def periode():
    fin = date.today().replace(day=1) - timedelta(days=1)
    return ((fin.replace(day=1) - timedelta(days=360)).replace(day=1).strftime('%Y%m%d'),
            fin.strftime('%Y%m%d'))


DEBUT, FIN = periode()


def pageviews(titre):
    art = urllib.parse.quote(titre.replace(' ', '_'), safe='')
    url = ('https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/'
           f'fr.wikipedia/all-access/user/{art}/monthly/{DEBUT}/{FIN}')
    if url in _pv:
        return _pv[url]
    total = 0
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                total = sum(x.get('views', 0) for x in
                            json.loads(r.read().decode('utf-8')).get('items', []))
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                break
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    _pv[url] = total
    time.sleep(0.03)
    return total


def slugifier(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def lien(titre):
    return 'https://fr.wikipedia.org/wiki/' + urllib.parse.quote(titre.replace(' ', '_'))


def norm(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '', s)


def main():
    cles = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not cles or cles[0] not in PLANS:
        sys.exit('clé attendue : ' + ' | '.join(PLANS))
    cle, plan = cles[0], PLANS[cles[0]]
    essai = '--essai' in sys.argv

    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    notes = json.loads((RACINE / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))
    sources = json.loads((RACINE / 'build' / 'images_sources.json').read_text(encoding='utf-8'))
    charges, touches, signalements = {}, set(), []
    cartes, pris = [], set()

    # --- transferts
    for slug, nom in plan['transferts']:
        d = charges.setdefault(slug, json.loads(par_slug[slug].read_text(encoding='utf-8')))
        c = next((x for x in d['cartes'] if x['nom'] == nom), None)
        if c is None:
            signalements.append(f'{slug} · « {nom} » introuvable')
            continue
        ancien = c['id']
        fslug = ancien.split('_', 1)[1]
        nouveau = f'{cle}_{fslug}'
        pris.add(nouveau)
        if not essai:
            for rep in ('full', 'thumbs', 'originaux'):
                a = RACINE / 'images' / rep / slug / f'{fslug}.webp'
                if a.exists():
                    b = RACINE / 'images' / rep / cle / f'{fslug}.webp'
                    b.parent.mkdir(parents=True, exist_ok=True)
                    a.replace(b)
        if ancien in notes.get('cadrages', {}):
            notes['cadrages'][nouveau] = notes['cadrages'].pop(ancien)
        if ancien in sources:
            sources[nouveau] = sources.pop(ancien)
        for n in notes.get('notes', []):
            n['images'] = [nouveau if i == ancien else i for i in n.get('images', [])]
        c.update(id=nouveau, collection=plan['nom'],
                 imageUrl=f'images/full/{cle}/{fslug}.webp',
                 thumbUrl=f'images/thumbs/{cle}/{fslug}.webp')
        c.pop('tags', None)
        c.pop('liensSortants', None)
        d['cartes'] = [x for x in d['cartes'] if x is not c]
        cartes.append(c)
        touches.add(slug)
        print(f'  {slug} -> {cle} : {nom}')

    # --- créations
    # Consigne 5 : un nom deja pris ailleurs dans le jeu n'est pas recree, il
    # est signale. Les collections thematiques se recoupent beaucoup — le
    # Colosse de Rhodes est deja une merveille, Michel-Ange deja un peintre.
    # La collection en cours est EXCLUE du releve : elle est reconstruite de
    # zero a chaque execution, donc ses propres cartes ne sont pas des
    # homonymes. Sans cette exclusion, rejouer une collection la vidait.
    pris_partout = {}
    for c in idx['collections']:
        if c['slug'] == cle:
            continue
        for x in json.loads((RACINE / c['fichier']).read_text(encoding='utf-8'))['cartes']:
            pris_partout[norm(x['nom'])] = (c['slug'], x['nom'])
    R.charger_fiches([t for _, t in plan['ajouts']])
    for nom, titre in plan['ajouts']:
        deja = pris_partout.get(norm(nom))
        if deja:
            signalements.append(f'« {nom} » : homonyme de {deja[0]} · {deja[1]}, '
                                'non créée')
            continue
        f = R._cache.get('fiche:' + titre)
        if not f or f['statut'] != 'ok' or not f.get('extrait'):
            signalements.append(f'« {nom} » : page « {titre} » non résolue')
            continue
        fslug = slugifier(f['titre'])
        while f'{cle}_{fslug}' in pris:
            fslug += '-b'
        pris.add(f'{cle}_{fslug}')
        cartes.append({
            'id': f'{cle}_{fslug}', 'nom': nom, 'titrePage': f['titre'],
            'imageUrl': f'images/full/{cle}/{fslug}.webp',
            'thumbUrl': f'images/thumbs/{cle}/{fslug}.webp',
            'description': f['extrait'], 'collection': plan['nom'],
            'lienWikipedia': lien(f['titre']), 'tags': [], 'numero': 0,
        })

    for c in cartes:
        c['pageviews'] = pageviews(c['titrePage'])
    CACHE_PV.write_bytes(pickle.dumps(_pv))

    charges[cle] = {'collection': plan['nom'], 'slug': cle, 'cartes': cartes}
    touches.add(cle)
    for slug in sorted(touches):
        lot = charges[slug]['cartes']
        paliers, rangs = rarete_pv.raretes([c.get('pageviews', 0) for c in lot])
        for c, p, r in zip(lot, paliers, rangs):
            if not c.get('rareteManuel'):
                c['rarete'], c['pv'] = p, rarete_pv.pv(r)
        for i, c in enumerate(lot, 1):
            c['numero'] = i
        print(f'  {slug:<32} {len(lot)} cartes')
    for s in signalements:
        print(' •', s)
    if essai:
        print('[essai] rien écrit')
        return

    for slug in touches:
        chemin = par_slug.get(slug, RACINE / 'data' / f'{slug}.json')
        chemin.write_text(json.dumps(charges[slug], ensure_ascii=False), encoding='utf-8')
        entree = next((e for e in idx['collections'] if e['slug'] == slug), None)
        if entree:
            entree['nbCartes'] = len(charges[slug]['cartes'])
        else:
            idx['collections'].append({'slug': slug, 'nom': plan['nom'],
                                       'nbCartes': len(charges[slug]['cartes']),
                                       'fichier': f'data/{slug}.json'})
    (RACINE / 'data' / 'collections.json').write_text(
        json.dumps(idx, ensure_ascii=False, indent=1), encoding='utf-8')
    (RACINE / 'build' / 'notes_atelier.json').write_text(
        json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
    (RACINE / 'build' / 'images_sources.json').write_text(
        json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'{len(idx["collections"])} collections')


if __name__ == '__main__':
    main()
