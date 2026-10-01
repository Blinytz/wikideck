#!/usr/bin/env python3
"""Ajoute un encart de situation dans le coin d'une photo de carte.

  deserts, lacs        : planisphere avec epingle sur les coordonnees Wikidata
                         (build/audit/geo/coords_lieux.json)
  regions-francaises   : carte de France, la region en rouge (contours
                         build/audit/geo/regions_france.geojson) ; Guyane :
                         planisphere

L'encart est incruste dans l'IMAGE D'ORIGINE, dans le coin le plus calme de
la partie que la carte montre (cadrage de l'atelier) : il survit donc a un
recadrage leger. L'operation est notee dans images_sources.json (« encart »)
et n'est jamais appliquee deux fois.

Usage : python encart_photos.py <slug>... [--apercu]
"""
import io, sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE / 'build'))
import planisphere
import images_lib as il

BROUILLON = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                 r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                 r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\encarts')
REGIONS = {  # titre de page -> nom dans le geojson
    'Auvergne-Rhône-Alpes': 'Auvergne-Rhône-Alpes', 'Bourgogne-Franche-Comté': 'Bourgogne-Franche-Comté',
    'Bretagne (région administrative)': 'Bretagne', 'Centre-Val de Loire': 'Centre-Val de Loire',
    'Politique en Corse': 'Corse', 'Grand Est': 'Grand Est', 'Hauts-de-France': 'Hauts-de-France',
    'Île-de-France': 'Île-de-France', 'Nouvelle-Aquitaine': 'Nouvelle-Aquitaine',
    'Occitanie (région administrative)': 'Occitanie', 'Pays de la Loire': 'Pays de la Loire',
    "Provence-Alpes-Côte d'Azur": "Provence-Alpes-Côte d'Azur", 'Normandie (région administrative)': 'Normandie',
}
GUYANE = (4.0, -53.0)


def carte_france(region, W=700):
    geo = json.loads((ICI / 'geo' / 'regions_france.geojson').read_text(encoding='utf-8'))
    x0, x1, y0, y1 = -5.4, 9.8, 41.2, 51.3                     # emprise metropole + Corse
    import math
    k = math.cos(math.radians(46.5))
    H = round(W * (y1 - y0) / ((x1 - x0) * k))
    S = 3
    im = Image.new('RGB', (W * S, H * S), planisphere.EAU)
    d = ImageDraw.Draw(im)

    def pt(lo, la):
        return (lo - x0) * k / ((x1 - x0) * k) * W * S, (y1 - la) / (y1 - y0) * H * S
    for f in geo['features']:
        g = f['geometry']
        polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        rouge = f['properties']['nom'] == region
        for poly in polys:
            d.polygon([pt(*p) for p in poly[0]], fill=(222, 52, 46) if rouge else planisphere.TERRE,
                      outline=(150, 150, 150))
    return im.resize((W, H), Image.LANCZOS)


def coin_calme(img, vis, ew, eh):
    """Coin de la zone visible ou l'image est la plus uniforme."""
    x0, y0, x1, y1 = vis
    m = int((x1 - x0) * 0.03)
    coins = [(x0 + m, y1 - m - eh), (x1 - m - ew, y1 - m - eh), (x0 + m, y0 + m), (x1 - m - ew, y0 + m)]
    g = np.asarray(img.convert('L')).astype(float)

    def agitation(c):
        x, y = c
        z = g[max(0, y):y + eh, max(0, x):x + ew]
        return z.std() if z.size else 1e9
    return min(coins, key=agitation)


def poser(img, encart, vis):
    x0, y0, x1, y1 = vis
    ew = int((x1 - x0) * 0.3)
    eh = round(ew * encart.height / encart.width)
    e = encart.resize((ew, eh), Image.LANCZOS)
    x, y = coin_calme(img, vis, ew, eh)
    b = max(3, ew // 120)
    ombre = Image.new('L', (ew + 8 * b, eh + 8 * b), 0)
    ImageDraw.Draw(ombre).rectangle((4 * b, 4 * b, ew + 4 * b, eh + 4 * b), fill=110)
    ombre = ombre.filter(ImageFilter.GaussianBlur(3 * b))
    img.paste((0, 0, 0), (x - 3 * b, y - 2 * b), ombre)
    ImageDraw.Draw(img).rectangle((x - b, y - b, x + ew + b - 1, y + eh + b - 1), fill='white')
    img.paste(e, (x, y))


def main():
    apercu = '--apercu' in sys.argv
    slugs = [a for a in sys.argv[1:] if not a.startswith('--')]
    coords = json.loads((ICI / 'geo' / 'coords_lieux.json').read_text(encoding='utf-8'))
    fn, fs = RACINE / 'build' / 'notes_atelier.json', RACINE / 'build' / 'images_sources.json'
    notes, sources = json.loads(fn.read_text(encoding='utf-8')), json.loads(fs.read_text(encoding='utf-8'))
    BROUILLON.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        cartes = json.loads((RACINE / 'data' / f'{slug}.json').read_text(encoding='utf-8'))['cartes']
        n = 0
        for c in cartes:
            if (sources.get(c['id']) or {}).get('encart'):
                continue
            f = c['id'].split('_', 1)[1]
            orig = RACINE / 'images' / 'originaux' / slug / f'{f}.webp'
            img = Image.open(orig if orig.exists() else RACINE / c['imageUrl']).convert('RGB')
            iw, ih = img.size
            cad = notes['cadrages'].get(c['id']) if orig.exists() else None
            if cad and cad.get('w'):
                w = cad['w'] * iw
                h = w * 3 / 4
                vis = [cad['cx'] * iw - w / 2, cad['cy'] * ih - h / 2, cad['cx'] * iw + w / 2, cad['cy'] * ih + h / 2]
            else:
                vis = [0, 0, iw, ih]
            vis = [int(max(0, vis[0])), int(max(0, vis[1])), int(min(iw, vis[2])), int(min(ih, vis[3]))]
            if slug == 'regions-francaises':
                enc = carte_france(REGIONS[c['titrePage']]) if c['titrePage'] in REGIONS \
                    else planisphere.carte(*GUYANE, 900)
            else:
                ll = coords.get(c['titrePage'])
                if not ll:
                    print(f"  ✗ {c['nom']} : pas de coordonnees")
                    continue
                enc = planisphere.carte(ll[0], ll[1], 900)
            poser(img, enc, vis)
            carte = img.crop(vis)
            if apercu:
                carte.save(BROUILLON / f'{slug}_{f}.png')
                n += 1
                continue
            if orig.exists():
                b = io.BytesIO(); img.save(b, 'WEBP', quality=90); orig.write_bytes(b.getvalue())
            brut = io.BytesIO(); carte.save(brut, 'PNG')
            (RACINE / c['imageUrl']).write_bytes(il.to_full(brut.getvalue()))
            (RACINE / c['thumbUrl']).write_bytes(il.to_thumb(brut.getvalue()))
            sources[c['id']] = dict(sources.get(c['id']) or {}, encart='region' if slug == 'regions-francaises' else 'planisphere')
            n += 1
        print(f'{slug} : {n} encart(s)')
    if not apercu:
        fs.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
