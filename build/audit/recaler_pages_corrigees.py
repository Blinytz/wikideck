#!/usr/bin/env python3
"""Recalage des cartes dont l'audit a changé la page (§2.1, §15.1, §18.1, §30.1).

Ces cartes ont changé de sujet, pas seulement de titre. Deux conséquences que
`creer_cartes.py` ne pouvait pas traiter, l'`id` y servant encore de clé de
déménagement :

  - l'`id` gardait le slug de l'ANCIEN sujet : la carte du télégraphe
    s'appelait `inventions-importantes_telephone`, celle du Seigneur des
    anneaux gardait « serie-de-films ». L'atelier en déduit les chemins
    d'image : autant qu'il désigne le bon sujet.
  - pour les deux cartes que §18.1 demandait de VÉRIFIER, le nom affiché doit
    suivre la page retenue. « Aigle pêcheur » est un terme ambigu ; la page
    est celle du Balbuzard pêcheur, la carte prend ce nom.

§18.1 tranche par ailleurs le cas du pigeon voyageur : l'oiseau disparu
emblématique est la Tourte voyageuse, le pigeon voyageur n'étant qu'une
variété domestique. Le résolveur ne pouvait pas choisir seul entre les deux —
il rapproche les titres, et « Pigeon voyageur » ressemble plus à lui-même.

Usage : python recaler_pages_corrigees.py
"""
import sys, json, re, unicodedata, urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent

# cartes dont le nom affiché doit suivre la page retenue (§18.1)
RENOMMER_SUR_PAGE = {'oiseaux_balbuzard-pecheur', 'oiseaux_corbeau'}
# le choix que le résolveur ne pouvait pas faire (§18.1)
TOURTE = ('oiseaux', 'Pigeon voyageur', 'Tourte voyageuse')


def slugifier(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def main():
    from resoudre_pages import _cache
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    notes = json.loads((RACINE / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))
    sources = json.loads((RACINE / 'build' / 'images_sources.json').read_text(encoding='utf-8'))

    # la carte du pigeon voyageur bascule sur la tourte
    for c in idx['collections']:
        if c['slug'] != TOURTE[0]:
            continue
        d = json.loads((RACINE / c['fichier']).read_text(encoding='utf-8'))
        for x in d['cartes']:
            if x['nom'] != TOURTE[1]:
                continue
            f = _cache.get('fiche:' + TOURTE[2])
            if not f or f['statut'] != 'ok':
                print(f'  ✗ page « {TOURTE[2]} » introuvable, carte laissée en état')
                break
            x['nom'], x['titrePage'] = TOURTE[2], f['titre']
            x['description'] = f['extrait']
            x['lienWikipedia'] = ('https://fr.wikipedia.org/wiki/'
                                  + urllib.parse.quote(f['titre'].replace(' ', '_')))
            print(f'  {TOURTE[1]} -> {f["titre"]} (§18.1)')
        (RACINE / c['fichier']).write_text(json.dumps(d, ensure_ascii=False),
                                           encoding='utf-8')

    renommees = 0
    for c in idx['collections']:
        chemin = RACINE / c['fichier']
        d = json.loads(chemin.read_text(encoding='utf-8'))
        pris = {x['id'] for x in d['cartes']}
        change = False
        for x in d['cartes']:
            if x['id'] in RENOMMER_SUR_PAGE and x['nom'] != x['titrePage']:
                print(f"  {x['nom']} -> {x['titrePage']} (nom aligné sur la page)")
                x['nom'] = x['titrePage']
                change = True
            attendu = slugifier(x['titrePage'])
            actuel = x['id'].split('_', 1)[1]
            if attendu == actuel or f"{c['slug']}_{attendu}" in pris:
                continue
            ancien_id, nouveau_id = x['id'], f"{c['slug']}_{attendu}"
            for rep in ('full', 'thumbs', 'originaux'):
                src = RACINE / 'images' / rep / c['slug'] / f'{actuel}.webp'
                if src.exists():
                    src.replace(RACINE / 'images' / rep / c['slug'] / f'{attendu}.webp')
            if ancien_id in notes.get('cadrages', {}):
                notes['cadrages'][nouveau_id] = notes['cadrages'].pop(ancien_id)
            if ancien_id in sources:
                sources[nouveau_id] = sources.pop(ancien_id)
            for n in notes.get('notes', []):
                n['images'] = [nouveau_id if i == ancien_id else i
                               for i in n.get('images', [])]
            pris.discard(ancien_id)
            pris.add(nouveau_id)
            x['id'] = nouveau_id
            x['imageUrl'] = f"images/full/{c['slug']}/{attendu}.webp"
            x['thumbUrl'] = f"images/thumbs/{c['slug']}/{attendu}.webp"
            print(f'  {ancien_id} -> {nouveau_id}')
            renommees += 1
            change = True
        if change:
            chemin.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')

    (RACINE / 'build' / 'notes_atelier.json').write_text(
        json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
    (RACINE / 'build' / 'images_sources.json').write_text(
        json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'{renommees} identifiant(s) recalé(s) sur leur page')


if __name__ == '__main__':
    sys.path.insert(0, str(ICI))
    main()
