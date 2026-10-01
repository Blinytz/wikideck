#!/usr/bin/env python3
"""Planisphere avec epingle rouge, pour l'encart des cartes d'iles.

Fond : les pays de Natural Earth (1:50 m, build/audit/geo/pays_50m.geojson),
en projection equirectangulaire, aux couleurs de Google Maps pour que
l'encart se fonde avec la carte principale. L'epingle a la forme de celle de
Google : sa pointe tombe exactement sur la latitude et la longitude donnees.

Usage en module : planisphere.carte(lat, lng, largeur) -> Image RGB
Usage direct    : python planisphere.py <lat> <lng> [fichier.png]
"""
import sys, json, math, functools
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


# ---------- cartes par continent (01/10/2026) ----------
# Le planisphere entier situait mal : l'epingle tombait dans un monde minuscule.
# On choisit la zone du lieu (dans cet ordre) et on la dessine avec les
# frontieres des Etats bien visibles. Emprises en degres : lng min, lng max,
# lat min, lat max ; l'Oceanie deborde l'antimeridien (lng jusqu'a 235).
ZONES = [
    ('Europe', (-32, 45, 34, 72)),
    ('Afrique', (-26, 56, -42, 38)),
    ('Amérique du Nord', (-170, -12, 7, 84)),
    ('Amérique du Sud', (-95, -28, -57, 14)),
    ('Asie', (25, 150, -11, 78)),
    ('Océanie', (105, 250, -50, 25)),
    ('Océan Indien', (15, 125, -58, 28)),
    ('Antarctique', (-180, 180, -90, -58)),
]
BORD = (120, 128, 120)          # frontieres
LITTORAL = (110, 160, 200)


def zone_de(lat, lng):
    lo = lng
    for nom, (a, b, c, d) in ZONES:
        x = lo + 360 if (b > 180 and lo < 0) else lo
        if nom == 'Afrique' and lo > 34 and lat > 12:        # Proche-Orient, Arabie : Asie
            continue
        if nom == 'Asie' and lo > 128 and lat < 0:           # Nouvelle-Guinee et au-dela : Oceanie
            continue
        if a <= x <= b and c <= lat <= d:
            return nom
    return None


@functools.lru_cache(maxsize=16)
def _anneaux():
    geo = json.loads((ICI / 'geo' / 'pays_50m.geojson').read_text(encoding='utf-8'))
    out = []
    for f in geo['features']:
        g = f['geometry']
        for poly in ([g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']):
            out.append(poly[0])
    return out


def _etendre(emprise, ratio):
    """Elargit l'emprise (en gardant son centre) pour atteindre le rapport
    largeur/hauteur voulu, une fois la correction cos(lat) appliquee."""
    a, b, c, d = emprise
    k = math.cos(math.radians((c + d) / 2))
    w, h = (b - a) * k, (d - c)
    if w / h < ratio:
        dw = (ratio * h - w) / k / 2
        a, b = a - dw, b + dw
    else:
        dh = (w / ratio - h) / 2
        c, d = max(-90, c - dh), min(90, d + dh)
    return a, b, c, d


def carte_zone(lat, lng, W=900, ratio=None):
    """Carte de la zone du lieu, frontieres visibles, epingle sur le lieu.
    `ratio` (largeur/hauteur) impose le format ; sinon celui de la zone."""
    nom = zone_de(lat, lng)
    if not nom:
        return carte(lat, lng, W)
    emprise = dict(ZONES)[nom]
    if ratio:
        emprise = _etendre(emprise, ratio)
    a, b, c, d = emprise
    k = math.cos(math.radians((c + d) / 2))
    H = round(W * (d - c) / ((b - a) * k))
    Ws, Hs = W * SUR, H * SUR
    im = Image.new('RGB', (Ws, Hs), EAU)
    dr = ImageDraw.Draw(im)
    deca = (0, 360) if b > 180 else (0,)

    def pt(x, y, dx):
        return (x + dx - a) / (b - a) * Ws, (d - y) / (d - c) * Hs
    for dx in deca:
        for an in _anneaux():
            xs = [x + dx for x, _ in an]
            if max(xs) < a - 5 or min(xs) > b + 5:
                continue
            dr.polygon([pt(x, y, dx) for x, y in an], fill=TERRE, outline=BORD, width=SUR)
    im = im.resize((W, H), Image.LANCZOS)
    x = lng + (360 if (b > 180 and lng < 0) else 0)
    px, py = (x - a) / (b - a) * W, (d - lat) / (d - c) * H
    hp = max(H * 0.13, W * 0.075)          # une carte large garde une epingle lisible
    if py - hp < 0:                                    # epingle hors du cadre en haut : bande d'eau
        marge = round(hp - py + 4)
        im2 = Image.new('RGB', (W, H + marge), EAU)
        im2.paste(im, (0, marge))
        im, py = im2, py + marge
    epingle(im, px, py, hp)
    return im
