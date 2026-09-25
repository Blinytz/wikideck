#!/usr/bin/env python3
"""Remplace les billets mal detoures par un scan droit, decoupe en rectangle.

Certains billets resistent au detourage : le reseau ne garde que le portrait,
ou ronge les bords clairs. Commons a souvent, pour la meme monnaie, un scan
droit d'un billet seul sur fond uni. Un tel scan se decoupe EXACTEMENT : le
billet est le rectangle englobant de tout ce qui differe du fond. On le
cherche parmi les candidates de l'onglet Choix, en exigeant des proportions
de billet (rapport 1,6 a 2,8).

Usage : python billets_droits.py <slug> "Nom" ["Nom"...] [--apercu]
"""
import io, sys, json
from pathlib import Path
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build')); sys.path.insert(0, str(ICI))
import images_lib as il
import habiller_images as hab
import unifier_rembg as U


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apercu = '--apercu' in sys.argv
    slug, noms = args[0], args[1:]
    cartes = {c['nom']: c for c in json.loads((RACINE / 'data' / f'{slug}.json').read_text(encoding='utf-8'))['cartes']}
    cands = json.loads((RACINE / 'data' / 'choix' / f'{slug}.json').read_text(encoding='utf-8'))
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))
    style = dict(hab.STYLES[slug])
    for nom in noms:
        c = cartes[nom]
        trouve = None
        for k in cands.get(c['id'], []):
            im = hab.charger(k['g'])
            if im is None:
                continue
            vide = Image.new('L', im.size, 0)
            r = U.rectangle(im.convert('RGB'), vide)
            if r is None:
                continue
            ratio = max(r.size) / min(r.size)
            if 1.6 <= ratio <= 2.8 and min(r.size) >= 150:
                trouve = (r, k['f'])
                break
        if not trouve:
            print(f'  ✗ {nom} : aucun scan droit parmi les candidates')
            continue
        r, f = trouve
        img = hab.composer(r, dict(style, _nom=nom), True)
        print(f'  {nom:<28} <- {f[:60]}')
        if apercu:
            img.save(U.BROUILLON / (c['id'].split('_', 1)[1] + '.png'))
            continue
        brut = io.BytesIO(); img.save(brut, 'PNG')
        for rel, o in ((c['imageUrl'], il.to_full(brut.getvalue())), (c['thumbUrl'], il.to_thumb(brut.getvalue()))):
            (RACINE / rel).write_bytes(o)
        sources[c['id']] = {'source': 'commons', 'fichier': f, 'detourage': 'rectangle'}
    if not apercu:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
