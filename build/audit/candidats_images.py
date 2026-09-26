#!/usr/bin/env python3
"""Rassemble les images candidates des cartes sans image, en planches a juger.

Pour le grand complement, le choix d'image se fait A L'OEIL, comme
l'utilisateur le fait dans l'atelier. Ce script ne choisit rien : il reunit
pour chaque carte jusqu'a dix candidates, de trois sources :

  - l'image de tete de la page fr, puis de la page en (sans filtre) ;
  - la recherche de Commons ;
  - la recherche d'images du web, avec une requete propre a la collection
    (« portrait », « film », « plat », « digital art »...) : l'usage est
    strictement personnel, les images sous droits sont admises.

Les candidates trop petites sont ecartees (petit cote < MINI), les doublons
aussi. Chaque carte donne une ligne de planche : ses candidates numerotees,
avec leur taille. Le choix s'ecrit ensuite dans choix_grand/<slug>.json et
s'applique avec appliquer_choix.py.

Sortie : <scratch>/candidats/<slug>/<fslug>_<k>.img  + <fslug>.json
         <scratch>/planches/<slug>_<n>.png

Usage : python candidats_images.py <slug> [<slug>...] [--seul <id>] [--requete "<texte>"]
"""
import io, re, sys, json, hashlib, argparse, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
sys.path.insert(0, str(ICI))
import images_lib as il
import choix_images

SCRATCH = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
               r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
               r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad')
CAND = SCRATCH / 'candidats'
PLANCHES = SCRATCH / 'planches'
MINI = 450
N_WEB = 9
POLICE = r'C:\Windows\Fonts\segoeui.ttf'
POLICE_G = r'C:\Windows\Fonts\segoeuib.ttf'

from requetes_images import REQUETES, PORTRAIT


def telecharger(url):
    for nav in (False, True):
        d = il.http_get(url, cache=False, navigateur=nav, timeout=20)
        if d and len(d) > 4000:
            try:
                im = Image.open(io.BytesIO(d))
                im.load()
                return d, im.size
            except Exception:
                return None, None
    return None, None


def urls_web(requete):
    """Recherche d'images DuckDuckGo. Bing, apres quelques centaines de
    requetes, rendait des resultats sans rapport (des gobelets pour « Stanley
    Kubrick ») : DuckDuckGo reste pertinent, et donne la taille des images,
    ce qui ecarte les petites avant meme de les telecharger."""
    import time
    from ddgs import DDGS
    for essai in range(3):
        try:
            with DDGS() as d:
                res = list(d.images(requete, max_results=N_WEB * 2))
            return [r['image'] for r in res
                    if min(int(r.get('width') or 0), int(r.get('height') or 0)) >= MINI][:N_WEB]
        except Exception:
            time.sleep(3 * (essai + 1))
    return []


def urls_commons(nom):
    try:
        return [(c.get('g') or c.get('v')) for c in choix_images.chercher(nom)[:3]]
    except Exception:
        return []


def rassembler(slug, carte, wiki_fr, wiki_en, requete=None, titre_en=None):
    urls = []
    for u in (wiki_fr, wiki_en):
        if u:
            # l'original de Wikimedia est souvent refuse (429) : on demande
            # une vignette standard de 1280 px, l'original en dernier recours
            f = urllib.parse.unquote(u.split('?')[0].rsplit('/', 1)[-1])
            if '/commons/' in u:
                t = il.commons_thumb(f, 1280)
                if t:
                    urls.append(('wiki', t))
            urls.append(('wiki', u.split('?')[0]))
    reqs = [requete] if requete else REQUETES.get(slug, PORTRAIT)
    for r in reqs:
        for u in urls_web(r.format(n=carte['nom'], t=carte['titrePage'],
                                   e=titre_en or carte['nom']).strip()):
            urls.append(('web', u))
    if not requete:
        for u in urls_commons(carte['titrePage']):
            if u:
                urls.append(('commons', u))
    vus, propres = set(), []
    for s, u in urls:
        if u not in vus:
            vus.add(u)
            propres.append((s, u))
    fslug = carte['id'].split('_', 1)[1]
    d = CAND / slug
    d.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda su: (su, telecharger(su[1])), propres[:22]))
    meta, empreintes = [], []
    for (s, u), (data, taille) in res:
        if not data or min(taille) < MINI:
            continue
        # empreinte moyenne 8x8 : deux tailles d'une meme image sont des doublons
        px = list(Image.open(io.BytesIO(data)).convert('L').resize((8, 8)).getdata())
        moy = sum(px) / 64
        e = sum(1 << i for i, v in enumerate(px) if v > moy)
        if any(bin(e ^ x).count('1') <= 6 for x in empreintes):
            continue
        empreintes.append(e)
        k = len(meta)
        (d / f'{fslug}_{k}.img').write_bytes(data)
        meta.append({'k': k, 'url': u, 'source': s, 'l': taille[0], 'h': taille[1]})
        if len(meta) >= 12:
            break
    (d / f'{fslug}.json').write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')
    return meta


def tuile(chemin, L=220, H=165):
    im = Image.open(chemin).convert('RGB')
    r = max(L / im.width, H / im.height)
    im = im.resize((max(L, round(im.width * r)), max(H, round(im.height * r))), Image.LANCZOS)
    x, y = (im.width - L) // 2, (im.height - H) // 2
    return im.crop((x, y, x + L, y + H))


def planches(slug, cartes, par=5, suffixe=''):
    PLANCHES.mkdir(parents=True, exist_ok=True)
    fg, fp = ImageFont.truetype(POLICE_G, 20), ImageFont.truetype(POLICE, 15)
    L, H, COLS = 220, 165, 12
    sorties = []
    for n in range(0, len(cartes), par):
        lot = cartes[n:n + par]
        img = Image.new('RGB', (COLS * (L + 6) + 6, len(lot) * (H + 44) + 6), (24, 24, 30))
        dr = ImageDraw.Draw(img)
        for i, c in enumerate(lot):
            fslug = c['id'].split('_', 1)[1]
            y = 6 + i * (H + 44)
            fj = CAND / slug / f'{fslug}.json'
            meta = json.loads(fj.read_text(encoding='utf-8')) if fj.exists() else []
            dr.text((8, y), f"{c['nom']}   ({c['id']})", font=fg, fill=(255, 220, 90))
            for m in meta[:COLS]:
                x = 6 + m['k'] * (L + 6)
                try:
                    img.paste(tuile(CAND / slug / f"{fslug}_{m['k']}.img"), (x, y + 26))
                except Exception:
                    continue
                dr.rectangle((x, y + 26, x + 64, y + 46), fill=(0, 0, 0))
                dr.text((x + 4, y + 27), f"{m['k']}  {dict(wiki='W', web='B', commons='C').get(m['source'], '?')}", font=fp, fill=(255, 255, 255))
                dr.text((x + 4, y + 26 + H - 18), f"{m['l']}×{m['h']}", font=fp, fill=(255, 255, 0),
                        stroke_width=2, stroke_fill=(0, 0, 0))
            if not meta:
                dr.text((8, y + 60), 'aucune candidate', font=fg, fill=(255, 80, 80))
        f = PLANCHES / f'{slug}{suffixe}_{n // par:03d}.png'
        img.save(f)
        sorties.append(f)
    return sorties


def cartes_sans_image(slug):
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    e = next(c for c in idx['collections'] if c['slug'] == slug)
    d = json.loads((RACINE / e['fichier']).read_text(encoding='utf-8'))
    return [c for c in d['cartes'] if not (RACINE / c['imageUrl']).exists()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='+')
    ap.add_argument('--seul', action='append', default=[])
    ap.add_argument('--requete')
    ap.add_argument('--planches-seules', action='store_true')
    a = ap.parse_args()
    for slug in a.slugs:
        cartes = cartes_sans_image(slug)
        if a.seul:
            cartes = [c for c in cartes if c['id'] in a.seul]
        if not cartes:
            print(f'{slug} : aucune carte sans image')
            continue
        # reprise : une carte deja rassemblee n'est pas refaite (deux passes
        # peuvent tourner en parallele sur la liste, dans les deux sens)
        a_faire = cartes if (a.seul or a.requete) else [
            c for c in cartes if not (CAND / slug / f"{c['id'].split('_', 1)[1]}.json").exists()]
        toutes = cartes
        if not a.planches_seules and a_faire:
            cartes = a_faire
            titres = [c['titrePage'] for c in cartes]
            fr = il.wiki_images_batch(titres, 'fr.wikipedia.org', filtrer=False)
            en_de = il.langlinks_en(titres)
            en = il.wiki_images_batch(list(en_de.values()), 'en.wikipedia.org', filtrer=False)
            for c in cartes:
                m = rassembler(slug, c, fr.get(c['titrePage']), en.get(en_de.get(c['titrePage'], '')),
                               a.requete, en_de.get(c['titrePage']))
                print(f"  {slug} · {c['nom']:<40} {len(m)} candidate(s)")
        for f in planches(slug, toutes, suffixe='_reprise' if a.seul else ''):
            print('planche', f)


if __name__ == '__main__':
    main()
