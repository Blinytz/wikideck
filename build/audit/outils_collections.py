#!/usr/bin/env python3
"""Petites operations sur les collections, sans perdre images ni retouches.

    deplacer(nom, src, dst)        une carte change de collection
    supprimer_collection(slug)     une collection disparait (cartes et images)
    ordonner(slug, titres)         les cartes suivent l'ordre donne (titres de pages)

Chaque operation garde ensemble : la carte, ses trois images (originaux, full,
thumbs), son cadrage et son statut d'atelier, sa source d'image, et recalcule
raretes et numeros.
"""
import sys, json, shutil
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
import rarete_pv

NOTES = RACINE / 'build' / 'notes_atelier.json'
SOURCES = RACINE / 'build' / 'images_sources.json'
INDEX = RACINE / 'data' / 'collections.json'


def _lire(p):
    return json.loads(p.read_text(encoding='utf-8'))


def _ecrire(p, d, indent=None):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=indent), encoding='utf-8')


def _fichier(slug):
    return RACINE / 'data' / f'{slug}.json'


def _recalculer(d, garder_ordre=True):
    paliers, rangs = rarete_pv.raretes([x.get('pageviews', 0) for x in d['cartes']])
    for i, (x, p, r) in enumerate(zip(d['cartes'], paliers, rangs), 1):
        if not x.get('rareteManuel'):
            x['rarete'], x['pv'] = p, rarete_pv.pv(r)
        x['numero'] = i


def _maj_index(slug, n=None, supprimer=False):
    idx = _lire(INDEX)
    if supprimer:
        idx['collections'] = [e for e in idx['collections'] if e['slug'] != slug]
    else:
        next(e for e in idx['collections'] if e['slug'] == slug)['nbCartes'] = n
    _ecrire(INDEX, idx, 1)


def deplacer(nom, src, dst):
    ds, dd = _lire(_fichier(src)), _lire(_fichier(dst))
    c = next(x for x in ds['cartes'] if x['nom'] == nom)
    ancien = c['id']
    f = ancien.split('_', 1)[1]
    nouveau = f'{dst}_{f}'
    for rep in ('full', 'thumbs', 'originaux'):
        a = RACINE / 'images' / rep / src / f'{f}.webp'
        if a.exists():
            b = RACINE / 'images' / rep / dst / f'{f}.webp'
            b.parent.mkdir(parents=True, exist_ok=True)
            a.replace(b)
    notes, sources = _lire(NOTES), _lire(SOURCES)
    for cle in ('cadrages', 'statuts'):
        if ancien in notes.get(cle, {}):
            notes[cle][nouveau] = notes[cle].pop(ancien)
    for n in notes.get('notes', []):
        n['images'] = [nouveau if i == ancien else i for i in n.get('images', [])]
    if ancien in sources:
        sources[nouveau] = sources.pop(ancien)
    c.update(id=nouveau, collection=dd['collection'], imageUrl=f'images/full/{dst}/{f}.webp',
             thumbUrl=f'images/thumbs/{dst}/{f}.webp')
    ds['cartes'] = [x for x in ds['cartes'] if x is not c]
    dd['cartes'].append(c)
    for slug, d in ((src, ds), (dst, dd)):
        _recalculer(d)
        _ecrire(_fichier(slug), d)
        _maj_index(slug, len(d['cartes']))
    _ecrire(NOTES, notes, 1)
    _ecrire(SOURCES, sources, 0)
    return nouveau


def supprimer_collection(slug):
    d = _lire(_fichier(slug))
    ids = {c['id'] for c in d['cartes']}
    notes, sources = _lire(NOTES), _lire(SOURCES)
    for cle in ('cadrages', 'statuts'):
        for i in ids:
            notes.get(cle, {}).pop(i, None)
    for i in ids:
        sources.pop(i, None)
    for rep in ('full', 'thumbs', 'originaux'):
        shutil.rmtree(RACINE / 'images' / rep / slug, ignore_errors=True)
    (RACINE / 'images' / 'planches' / f'{slug}.webp').unlink(missing_ok=True)
    _fichier(slug).unlink()
    _maj_index(slug, supprimer=True)
    pl = RACINE / 'data' / 'planches.json'
    if pl.exists():
        p = _lire(pl)
        p.pop(slug, None)
        _ecrire(pl, p)
    _ecrire(NOTES, notes, 1)
    _ecrire(SOURCES, sources, 0)
    return len(ids)


def ordonner(slug, titres):
    """Range les cartes dans l'ordre des titres de pages donnes ; les cartes
    absentes de la liste passent a la fin, dans leur ordre actuel."""
    d = _lire(_fichier(slug))
    rang = {t: i for i, t in enumerate(titres)}
    d['cartes'].sort(key=lambda c: rang.get(c['titrePage'], len(rang)))
    _recalculer(d)
    _ecrire(_fichier(slug), d)
    return [c['nom'] for c in d['cartes'] if c['titrePage'] not in rang]
