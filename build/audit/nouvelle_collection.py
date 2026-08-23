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
    R.charger_fiches([t for _, t in plan['ajouts']])
    for nom, titre in plan['ajouts']:
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
