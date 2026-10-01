#!/usr/bin/env python3
"""Planisphere avec epingle rouge, pour l'encart des cartes d'iles.

Fond : les pays de Natural Earth (1:50 m, build/audit/geo/pays_50m.geojson),
en projection equirectangulaire, aux couleurs de Google Maps pour que
l'encart se fonde avec la carte principale. L'epingle a la forme de celle de
Google : sa pointe tombe exactement sur la latitude et la longitude donnees.

Usage en module : planisphere.carte(lat, lng, largeur) -> Image RGB
Usage direct    : python planisphere.py <lat> <lng> [fichier.png]
"""
import sys, json, functools
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ICI = Path(__file__).resolve().parent
EAU = (170, 218, 255)
TERRE = (236, 240, 232)
FRONTIERE = (196, 202, 196)
COTE = (160, 196, 222)
LAT_HAUT, LAT_BAS = 84, -60          # l'Antarctique et le Grand Nord n'apportent rien
SUR = 3                              # sur-echantillonnage (lissage des traits)


def xy(lng, lat, W, H):
    return (lng + 180) / 360 * W, (LAT_HAUT - lat) / (LAT_HAUT - LAT_BAS) * H


@functools.lru_cache(maxsize=4)
def fond(W):
    H = round(W * (LAT_HAUT - LAT_BAS) / 360)
    Ws, Hs = W * SUR, H * SUR
    im = Image.new('RGB', (Ws, Hs), EAU)
    d = ImageDraw.Draw(im)
    geo = json.loads((ICI / 'geo' / 'pays_50m.geojson').read_text(encoding='utf-8'))
    anneaux = []
    for f in geo['features']:
        g = f['geometry']
        polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        for poly in polys:
            anneaux.append([xy(x, y, Ws, Hs) for x, y in poly[0]])
    for a in anneaux:                                    # terres
        if len(a) > 2:
            d.polygon(a, fill=TERRE)
    for a in anneaux:                                    # frontieres, fines
        if len(a) > 2:
            d.line(a + [a[0]], fill=FRONTIERE, width=max(1, SUR // 2))
    im = im.resize((W, H), Image.LANCZOS)
    return im


def epingle(im, x, y, h):
    """Epingle facon Google, pointe en (x, y), hauteur h."""
    r = h * 0.36
    cx, cy = x, y - h + r
    ombre = Image.new('L', im.size, 0)
    ImageDraw.Draw(ombre).ellipse((x - r * 0.7, y - r * 0.18, x + r * 0.7, y + r * 0.18), fill=90)
    noir = (0, 0, 0, 255) if im.mode == 'RGBA' else (0, 0, 0)
    im.paste(noir, (0, 0), ombre.filter(ImageFilter.GaussianBlur(r * 0.2)))
    d = ImageDraw.Draw(im)
    rouge, sombre = (234, 67, 53), (165, 39, 30)
    # la goutte : un disque et un triangle vers la pointe
    d.polygon([(cx - r * 0.86, cy + r * 0.5), (cx + r * 0.86, cy + r * 0.5), (x, y)], fill=rouge, outline=sombre)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rouge, outline=sombre, width=max(1, int(r * 0.08)))
    d.polygon([(cx - r * 0.8, cy + r * 0.55), (cx + r * 0.8, cy + r * 0.55), (x, y - 1)], fill=rouge)
    ri = r * 0.38
    d.ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=sombre)


def carte(lat, lng, W=900):
    base = fond(W)
    h = base.height * 0.16
    # une bande d'eau en haut : l'epingle d'une ile du Grand Nord (Groenland,
    # Svalbard) ne sort pas du cadre
    marge = round(h)
    im = Image.new('RGB', (base.width, base.height + marge), EAU)
    im.paste(base, (0, marge))
    x, y = xy(lng, lat, base.width, base.height)
    epingle(im, x, y + marge, h)
    return im


if __name__ == '__main__':
    lat, lng = float(sys.argv[1]), float(sys.argv[2])
    carte(lat, lng).save(sys.argv[3] if len(sys.argv) > 3 else 'planisphere.png')
