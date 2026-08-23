#!/usr/bin/env python3
"""Crée les 33 cartes de personnage que fr.wikipedia ne traite pas à part.

fr.wikipedia a l'article de l'oeuvre, pas celui du personnage : pas de page
« Tanjiro Kamado », seulement « Demon Slayer » ; pas de « Travis Bickle »,
seulement « Taxi Driver ». Le document d'audit interdisait de substituer un
choix arbitraire, ces cartes étaient donc restées à créer.

Décision de l'utilisateur : accepter la page de l'oeuvre. Ce que cela implique,
et qu'il faut assumer les yeux ouverts :

  - le résumé de la carte parle de l'oeuvre, pas du personnage ;
  - §28.10 du document voulait qu'aucune carte n'existe des deux côtés du
    registre personnage/oeuvre. Sept de ces pages sont DÉJÀ des cartes des
    collections d'oeuvres. Pour celles-là, le `nom` de la carte reste celui du
    personnage — donc pas d'homonyme, la règle 5 tient — mais les deux cartes
    pointent sur la même page. C'est le prix, et il est signalé.

L'image, elle, est cherchée sur la page de l'oeuvre : c'est souvent l'affiche
ou la jaquette. Elle vaut mieux qu'une recherche web, qui donnait des acteurs.

Usage : python personnages_par_oeuvre.py [--essai]
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

CACHE_PV = RACINE / 'build' / '.cache_pageviews.pkl'
_pv = pickle.loads(CACHE_PV.read_bytes()) if CACHE_PV.exists() else {}

# (slug, nom de carte, page de l'oeuvre)
CARTES = [
    ('personnages-manga-anime', 'Tanjiro Kamado', 'Demon Slayer'),
    ('personnages-manga-anime', 'Nezuko Kamado', 'Demon Slayer'),
    ('personnages-manga-anime', 'Gojo Satoru', 'Jujutsu Kaisen'),
    ('personnages-manga-anime', 'Denji', 'Chainsaw Man'),
    ('personnages-manga-anime', 'Levi Ackerman', "L'Attaque des Titans"),
    ('personnages-manga-anime', 'Gon Freecss', 'Hunter × Hunter'),
    ('personnages-manga-anime', 'Killua Zoldyck', 'Hunter × Hunter'),
    ('personnages-manga-anime', 'Lelouch Lamperouge', 'Code Geass'),
    ('personnages-manga-anime', 'Portgas D. Ace', 'One Piece'),
    ('personnages-manga-anime', 'Shanks', 'One Piece'),
    ('personnages-cinema-serie', 'Travis Bickle', 'Taxi Driver'),
    ('personnages-cinema-serie', 'Amélie Poulain', "Le Fabuleux Destin d'Amélie Poulain"),
    ('personnages-cinema-serie', 'Jack Torrance', "Shining, l'enfant lumière"),
    ('personnages-cinema-serie', 'Maximus', 'Gladiator (film, 2000)'),
    ('personnages-cinema-serie', 'Omar Little', 'Sur écoute'),
    ('personnages-cinema-serie', 'Jack Bauer', '24 Heures chrono'),
    ('personnages-cinema-serie', 'OSS 117', 'OSS 117'),
    ('personnages-cinema-serie', 'E.T', "E.T., l'extra-terrestre"),
    ('personnages-jeu-video', 'Pyramid Head', 'Silent Hill 2'),
    ('personnages-jeu-video', '2B', 'Nier: Automata'),
    ('personnages-jeu-video', 'Sackboy', 'Little Big Planet (jeu vidéo, 2008)'),
    ('personnages-jeu-video', 'Big Daddy', 'BioShock'),
    ('personnages-jeu-video', 'Nemesis', 'Resident Evil 3: Nemesis'),
    ('personnages-jeu-video', 'Cuphead (personnage)', 'Cuphead'),
    ('personnages-litterature', 'Emma Bovary', 'Madame Bovary'),
    ('personnages-litterature', 'Anna Karénine', 'Anna Karénine'),
    ('personnages-litterature', 'Meursault', "L'Étranger"),
    ('personnages-litterature', 'Roméo et Juliette', 'Roméo et Juliette'),
    ('personnages-animation', 'WALL-E (personnage)', 'WALL-E'),
    ('personnages-animation', 'Vaiana', 'Vaiana : La Légende du bout du monde'),
    ('personnages-animation', 'Stitch', 'Lilo et Stitch'),
    ('personnages-animation', 'Sulli', 'Monstres et Cie'),
    ('personnages-bd-comics', 'Blake et Mortimer', 'Blake et Mortimer'),
    ('personnages-bd-comics', 'Rahan', 'Rahan'),
]


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


UA = 'wikideck-build/1.0 (projet perso; contact: claude.elk041@passmail.net)'


def slugifier(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def main():
    essai = '--essai' in sys.argv
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    # pages deja utilisees par une carte d'oeuvre : on veut savoir lesquelles
    pages_oeuvres = {}
    for c in idx['collections']:
        d = json.loads((RACINE / c['fichier']).read_text(encoding='utf-8'))
        for x in d['cartes']:
            pages_oeuvres.setdefault(x['titrePage'], []).append((c['slug'], x['nom']))

    R.charger_fiches([t for _, _, t in CARTES])
    charges, signalements, partagees = {}, [], []

    for slug, nom, titre in CARTES:
        f = R._cache.get('fiche:' + titre)
        if not f or f['statut'] != 'ok' or not f.get('extrait'):
            signalements.append(f'{slug} · {nom} : page « {titre} » non résolue')
            continue
        d = charges.setdefault(slug, json.loads(par_slug[slug].read_text(encoding='utf-8')))
        if any(x['nom'] == nom for x in d['cartes']):
            continue
        fslug = slugifier(nom)
        pris = {x['id'] for x in d['cartes']}
        while f'{slug}_{fslug}' in pris:
            fslug += '-b'
        d['cartes'].append({
            'id': f'{slug}_{fslug}', 'nom': nom, 'titrePage': f['titre'],
            'imageUrl': f'images/full/{slug}/{fslug}.webp',
            'thumbUrl': f'images/thumbs/{slug}/{fslug}.webp',
            'description': f['extrait'], 'collection': d['collection'],
            'lienWikipedia': 'https://fr.wikipedia.org/wiki/'
                             + urllib.parse.quote(f['titre'].replace(' ', '_')),
            'pageviews': pageviews(f['titre']), 'tags': [], 'numero': 0,
        })
        deja = pages_oeuvres.get(f['titre'])
        if deja:
            partagees.append(f"{nom} partage la page « {f['titre'] }» avec "
                             + ', '.join(f'{s} · {n}' for s, n in deja))
        print(f'  {slug:<26} {nom:<20} <- {f["titre"]}')

    CACHE_PV.write_bytes(pickle.dumps(_pv))
    for slug, d in charges.items():
        paliers, rangs = rarete_pv.raretes([c.get('pageviews', 0) for c in d['cartes']])
        for c, p, r in zip(d['cartes'], paliers, rangs):
            if not c.get('rareteManuel'):
                c['rarete'], c['pv'] = p, rarete_pv.pv(r)
        for i, c in enumerate(d['cartes'], 1):
            c['numero'] = i
        print(f'  {slug:<32} {len(d["cartes"])} cartes')

    print(f'\n{len(partagees)} carte(s) partagent leur page avec une carte d\'oeuvre :')
    for p in partagees:
        print('  •', p)
    for s in signalements:
        print(' ✗', s)
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
