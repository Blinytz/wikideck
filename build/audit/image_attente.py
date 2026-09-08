#!/usr/bin/env python3
"""Pose une image d'attente, la meme pour toutes les cartes visees.

Cas d'usage : une collection dont aucune image libre n'existe. Les series
televisees en sont l'exemple. fr.wikipedia refuse toute image non libre, et
Commons n'heberge que les logos en lettrage, sous le seuil d'originalite.
Ce que la chaine trouve ensuite est du hors-sujet : un acteur, un cosplayeur,
un groupe homonyme.

Plutot que de livrer ce hors-sujet, on pose une image neutre et IDENTIQUE
partout. Trois consequences voulues :

  - la consigne 10 est respectee, aucune carte ne part sans image ;
  - l'utilisateur voit d'un coup d'oeil ce qui reste a faire, puisque toute
    carte encore grise est une carte non traitee ;
  - la provenance est marquee `attente`, ce qui range la carte dans la note
    d'atelier des images a relire.

L'image est un aplat sombre neutre avec un rectangle fin centre. Pas de
texte : un texte se lirait comme un titre de carte, et il faudrait le
traduire. Pas de couleur vive non plus, pour ne pas concurrencer les vraies
images dans la grille de l'atelier.

Usage : python image_attente.py <slug> [--essai]
"""
import sys, io, json
from pathlib import Path
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
import images_lib as il

FOND = (38, 40, 46)
TRAIT = (74, 78, 88)


def image():
    """Un aplat sombre, format portrait, avec un cadre fin centre."""
    L, H = 600, 800
    img = Image.new('RGB', (L, H), FOND)
    d = ImageDraw.Draw(img)
    m, e = 150, 3
    d.rectangle([m, m + 90, L - m, H - m - 90], outline=TRAIT, width=e)
    # deux traits obliques legers : lisibles en vignette, discrets en grand
    d.line([m, m + 90, L - m, H - m - 90], fill=TRAIT, width=e)
    d.line([L - m, m + 90, m, H - m - 90], fill=TRAIT, width=e)
    out = io.BytesIO()
    img.save(out, 'PNG')
    return out.getvalue()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit('slug de collection attendu')
    slug, essai = args[0], '--essai' in sys.argv

    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    entree = next((c for c in idx['collections'] if c['slug'] == slug), None)
    if not entree:
        sys.exit(f'collection « {slug} » inconnue')
    d = json.loads((RACINE / entree['fichier']).read_text(encoding='utf-8'))

    brut = image()
    th, fu = il.to_thumb(brut), il.to_full(brut)
    if not (th and fu):
        sys.exit("l'image d'attente n'a pas pu etre encodee")

    sources_f = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sources_f.read_text(encoding='utf-8'))

    posees = 0
    for c in d['cartes']:
        f = RACINE / c['imageUrl']
        if f.exists():
            continue
        posees += 1
        if essai:
            continue
        for rel, octets in ((c['imageUrl'], fu), (c['thumbUrl'], th)):
            p = RACINE / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(octets)
        sources[c['id']] = {'source': 'attente'}

    if not essai:
        sources_f.write_text(json.dumps(sources, ensure_ascii=False, indent=0),
                             encoding='utf-8')
    print(f'{posees} image(s) d\'attente posee(s) sur {len(d["cartes"])} cartes'
          + (' [essai]' if essai else ''))


if __name__ == '__main__':
    main()
