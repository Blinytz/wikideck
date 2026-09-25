#!/usr/bin/env python3
"""Prepare les photos candidates de la page « Choix » de l'atelier.

Chercher une image, c'etait le plus long du travail manuel. Ce script le fait
a l'avance : pour chaque carte, il interroge Commons et garde jusqu'a huit
photos candidates, avec leur vignette et leur grande version. L'atelier les
affiche sous la carte ; un clic ouvre l'editeur avec la photo deja chargee,
il ne reste qu'a cadrer et enregistrer.

Les vignettes sont servies par upload.wikimedia.org, pas par GitHub Pages :
afficher des centaines de candidates n'use pas le quota de Pages.

Sortie : data/choix/<slug>.json  { id: [ {f, v, g, l, h}, ... ] }
         data/choix/index.json   { slug: nombre de cartes }

Usage : python choix_images.py <slug> [<slug>...] [--seul "Nom de carte"]...
"""
import re, sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
sys.path.insert(0, str(ICI))
import images_lib as il
from habiller_images import PARASITES

N = 8
# mots ajoutes a la recherche, par collection : ce qu'on veut VOIR sur la photo
SUFFIXES = {
    'noeuds': ['{en} knot', '{en}'],
    'cepages': ['{fr} raisin', '{en} grape', '{en} grapes vine'],
    'monnaies-du-monde': ['{en} banknote', '{en} coin', '{en}'],
    'monnaies-historiques': ['{en} coin', '{en}', '{fr}'],
    'langues-du-monde': ['{en} text', '{en} script', '{en} manuscript'],
}
DEFAUT = ['{en}', '{fr}']
ECARTER = re.compile(r'\.(svg|pdf|djvu|tif|tiff|webm|ogv|gif)$|map|flag|logo|locator|'
                     r'distribution|chart|graph|diagram|icon|coat of arms', re.I)


def chercher(requete):
    d = il.api('commons.wikimedia.org', dict(
        action='query', generator='search', gsrsearch=f'{requete} filetype:bitmap',
        gsrnamespace=6, gsrlimit=20, prop='imageinfo', iiprop='url|size',
        iiurlwidth=330))
    pages = ((d or {}).get('query') or {}).get('pages') or []
    pages = list(pages.values()) if isinstance(pages, dict) else pages
    pages.sort(key=lambda p: p.get('index', 99))
    for p in pages:
        f = p['title'].split(':', 1)[1]
        ii = (p.get('imageinfo') or [{}])[0]
        if ECARTER.search(f) or PARASITES.search(f) or not ii.get('thumburl'):
            continue
        l, h = ii.get('width', 0), ii.get('height', 0)
        if max(l, h) < 600:
            continue
        # grande version : la plus grande vignette STANDARD plus petite que
        # l'original. Wikimedia refuse les largeurs hors liste (400) et limite
        # le telechargement des originaux (429) : il ne sert que ses vignettes
        # de 330, 500, 960, 1280 ou 1920 px.
        largeur = max([w for w in (330, 500, 960, 1280) if w < l] or [330])
        grand = ii['thumburl'].replace('/330px-', f'/{largeur}px-')
        yield {'f': f, 'v': ii['thumburl'], 'g': grand, 'l': l, 'h': h}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    seuls = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == '--seul']
    slugs = [a for a in args if a not in seuls]
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    dossier = RACINE / 'data' / 'choix'
    dossier.mkdir(exist_ok=True)
    fi = dossier / 'index.json'
    index = json.loads(fi.read_text(encoding='utf-8')) if fi.exists() else {}

    for slug in slugs:
        cartes = json.loads(par_slug[slug].read_text(encoding='utf-8'))['cartes']
        if seuls:
            cartes = [c for c in cartes if c['nom'] in seuls]
        en = il.langlinks_en([c['titrePage'] for c in cartes])
        fs = dossier / f'{slug}.json'
        sortie = json.loads(fs.read_text(encoding='utf-8')) if fs.exists() else {}
        for c in cartes:
            nom_en = re.sub(r'\s*\(.*?\)', '', en.get(c['titrePage']) or c['nom'])
            nom_fr = re.sub(r'\s*\(.*?\)', '', c['nom'])
            vus, cands = set(), []
            for motif in SUFFIXES.get(slug, DEFAUT):
                for cand in chercher(motif.format(en=nom_en, fr=nom_fr)):
                    if cand['f'] not in vus:
                        vus.add(cand['f'])
                        cands.append(cand)
                if len(cands) >= N:
                    break
            sortie[c['id']] = cands[:N]
            print(f"  {c['nom']:<38} {len(cands[:N])} candidate(s)")
        fs.write_text(json.dumps(sortie, ensure_ascii=False, separators=(',', ':')),
                      encoding='utf-8')
        index[slug] = len(sortie)
    fi.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
