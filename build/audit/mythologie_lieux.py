#!/usr/bin/env python3
"""Passe mythologie : les lieux rejoignent « Lieux légendaires ».

Règle posée par l'utilisateur, et qui prime sur la §26.1 du document d'audit :
une carte qui désigne un ENDROIT et non un être est un terrain, donc elle va
avec les lieux, quel que soit le panthéon dont elle vient. Le Valhalla n'est
pas un personnage.

Les candidats ont été cherchés en lisant le résumé Wikipédia de chacune des
390 cartes de mythologie, pas au jugé. Trois passent la règle :

  Valhalla   « l'endroit où les valeureux guerriers défunts sont amenés »
  Yggdrasil  l'Arbre Monde, l'axe qui relie les neuf mondes
  Apsû       « le nom de l'océan souterrain », et non la divinité

Trois autres ont été examinées puis laissées où elles sont, faute d'être des
lieux : Ragnarök est un événement, Mjöllnir un objet, le Temps du rêve un
cadre cosmologique. Styx, Chaos et Érèbe restent aussi : leurs articles
traitent de la divinité, pas du fleuve ni de l'espace.

La même lecture a révélé deux cartes pointant sur un TABLEAU au lieu du sujet
mythologique — « Les Muses » sur une huile de Maurice Denis, « Hélène de
Troie » sur une toile de Rossetti. Corrigées ici.

Usage : python mythologie_lieux.py [--essai]
"""
import sys, json, re, unicodedata, urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE / 'build'))
import rarete_pv
import resoudre_pages as R

CIBLE, NOM_CIBLE = 'lieux-legendaires', 'Lieux légendaires'

# (slug d'origine, nom de la carte)
LIEUX = [
    ('mythologie-nordique', 'Valhalla'),
    ('mythologie-nordique', 'Yggdrasil'),
    ('mythologies-proche-orient', 'Apsû'),
]

# (slug, nom de carte, titre fr.wikipedia correct)
PAGES_FAUSSES = [
    ('dieux-et-figures-mythologiques-grecques', 'Les Muses', 'Muses'),
    ('dieux-et-figures-mythologiques-grecques', 'Hélène de Troie', 'Hélène (mythologie)'),
]


def slugifier(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def main():
    essai = '--essai' in sys.argv
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    notes = json.loads((RACINE / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))
    sources = json.loads((RACINE / 'build' / 'images_sources.json').read_text(encoding='utf-8'))
    charges, touches, signalements = {}, set(), []

    def charger(slug):
        if slug not in charges:
            charges[slug] = json.loads(par_slug[slug].read_text(encoding='utf-8'))
        return charges[slug]

    # --- pages fausses : le sujet est un tableau, pas la figure mythologique
    for slug, nom, titre in PAGES_FAUSSES:
        d = charger(slug)
        c = next((x for x in d['cartes'] if x['nom'] == nom), None)
        f = R._cache.get('fiche:' + titre)
        if c is None or not f or f['statut'] != 'ok':
            signalements.append(f'{slug} · « {nom} » : correction impossible')
            continue
        ancien = c['id']
        fslug = slugifier(f['titre'])
        c.update(titrePage=f['titre'], description=f['extrait'],
                 lienWikipedia='https://fr.wikipedia.org/wiki/'
                               + urllib.parse.quote(f['titre'].replace(' ', '_')),
                 id=f'{slug}_{fslug}',
                 imageUrl=f'images/full/{slug}/{fslug}.webp',
                 thumbUrl=f'images/thumbs/{slug}/{fslug}.webp')
        for rep in ('full', 'thumbs', 'originaux'):   # l'ancienne image est le tableau
            p = RACINE / 'images' / rep / slug / f'{ancien.split("_", 1)[1]}.webp'
            if p.exists() and not essai:
                p.unlink()
        sources.pop(ancien, None)
        notes.get('cadrages', {}).pop(ancien, None)
        touches.add(slug)
        print(f'  page corrigée : {nom} -> {f["titre"]}')

    # --- les lieux déménagent
    cible = charger(CIBLE)
    pris = {c['id'] for c in cible['cartes']}
    for slug, nom in LIEUX:
        d = charger(slug)
        c = next((x for x in d['cartes'] if x['nom'] == nom), None)
        if c is None:
            signalements.append(f'{slug} · « {nom} » introuvable')
            continue
        ancien = c['id']
        fslug = ancien.split('_', 1)[1]
        while f'{CIBLE}_{fslug}' in pris:
            fslug += '-b'
        nouveau = f'{CIBLE}_{fslug}'
        pris.add(nouveau)
        if not essai:
            for rep in ('full', 'thumbs', 'originaux'):
                a = RACINE / 'images' / rep / slug / f'{ancien.split("_", 1)[1]}.webp'
                if a.exists():
                    b = RACINE / 'images' / rep / CIBLE / f'{fslug}.webp'
                    b.parent.mkdir(parents=True, exist_ok=True)
                    a.replace(b)
        if ancien in notes.get('cadrages', {}):
            notes['cadrages'][nouveau] = notes['cadrages'].pop(ancien)
        if ancien in sources:
            sources[nouveau] = sources.pop(ancien)
        for n in notes.get('notes', []):
            n['images'] = [nouveau if i == ancien else i for i in n.get('images', [])]
        c.update(id=nouveau, collection=NOM_CIBLE,
                 imageUrl=f'images/full/{CIBLE}/{fslug}.webp',
                 thumbUrl=f'images/thumbs/{CIBLE}/{fslug}.webp')
        c.pop('tags', None)
        c.pop('liensSortants', None)
        d['cartes'] = [x for x in d['cartes'] if x is not c]
        cible['cartes'].append(c)
        touches.add(slug)
        touches.add(CIBLE)
        print(f'  {slug} -> {CIBLE} : {nom}')

    # --- rareté et numérotation des collections touchées
    for slug in sorted(touches):
        cartes = charges[slug]['cartes']
        paliers, rangs = rarete_pv.raretes([c.get('pageviews', 0) for c in cartes])
        for c, p, r in zip(cartes, paliers, rangs):
            if not c.get('rareteManuel'):
                c['rarete'], c['pv'] = p, rarete_pv.pv(r)
        for i, c in enumerate(cartes, 1):
            c['numero'] = i
        print(f'  {slug:<42} {len(cartes)} cartes')

    for s in signalements:
        print(' •', s)
    if essai:
        print('[essai] rien écrit')
        return

    for slug in touches:
        par_slug[slug].write_text(json.dumps(charges[slug], ensure_ascii=False),
                                  encoding='utf-8')
        for e in idx['collections']:
            if e['slug'] == slug:
                e['nbCartes'] = len(charges[slug]['cartes'])
    (RACINE / 'data' / 'collections.json').write_text(
        json.dumps(idx, ensure_ascii=False, indent=1), encoding='utf-8')
    (RACINE / 'build' / 'notes_atelier.json').write_text(
        json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
    (RACINE / 'build' / 'images_sources.json').write_text(
        json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')
    print('écrit')


if __name__ == '__main__':
    main()
