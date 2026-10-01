#!/usr/bin/env python3
"""Remplace l'ancien planisphere des cartes par la carte du continent.

L'ancien encart est retrouve dans l'image d'origine (images/originaux) a sa
couleur d'eau, propre au planisphere ; la nouvelle carte de zone, au meme
format, est posee exactement par-dessus. L'image de la carte est ensuite
recoupee selon le cadrage enregistre : les retouches de l'atelier restent.

Usage : python remplacer_encarts.py <slug>... [--apercu]
"""
import io, re, sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI)); sys.path.insert(0, str(RACINE / 'build'))
import planisphere as P
import images_lib as il
BROUILLON = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                 r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                 r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\encarts2')


def coordonnees():
    """{titrePage ou nom: (lat, lng)} depuis toutes les sources connues."""
    import iles_maps as M, fleuves_maps as F
    out = {}
    for nom, v in list(M.COORDS.items()) + list(M.ETENDUES.items()):
        out[nom] = (v[0], v[1])
    for nom, v in F.FLEUVES.items():
        out[nom] = (v[1], v[2])
    for nom, v in F.LIEUX.items():
        out[nom] = (v[4][1], v[4][2]) if v[4] and v[4][0] == 'pin' else (v[0], v[1])
    for nom, t in F.TRACES.items():
        e = F.etendue(t)
        if e:
            out.setdefault(nom, (e[0], e[1]))
    out.update({k: tuple(v) for k, v in json.loads((ICI / 'geo' / 'coords_lieux.json').read_text(encoding='utf-8')).items()})
    return out


def trouver_encart(im):
    """Boite (x0, y0, x1, y1) de l'ancien planisphere, cadre blanc exclu."""
    a = np.asarray(im).astype(int)
    m = (abs(a[..., 0] - P.EAU[0]) < 9) & (abs(a[..., 1] - P.EAU[1]) < 9) & (abs(a[..., 2] - P.EAU[2]) < 9)
    lig, col = m.sum(1), m.sum(0)
    if lig.max() < 40:
        return None
    ys = np.nonzero(lig > lig.max() * 0.25)[0]
    xs = np.nonzero(col > col.max() * 0.25)[0]
    # le plus long segment continu (l'encart, pas une flaque isolee)
    def segment(v):
        best, cur = (v[0], v[0]), [v[0], v[0]]
        for x in v[1:]:
            if x <= cur[1] + 3:
                cur[1] = x
            else:
                cur = [x, x]
            if cur[1] - cur[0] > best[1] - best[0]:
                best = tuple(cur)
        return best
    (x0, x1), (y0, y1) = segment(xs), segment(ys)
    # on reprend jusqu'au cadre blanc
    def blanc(x, y):
        return a[y, x].min() > 238
    while x0 > 0 and not blanc(x0 - 1, (y0 + y1) // 2): x0 -= 1
    while x1 < a.shape[1] - 1 and not blanc(x1 + 1, (y0 + y1) // 2): x1 += 1
    while y0 > 0 and not blanc((x0 + x1) // 2, y0 - 1): y0 -= 1
    while y1 < a.shape[0] - 1 and not blanc((x0 + x1) // 2, y1 + 1): y1 += 1
    return x0, y0, x1 + 1, y1 + 1


def main():
    apercu = '--apercu' in sys.argv
    slugs = [a for a in sys.argv[1:] if not a.startswith('--')]
    co = coordonnees()
    notes = json.loads((RACINE / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))
    fs = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(fs.read_text(encoding='utf-8'))
    BROUILLON.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        cartes = json.loads((RACINE / 'data' / f'{slug}.json').read_text(encoding='utf-8'))['cartes']
        n = 0
        for c in cartes:
            if (sources.get(c['id']) or {}).get('encart_zone'):
                continue
            ll = co.get(c['nom']) or co.get(c['titrePage'])
            if not ll:
                u = (sources.get(c['id']) or {}).get('url') or ''
                m = re.search(r'!3d(-?[\d.]+)!4d(-?[\d.]+)', u) or re.search(r'/@(-?[\d.]+),(-?[\d.]+)', u)
                ll = (float(m.group(1)), float(m.group(2))) if m else None
            f = c['id'].split('_', 1)[1]
            orig = RACINE / 'images' / 'originaux' / slug / f'{f}.webp'
            if not ll or not orig.exists():
                continue
            im = Image.open(orig).convert('RGB')
            b = trouver_encart(im)
            if not b:
                continue
            x0, y0, x1, y1 = b
            w, h = x1 - x0, y1 - y0
            if w < 60 or h < 30:
                continue
            neuf = P.carte_zone(ll[0], ll[1], max(900, w), ratio=w / h).resize((w, h), Image.LANCZOS)
            im.paste(neuf, (x0, y0))
            cad = notes['cadrages'].get(c['id']) or {'cx': .5, 'cy': .5, 'w': 1}
            iw, ih = im.size
            cw = cad.get('w', 1) * iw
            ch = cw * 3 / 4
            vis = (max(0, round(cad['cx'] * iw - cw / 2)), max(0, round(cad['cy'] * ih - ch / 2)),
                   min(iw, round(cad['cx'] * iw + cw / 2)), min(ih, round(cad['cy'] * ih + ch / 2)))
            carte = im.crop(vis)
            if apercu:
                carte.resize((800, 600)).save(BROUILLON / f'{slug}_{f}.png')
                n += 1
                continue
            bo = io.BytesIO(); im.save(bo, 'WEBP', quality=90); orig.write_bytes(bo.getvalue())
            br = io.BytesIO(); carte.save(br, 'PNG')
            (RACINE / c['imageUrl']).write_bytes(il.to_full(br.getvalue()))
            (RACINE / c['thumbUrl']).write_bytes(il.to_thumb(br.getvalue()))
            sources[c['id']] = dict(sources.get(c['id']) or {}, encart_zone=P.zone_de(*ll) or 'monde')
            n += 1
        print(f'{slug} : {n} encart(s) remplace(s) sur {len(cartes)}')
    if not apercu:
        fs.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
