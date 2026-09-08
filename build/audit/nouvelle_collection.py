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
    'philosophes': dict(
        nom='Philosophes',
        # La philosophie n'avait pas de collection : elle etait rangee par
        # metier d'appoint. Aristote et Descartes chez les scientifiques,
        # Voltaire et Seneque chez les auteurs. Les quatre transferts sont ceux
        # dont la page fr dit « philosophe » en premier — Hypatie comprise,
        # « philosophe neoplatonicienne, astronome et mathematicienne ».
        # Restent aux sciences Bourdieu, Durkheim, Weber et Adam Smith, qui
        # sont sociologues et economistes ; restent aux auteurs Ciceron,
        # Voltaire, Rousseau, Confucius, Seneque, Sartre et Camus, qu'on lit
        # comme ecrivains. Avicenne et Leibniz sont deja au jeu sous « Ibn
        # Sina » et « Gottfried Leibniz » : les reprendre doublerait la
        # personne.
        transferts=[('scientifiques-celebres', 'Aristote'),
                    ('scientifiques-celebres', 'René Descartes'),
                    ('scientifiques-celebres', 'Karl Marx'),
                    ('scientifiques-celebres', 'Hypatie')],
        ajouts=[
            # Antiquite grecque et romaine
            ('Socrate', 'Socrate'),
            ('Platon', 'Platon'),
            ('Héraclite', 'Héraclite'),
            ('Parménide', 'Parménide'),
            ('Démocrite', 'Démocrite'),
            ('Épicure', 'Épicure'),
            ('Diogène de Sinope', 'Diogène de Sinope'),
            ('Zénon de Kition', 'Zénon de Kition'),
            ('Plotin', 'Plotin'),
            ('Épictète', 'Épictète'),
            # Pensees d'Asie
            ('Lao Tseu', 'Lao Tseu'),
            # « Zhuangzi » sans parenthese est le LIVRE, pas l'auteur
            ('Zhuangzi', 'Tchouang-tseu'),
            ('Mencius', 'Mencius'),
            ('Nagarjuna', 'Nagarjuna'),
            ('Adi Shankara', 'Adi Shankara'),
            # Monde medieval chretien, juif et musulman
            ('Saint Augustin', "Augustin d'Hippone"),
            ("Thomas d'Aquin", "Thomas d'Aquin"),
            ('Maïmonide', 'Moïse Maïmonide'),
            ('Al-Ghazali', 'Al-Ghazali'),
            ('Ibn Khaldoun', 'Ibn Khaldoun'),
            ("Guillaume d'Ockham", "Guillaume d'Ockham"),
            # Age classique et Lumieres
            ('Machiavel', 'Nicolas Machiavel'),
            ('Thomas Hobbes', 'Thomas Hobbes'),
            ('Baruch Spinoza', 'Baruch Spinoza'),
            ('John Locke', 'John Locke'),
            ('David Hume', 'David Hume'),
            ('Montesquieu', 'Montesquieu'),
            ('Emmanuel Kant', 'Emmanuel Kant'),
            ('John Stuart Mill', 'John Stuart Mill'),
            # Les femmes de la philosophie moderne, absentes de ma premiere
            # liste : elle comptait cinquante noms et deux femmes.
            ('Mary Wollstonecraft', 'Mary Wollstonecraft'),
            ('Élisabeth de Bohême', 'Élisabeth de Bohême (1618-1680)'),
            ('Anne Conway', 'Anne Conway'),
            # XIXe siecle
            ('Hegel', 'Georg Wilhelm Friedrich Hegel'),
            ('Arthur Schopenhauer', 'Arthur Schopenhauer'),
            ('Søren Kierkegaard', 'Søren Kierkegaard'),
            ('Friedrich Nietzsche', 'Friedrich Nietzsche'),
            # XXe siecle
            ('Henri Bergson', 'Henri Bergson'),
            ('Edmund Husserl', 'Edmund Husserl'),
            ('Bertrand Russell', 'Bertrand Russell'),
            ('Ludwig Wittgenstein', 'Ludwig Wittgenstein'),
            ('Martin Heidegger', 'Martin Heidegger'),
            ('Karl Popper', 'Karl Popper'),
            ('Hannah Arendt', 'Hannah Arendt'),
            ('Maurice Merleau-Ponty', 'Maurice Merleau-Ponty'),
            ('Simone Weil', 'Simone Weil'),
            ('Elizabeth Anscombe', 'Elizabeth Anscombe'),
            ('Philippa Foot', 'Philippa Foot'),
            ('Michel Foucault', 'Michel Foucault'),
            ('Jacques Derrida', 'Jacques Derrida'),
            ('Gilles Deleuze', 'Gilles Deleuze'),
            ('Jürgen Habermas', 'Jürgen Habermas'),
            # « John Rawls » sans parenthese est un homonyme
            ('John Rawls', 'John Rawls (philosophe)'),
            ('Martha Nussbaum', 'Martha Nussbaum'),
            ('Judith Butler', 'Judith Butler'),
            ('Donna Haraway', 'Donna Haraway'),
        ],
        # Ecartes : Iris Murdoch, Susan Sontag et Christine de Pizan, dont la
        # page dit « ecrivain » d'abord ; Rosa Luxemburg et Angela Davis,
        # militantes ; Therese d'Avila et Hildegarde de Bingen, mystiques ;
        # Emilie du Chatelet, deja carte et physicienne ; Ban Zhao,
        # historienne ; Diotime, sans page et d'existence douteuse.
    ),
    'figures-religieuses': dict(
        nom='Fondateurs et figures religieuses',
        # « Croyances et notions sacrees » traite des notions : karma, samsara,
        # yin et yang. Les PERSONNES n'existaient nulle part. Ni Jesus, ni
        # Bouddha, ni Mahomet, ni Moise. C'etait le trou le plus net du jeu.
        # Ecartes : Rumi, deja carte chez les auteurs classiques ou il est a sa
        # place de poete ; Averroes, Al-Ghazali, Augustin, Thomas d'Aquin et
        # Ibn Khaldoun, deja aux sciences ou a la philosophie ; Salomon, qui
        # est un roi et releve des souverains.
        transferts=[],
        ajouts=[
            # Fondateurs et prophetes
            ('Jésus', 'Jésus de Nazareth'),
            ('Bouddha', 'Siddhartha Gautama'),
            ('Mahomet', 'Mahomet'),
            ('Moïse', 'Moïse'),
            ('Abraham', 'Abraham'),
            ('Zarathoustra', 'Zoroastre'),
            ('Mahâvîra', 'Mahāvīra'),
            ('Guru Nanak', 'Guru Nanak'),
            # le titre porte une lettre modificative, pas une apostrophe
            ('Bahaullah', "Baháʼu'lláh"),
            ('Joseph Smith', 'Joseph Smith'),
            ('Mani', 'Mani (prophète)'),
            # Judaisme
            ('Hillel', 'Hillel Hazaken'),
            ('Baal Shem Tov', 'Baal Shem Tov'),
            # Christianisme des origines
            ('Paul de Tarse', 'Paul de Tarse'),
            ('Pierre (apôtre)', 'Pierre (apôtre)'),
            ('Marie (mère de Jésus)', 'Marie (mère de Jésus)'),
            ('Jean le Baptiste', 'Jean le Baptiste'),
            ('Marie Madeleine', 'Marie Madeleine'),
            # Saints, moines et reformateurs chretiens
            ("François d'Assise", "François d'Assise"),
            ("Jeanne d'Arc", "Jeanne d'Arc"),
            ('Martin Luther', 'Martin Luther'),
            ('Jean Calvin', 'Jean Calvin'),
            ('Ignace de Loyola', 'Ignace de Loyola'),
            ("Thérèse d'Avila", "Thérèse d'Avila"),
            ('Hildegarde de Bingen', 'Hildegarde de Bingen'),
            ('Mère Teresa', 'Mère Teresa'),
            ('Jean-Paul II', 'Jean-Paul II'),
            ('Benoît de Nursie', 'Benoît de Nursie'),
            ('Bernard de Clairvaux', 'Bernard de Clairvaux'),
            ('Savonarole', 'Jérôme Savonarole'),
            ('Grégoire Ier', 'Grégoire Ier'),
            ('Cyrille et Méthode', 'Cyrille et Méthode'),
            ('Sainte Geneviève', 'Geneviève de Paris'),
            ('Saint Nicolas', 'Nicolas de Myre'),
            ('Saint Patrick', "Patrick d'Irlande"),
            # Islam
            ('Ali ibn Abi Talib', 'Ali ibn Abi Talib'),
            ('Abou Bakr', 'Abou Bakr As-Siddiq'),
            ('Fatima Zahra', 'Fatima Zahra'),
            ('Ibn Arabi', 'Ibn Arabi'),
            ('Aïcha', 'Aïcha'),
            ('Rabia al-Adawiyya', 'Rabia al Adawiyya'),
            # Bouddhisme et hindouisme
            ('Bodhidharma', 'Bodhidharma'),
            ('Dalaï-lama', 'Tenzin Gyatso'),
            ('Milarepa', 'Milarepa'),
            ('Padmasambhava', 'Padmasambhava'),
            ('Nichiren', 'Nichiren'),
            ('Kukai', 'Kūkai'),
            ('Ramakrishna', 'Râmakrishna'),
            ('Vivekananda', 'Vivekananda'),
        ],
    ),
    'figures-emancipation': dict(
        nom="Figures de l'émancipation",
        # Les revolutionnaires devenus chefs d'Etat etaient chez les dirigeants
        # contemporains : Gandhi, Mandela, Lenine, Mao, Bolivar, Robespierre,
        # Toussaint Louverture, Lumumba, Sankara, Nkrumah, Ho Chi Minh. Ceux
        # qui n'ont jamais pris le pouvoir n'etaient nulle part. La regle 5
        # interdit de dedoubler les premiers : ils ne sont pas repris ici.
        # Ecarte aussi Aime Cesaire, poete avant tout, qui manque aux auteurs
        # modernes, et Andrei Sakharov, deja carte chez les scientifiques.
        transferts=[],
        ajouts=[
            # Esclavage, segregation, droits civiques
            ('Martin Luther King', 'Martin Luther King'),
            ('Malcolm X', 'Malcolm X'),
            ('Rosa Parks', 'Rosa Parks'),
            ('Frederick Douglass', 'Frederick Douglass'),
            ('Harriet Tubman', 'Harriet Tubman'),
            ('Sojourner Truth', 'Sojourner Truth'),
            ('W. E. B. Du Bois', 'W. E. B. Du Bois'),
            ('Ida B. Wells', 'Ida B. Wells'),
            ('Nat Turner', 'Nat Turner'),
            ('Angela Davis', 'Angela Davis'),
            ('William Wilberforce', 'William Wilberforce'),
            ('Victor Schœlcher', 'Victor Schœlcher'),
            ('Ruth Bader Ginsburg', 'Ruth Bader Ginsburg'),
            # Apartheid
            ('Steve Biko', 'Steve Biko'),
            ('Desmond Tutu', 'Desmond Tutu'),
            ('Winnie Mandela', 'Winnie Mandela'),
            # Droits des femmes
            ('Olympe de Gouges', 'Olympe de Gouges'),
            ('Emmeline Pankhurst', 'Emmeline Pankhurst'),
            ('Emily Davison', 'Emily Davison'),
            ('Susan B. Anthony', 'Susan B. Anthony'),
            ('Elizabeth Cady Stanton', 'Elizabeth Cady Stanton'),
            ('Simone Veil', 'Simone Veil'),
            ('Gisèle Halimi', 'Gisèle Halimi'),
            ('Louise Michel', 'Louise Michel'),
            ('Flora Tristan', 'Flora Tristan'),
            ('Clara Zetkin', 'Clara Zetkin'),
            ('Rosa Luxemburg', 'Rosa Luxemburg'),
            ('Malala Yousafzai', 'Malala Yousafzai'),
            # Peuples autochtones
            ('Sitting Bull', 'Sitting Bull'),
            ('Geronimo', 'Geronimo'),
            # « Crazy Horse » seul est le cabaret parisien
            ('Crazy Horse', 'Crazy Horse (chef amérindien)'),
            ('Chef Joseph', 'Chef Joseph'),
            ('Rigoberta Menchú', 'Rigoberta Menchú'),
            # Decolonisation et anticolonialisme
            ('Frantz Fanon', 'Frantz Fanon'),
            ('Amílcar Cabral', 'Amílcar Cabral'),
            ('Emiliano Zapata', 'Emiliano Zapata'),
            ('Pancho Villa', 'Pancho Villa'),
            ('Che Guevara', 'Che Guevara'),
            # Castes, travail, environnement
            ('Bhimrao Ramji Ambedkar', 'Bhimrao Ramji Ambedkar'),
            ('César Chávez', 'César Chávez'),
            ('Dolores Huerta', 'Dolores Huerta'),
            ('Wangari Maathai', 'Wangari Muta Maathai'),
            # Dissidence dans le bloc de l'Est
            ('Lech Wałęsa', 'Lech Wałęsa'),
            ('Václav Havel', 'Václav Havel'),
            ('Aung San Suu Kyi', 'Aung San Suu Kyi'),
            # Droits LGBT
            ('Harvey Milk', 'Harvey Milk'),
            ('Marsha P. Johnson', 'Marsha P. Johnson'),
            ('Sylvia Rivera', 'Sylvia Rivera'),
        ],
    ),
    'photographies-celebres': dict(
        nom='Photographies célèbres',
        # Le jeu avait les tableaux, les sculptures et les films, mais pas la
        # photographie. Collection volontairement courte : n'y entrent que les
        # images qui ont leur PROPRE page sur fr.wikipedia. Beaucoup de photos
        # celebres n'ont que la page de leur sujet : Sharbat Gula pour « la
        # jeune fille afghane », Kim Phuc pour la petite fille au napalm,
        # Nguyen Van Lem pour l'execution de Saigon. Prendre ces pages ferait
        # des cartes de personne deguisees en cartes de photo.
        transferts=[],
        ajouts=[
            # Les commencements
            ('Point de vue du Gras', 'Point de vue du Gras'),
            ('Boulevard du Temple', 'Boulevard du Temple'),
            ('La Table servie', 'La Table servie'),
            # Guerre et pouvoir
            ("Mort d'un soldat républicain", "Mort d'un soldat républicain"),
            ('Raising the Flag on Iwo Jima', 'Raising the Flag on Iwo Jima'),
            ('Le Drapeau rouge sur le Reichstag', 'Le Drapeau rouge sur le Reichstag'),
            ('V-J Day in Times Square', 'V-J Day in Times Square'),
            ('Samedi sanglant', 'Samedi sanglant'),
            ('Tank Man', 'Tank Man'),
            ('The Falling Man', 'The Falling Man'),
            ('La Fillette et le Vautour', 'La Fillette et le Vautour'),
            ('La Fille à la fleur', 'La Fille à la fleur'),
            ('Guerrillero Heroico', 'Guerrillero Heroico'),
            # Le travail et la rue
            ('Migrant Mother', 'Migrant Mother'),
            ('Lunch atop a Skyscraper', 'Lunch atop a Skyscraper'),
            ("Le Baiser de l'hôtel de ville", "Le Baiser de l'hôtel de ville"),
            ('Moonrise, Hernandez, New Mexico', 'Moonrise, Hernandez, New Mexico'),
            # La science regarde
            ('Photo 51', 'Photo 51'),
            ('Lever de Terre', 'Lever de Terre'),
            ('La Bille bleue', 'La Bille bleue'),
            ('Pale Blue Dot', 'Pale Blue Dot'),
            ('Champ profond de Hubble', 'Champ profond de Hubble'),
        ],
    ),
    # Livree SANS images. Aucune image libre n'existe pour une serie :
    # fr.wikipedia refuse le non-libre, et Commons n'a que les logos en
    # lettrage, sous le seuil d'originalite. Ce que la chaine trouve ensuite
    # est du hors-sujet : un acteur pour Breaking Bad, des cosplayeurs pour
    # Game of Thrones, un groupe homonyme pour Mad Men, une ambulance pour
    # Urgences. Decision de l'utilisateur : poser une image d'attente
    # identique partout et remplacer a la main depuis l'atelier. Voir
    # image_attente.py.
    'series-televisees': dict(
        nom='Séries télévisées',
        # Le cinema avait deux collections, la television aucune. Columbo n'y
        # est pas : c'est deja une carte de personnage, et la regle 5 interdit
        # l'homonyme.
        transferts=[],
        ajouts=[
            ('Les Soprano', 'Les Soprano'),
            ('Breaking Bad', 'Breaking Bad'),
            ('Better Call Saul', 'Better Call Saul'),
            ('Game of Thrones', 'Game of Thrones'),
            ('Mad Men', 'Mad Men'),
            ('Six Feet Under', 'Six Feet Under (série télévisée)'),
            ('Twin Peaks', 'Twin Peaks (série télévisée)'),
            ('Deadwood', 'Deadwood (série télévisée)'),
            ('The Wire', 'Sur écoute'),
            ('Friends', 'Friends'),
            ('Seinfeld', 'Seinfeld'),
            ('The Office', 'The Office (série télévisée, 2005)'),
            ('How I Met Your Mother', 'How I Met Your Mother'),
            ('The Big Bang Theory', 'The Big Bang Theory'),
            ('Sex and the City', 'Sex and the City'),
            ('Desperate Housewives', 'Desperate Housewives'),
            ("Grey's Anatomy", "Grey's Anatomy"),
            ('Urgences', 'Urgences'),
            ('Dr House', 'Dr House'),
            ('Lost : Les Disparus', 'Lost : Les Disparus'),
            ('X-Files', 'X-Files'),
            ('Buffy contre les vampires', 'Buffy contre les vampires'),
            ('Doctor Who', 'Doctor Who'),
            ('Star Trek', 'Star Trek'),
            ('Battlestar Galactica', 'Battlestar Galactica'),
            ('Le Prisonnier', 'Le Prisonnier'),
            ('Chapeau melon et bottes de cuir', 'Chapeau melon et bottes de cuir'),
            ('Les Simpson', 'Les Simpson'),
            ('South Park', 'South Park'),
            ('Futurama', 'Futurama'),
            ('Rick et Morty', 'Rick et Morty'),
            ('Cowboy Bebop', 'Cowboy Bebop'),
            ('Black Mirror', 'Black Mirror (série télévisée)'),
            ('Stranger Things', 'Stranger Things'),
            ('Dark', 'Dark (série télévisée)'),
            ('Westworld', 'Westworld (série télévisée)'),
            ('The Walking Dead', 'The Walking Dead (série télévisée)'),
            ("The Handmaid's Tale", "The Handmaid's Tale : La Servante écarlate"),
            ('Chernobyl', 'Chernobyl (mini-série)'),
            ('The Crown', 'The Crown (série télévisée)'),
            ('Downton Abbey', 'Downton Abbey'),
            ('Peaky Blinders', 'Peaky Blinders (série télévisée)'),
            ('Succession', 'Succession (série télévisée)'),
            ('Fargo', 'Fargo (série télévisée)'),
            ('True Detective', 'True Detective'),
            ('Homeland', 'Homeland (série télévisée)'),
            ('Prison Break', 'Prison Break'),
            ('Dexter', 'Dexter (série télévisée)'),
            ('Narcos', 'Narcos'),
            ('La Casa de papel', 'La Casa de papel'),
            ('Squid Game', 'Squid Game'),
            ('Le Jeu de la dame', 'Le Jeu de la dame'),
            ('Sherlock', 'Sherlock (série télévisée)'),
            ('Kaamelott', 'Kaamelott'),
            ('Le Bureau des légendes', 'Le Bureau des légendes'),
            ('Engrenages', 'Engrenages'),
            ('Dix pour cent', 'Dix pour cent'),
        ],
    ),
    'villes-du-monde': dict(
        nom='Villes du monde',
        # Le jeu avait les monuments et les sites antiques, mais aucune ville.
        # « Paris » n'y est pas : Pâris, le prince troyen, est deja carte, et la
        # regle 5 ne distingue pas les accents. A rouvrir si tu acceptes de
        # renommer le Troyen en « Pâris (mythologie) ».
        # Bombay figure sous « Mumbai » : « Bombay » est deja une race de chat.
        transferts=[],
        ajouts=[
            ('Londres', 'Londres'),
            ('New York', 'New York'),
            ('Tokyo', 'Tokyo'),
            ('Rome', 'Rome'),
            ('Le Caire', 'Le Caire'),
            ('Istanbul', 'Istanbul'),
            ('Pékin', 'Pékin'),
            ('Moscou', 'Moscou'),
            ('Berlin', 'Berlin'),
            ('Venise', 'Venise'),
            ('Barcelone', 'Barcelone'),
            ('Athènes', 'Athènes'),
            ('Jérusalem', 'Jérusalem'),
            ('Mumbai', 'Bombay'),
            ('Rio de Janeiro', 'Rio de Janeiro'),
            ('Buenos Aires', 'Buenos Aires'),
            ('Mexico', 'Mexico'),
            ('Marrakech', 'Marrakech'),
            ('Le Cap', 'Le Cap'),
            ('Sydney', 'Sydney'),
            ('San Francisco', 'San Francisco'),
            ('La Havane', 'La Havane'),
            ('Saint-Pétersbourg', 'Saint-Pétersbourg'),
            ('Vienne', 'Vienne (Autriche)'),
            ('Amsterdam', 'Amsterdam'),
            ('Prague', 'Prague'),
            ('Lisbonne', 'Lisbonne'),
            ('Dubaï', 'Dubaï (ville)'),
            ('Singapour', 'Singapour'),
            ('Bangkok', 'Bangkok'),
            ('Séoul', 'Séoul'),
            ('Shanghai', 'Shanghai'),
            ('Kyoto', 'Kyoto'),
            ('Delhi', 'Delhi'),
            ('Katmandou', 'Katmandou'),
            ('Tombouctou', 'Tombouctou'),
            ('Lagos', 'Lagos'),
            ('Nairobi', 'Nairobi'),
            ('Addis-Abeba', 'Addis-Abeba'),
            ('Damas', 'Damas'),
            ('Bagdad', 'Bagdad'),
            ('Samarcande', 'Samarcande'),
            ('Ispahan', 'Ispahan'),
            ('Cuzco', 'Cuzco'),
            ('Vancouver', 'Vancouver'),
            ('Chicago', 'Chicago'),
            ('La Nouvelle-Orléans', 'La Nouvelle-Orléans'),
            ('Reykjavik', 'Reykjavik'),
            ('Oslo', 'Oslo'),
        ],
    ),
    'montagnes-et-volcans': dict(
        nom='Montagnes et volcans',
        # Le Mont Rushmore n'y est pas : c'est deja un monument.
        transferts=[],
        ajouts=[
            ('Everest', 'Everest'),
            ('K2', 'K2'),
            ('Mont Blanc', 'Mont Blanc'),
            ('Cervin', 'Cervin'),
            ('Kilimandjaro', 'Kilimandjaro'),
            ('Denali', 'Denali'),
            ('Aconcagua', 'Aconcagua'),
            ('Fujiyama', 'Fujiyama'),
            ('Vésuve', 'Vésuve'),
            ('Etna', 'Etna'),
            ('Stromboli', 'Stromboli'),
            ('Krakatoa', 'Krakatoa'),
            ('Mauna Kea', 'Mauna Kea'),
            ('Mauna Loa', 'Mauna Loa'),
            ('Popocatepetl', 'Popocatepetl'),
            ('Eyjafjallajökull', 'Eyjafjallajökull'),
            ('Mont Saint Helens', 'Mont Saint Helens'),
            ('Piton de la Fournaise', 'Piton de la Fournaise'),
            ('Mont Ararat', 'Mont Ararat'),
            ('Olympe', 'Olympe'),
            ('Kailash', 'Kailash'),
            ('Annapurna', 'Annapurna'),
            ('Nanga Parbat', 'Nanga Parbat'),
            ('Elbrouz', 'Elbrouz'),
            ('Table Mountain', 'Table Mountain'),
            ('Uluru', 'Uluru'),
            ('Caldeira de Yellowstone', 'Caldeira de Yellowstone'),
            ('Mont Erebus', 'Mont Erebus'),
            ('Pinatubo', 'Pinatubo'),
            ('Teide', 'Teide'),
            ('Cotopaxi', 'Cotopaxi'),
            ('Sinaï', 'Sinaï'),
            ('Fitz Roy', 'Fitz Roy'),
            ('Cerro Torre', 'Cerro Torre'),
        ],
    ),
    'fleuves-mers-et-oceans': dict(
        nom='Fleuves, mers et océans',
        # Le Tigre porte « (fleuve) » dans son nom de carte : sans cela il
        # serait l'homonyme du felin, deja carte chez les mammiferes.
        transferts=[],
        ajouts=[
            ('Nil', 'Nil'),
            ('Amazone', 'Amazone (fleuve)'),
            ('Yangtsé', 'Yangtsé'),
            ('Mississippi', 'Mississippi (fleuve)'),
            ('Danube', 'Danube'),
            ('Gange', 'Gange'),
            ('Indus', 'Indus'),
            ('Rhin', 'Rhin'),
            ('Volga', 'Volga'),
            ('Congo', 'Congo (fleuve)'),
            ('Niger', 'Niger (fleuve)'),
            ('Mékong', 'Mékong'),
            ('Tigre (fleuve)', 'Tigre'),
            ('Euphrate', 'Euphrate'),
            ('Loire', 'Loire'),
            ('Seine', 'Seine'),
            ('Amour', 'Amour (fleuve)'),
            ('Zambèze', 'Zambèze'),
            ('Colorado', 'Colorado (fleuve)'),
            ('Río Grande', 'Río Grande (fleuve)'),
            ('Mer Méditerranée', 'Mer Méditerranée'),
            ('Mer Rouge', 'Mer Rouge'),
            ('Mer Morte', 'Mer Morte'),
            ('Mer Noire', 'Mer Noire'),
            ('Mer Caspienne', 'Mer Caspienne'),
            ('Mer des Caraïbes', 'Mer des Caraïbes'),
            ('Mer Baltique', 'Mer Baltique'),
            ("Mer d'Aral", "Mer d'Aral"),
            ('Mer de Corail', 'Mer de Corail'),
            ('Océan Atlantique', 'Océan Atlantique'),
            ('Océan Pacifique', 'Océan Pacifique'),
            ('Océan Indien', 'Océan Indien'),
            ('Océan Arctique', 'Océan Arctique'),
            ('Océan Austral', 'Océan Austral'),
            ('Lac Baïkal', 'Lac Baïkal'),
            ('Lac Victoria', 'Lac Victoria'),
            ('Lac Titicaca', 'Lac Titicaca'),
            ('Grands Lacs', 'Grands Lacs (Amérique du Nord)'),
            ('Chutes Victoria', 'Chutes Victoria'),
            ('Chutes du Niagara', 'Chutes du Niagara'),
            ("Chutes d'Iguazú", "Chutes d'Iguazú"),
            ('Fosse des Mariannes', 'Fosse des Mariannes'),
            ('Grande Barrière de corail', 'Grande Barrière de corail'),
            ('Détroit de Gibraltar', 'Détroit de Gibraltar'),
            ('Canal de Suez', 'Canal de Suez'),
            ('Canal de Panama', 'Canal de Panama'),
        ],
    ),
    'iles': dict(
        nom='Îles',
        # Terre-Neuve porte « (île) » : la race de chien est deja carte. Le
        # Mont-Saint-Michel n'y est pas, c'est deja un monument.
        transferts=[],
        ajouts=[
            ('Madagascar', 'Madagascar'),
            ('Islande', 'Islande'),
            ('Bornéo', 'Bornéo'),
            ('Groenland', 'Groenland'),
            ('Nouvelle-Guinée', 'Nouvelle-Guinée'),
            ('Honshu', 'Honshu'),
            ('Grande-Bretagne', 'Grande-Bretagne'),
            ('Sicile', 'Sicile'),
            ('Sardaigne', 'Sardaigne'),
            ('Corse', 'Corse'),
            ('Crète', 'Crète'),
            ('Chypre', 'Chypre (île)'),
            ('Bali', 'Bali'),
            ('Java', 'Java (île)'),
            ('Sumatra', 'Sumatra'),
            ('Hawaï', 'Hawaï (île)'),
            ('Tahiti', 'Tahiti'),
            ('Île de Pâques', 'Île de Pâques'),
            ('Galápagos', 'Galápagos'),
            ('Îles Féroé', 'Îles Féroé'),
            ('Svalbard', 'Svalbard'),
            ('Sainte-Hélène', 'Sainte-Hélène (île)'),
            ('Zanzibar', 'Zanzibar (archipel)'),
            ('Socotra', 'Socotra'),
            ('Malte', 'Malte'),
            ('Santorin', 'Santorin'),
            ('Capri', 'Capri'),
            ('Ibiza', 'Ibiza'),
            ('Bahamas', 'Bahamas'),
            ('Cuba', 'Cuba'),
            ('Jamaïque', 'Jamaïque'),
            ('Hispaniola', 'Hispaniola'),
            ('Terre-Neuve (île)', 'Terre-Neuve'),
            ('Tasmanie', 'Tasmanie'),
            ('Nouvelle-Zélande', 'Nouvelle-Zélande'),
            ('Fidji', 'Fidji'),
            ('Palaos', 'Palaos'),
            ('Maldives', 'Maldives'),
            ('Seychelles', 'Seychelles'),
            ('Comores', 'Archipel des Comores'),
            ('Île Maurice', 'Île Maurice'),
            ('La Réunion', 'La Réunion'),
            ('Ouessant', 'Ouessant'),
            ('Spitzberg', 'Spitzberg'),
        ],
    ),
    'champions-olympiques': dict(
        nom='Grands champions olympiques',
        # Tu as ecarte « Disciplines olympiques » au profit de celle-ci : ce
        # sont les athletes qui font l'histoire des Jeux, pas la liste des
        # epreuves. Senna et Schumacher n'y sont pas, ils sont deja pilotes.
        transferts=[],
        ajouts=[
            ('Jesse Owens', 'Jesse Owens'),
            ('Carl Lewis', 'Carl Lewis'),
            ('Usain Bolt', 'Usain Bolt'),
            ('Michael Phelps', 'Michael Phelps'),
            ('Mark Spitz', 'Mark Spitz'),
            ('Nadia Comăneci', 'Nadia Comăneci'),
            ('Larissa Latynina', 'Larissa Latynina'),
            ('Simone Biles', 'Simone Biles'),
            ('Paavo Nurmi', 'Paavo Nurmi'),
            ('Emil Zátopek', 'Emil Zátopek'),
            ('Abebe Bikila', 'Abebe Bikila'),
            ('Bob Beamon', 'Bob Beamon'),
            ('Sergueï Bubka', 'Sergueï Bubka'),
            ('Haile Gebrselassie', 'Haile Gebrselassie'),
            ('Katie Ledecky', 'Katie Ledecky'),
            ('Ian Thorpe', 'Ian Thorpe'),
            ('Michael Johnson', 'Michael Johnson'),
            ('Florence Griffith-Joyner', 'Florence Griffith-Joyner'),
            ('Nikolaï Andrianov', 'Nikolai Andrianov'),
            ('Birgit Fischer', 'Birgit Fischer'),
            ('Steve Redgrave', 'Steve Redgrave'),
            ('Marit Bjørgen', 'Marit Bjørgen'),
            ('Ole Einar Bjørndalen', 'Ole Einar Bjørndalen'),
            ('Eric Heiden', 'Eric Heiden'),
            ('Jean-Claude Killy', 'Jean-Claude Killy'),
            ('Teófilo Stevenson', 'Teófilo Stevenson'),
            ('László Papp', 'László Papp'),
            ('Alexandre Karéline', 'Alexander Kareline'),
            ('Kōhei Uchimura', 'Kōhei Uchimura'),
            ('Allyson Felix', 'Allyson Felix'),
            ('Teddy Riner', 'Teddy Riner'),
            ('Marie-José Pérec', 'Marie-José Pérec'),
            ('David Douillet', 'David Douillet'),
            ('Cathy Freeman', 'Cathy Freeman'),
            ('Fanny Blankers-Koen', 'Fanny Blankers-Koen'),
            ('Al Oerter', 'Al Oerter'),
            ('Dick Fosbury', 'Dick Fosbury'),
            ('Greg Louganis', 'Greg Louganis'),
            ('Naim Süleymanoğlu', 'Naim Süleymanoğlu'),
            ('Wilma Rudolph', 'Wilma Rudolph'),
        ],
    ),
    'jeux-olympiques': dict(
        nom='Jeux olympiques',
        # Les editions elles-memes, comme les Coupes du monde de la FIFA ont
        # deja leur collection.
        transferts=[],
        ajouts=[
            ('Jeux olympiques', 'Jeux olympiques'),
            ('Jeux olympiques antiques', 'Jeux olympiques antiques'),
            ("Jeux olympiques d'été de 1896", "Jeux olympiques d'été de 1896"),
            ("Jeux olympiques d'été de 1900", "Jeux olympiques d'été de 1900"),
            ("Jeux olympiques d'été de 1936", "Jeux olympiques d'été de 1936"),
            ("Jeux olympiques d'été de 1968", "Jeux olympiques d'été de 1968"),
            ("Jeux olympiques d'été de 1972", "Jeux olympiques d'été de 1972"),
            ("Jeux olympiques d'été de 1980", "Jeux olympiques d'été de 1980"),
            ("Jeux olympiques d'été de 1984", "Jeux olympiques d'été de 1984"),
            ("Jeux olympiques d'été de 1992", "Jeux olympiques d'été de 1992"),
            ("Jeux olympiques d'été de 2008", "Jeux olympiques d'été de 2008"),
            ("Jeux olympiques d'été de 2012", "Jeux olympiques d'été de 2012"),
            ("Jeux olympiques d'été de 2024", "Jeux olympiques d'été de 2024"),
            ("Jeux olympiques d'hiver de 1924", "Jeux olympiques d'hiver de 1924"),
            ("Jeux olympiques d'hiver de 1992", "Jeux olympiques d'hiver de 1992"),
            ('Jeux paralympiques', 'Jeux paralympiques'),
            ('Comité international olympique', 'Comité international olympique'),
            ('Flamme olympique', 'Flamme olympique'),
            ('Drapeau olympique', 'Drapeau olympique'),
            ('Pierre de Coubertin', 'Pierre de Coubertin'),
            ('Marathon', 'Marathon (sport)'),
            ('Décathlon', 'Décathlon'),
            ('Stade olympique de Berlin', 'Stade olympique de Berlin'),
        ],
    ),
    'legendes-du-sport': dict(
        nom='Légendes du sport',
        # Hors football et hors formule 1, qui ont deja leurs collections :
        # d'ou l'absence de Senna, Schumacher et des footballeurs.
        transferts=[],
        ajouts=[
            ('Muhammad Ali', 'Muhammad Ali'),
            ('Michael Jordan', 'Michael Jordan'),
            ('LeBron James', 'LeBron James'),
            ('Roger Federer', 'Roger Federer'),
            ('Rafael Nadal', 'Rafael Nadal'),
            ('Novak Djokovic', 'Novak Djokovic'),
            ('Serena Williams', 'Serena Williams'),
            ('Steffi Graf', 'Steffi Graf'),
            ('Björn Borg', 'Björn Borg'),
            ('Tiger Woods', 'Tiger Woods'),
            ('Eddy Merckx', 'Eddy Merckx'),
            ('Bernard Hinault', 'Bernard Hinault'),
            ('Jacques Anquetil', 'Jacques Anquetil'),
            ('Miguel Indurain', 'Miguel Indurain'),
            ('Babe Ruth', 'Babe Ruth'),
            ('Wayne Gretzky', 'Wayne Gretzky'),
            ('Kobe Bryant', 'Kobe Bryant'),
            ('Magic Johnson', 'Magic Johnson'),
            ('Larry Bird', 'Larry Bird'),
            ('Kareem Abdul-Jabbar', 'Kareem Abdul-Jabbar'),
            ('Wilt Chamberlain', 'Wilt Chamberlain'),
            ('Jack Nicklaus', 'Jack Nicklaus'),
            ('Rod Laver', 'Rod Laver'),
            ('Martina Navrátilová', 'Martina Navrátilová'),
            ('Mike Tyson', 'Mike Tyson'),
            ('Sugar Ray Robinson', 'Sugar Ray Robinson'),
            ('Joe Louis', 'Joe Louis'),
            ('Rocky Marciano', 'Rocky Marciano'),
            ('Bobby Fischer', 'Bobby Fischer'),
            ('Garry Kasparov', 'Garry Kasparov'),
            ('Jahangir Khan', 'Jahangir Khan'),
            ('Sachin Tendulkar', 'Sachin Tendulkar'),
            ('Don Bradman', 'Don Bradman'),
            ('Jonny Wilkinson', 'Jonny Wilkinson'),
            ('Richie McCaw', 'Richie McCaw'),
            ('Jonah Lomu', 'Jonah Lomu'),
            ('Sébastien Loeb', 'Sébastien Loeb'),
            ('Valentino Rossi', 'Valentino Rossi'),
            ('Tony Hawk', 'Tony Hawk'),
            ('Kelly Slater', 'Kelly Slater'),
        ],
    ),
    'conquete-spatiale': dict(
        nom='Conquête spatiale',
        # Les VAISSEAUX, les missions et les lieux. Gagarine, Terechkova,
        # Armstrong et Aldrin n'y sont pas : ils sont deja des pionniers de
        # l'extreme, et Korolev un ingenieur. Von Braun non plus, il est deja
        # carte sous « Werner von Braun ».
        transferts=[],
        ajouts=[
            ('Spoutnik 1', 'Spoutnik 1'),
            ('Alan Shepard', 'Alan Shepard'),
            ('John Glenn', 'John Glenn'),
            ('Apollo 8', 'Apollo 8'),
            ('Apollo 11', 'Apollo 11'),
            ('Apollo 13', 'Apollo 13'),
            ('Programme Apollo', 'Programme Apollo'),
            ('Programme Vostok', 'Programme Vostok'),
            ('Laïka', 'Laïka'),
            ('Saturn V', 'Saturn V'),
            ('Navette spatiale américaine', 'Navette spatiale américaine'),
            ('Station spatiale internationale', 'Station spatiale internationale'),
            ('Mir', 'Mir (station spatiale)'),
            ('Skylab', 'Skylab'),
            ('Soyouz', 'Soyouz (véhicule spatial)'),
            ('Télescope spatial Hubble', 'Télescope spatial Hubble'),
            ('Télescope spatial James-Webb', 'Télescope spatial James-Webb'),
            ('Voyager 1', 'Voyager 1'),
            ('Voyager 2', 'Voyager 2'),
            ('Pioneer 10', 'Pioneer 10'),
            ('Cassini-Huygens', 'Cassini-Huygens'),
            ('New Horizons', 'New Horizons'),
            ('Curiosity', 'Curiosity (astromobile)'),
            ('Perseverance', 'Perseverance (rover)'),
            ('Spirit', 'Spirit (rover)'),
            ('Rosetta', 'Rosetta (sonde spatiale)'),
            ('Sonde Parker', 'Sonde Parker'),
            ('Ariane 5', 'Ariane 5'),
            ('Falcon 9', 'Falcon 9'),
            ('SpaceX', 'SpaceX'),
            ('NASA', 'NASA'),
            ('Agence spatiale européenne', 'Agence spatiale européenne'),
            ('Cosmodrome de Baïkonour', 'Cosmodrome de Baïkonour'),
            ('Cap Canaveral', 'Cap Canaveral'),
            ('Thomas Pesquet', 'Thomas Pesquet'),
            ("Chang'e 4", "Chang'e 4"),
            ('Sortie extravéhiculaire', 'Sortie extravéhiculaire'),
        ],
    ),
    'mineraux-et-pierres': dict(
        nom='Minéraux et pierres précieuses',
        # Soufre et platine n'y sont pas : ce sont deja des elements chimiques.
        # Les mineraux natifs de l'or, de l'argent et du cuivre, eux, sont des
        # pages distinctes de celles des elements.
        transferts=[],
        ajouts=[
            ('Diamant', 'Diamant'),
            ('Rubis', 'Rubis'),
            ('Saphir', 'Saphir'),
            ('Émeraude', 'Émeraude'),
            ('Améthyste', 'Améthyste'),
            ('Topaze', 'Topaze (minéral)'),
            ('Opale', 'Opale'),
            ('Turquoise', 'Turquoise (minéral)'),
            ('Lapis-lazuli', 'Lapis-lazuli'),
            ('Jade', 'Jade'),
            ('Ambre', 'Ambre'),
            ('Perle', 'Perle'),
            ('Quartz', 'Quartz (minéral)'),
            ('Citrine', 'Citrine'),
            ('Malachite', 'Malachite'),
            ('Obsidienne', 'Obsidienne'),
            ('Pyrite', 'Pyrite'),
            ('Hématite', 'Hématite'),
            ('Magnétite', 'Magnétite'),
            ('Fluorite', 'Fluorite'),
            ('Calcite', 'Calcite'),
            ('Gypse', 'Gypse'),
            ('Halite', 'Halite'),
            ('Talc', 'Talc'),
            ('Graphite', 'Graphite'),
            ('Or natif', 'Or natif'),
            ('Argent natif', 'Argent natif'),
            ('Cuivre natif', 'Cuivre natif'),
            ('Galène', 'Galène'),
            ('Cinabre', 'Cinabre'),
            ('Bauxite', 'Bauxite'),
            ('Météorite', 'Météorite'),
            ('Silex', 'Silex'),
            ('Grenat', 'Grenat'),
            ('Tourmaline', 'Tourmaline'),
            ('Péridot', 'Péridot'),
            ('Aigue-marine', 'Aigue-marine'),
            ('Onyx', 'Onyx (minéral)'),
            ('Agate', 'Agate'),
            ('Jaspe', 'Jaspe'),
            ('Cristal de roche', 'Cristal de roche'),
            ('Uraninite', 'Uraninite'),
            ('Béryl', 'Béryl'),
            ('Corindon', 'Corindon'),
            ('Olivine', 'Olivine'),
            ('Feldspath', 'Feldspath'),
        ],
    ),
    'vehicules-mythiques': dict(
        nom='Véhicules mythiques',
        # Nom choisi par toi, en remplacement de « Navires et vehicules
        # legendaires ». N'y sont PAS : l'Arche de Noe et le cheval de Troie,
        # deja objets mythiques ; Sleipnir et Pegase, deja montures divines ;
        # le Titanic, deja carte de cinema. Les vaisseaux mythiques restants
        # etant peu nombreux, la collection s'ouvre aux navires et aeronefs
        # entres dans la legende par leur histoire reelle.
        transferts=[],
        ajouts=[
            ('Argo', 'Argo (mythologie)'),
            ('Hollandais volant', 'Hollandais volant'),
            ('Vimana', 'Vimana'),
            ('Skidbladnir', 'Skidbladnir'),
            ('Naglfar', 'Naglfar'),
            ('Barque solaire', 'Barque solaire'),
            ('Tapis volant', 'Tapis volant'),
            ('Buraq', 'Buraq'),
            ('La Nef des fous', 'La Nef des fous (Bosch)'),
            ('Bateau-dragon', 'Bateau-dragon (pirogue)'),
            ('Drakkar', 'Drakkar'),
            ('Jonque', 'Jonque'),
            ('Trirème', 'Trirème'),
            ('Galion', 'Galion'),
            ('Caravelle', 'Caravelle (navire)'),
            ('Mayflower', 'Mayflower'),
            ('HMS Victory', 'HMS Victory (1765)'),
            ('Bounty', 'Bounty (navire)'),
            ('Kon-Tiki', 'Kon-Tiki'),
            ('Nautilus', 'Nautilus (Jules Verne)'),
            ('LZ 129 Hindenburg', 'LZ 129 Hindenburg'),
            ('Spirit of St. Louis', 'Spirit of St. Louis'),
            ('Concorde', 'Concorde (avion)'),
            ('Orient-Express', 'Orient-Express'),
            ('Cutty Sark', 'Cutty Sark'),
            ('Endurance', 'Endurance (navire)'),
            ('Santa María', 'Santa María (1492)'),
            ('Golden Hind', 'Golden Hind'),
            ('SS Great Eastern', 'SS Great Eastern'),
            ('Belem', 'Belem'),
            ('Vaisseau fantôme', 'Vaisseau fantôme'),
            ('Char solaire', 'Char solaire'),
            ('Balai de sorcière', 'Balai de sorcière'),
        ],
    ),
    'langues-du-monde': dict(
        nom='Langues du monde',
        # Le persan porte « (langue) » dans son nom de carte : sans cela il
        # serait l'homonyme du chat. Le braille n'y est pas, c'est deja une
        # invention.
        transferts=[],
        ajouts=[
            ('Latin', 'Latin'),
            ('Grec ancien', 'Grec ancien'),
            ('Sanskrit', 'Sanskrit'),
            ('Hébreu', 'Hébreu'),
            ('Arabe', 'Arabe'),
            ('Langues chinoises', 'Langues chinoises'),
            ('Mandarin standard', 'Mandarin standard'),
            ('Japonais', 'Japonais'),
            ('Coréen', 'Coréen'),
            ('Hindi', 'Hindi'),
            ('Bengali', 'Bengali'),
            ('Ourdou', 'Ourdou'),
            ('Persan (langue)', 'Persan'),
            ('Turc', 'Turc'),
            ('Russe', 'Russe'),
            ('Polonais', 'Polonais'),
            ('Allemand', 'Allemand'),
            ('Anglais', 'Anglais'),
            ('Français', 'Français'),
            ('Espagnol', 'Espagnol'),
            ('Portugais', 'Portugais'),
            ('Italien', 'Italien'),
            ('Néerlandais', 'Néerlandais'),
            ('Suédois', 'Suédois'),
            ('Finnois', 'Finnois'),
            ('Hongrois', 'Hongrois'),
            ('Basque', 'Basque'),
            ('Breton', 'Breton'),
            ('Gallois', 'Gallois'),
            ('Irlandais', 'Irlandais'),
            ('Islandais', 'Islandais'),
            ('Swahili', 'Swahili'),
            ('Yoruba', 'Yoruba (langue)'),
            ('Zoulou', 'Zoulou'),
            ('Amharique', 'Amharique'),
            ('Haoussa', 'Haoussa'),
            ('Quechua', 'Quechua'),
            ('Guarani', 'Guarani (langue)'),
            ('Nahuatl', 'Nahuatl'),
            ('Langues maories', 'Langues maories'),
            ('Hawaïen', 'Hawaïen'),
            ('Espéranto', 'Espéranto'),
            ('Langue des signes française', 'Langue des signes française'),
            ('Écriture cunéiforme', 'Écriture cunéiforme'),
            ('Écriture hiéroglyphique égyptienne', 'Écriture hiéroglyphique égyptienne'),
            ('Tamoul', 'Tamoul'),
            ('Vietnamien', 'Vietnamien'),
            ('Thaï', 'Thaï'),
            ('Araméen', 'Araméen'),
            ('Copte', 'Copte'),
            ('Gotique', 'Gotique'),
            ('Sumérien', 'Sumérien'),
        ],
    ),
    'traites-et-textes-fondateurs': dict(
        nom='Traités et textes fondateurs',
        transferts=[],
        ajouts=[
            ('Code de Hammurabi', 'Code de Hammurabi'),
            ('Magna Carta', 'Magna Carta'),
            ('Édit de Nantes', 'Édit de Nantes'),
            ('Traité de Westphalie', 'Traité de Westphalie'),
            ("Déclaration d'indépendance des États-Unis", "Déclaration d'indépendance des États-Unis"),
            ('Constitution des États-Unis', 'Constitution des États-Unis'),
            ("Déclaration des droits de l'homme et du citoyen de 1789", "Déclaration des droits de l'homme et du citoyen de 1789"),
            ('Code civil', 'Code civil (France)'),
            ('Traité de Versailles', 'Traité de Versailles'),
            ('Charte des Nations unies', 'Charte des Nations unies'),
            ("Déclaration universelle des droits de l'homme", "Déclaration universelle des droits de l'homme"),
            ('Conventions de Genève', 'Conventions de Genève'),
            ('Traité de Rome', 'Traité instituant la Communauté économique européenne'),
            ('Traité de Maastricht', 'Traité de Maastricht'),
            ('Accords de Camp David', 'Accords de Camp David'),
            ('Accord de Paris sur le climat', 'Accord de Paris sur le climat'),
            ('Protocole de Kyoto', 'Protocole de Kyoto'),
            ('Traité de Tordesillas', 'Traité de Tordesillas'),
            ('Actes de navigation', 'Actes de navigation'),
            ("Traité de l'Antarctique", "Traité de l'Antarctique"),
            ('Traité sur la non-prolifération des armes nucléaires', 'Traité sur la non-prolifération des armes nucléaires'),
            ('Convention de Vienne sur le droit des traités', 'Convention de Vienne sur le droit des traités'),
            ('Charte des droits de 1689', 'Charte des droits de 1689'),
            ('Habeas corpus', 'Habeas corpus'),
            ('Édit de Milan', 'Édit de Milan'),
            ('Traité de Verdun', 'Traité de Verdun'),
            ('Traité de Troyes', 'Traité de Troyes'),
            ("Paix d'Augsbourg", "Paix d'Augsbourg"),
            ('Congrès de Vienne', 'Congrès de Vienne'),
            ("Convention relative aux droits de l'enfant", "Convention relative aux droits de l'enfant"),
            ('Charte du Manden', 'Charte du Manden'),
        ],
    ),
    'mode-et-couturiers': dict(
        nom='Mode et couturiers',
        transferts=[],
        ajouts=[
            ('Coco Chanel', 'Coco Chanel'),
            ('Christian Dior', 'Christian Dior'),
            ('Yves Saint Laurent', 'Yves Saint Laurent'),
            ('Karl Lagerfeld', 'Karl Lagerfeld'),
            ('Giorgio Armani', 'Giorgio Armani'),
            ('Gianni Versace', 'Gianni Versace'),
            ('Valentino Garavani', 'Valentino Garavani'),
            ('Hubert de Givenchy', 'Hubert de Givenchy'),
            ('Cristóbal Balenciaga', 'Cristóbal Balenciaga'),
            ('Paul Poiret', 'Paul Poiret'),
            ('Madeleine Vionnet', 'Madeleine Vionnet'),
            ('Elsa Schiaparelli', 'Elsa Schiaparelli'),
            ('Jeanne Lanvin', 'Jeanne Lanvin'),
            ('Charles Frederick Worth', 'Charles Frederick Worth'),
            ('Pierre Cardin', 'Pierre Cardin'),
            ('André Courrèges', 'André Courrèges'),
            ('Sonia Rykiel', 'Sonia Rykiel'),
            ('Jean Paul Gaultier', 'Jean Paul Gaultier'),
            ('Thierry Mugler', 'Thierry Mugler'),
            ('Alexander McQueen', 'Alexander McQueen'),
            ('Vivienne Westwood', 'Vivienne Westwood'),
            ('Ralph Lauren', 'Ralph Lauren'),
            ('Calvin Klein', 'Calvin Klein'),
            ('Tom Ford', 'Tom Ford'),
            ('Marc Jacobs', 'Marc Jacobs'),
            ('Miuccia Prada', 'Miuccia Prada'),
            ('Donatella Versace', 'Donatella Versace'),
            ('Rei Kawakubo', 'Rei Kawakubo'),
            ('Yohji Yamamoto', 'Yohji Yamamoto'),
            ('Issey Miyake', 'Issey Miyake'),
            ('Kenzo Takada', 'Kenzo Takada'),
            ('Manolo Blahnik', 'Manolo Blahnik'),
            ('Christian Louboutin', 'Christian Louboutin'),
            ('Virgil Abloh', 'Virgil Abloh'),
            ('Azzedine Alaïa', 'Azzedine Alaïa'),
            ('Emilio Pucci', 'Emilio Pucci'),
            ('Salvatore Ferragamo', 'Salvatore Ferragamo'),
            ('Nina Ricci', 'Nina Ricci'),
            ('Guccio Gucci', 'Guccio Gucci'),
            ('Louis Vuitton', 'Louis Vuitton (malletier)'),
        ],
    ),
    'instruments-de-musique': dict(
        nom='Instruments de musique',
        transferts=[],
        ajouts=[
            ('Piano', 'Piano'),
            ('Violon', 'Violon'),
            ('Violoncelle', 'Violoncelle'),
            ('Contrebasse', 'Contrebasse'),
            ('Alto', 'Alto (instrument à cordes)'),
            ('Harpe', 'Harpe'),
            ('Guitare', 'Guitare'),
            ('Guitare électrique', 'Guitare électrique'),
            ('Luth', 'Luth'),
            ('Sitar', 'Sitar'),
            ('Banjo', 'Banjo'),
            ('Mandoline', 'Mandoline'),
            ('Balalaïka', 'Balalaïka'),
            ('Oud', 'Oud'),
            ('Koto', 'Koto'),
            ('Flûte traversière', 'Flûte traversière'),
            ('Clarinette', 'Clarinette'),
            ('Hautbois', 'Hautbois'),
            ('Basson', 'Basson'),
            ('Saxophone', 'Saxophone'),
            ('Trompette', 'Trompette'),
            ("Cor d'harmonie", "Cor d'harmonie"),
            ('Trombone', 'Trombone (instrument)'),
            ('Tuba', 'Tuba (instrument)'),
            ('Cornemuse', 'Cornemuse'),
            ('Didgeridoo', 'Didgeridoo'),
            ('Orgue', 'Orgue'),
            ('Clavecin', 'Clavecin'),
            ('Accordéon', 'Accordéon'),
            ('Harmonica', 'Harmonica'),
            ('Batterie', 'Batterie (musique)'),
            ('Timbales', 'Timbales (musique classique)'),
            ('Xylophone', 'Xylophone'),
            ('Marimba', 'Marimba'),
            ('Vibraphone', 'Vibraphone'),
            ('Djembé', 'Djembé'),
            ('Tabla', 'Tabla'),
            ('Gamelan', 'Gamelan'),
            ('Steel drum', 'Steel drum'),
            ('Thérémine', 'Thérémine'),
            ('Synthétiseur', 'Synthétiseur'),
            ('Orgue de Barbarie', 'Orgue de Barbarie'),
            ('Kora', 'Kora'),
            ('Shamisen', 'Shamisen'),
            ('Erhu', 'Erhu'),
            ('Bandonéon', 'Bandonéon'),
            ('Ukulélé', 'Ukulélé'),
            ('Triangle', 'Triangle (musique)'),
        ],
    ),
    'races-de-cheval': dict(
        nom='Races de cheval',
        # Le cheval de Przewalski n'y est pas : c'est une espece sauvage, deja
        # carte chez les mammiferes, et non une race domestique.
        transferts=[],
        ajouts=[
            ('Pur-sang', 'Pur-sang'),
            ('Arabe', 'Arabe (cheval)'),
            ('Frison', 'Frison (cheval)'),
            ('Andalou', 'Andalou (cheval)'),
            ('Lipizzan', 'Lipizzan'),
            ('Akhal-Teké', 'Akhal-Teké'),
            ('Quarter Horse', 'Quarter Horse'),
            ('Appaloosa', 'Appaloosa'),
            ('Mustang', 'Mustang (cheval)'),
            ('Shire', 'Shire (cheval)'),
            ('Percheron', 'Percheron'),
            ('Trait belge', 'Trait belge'),
            ('Clydesdale', 'Clydesdale'),
            ('Haflinger', 'Haflinger'),
            ('Fjord', 'Fjord (cheval)'),
            ('Islandais', 'Islandais (cheval)'),
            ('Shetland', 'Shetland (poney)'),
            ('Connemara', 'Connemara (cheval)'),
            ('Camargue', 'Camargue (cheval)'),
            ('Selle français', 'Selle français'),
            ('Hanovrien', 'Hanovrien'),
            ('Holsteiner', 'Holsteiner'),
            ('Trakehner', 'Trakehner'),
            ('Oldenbourg', 'Oldenbourg (cheval)'),
            ('Lusitanien', 'Lusitanien (cheval)'),
            ('Marwari', 'Marwari (cheval)'),
            ('Criollo', 'Criollo'),
            ('Paso Fino', 'Paso Fino'),
            ('Tennessee Walker', 'Tennessee Walker'),
            ('Morgan', 'Morgan (cheval)'),
            ('Ardennais', 'Ardennais (cheval)'),
            ('Boulonnais', 'Boulonnais (cheval)'),
            ('Comtois', 'Comtois (cheval)'),
            ('Welsh', 'Welsh (cheval)'),
            ('Trotteur français', 'Trotteur français'),
            ('Standardbred', 'Standardbred'),
            ('Barbe', 'Barbe (cheval)'),
            ('Konik', 'Konik'),
            ('Falabella', 'Falabella'),
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
