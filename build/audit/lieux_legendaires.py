#!/usr/bin/env python3
"""Sépare les lieux des créatures : nouvelle collection « Lieux légendaires ».

`creatures-et-legendes` mélangeait deux natures : des êtres (dragon, kraken,
vampire) et des endroits (Atlantide, El Dorado, Camelot). Les sept lieux
partent dans leur propre collection, complétée de vingt autres.

Ligne retenue pour ce qui entre : un lieu dont la renommée EST d'être un lieu
mythique — cité perdue, île fantôme, paradis, utopie. Sont donc écartés les
royaumes rattachés à un panthéon (Valhalla, Asgard, Niflheim, Duat, Tartare) :
la règle §26.1 du document d'audit les rend à leur mythologie, et Valhalla y
est déjà. Écartées aussi l'Arcadie, région grecque réelle, et les Hespérides,
dont l'article parle des nymphes et non du jardin.

Une carte déménage avec son image : l'`id` porte le slug de la collection, et
l'atelier en déduit chemins d'image, clé de cadrage et entrée de sources.

Usage : python lieux_legendaires.py [--essai]
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

SOURCE = 'creatures-et-legendes'
CIBLE = 'lieux-legendaires'
NOM_CIBLE = 'Lieux légendaires'

# les lieux déjà présents chez les créatures
A_DEPLACER = ['Atlantide', 'El Dorado', 'Shangri-La', 'Camelot',
              "Jardin d'Éden", 'Lémurie', 'Avalon']

# La carte El Dorado pointait sur « El Dorado (film, 1966) », un western de
# Howard Hawks. Le mythe, c'est « Eldorado ».
CORRECTIONS = {'El Dorado': 'Eldorado'}

# (nom de carte, titre fr.wikipedia) — chaque page a été ouverte et vérifiée
AJOUTS = [
    ('Hyperborée', 'Hyperboréens'),
    ('Thulé', 'Thulé (mythologie)'),
    ('Ys', 'Ys'),
    ('Brocéliande', 'Brocéliande'),
    ('Agartha', 'Agartha'),
    ('Shambhala', 'Shambhala (mythe)'),
    ("Cités d'or de Cibola", "Cités d'or"),
    ('Mu', 'Mu (continent)'),
    ('Aztlan', 'Aztlan'),
    ('Île de Brasil', 'Île de Brasil'),
    ('Kitej', 'Kitej'),
    # Ophir a été essayé puis retiré : ni fr.wikipedia ni Commons n'ont
    # d'image de ce pays biblique — tout ce qui porte ce nom est une ville du
    # Colorado, une ruée vers l'or australienne ou un canyon de Mars. Une
    # carte sans illustration juste vaut mieux qu'une illustration fausse.
    ('Pays de Pount', 'Pays de Pount'),
    ('Fontaine de Jouvence', 'Fontaine de Jouvence'),
    ('Pays de Cocagne', 'Pays de Cocagne'),
    ('Île de Saint-Brendan', 'Île de Saint-Brendan'),
    ('Tour de Babel', 'Tour de Babel'),
    ('Jérusalem céleste', 'Jérusalem céleste'),
    ('Sodome et Gomorrhe', 'Sodome et Gomorrhe'),
    ('Îles des Bienheureux', 'Îles des Bienheureux'),
]

UA = 'wikideck-build/1.0 (projet perso; contact: claude.elk041@passmail.net)'
CACHE_PV = RACINE / 'build' / '.cache_pageviews.pkl'
_pv = pickle.loads(CACHE_PV.read_bytes()) if CACHE_PV.exists() else {}


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
    essai = '--essai' in sys.argv
    fichier_src = RACINE / 'data' / f'{SOURCE}.json'
    src = json.loads(fichier_src.read_text(encoding='utf-8'))
    notes = json.loads((RACINE / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))
    sources = json.loads((RACINE / 'build' / 'images_sources.json').read_text(encoding='utf-8'))

    # --- 1. les lieux quittent les créatures
    deplacees, restantes, signalements = [], [], []
    for c in src['cartes']:
        (deplacees if c['nom'] in A_DEPLACER else restantes).append(c)
    absents = [n for n in A_DEPLACER if not any(c['nom'] == n for c in deplacees)]
    signalements += [f'{SOURCE} · « {n} » introuvable' for n in absents]

    for c in deplacees:
        ancien_id = c['id']
        fslug = ancien_id.split('_', 1)[1]
        nouveau_titre = CORRECTIONS.get(c['nom'])
        if nouveau_titre:
            fiche = R._cache.get('fiche:' + nouveau_titre)
            if not fiche or fiche['statut'] != 'ok':
                signalements.append(f'correction « {c["nom"]} » : page non résolue')
            else:
                c['titrePage'], c['description'] = fiche['titre'], fiche['extrait']
                c['lienWikipedia'] = lien(fiche['titre'])
                fslug = slugifier(fiche['titre'])
                # l'ancienne image illustrait le western, pas le mythe
                for rep in ('full', 'thumbs', 'originaux'):
                    f = RACINE / 'images' / rep / SOURCE / f'{ancien_id.split("_", 1)[1]}.webp'
                    if f.exists() and not essai:
                        f.unlink()
                sources.pop(ancien_id, None)
                print(f'  page corrigée : {c["nom"]} -> {fiche["titre"]}')
        nouveau_id = f'{CIBLE}_{fslug}'
        if not essai:
            for rep in ('full', 'thumbs', 'originaux'):
                a = RACINE / 'images' / rep / SOURCE / f'{ancien_id.split("_", 1)[1]}.webp'
                if a.exists():
                    b = RACINE / 'images' / rep / CIBLE / f'{fslug}.webp'
                    b.parent.mkdir(parents=True, exist_ok=True)
                    a.replace(b)
        if ancien_id in notes.get('cadrages', {}):
            notes['cadrages'][nouveau_id] = notes['cadrages'].pop(ancien_id)
        if ancien_id in sources:
            sources[nouveau_id] = sources.pop(ancien_id)
        for n in notes.get('notes', []):
            n['images'] = [nouveau_id if i == ancien_id else i for i in n.get('images', [])]
        c.update(id=nouveau_id, collection=NOM_CIBLE,
                 imageUrl=f'images/full/{CIBLE}/{fslug}.webp',
                 thumbUrl=f'images/thumbs/{CIBLE}/{fslug}.webp')
        c.pop('tags', None)
        c.pop('liensSortants', None)

    # --- 2. les lieux ajoutés
    R.charger_fiches([t for _, t in AJOUTS])
    pris = {c['id'] for c in deplacees}
    for nom, titre in AJOUTS:
        f = R._cache.get('fiche:' + titre)
        if not f or f['statut'] != 'ok' or not f.get('extrait'):
            signalements.append(f'{nom} · « {titre} » non résolue, carte non créée')
            continue
        fslug = slugifier(f['titre'])
        while f'{CIBLE}_{fslug}' in pris:
            fslug += '-b'
        pris.add(f'{CIBLE}_{fslug}')
        deplacees.append({
            'id': f'{CIBLE}_{fslug}', 'nom': nom, 'titrePage': f['titre'],
            'imageUrl': f'images/full/{CIBLE}/{fslug}.webp',
            'thumbUrl': f'images/thumbs/{CIBLE}/{fslug}.webp',
            'description': f['extrait'], 'collection': NOM_CIBLE,
            'lienWikipedia': lien(f['titre']), 'tags': [], 'numero': 0,
        })

    # --- 3. pageviews, rareté par quotas, renumérotation
    print(f'pageviews {DEBUT} -> {FIN}…')
    for lot in (deplacees, restantes):
        for c in lot:
            c['pageviews'] = pageviews(c['titrePage'])
    CACHE_PV.write_bytes(pickle.dumps(_pv))
    for cartes in (deplacees, restantes):
        paliers, rangs = rarete_pv.raretes([c['pageviews'] for c in cartes])
        for c, p, r in zip(cartes, paliers, rangs):
            if not c.get('rareteManuel'):
                c['rarete'], c['pv'] = p, rarete_pv.pv(r)
        for i, c in enumerate(cartes, 1):
            c['numero'] = i

    print(f'\n{NOM_CIBLE} : {len(deplacees)} cartes '
          f'({len(A_DEPLACER) - len(absents)} déplacées + {len(AJOUTS)} créées)')
    print(f'{src["collection"]} : {len(restantes)} cartes restantes')
    for s in signalements:
        print(' •', s)
    if essai:
        return

    # --- 4. écriture
    (RACINE / 'data' / f'{CIBLE}.json').write_text(json.dumps(
        {'collection': NOM_CIBLE, 'slug': CIBLE, 'cartes': deplacees},
        ensure_ascii=False), encoding='utf-8')
    src['cartes'] = restantes
    fichier_src.write_text(json.dumps(src, ensure_ascii=False), encoding='utf-8')

    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    for c in idx['collections']:
        if c['slug'] == SOURCE:
            c['nbCartes'] = len(restantes)
    rang = next(i for i, c in enumerate(idx['collections']) if c['slug'] == SOURCE)
    idx['collections'].insert(rang + 1, {
        'slug': CIBLE, 'nom': NOM_CIBLE, 'nbCartes': len(deplacees),
        'fichier': f'data/{CIBLE}.json'})
    (RACINE / 'data' / 'collections.json').write_text(
        json.dumps(idx, ensure_ascii=False, indent=1), encoding='utf-8')
    (RACINE / 'build' / 'notes_atelier.json').write_text(
        json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
    (RACINE / 'build' / 'images_sources.json').write_text(
        json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'{len(idx["collections"])} collections écrites')


if __name__ == '__main__':
    main()
