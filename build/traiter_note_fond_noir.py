#!/usr/bin/env python3
"""Note atelier n1785504400444 — « Mettre un fond noir derrière ces images ».

Les logos des Coupes du monde viennent de l'app memo en JPEG : plus aucune
transparence, le fond est un aplat blanc. On ne peut donc pas recomposer sur
noir, il faut retrouver le fond.

Méthode : remplissage par diffusion depuis les bords sur les pixels quasi
blancs — seule la zone blanche CONNECTÉE au cadre devient noire. Les blancs
intérieurs (le trophée de 2022, le ballon de France 98) sont préservés parce
qu'ils ne touchent pas le bord. Une couronne de 3 px autour du masque est
fondue vers le noir proportionnellement à sa blancheur, sinon l'anticrénelage
du logo laisse un halo clair sur le fond noir.

La vignette est régénérée depuis la version full retouchée (mêmes réglages
d'encodage que build/images_lib.py).

L'edition 1958 ne figurait pas dans la selection de la note — 21 des 22
cartes. Elle a ete traitee ensuite, a la demande : un seul logo sur fond blanc
au milieu de vingt-et-un sur fond noir se lisait comme un oubli.

Usage : python traiter_note_fond_noir.py [--verifier] [id de carte...]
"""
import sys, json, io
from pathlib import Path
from collections import deque

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
NOTE = 'n1785504400444'

SEUIL_FOND = 238        # min(R,V,B) au-dessus -> candidat « fond blanc »
SEUIL_GRIS = 14         # max-min : au-delà, c'est une couleur, pas du blanc
COURONNE = 3            # px fondus autour du masque
THUMB_H = 160
QUALITE_FULL, QUALITE_THUMB = 90, 82


def masque_fond(arr):
    """Masque booléen du blanc connecté aux bords (diffusion 4-voisins)."""
    h, w, _ = arr.shape
    mini = arr.min(axis=2).astype(np.int16)
    maxi = arr.max(axis=2).astype(np.int16)
    blanc = (mini >= SEUIL_FOND) & (maxi - mini <= SEUIL_GRIS)

    vu = np.zeros((h, w), dtype=bool)
    file = deque()
    for x in range(w):
        for y in (0, h - 1):
            if blanc[y, x] and not vu[y, x]:
                vu[y, x] = True
                file.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if blanc[y, x] and not vu[y, x]:
                vu[y, x] = True
                file.append((y, x))
    while file:
        y, x = file.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and blanc[ny, nx] and not vu[ny, nx]:
                vu[ny, nx] = True
                file.append((ny, nx))
    return vu


def dilater(m, n):
    out = m.copy()
    for _ in range(n):
        d = out.copy()
        d[1:, :] |= out[:-1, :]
        d[:-1, :] |= out[1:, :]
        d[:, 1:] |= out[:, :-1]
        d[:, :-1] |= out[:, 1:]
        out = d
    return out


def sur_fond_noir(img):
    arr = np.asarray(img.convert('RGB')).astype(np.float32)
    m = masque_fond(arr.astype(np.uint8))
    couronne = dilater(m, COURONNE) & ~m

    # blancheur de la couronne : 215 -> 0 %, 255 -> 100 %
    mini = arr.min(axis=2)
    alpha = np.clip((mini - 215.0) / 40.0, 0.0, 1.0)
    alpha[~couronne] = 0.0
    alpha[m] = 1.0

    arr *= (1.0 - alpha)[:, :, None]        # fondu vers le noir
    return Image.fromarray(arr.round().clip(0, 255).astype(np.uint8)), m.mean()


def encoder(img, qualite):
    buf = io.BytesIO()
    img.save(buf, 'WEBP', quality=qualite)
    return buf.getvalue()


def main():
    verifier = '--verifier' in sys.argv
    explicites = [a for a in sys.argv[1:] if not a.startswith('--')]
    if explicites:
        cibles = explicites
    else:
        notes = json.loads((ROOT / 'build' / 'notes_atelier.json')
                           .read_text(encoding='utf-8'))
        cibles = next(n for n in notes['notes'] if n['id'] == NOTE)['images']

    for cid in cibles:
        col, slug = cid.split('_', 1)
        full = ROOT / 'images' / 'full' / col / f'{slug}.webp'
        thumb = ROOT / 'images' / 'thumbs' / col / f'{slug}.webp'
        if not full.exists():
            print(f'  ✗ {cid} : full absent')
            continue
        img, part = sur_fond_noir(Image.open(full))
        print(f'  {slug} — fond détecté sur {part * 100:.0f} % de l\'image')
        if verifier:
            continue
        full.write_bytes(encoder(img, QUALITE_FULL))
        r = THUMB_H / img.height
        thumb.write_bytes(encoder(
            img.resize((max(1, round(img.width * r)), THUMB_H), Image.LANCZOS),
            QUALITE_THUMB))
        orig = ROOT / 'images' / 'originaux' / col / f'{slug}.webp'
        if orig.exists():
            o, _ = sur_fond_noir(Image.open(orig))
            orig.write_bytes(encoder(o, 92))

    print(f'{len(cibles)} image(s) traitée(s)' if not verifier else 'contrôle seul')


if __name__ == '__main__':
    main()
