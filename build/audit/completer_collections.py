#!/usr/bin/env python3
"""Comble les trous releves dans les collections existantes.

Chaque liste vient d'une lecture carte par carte de la collection, pas d'une
intuition. Le commentaire au-dessus dit quel angle mort elle repare.

Le script refuse d'ecrire une carte dont le nom existe deja ailleurs dans le
jeu (consigne 5) : il signale au lieu de creer un homonyme.

Usage : python completer_collections.py [--essai] [--slug <slug>]
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

# (nom de carte, titre fr.wikipedia) par collection
AJOUTS = {
    # Sur 160 cartes, la psychologie avait quatre entrees et le reste des
    # sciences humaines aucune : ni economie, ni linguistique, ni sociologie,
    # ni anthropologie. Second angle mort : l'Antiquite et le monde medieval
    # non europeen, alors qu'Al-Khwarizmi et Ibn Sina y figuraient deja.
    # Deux cartes demandees a la lecture de l'atelier. Zenobie manquait alors
    # que Boadicee, Cleopatre et Amanitore y figurent : la reine de Palmyre est
    # du meme registre, souveraine qui tient tete a Rome.
    'souverains-et-conquerants': [
        # « Zenobie » seul est une page d'homonymie
        ('Zénobie', 'Septimia Bathzabbai Zénobie'),
    ],
    # Hebe manquait au pantheon grec, alors que Hestia, Selene et Helios y sont :
    # elle est l'echanson des dieux, fille de Zeus et d'Hera.
    'dieux-et-figures-mythologiques-grecques': [
        ('Hébé', 'Hébé'),
    ],
    'scientifiques-celebres': [
        ('Adam Smith', 'Adam Smith'),
        ('Karl Marx', 'Karl Marx'),
        ('John Maynard Keynes', 'John Maynard Keynes'),
        ('David Ricardo', 'David Ricardo'),
        ('Ferdinand de Saussure', 'Ferdinand de Saussure'),
        ('Noam Chomsky', 'Noam Chomsky'),
        ('Jean-François Champollion', 'Jean-François Champollion'),
        ('Émile Durkheim', 'Émile Durkheim'),
        ('Max Weber', 'Max Weber'),
        ('Pierre Bourdieu', 'Pierre Bourdieu'),
        ('Claude Lévi-Strauss', 'Claude Lévi-Strauss'),
        ('Franz Boas', 'Franz Boas'),
        ('Bronisław Malinowski', 'Bronisław Malinowski'),
        ('Margaret Mead', 'Margaret Mead'),
        ('Ératosthène', 'Ératosthène'),
        ('Hypatie', 'Hypatie'),
        ('Averroès', 'Averroès'),
        ('Aryabhata', 'Aryabhata'),
        ('Brahmagupta', 'Brahmagupta'),
        ('Nasir al-Din al-Tusi', 'Nasir ad-Din at-Tusi'),
        ('Mary Anning', 'Mary Anning'),
    ],
    # La collection privilegiait les objets. Manquaient les inventions qui ont
    # le plus change le monde sans etre spectaculaires.
    'inventions-importantes': [
        ('Zéro', 'Zéro'),
        ('Alphabet', 'Alphabet'),
        ('Calendrier', 'Calendrier'),
        ('Conteneur', 'Conteneur'),
        ('Chaîne de montage', 'Chaîne de montage'),
        ('Écluse', 'Écluse'),
        ('Antisepsie', 'Antisepsie'),
        ('Braille', 'Braille'),
        ('Code Morse', 'Code Morse'),
        ('Roulement à billes', 'Roulement à billes'),
        ('Papier-monnaie', 'Papier-monnaie'),
    ],
    # Deux angles morts : l'Amerique precolombienne s'arretait aux Azteques,
    # Mayas et Incas ; et les peuples sans Etat centralise etaient absents en
    # bloc, alors que Carthage et les Minoens y figuraient.
    'empires-et-civilisations': [
        ('Olmèques', 'Olmèques'),
        ('Moche', 'Moche (culture)'),
        ('Nazca', 'Nazca (civilisation)'),
        ('Tiwanaku', 'Tiwanaku'),
        ('Chavín', 'Chavín de Huántar'),
        ('Cahokia', 'Cahokia'),
        ('Étrusques', 'Étrusques'),
        ('Phéniciens', 'Phéniciens'),
        ('Celtes', 'Celtes'),
        ('Vikings', 'Vikings'),
        ('Scythes', 'Scythes'),
        ('Huns', 'Huns'),
        ('Xiongnu', 'Xiongnu'),
        ('Empire kouchan', 'Empire kouchan'),
        ('Royaume du Kongo', 'Royaume de Kongo'),
        ('Monomotapa', 'Monomotapa'),
        ("Empire d'Oyo", 'Royaume d’Oyo'),
    ],
    # Aucune guerre latino-americaine, et les revolutions manquaient comme
    # genre : la guerre civile russe y etait, pas la Revolution russe.
    'grandes-guerres': [
        ('Guerre de la Triple-Alliance', 'Guerre de la Triple-Alliance'),
        ('Guerre du Chaco', 'Guerre du Chaco'),
        ("Guerres d'indépendance hispano-américaines",
         "Guerres d'indépendance en Amérique du Sud"),
        ('Révolution haïtienne', 'Révolution haïtienne'),
        ('Révolution mexicaine', 'Révolution mexicaine'),
        ('Révolution russe', 'Révolution russe'),
        ('Révolution française', 'Révolution française'),
    ],
    # L'architecture du XXe siecle tenait en deux cartes ; l'Inde, l'Asie du
    # Sud-Est et l'Afrique etaient maigres.
    'monuments-emblematiques': [
        ('Villa Savoye', 'Villa Savoye'),
        ('Maison sur la cascade', 'Fallingwater'),
        ('Musée Guggenheim (New York)', 'Musée Solomon R. Guggenheim'),
        ('Bauhaus', 'Bauhaus'),
        ('Seagram Building', 'Seagram Building'),
        ('Cité radieuse', 'Cité radieuse de Marseille'),
        ('Ellorâ', 'Ellora'),
        ('Hampi', 'Hampi'),
        ('Fatehpur-Sikri', 'Fatehpur-Sikri'),
        ('Wat Arun', 'Wat Arun'),
        ('Grande mosquée de Kairouan', 'Grande Mosquée de Kairouan'),
    ],
    # Le seul vrai tableau orphelin : son peintre manquait a la collection.
    'grands-peintres': [
        ('Emanuel Leutze', 'Emanuel Leutze'),
    ],
}

# Cartes dont la page etait fausse (voir le brief) : le sujet change, l'image
# aussi puisque l'ancienne illustrait autre chose.
CORRECTIONS = [
    # pointait sur une toile de Felix Nussbaum de 1944
    ('tableaux-celebres', 'Le Triomphe de la mort', 'Le Triomphe de la Mort (Brueghel)'),
    # pointait sur la page du THEME iconographique, pas sur une oeuvre
    ('tableaux-celebres', 'Judith décapitant Holopherne',
     'Judith décapitant Holopherne (Artemisia Gentileschi)'),
]


def norm(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '', s)


def slugifier(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


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


def main():
    essai = '--essai' in sys.argv
    filtre = (sys.argv[sys.argv.index('--slug') + 1]
              if '--slug' in sys.argv else None)
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    charges, signalements = {}, []

    def charger(slug):
        if slug not in charges:
            charges[slug] = json.loads(par_slug[slug].read_text(encoding='utf-8'))
        return charges[slug]

    # noms deja pris dans TOUT le jeu
    pris_partout = {}
    for c in idx['collections']:
        for x in json.loads((RACINE / c['fichier']).read_text(encoding='utf-8'))['cartes']:
            pris_partout[norm(x['nom'])] = (c['slug'], x['nom'])

    R.charger_fiches([t for v in AJOUTS.values() for _, t in v]
                     + [t for _, _, t in CORRECTIONS])

    for slug, lot in AJOUTS.items():
        if filtre and slug != filtre:
            continue
        d = charger(slug)
        pris_ids = {x['id'] for x in d['cartes']}
        for nom, titre in lot:
            deja = pris_partout.get(norm(nom))
            if deja:
                signalements.append(f'{slug} · « {nom} » : homonyme de '
                                    f'{deja[0]} · {deja[1]}, non créée')
                continue
            f = R._cache.get('fiche:' + titre)
            if not f or f['statut'] != 'ok' or not f.get('extrait'):
                signalements.append(f'{slug} · {nom} : page « {titre} » non résolue')
                continue
            fslug = slugifier(f['titre'])
            while f'{slug}_{fslug}' in pris_ids:
                fslug += '-b'
            pris_ids.add(f'{slug}_{fslug}')
            pris_partout[norm(nom)] = (slug, nom)
            d['cartes'].append({
                'id': f'{slug}_{fslug}', 'nom': nom, 'titrePage': f['titre'],
                'imageUrl': f'images/full/{slug}/{fslug}.webp',
                'thumbUrl': f'images/thumbs/{slug}/{fslug}.webp',
                'description': f['extrait'], 'collection': d['collection'],
                'lienWikipedia': 'https://fr.wikipedia.org/wiki/'
                                 + urllib.parse.quote(f['titre'].replace(' ', '_')),
                'pageviews': pageviews(f['titre']), 'tags': [], 'numero': 0,
            })
            print(f'  + {slug:<28} {nom:<42} <- {f["titre"]}')

    for slug, nom, titre in CORRECTIONS:
        if filtre and slug != filtre:
            continue
        d = charger(slug)
        c = next((x for x in d['cartes'] if x['nom'] == nom), None)
        f = R._cache.get('fiche:' + titre)
        if c is None or not f or f['statut'] != 'ok':
            signalements.append(f'{slug} · « {nom} » : correction impossible')
            continue
        ancien = c['id']
        fslug = slugifier(f['titre'])
        for rep in ('full', 'thumbs', 'originaux'):
            p = RACINE / 'images' / rep / slug / f'{ancien.split("_", 1)[1]}.webp'
            if p.exists() and not essai:
                p.unlink()
        c.update(titrePage=f['titre'], description=f['extrait'],
                 lienWikipedia='https://fr.wikipedia.org/wiki/'
                               + urllib.parse.quote(f['titre'].replace(' ', '_')),
                 id=f'{slug}_{fslug}', pageviews=pageviews(f['titre']),
                 imageUrl=f'images/full/{slug}/{fslug}.webp',
                 thumbUrl=f'images/thumbs/{slug}/{fslug}.webp')
        print(f'  ~ {slug:<28} {nom:<42} -> {f["titre"]}')

    CACHE_PV.write_bytes(pickle.dumps(_pv))
    for slug, d in charges.items():
        paliers, rangs = rarete_pv.raretes([c.get('pageviews', 0) for c in d['cartes']])
        for c, p, r in zip(d['cartes'], paliers, rangs):
            if not c.get('rareteManuel'):
                c['rarete'], c['pv'] = p, rarete_pv.pv(r)
        for i, c in enumerate(d['cartes'], 1):
            c['numero'] = i
        print(f'  {slug:<32} {len(d["cartes"])} cartes')
    for s in signalements:
        print(' •', s)
    if essai:
        print('[essai] rien écrit')
        return

    for slug, d in charges.items():
        par_slug[slug].write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
        for e in idx['collections']:
            if e['slug'] == slug:
                e['nbCartes'] = len(d['cartes'])
    (RACINE / 'data' / 'collections.json').write_text(
        json.dumps(idx, ensure_ascii=False, indent=1), encoding='utf-8')
    print('écrit')


if __name__ == '__main__':
    main()
