#!/usr/bin/env python3
"""Carte de l'ocean Arctique : projection polaire (Google Maps ne montre pas
le pole), pays de Natural Earth avec frontieres, aux couleurs des cartes
Google du jeu, quelques noms, et l'encart planisphere. L'original fait
2000 x 1500 ; la carte en montre les 80 % du centre."""
import io, sys, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI)); sys.path.insert(0, str(RACINE / 'build'))
import planisphere as P, iles_maps as M, images_lib as il

W, H, S = 2000, 1500, 2
EAU, TERRE, BORD, GLACE = (144, 212, 232), (205, 232, 213), (150, 160, 150), (246, 248, 250)
R_MAX = 37                      # degres depuis le pole jusqu'au bord vertical
ROT = -105                      # orientation : l'Europe et l'Atlantique en bas


def proj(lng, lat):
    r = (90 - lat) / R_MAX * (H * S / 2)
    t = math.radians(lng + ROT)
    return W * S / 2 + r * math.cos(t), H * S / 2 - r * math.sin(t)     # vue du dessus du pole


def main():
    im = Image.new('RGB', (W * S, H * S), EAU)
    d = ImageDraw.Draw(im)
    geo = json.loads((ICI / 'geo' / 'pays_50m.geojson').read_text(encoding='utf-8'))
    for f in geo['features']:
        g = f['geometry']
        for poly in ([g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']):
            ring = poly[0]
            if max(y for _, y in ring) < 90 - R_MAX * 1.45:
                continue
            fill = GLACE if f['properties'].get('ADMIN') == 'Greenland' else TERRE
            d.polygon([proj(x, max(y, 40)) for x, y in ring], fill=fill, outline=BORD, width=2 * S)
    fnt = lambda t: ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', t * S)
    for nom, lng, lat, t in [('Océan Arctique', 20, 86.5, 34), ('Groenland', -41, 74, 28), ('Canada', -100, 66, 28),
                             ('Russie', 100, 68, 28), ('Alaska', -152, 66, 24), ('Norvège', 14, 66.5, 22),
                             ('Islande', -18.5, 65, 20), ('Svalbard', 18, 78.6, 20), ('Pôle Nord', 0, 90, 20)]:
        x, y = proj(lng, lat)
        d.text((x, y), nom, font=fnt(t), fill=(60, 70, 80) if nom != 'Océan Arctique' else (30, 90, 140), anchor='mm')
    x, y = proj(0, 90)
    d.ellipse((x - 7 * S, y + 18 * S - 7 * S, x + 7 * S, y + 18 * S + 7 * S), fill=(220, 50, 40))
    im = im.resize((W, H), Image.LANCZOS)
    img = M.composer(im, P.carte(89, 0, 900), None)
    c = next(c for c in json.loads((RACINE / 'data' / 'fleuves-mers-et-oceans.json').read_text(encoding='utf-8'))['cartes']
             if c['nom'] == 'Océan Arctique')
    f = c['id'].split('_', 1)[1]
    cw, ch = int(W * .8), int(H * .8)
    centre = img.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch))
    for rel, o in ((f'images/originaux/fleuves-mers-et-oceans/{f}.webp', M.webp(img, 88)),
                   (c['imageUrl'], M.webp(centre.resize((800, 600), Image.LANCZOS), 90)),
                   (c['thumbUrl'], M.webp(centre.resize((213, 160), Image.LANCZOS), 82))):
        (RACINE / rel).write_bytes(o)
    fn = RACINE / 'build' / 'notes_atelier.json'
    n = json.loads(fn.read_text(encoding='utf-8'))
    n['cadrages'][c['id']] = {'cx': .5, 'cy': .5, 'w': .8, 'original': True, 'editeLe': 0, 'auto': True}
    fn.write_text(json.dumps(n, ensure_ascii=False, indent=1), encoding='utf-8')
    fs = RACINE / 'build' / 'images_sources.json'
    s = json.loads(fs.read_text(encoding='utf-8'))
    s[c['id']] = {'source': 'natural-earth-polaire', 'encart_zone': 'monde'}
    fs.write_text(json.dumps(s, ensure_ascii=False, indent=0), encoding='utf-8')
    print('pose', c['id'])


if __name__ == '__main__':
    main()
