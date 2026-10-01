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
}
BLEU, CONTOUR = (24, 92, 214), (255, 255, 255)


def traces(noms):
    geo = json.loads((ICI / 'geo' / 'rivieres_10m.geojson').read_text(encoding='utf-8'))
    lignes = []
    for f in geo['features']:
        if (f['properties'].get('name') or '') in noms:
            g = f['geometry']
            lignes += [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
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
    noms = [a for a in sys.argv[1:] if not a.startswith('--')]
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
            ne, clat, clng, wk, hk = FLEUVES[nom]
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
