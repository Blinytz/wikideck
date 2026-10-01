#!/usr/bin/env python3
"""Cartes des fleuves : le fond Google Maps de la region, le trace du fleuve
surligne, et le planisphere avec epingle des cartes d'iles.

Google Maps ne met pas un fleuve en evidence : on dessine donc son trace
nous-memes, depuis Natural Earth (build/audit/geo/rivieres_10m.geojson),
projete exactement comme Google (Mercator web, tuiles de 256 px CSS) sur la
vue chargee par ses coordonnees.

Usage : python fleuves_maps.py [--apercu] <nom de carte>...
"""
import io, sys, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI))
import iles_maps as M
import planisphere

# carte -> (noms Natural Earth du trace, centre lat, centre lng, largeur km, hauteur km)
FLEUVES = {
    'Nil': (['Nile', 'Victoria Nile', 'Albert Nile', 'Bahr el Jebel', 'El Bahr el Abyad'], 15.0, 30.6, 1100, 3700),
    'Danube': (['Danube', 'Donau'], 46.3, 18.6, 1850, 720),
    'Garonne': (['Garonne', 'Gironde'], 44.15, 0.15, 260, 300),
    'Canal de Suez': ('Canal de Suez', 30.6, 32.4, 110, 190),
    'Canal de Panama': ('Canal de Panama', 9.15, -79.74, 75, 62),
}
# les autres fleuves : noms Natural Earth seulement, le cadre est calcule sur
# l'etendue du trace
TRACES = {
    'Amazone': ['Amazonas', 'Ucayali'], 'Yangtsé': ['Yangtze', 'Chang Jiang'], 'Mississippi': ['Mississippi'],
    'Gange': ['Ganges'], 'Indus': ['Indus'], 'Rhin': ['Rhine', 'Rhein', 'Rhin'], 'Volga': ['Volga'],
    'Congo': ['Congo', 'Lualaba'], 'Niger': ['Niger'], 'Mékong': ['Mekong'], 'Tigre (fleuve)': ['Tigris'],
    'Euphrate': ['Euphrates'], 'Loire': ['Loire'], 'Seine': ['Seine'], 'Amour': ['Amur', 'Heilong Jiang', 'Argun’'],
    'Zambèze': ['Zambezi'], 'Colorado': ['Colorado'], 'Río Grande': ['Rio Grande'], 'Saint-Laurent': 'Saint-Laurent',
    'Orénoque': ['Orinoco'], 'Paraná': ['Paraná'], 'Missouri': ['Missouri'], 'Tamise': ['Thames'], 'Tibre': ['Tevere'],
    'Pô': ['Po'], 'Elbe': ['Elbe'], 'Dniepr': ['Dnipro'], 'Rhône': ['Rhône'], 'Tage': ['Tajo', 'Tejo'],
    'Ienisseï': ['Yenisey'], 'Ob': ['Ob'], 'Léna': ['Lena'], 'Jourdain': ['Jordan'],
    'Brahmapoutre': ['Brahmaputra', 'Yarlung'], 'Fleuve Jaune': ['Huang'], 'Okavango': ['Okavango', 'Cubango'],
    'Sénégal (fleuve)': ['Sénégal'],
}


def etendue(noms):
    """Centre et taille (km, mesure Mercator au centre) du trace, avec marge."""
    pts = [pt for l in traces(noms) for pt in l]
    if not pts:
        return None
    los = [x for x, _ in pts]
    ys = [math.log(math.tan(math.pi / 4 + math.radians(max(-85, min(85, y))) / 2)) for _, y in pts]
    ymid = (min(ys) + max(ys)) / 2
    clat = math.degrees(2 * math.atan(math.exp(ymid)) - math.pi / 2)
    clng = (min(los) + max(los)) / 2
    k = 6371 * math.cos(math.radians(clat))
    w = max(math.radians(max(los) - min(los)) * k, 40)
    h = max((max(ys) - min(ys)) * k, 40)
    return clat, clng, w * 1.12, h * 1.12


# Lieux ponctuels de la collection : centre et etendue de la carte, et ce
# qu'on y dessine (une epingle sur le lieu, ou un contour)
LIEUX = {
    'Chutes Victoria': (-17.924, 25.857, 700, 520, ('pin', -17.924, 25.857)),
    'Chutes du Niagara': (43.08, -79.074, 600, 450, ('pin', 43.08, -79.074)),
    "Chutes d'Iguazú": (-25.695, -54.437, 700, 520, ('pin', -25.695, -54.437)),
    'Salto Ángel': (5.967, -62.535, 900, 680, ('pin', 5.967, -62.535)),
    'Fosse des Mariannes': (13.5, 143.5, 2600, 1950, ('pin', 11.35, 142.2)),
    'Cap Horn': (-55.7, -67.6, 330, 250, ('pin', -55.98, -67.27)),
    'Cap de Bonne-Espérance': (-34.1, 18.6, 230, 170, ('pin', -34.357, 18.474)),
    'Grande Barrière de corail': (-17.0, 148.5, 1500, 2100,
                                  ('poly', [(142.5, -10.7), (145.3, -14.5), (147.2, -18.2), (150.5, -21.8), (152.9, -24.6), (151.9, -24.9), (149.6, -22.4), (146.3, -18.9), (144.2, -15.0), (142.0, -10.9)])),
    'Triangle des Bermudes': (25.5, -72.5, 2700, 2000,
                              ('poly', [(-80.19, 25.76), (-64.78, 32.30), (-66.10, 18.47)])),
}


BLEU, CONTOUR = (24, 92, 214), (255, 255, 255)


# traces absents de Natural Earth (le Saint-Laurent y est traite comme un
# estuaire marin) : points releves a la main, du lac Ontario au golfe
MANUELS = {
    # canaux : leur trace sur la carte, sinon on ne les voit pas a cette echelle
    'Canal de Suez': [[(32.31, 31.26), (32.30, 30.95), (32.27, 30.59), (32.33, 30.42), (32.38, 30.35),
                       (32.45, 30.22), (32.55, 30.03), (32.56, 29.93)]],
    'Canal de Panama': [[(-79.92, 9.36), (-79.92, 9.27), (-79.86, 9.20), (-79.80, 9.13), (-79.69, 9.11),
                         (-79.65, 9.05), (-79.60, 9.01), (-79.57, 8.95), (-79.55, 8.89)]],
    # trace OpenStreetMap (relation « Fleuve Saint-Laurent »), du lac Ontario a l'estuaire
    'Saint-Laurent': json.loads((ICI / 'geo' / 'saint_laurent_osm.json').read_text(encoding='utf-8')),     # jusqu'a l'estuaire, pas dans le golfe
}
# un meme nom pour deux fleuves : on garde la bonne region (lng min, lng max)
FILTRES = {'Colorado': (-125, -100, -90, 90),
           # un autre Parana (Goias) et un autre Volga figurent sous le meme nom
           'Paraná': (-70, -40, -90, -15), 'Volga': (30, 60, -90, 90)}


def traces(noms):
    if isinstance(noms, str):
        return MANUELS[noms]
    geo = json.loads((ICI / 'geo' / 'rivieres_10m.geojson').read_text(encoding='utf-8'))
    lignes = []
    for f in geo['features']:
        n = f['properties'].get('name') or ''
        if n in noms:
            g = f['geometry']
            ls = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
            if n in FILTRES:
                a, b, c, d = FILTRES[n]
                ls = [l for l in ls if all(a <= x <= b and c <= y <= d for x, y in l)]
            lignes += ls
    return lignes


def vers_pixels(lat, lng, clat, clng, z, cx, cy):
    """Point geographique -> pixel de capture (Mercator web, z entier)."""
    monde = 256 * 2 ** z * M.ECHELLE

    def proj(la, lo):
        s = math.sin(math.radians(max(-85, min(85, la))))
        return (lo + 180) / 360 * monde, (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * monde
    x0, y0 = proj(clat, clng)
    x, y = proj(lat, lng)
    return cx + (x - x0), cy + (y - y0)


def main():
    from playwright.sync_api import sync_playwright
    apercu = '--apercu' in sys.argv
    noms = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--tous" in sys.argv:
        noms = list(TRACES) + list(LIEUX)
    cartes = {c['nom']: c for c in json.loads(
        (RACINE / 'data' / 'fleuves-mers-et-oceans.json').read_text(encoding='utf-8'))['cartes']}
    (M.BROUILLON / 'fleuves').mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch(channel='chrome', headless=True)
        ctx = nav.new_context(viewport={'width': M.VW, 'height': M.VH}, device_scale_factor=M.ECHELLE,
                              locale='fr-FR')
        pg = ctx.new_page()
        for nom in noms:
            c = cartes[nom]
            dessin = None
            if nom in LIEUX:
                clat, clng, wk, hk, dessin = LIEUX[nom]
                ne = []
            elif nom in FLEUVES:
                ne, clat, clng, wk, hk = FLEUVES[nom]
            else:
                ne = TRACES[nom]
                e = etendue(ne)
                if not e:
                    print(f'  ✗ {nom} : trace introuvable dans Natural Earth')
                    continue
                clat, clng, wk, hk = e
            zf = M.zoom_pour(clat, wk, hk)
            z = math.floor(zf)
            resserre = 2 ** (zf - z)
            pg.goto(f'https://www.google.com/maps/@{clat},{clng},{z}z', wait_until='domcontentloaded')
            M.refuser_consentement(pg)
            M.attendre(6)
            M.nettoyer(pg)
            im = M.capture(pg).convert('RGB')
            cx, cy = M.VW / 2 * M.ECHELLE, M.VH / 2 * M.ECHELLE
            # le trace : un liseré blanc puis le bleu, epaisseur lisible a l'echelle de la carte
            calque = Image.new('RGBA', im.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(calque)
            ep = max(7, round(im.width / 260))
            for ligne in traces(ne):
                pts = [vers_pixels(la, lo, clat, clng, z, cx, cy) for lo, la in ligne]
                if len(pts) > 1:
                    d.line(pts, fill=CONTOUR + (255,), width=ep + 6, joint='curve')
            for ligne in traces(ne):
                pts = [vers_pixels(la, lo, clat, clng, z, cx, cy) for lo, la in ligne]
                if len(pts) > 1:
                    d.line(pts, fill=BLEU + (255,), width=ep, joint='curve')
            if dessin and dessin[0] == 'pin':
                x, y = vers_pixels(dessin[1], dessin[2], clat, clng, z, cx, cy)
                planisphere.epingle(calque, x, y, im.height * 0.055)
            elif dessin and dessin[0] == 'poly':
                pts = [vers_pixels(la, lo, clat, clng, z, cx, cy) for lo, la in dessin[1]]
                d.polygon(pts, fill=(234, 67, 53, 50))
                d.line(pts + [pts[0]], fill=(234, 67, 53, 255), width=ep, joint='curve')
            im.paste(calque, (0, 0), calque)
            x0z, y0z, x1z, y1z = M.ZONE_DIRECTE
            h_max = min(y1z - y0z, (x1z - x0z) * 3 / 4) * M.ECHELLE
            gros, _ = M.recadrer(im, (cx, cy), h_max / resserre, M.ZONE_DIRECTE)
            img = M.composer(gros, planisphere.carte(clat, clng, 900), None)
            f = c['id'].split('_', 1)[1]
            if apercu:
                img.save(M.BROUILLON / 'fleuves' / f'{f}.png')
                print(f'  {nom:<12} apercu')
                continue
            W, H = img.size
            cw, ch = int(W * 0.8), int(H * 0.8)
            centre = img.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch))
            orig = img if max(img.size) <= 2400 else img.resize((2400, 1800), Image.LANCZOS)
            for rel, octets in ((f'images/originaux/fleuves-mers-et-oceans/{f}.webp', M.webp(orig, 88)),
                                (c['imageUrl'], M.webp(centre.resize((800, 600), Image.LANCZOS), 90)),
                                (c['thumbUrl'], M.webp(centre.resize((213, 160), Image.LANCZOS), 82))):
                (RACINE / rel).write_bytes(octets)
            fn = RACINE / 'build' / 'notes_atelier.json'
            notes = json.loads(fn.read_text(encoding='utf-8'))
            notes['cadrages'][c['id']] = {'cx': 0.5, 'cy': 0.5, 'w': 0.8, 'original': True, 'editeLe': 0, 'auto': True}
            fn.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
            fs = RACINE / 'build' / 'images_sources.json'
            src = json.loads(fs.read_text(encoding='utf-8'))
            src[c['id']] = {'source': 'google-maps+natural-earth'}
            fs.write_text(json.dumps(src, ensure_ascii=False, indent=0), encoding='utf-8')
            print(f'  {nom:<12} posee')
        nav.close()


if __name__ == '__main__':
    main()
