#!/usr/bin/env python3
"""Pose les images choisies a l'oeil dans choix_grand/<slug>.json.

Chaque carte recoit ce que l'atelier aurait produit si l'utilisateur l'avait
faite lui-meme :
  - images/originaux/<slug>/<f>.webp : l'image entiere, pour recadrer ;
  - un cadrage 4:3 {cx, cy, w} dans notes_atelier.json, `original: true` ;
  - images/full (800 x 600) et images/thumbs (213 x 160), tirees du cadrage.

Le cadrage suit ce que l'utilisateur fait dans l'atelier (mesure sur ses
5 015 cartes) : pour un portrait, toute la largeur et le visage dans le tiers
haut (cy ~ 0,42) ; pour une image large, toute la hauteur, centree. Un visage
detecte recale le cadre sur lui. Le fichier de choix peut imposer cx, cy, w.

choix_grand/<slug>.json : { "<id>": {"k": 3} | {"k": 3, "cy": 0.3, "w": 0.8} }

Usage : python appliquer_choix.py <slug> [<slug>...]
"""
import io, sys, json
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI))
from candidats_images import CAND

CHOIX = ICI / 'choix_grand'
ORIG_MAX = 1600

PORTRAITS = {
    'auteurs-classiques', 'auteurs-modernes', 'grands-compositeurs', 'philosophes',
    'scientifiques-celebres', 'inventeurs-et-ingenieurs', 'figures-religieuses',
    'figures-emancipation', 'dirigeants-contemporains', 'souverains-et-conquerants',
    'grands-explorateurs', 'pionniers-de-lextreme', 'architectes', 'mode-et-couturiers',
    'astronautes-et-cosmonautes', 'grands-peintres', 'musique-populaire', 'realisateurs',
    'acteurs-et-actrices', 'football-ere-moderne', 'legendes-du-football',
    'legendes-du-sport', 'champions-olympiques', 'aviateurs-celebres',
}

_visages = None


def visage(im):
    """Le plus grand visage de face : (cx, cy, h) en pixels, ou None."""
    global _visages
    try:
        import cv2, numpy as np
    except ImportError:
        return None
    if _visages is None:
        _visages = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    g = cv2.cvtColor(np.array(im.convert('RGB')), cv2.COLOR_RGB2GRAY)
    m = min(g.shape) // 12
    f = _visages.detectMultiScale(g, 1.1, 6, minSize=(max(24, m), max(24, m)))
    if len(f) == 0:
        return None
    x, y, w, h = max(f, key=lambda r: r[2] * r[3])
    return x + w / 2, y + h / 2, h


def cadrage(im, slug, impose):
    iw, ih = im.size
    portrait = slug in PORTRAITS
    if ih * 4 / 3 >= iw:                         # plus haute que 4:3 : toute la largeur
        w = 1.0
    else:                                         # plus large : toute la hauteur
        w = ih * 4 / 3 / iw
    cx, cy = 0.5, (0.42 if portrait else 0.5)
    v = visage(im) if portrait else None
    if v:
        fx, fy, fh = v
        cadre_h = w * iw * 3 / 4
        # visage minuscule (plan large) : on se rapproche, sans exceder 35 %
        if fh / cadre_h < 0.12:
            w = max(w * (fh / cadre_h) / 0.2, 0.3)
            cadre_h = w * iw * 3 / 4
        cx = fx / iw
        cy = (fy + cadre_h * 0.1) / ih          # visage un peu au-dessus du centre
    w = impose.get('w', w)
    cx, cy = impose.get('cx', cx), impose.get('cy', cy)
    cadre_l, cadre_h = w * iw, w * iw * 3 / 4
    cx = min(max(cx, cadre_l / 2 / iw), 1 - cadre_l / 2 / iw)
    cy = min(max(cy, cadre_h / 2 / ih), 1 - cadre_h / 2 / ih) if cadre_h <= ih else 0.5
    return {'cx': cx, 'cy': cy, 'w': w}


def tirer(im, c, L, H):
    iw, ih = im.size
    cl, ch = c['w'] * iw, c['w'] * iw * 3 / 4
    x0, y0 = c['cx'] * iw - cl / 2, c['cy'] * ih - ch / 2
    return im.crop((round(x0), round(y0), round(x0 + cl), round(y0 + ch))).resize((L, H), Image.LANCZOS)


def webp(im, q):
    b = io.BytesIO()
    im.save(b, 'WEBP', quality=q)
    return b.getvalue()


def main():
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    fn = RACINE / 'build' / 'notes_atelier.json'
    notes = json.loads(fn.read_text(encoding='utf-8'))
    fs = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(fs.read_text(encoding='utf-8'))
    # --seul <id> : ne poser que ces cartes. Rejouer tout un fichier de choix
    # ecraserait les cartes que l'utilisateur a retouchees depuis.
    seuls = {sys.argv[i + 1] for i, x in enumerate(sys.argv) if x == '--seul'}
    for slug in [x for x in sys.argv[1:] if not x.startswith('--') and x not in seuls]:
        fc = CHOIX / f'{slug}.json'
        if not fc.exists():
            print(f'{slug} : pas de fichier de choix')
            continue
        choix = json.loads(fc.read_text(encoding='utf-8'))
        e = next(c for c in idx['collections'] if c['slug'] == slug)
        cartes = {c['id']: c for c in json.loads((RACINE / e['fichier']).read_text(encoding='utf-8'))['cartes']}
        poses = 0
        for cid, ch in choix.items():
            if seuls and cid not in seuls:
                continue
            c = cartes.get(cid)
            if c is None or ch.get('k') is None or ch['k'] < 0:
                continue
            fslug = cid.split('_', 1)[1]
            meta = json.loads((CAND / slug / f'{fslug}.json').read_text(encoding='utf-8'))
            m = next(x for x in meta if x['k'] == ch['k'])
            im = Image.open(CAND / slug / f'{fslug}_{ch["k"]}.img').convert('RGB')
            if max(im.size) > ORIG_MAX:
                r = ORIG_MAX / max(im.size)
                im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
            cad = cadrage(im, slug, ch)
            for rel, octets in ((f'images/originaux/{slug}/{fslug}.webp', webp(im, 88)),
                                (c['imageUrl'], webp(tirer(im, cad, 800, 600), 90)),
                                (c['thumbUrl'], webp(tirer(im, cad, 213, 160), 82))):
                p = RACINE / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(octets)
            notes['cadrages'][cid] = dict(cad, original=True, editeLe=0, auto=True)
            sources[cid] = {'source': 'grand-complement', 'origine': m['source'], 'url': m['url']}
            poses += 1
        print(f'{slug} : {poses} image(s) posée(s)')
    fn.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
    fs.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
