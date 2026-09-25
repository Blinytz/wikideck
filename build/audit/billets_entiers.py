#!/usr/bin/env python3
"""Pose tel quel un billet dont la photo d'origine est un scan plein cadre.

Quand le scan remplit toute l'image, il n'y a pas de fond a retirer : le
billet EST l'image. Le detoureur, lui, cherchait un « sujet » dedans et ne
gardait que le portrait. On pose donc l'image entiere, sans liseré ni cadre,
avec l'inclinaison et l'ombre de la collection. Seulement si les proportions
sont celles d'un billet (1,6 a 2,8).

Usage : python billets_entiers.py <slug> "Nom" ["Nom"...] [--apercu]
"""
import io, sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build')); sys.path.insert(0, str(ICI))
import images_lib as il
import habiller_images as hab
import unifier_rembg as U


# Planches de plusieurs billets remplacees par un billet seul, scanne plein cadre
FICHIERS = {
    'Couronne tchèque': '2000 Czech koruna Obverse.jpg',
    'Euro': 'EUR 50 obverse (2002 issue).jpg',
    'Dinar irakien': 'Quarter Iraqi Dinar 1973 Replacement Banknote RR.jpg',
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apercu = '--apercu' in sys.argv
    slug, noms = args[0], args[1:]
    cartes = {c['nom']: c for c in json.loads((RACINE / 'data' / f'{slug}.json').read_text(encoding='utf-8'))['cartes']}
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))
    style = dict(hab.STYLES[slug])
    for nom in noms:
        c = cartes[nom]
        if nom in FICHIERS:
            f = FICHIERS[nom]
            im = hab.charger(hab.url_fichier(f, 1280))
        else:
            im, f = U.source(c, sources)
        im = im.convert('RGBA')
        ratio = max(im.size) / min(im.size)
        if not 1.6 <= ratio <= 2.8:
            print(f'  ✗ {nom} : proportions {ratio:.2f}, pas un billet seul ({f[:50]})')
            continue
        img = hab.composer(im, dict(style, _nom=nom), True)
        print(f'  {nom:<28} ratio {ratio:.2f} <- {f[:55]}')
        if apercu:
            img.save(U.BROUILLON / (c['id'].split('_', 1)[1] + '.png'))
            continue
        brut = io.BytesIO(); img.save(brut, 'PNG')
        for rel, o in ((c['imageUrl'], il.to_full(brut.getvalue())), (c['thumbUrl'], il.to_thumb(brut.getvalue()))):
            (RACINE / rel).write_bytes(o)
        sources[c['id']] = dict(sources.get(c['id']) or {}, fichier=f, detourage='scan-entier')
    if not apercu:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
