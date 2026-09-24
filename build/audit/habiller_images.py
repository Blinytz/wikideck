#!/usr/bin/env python3
"""Illustrations homogenes par collection : un sujet detoure sur un fond commun.

Demande de l'utilisateur : des images uniformes au sein d'une meme
collection, jamais sur fond tout blanc, et le droit de prendre des images non
libres puisque le jeu est a usage personnel.

Le principe :

  1. la SOURCE est l'image de l'infobox de la page anglaise (parametre
     `logo`, `image_1`, `image`...). C'est la que vivent les emblemes
     olympiques et les billets, que l'API des images de tete ecarte parce
     qu'ils sont non libres ;
  2. le sujet est DETOURE quand son fond d'origine est uni (logo, piece ou
     billet photographies sur blanc) ; sinon il est pose tel quel, comme une
     photo encadree ;
  3. il est pose sur le FOND de la collection, degrade doux et ombre portee,
     et cadre pour tenir dans le carre central : la carte l'affiche en 4:3,
     mais les grilles le recadrent en carre.

Usage : python habiller_images.py <slug> [<slug>...] [--essai] [--seul <nom>]
"""
import io, re, sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
import images_lib as il

L, H = 800, 600          # format de l'illustration sur la carte (4:3)

# Par collection : fond (centre, bord), cadre du sujet (largeur, hauteur max),
# parametres d'infobox a essayer dans l'ordre.
STYLES = {
    'jeux-olympiques': dict(
        fond=((251, 243, 228), (226, 204, 166)), boite=(470, 470),
        cles=('logo', 'emblem', 'image')),
    'jeux-olympiques-hiver': dict(
        fond=((240, 247, 252), (181, 208, 230)), boite=(470, 470),
        cles=('logo', 'emblem', 'image')),
    'monnaies-du-monde': dict(
        fond=((42, 74, 60), (14, 30, 24)), boite=(660, 420),
        cles=('image_1', 'image', 'image_2')),
    'monnaies-historiques': dict(
        fond=((38, 52, 78), (10, 16, 28)), boite=(560, 440),
        cles=('image_1', 'obverse', 'image', 'image_2')),
    'noeuds': dict(
        fond=((78, 92, 104), (28, 34, 40)), boite=(500, 470), tuile=460,
        cles=('image', 'image_1')),
}


# Fichiers imposes, reperes par une recherche Commons et un mot-cle du nom de
# fichier (les noms font parfois 80 caracteres). Pour ces cartes, l'infobox
# anglaise est vide ou ne montre que le glyphe de la monnaie, et le repli
# retombait sur l'image du passage precedent.
FORCES = {
    'Nouveau dollar de Taïwan': ('New Taiwan Dollar', '1955 bank note - 5 new Taiwan dollars (front)'),
    'Dong': ('dong banknote', 'Temple of Literature in Hanoi'),
    'Złoty': ('zlotych banknoty', '500 zł 1947'),
    'Rial iranien': ('Iranian rial banknote', 'Iranian rial banknote'),
    'Nœud de pêcheur': ("Fisherman's knot", "Fisherman's knot diagram"),
    'Nœud de cravate': ('Four-in-hand knot', 'Necktie Four-in-Hand knot'),
    'Nœud de franciscain': ('Franziskanerknoten', 'FranziskanerKnoten'),
}


# Billets dont le detourage laisse des bords dechiquetes (papier use, fond
# irregulier) : ils sont poses encadres, tels quels.
NE_PAS_DETOURER = {'Złoty', 'Rial iranien'}


def fichier_force(nom):
    if nom not in FORCES:
        return None
    requete, cle = FORCES[nom]
    d = il.api('commons.wikimedia.org', dict(action='query', list='search', srsearch=requete,
                                              srnamespace=6, srlimit=30))
    for h in ((d or {}).get('query') or {}).get('search', []):
        f = h['title'].split(':', 1)[1]
        if cle.lower() in f.lower():
            return f
    return None


# ------------------------------------------------------------------ sources

def pages_de(d):
    p = ((d or {}).get('query') or {}).get('pages') or []
    return list(p.values()) if isinstance(p, dict) else p


def wikitexte(page):
    d = il.api('en.wikipedia.org', dict(action='parse', page=page, prop='wikitext',
                                         section=0, redirects=1))
    wt = ((d or {}).get('parse') or {}).get('wikitext', '')
    return wt.get('*', '') if isinstance(wt, dict) else (wt or '')


FICHIER = r'(?:\[\[)?(?:File:|Image:)?\s*([^|\]\n{}<=]+?\.(?:svg|png|jpe?g|gif|webp))'


# Fichiers qui ne sont jamais le sujet : les icones des bandeaux de navigation
# et des portails. Le premier passage avait donne l'icone « argent » (liasse
# verte et pieces d'or) a une vingtaine de monnaies, et le logo de Wikimedia
# Commons a sept autres. Les symboles typographiques (rial, taka) non plus :
# un glyphe n'illustre pas une monnaie.
PARASITES = re.compile(
    r'commons-logo|wikimedia|wiki|icon|money|symbol|sign\b|question|portal|nuvola|'
    r'crystal|stub|flag|map|padlock|disambig|emblem-|ambox|red_x|'
    r'currency.?sign|\bsign\.', re.I)


def sans_accent(s):
    import unicodedata
    s = unicodedata.normalize('NFD', s)
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()


def fichier_infobox(page, cles):
    wt = wikitexte(page)
    for k in cles:
        m = re.search(r'^\s*\|\s*' + k + r'\s*=\s*' + FICHIER, wt, re.I | re.M)
        if m and not PARASITES.search(m.group(1)):
            return m.group(1).strip()
    return None


def fichier_image_de_tete(page):
    """Image de tete LIBRE de la page anglaise (l'API ecarte les non libres)."""
    d = il.api('en.wikipedia.org', dict(action='query', titles=page, prop='pageimages',
                                         piprop='name', redirects=1))
    for p in pages_de(d):
        nom = p.get('pageimage')
        if nom and not PARASITES.search(nom):
            return nom
    return None


def fichier_par_nom(page):
    """Repli : un fichier de la page dont le NOM contient un mot du sujet.

    Sans cette contrainte, le premier fichier qui contenait « coin » ou « knot »
    faisait l'affaire, et c'etait souvent l'icone d'un bandeau ou un autre
    noeud cite dans l'article."""
    mots = [m for m in re.findall(r'[a-z]{4,}', sans_accent(page))
            if m not in ('knot', 'hitch', 'bend', 'loop', 'coin', 'currency')]
    if not mots:
        return None
    d = il.api('en.wikipedia.org', dict(action='query', titles=page, prop='images',
                                         imlimit=100, redirects=1))
    for p in pages_de(d):
        for im in p.get('images') or []:
            nom = im['title'].split(':', 1)[1]
            n = sans_accent(nom)
            if PARASITES.search(nom) or not n.endswith(('.svg', '.png', '.jpg', '.jpeg')):
                continue
            if any(m in n for m in mots):
                return nom
    return None


def url_fichier(f, w=1100):
    d = il.api('en.wikipedia.org', dict(action='query', titles='File:' + f,
                                         prop='imageinfo', iiprop='url', iiurlwidth=w))
    for p in pages_de(d):
        ii = (p.get('imageinfo') or [{}])[0]
        return ii.get('thumburl') or ii.get('url')
    return None


def charger(url):
    data = il.telecharger_image(url, min_cote=150, navigateur=False)
    if not data:
        return None
    try:
        im = Image.open(io.BytesIO(data)).convert('RGBA')
    except Exception:
        return None
    # 1000 px suffisent pour une illustration de 800 : au-dela, le detourage
    # depassait la memoire disponible sur les grandes affiches.
    im.thumbnail((1000, 1000), Image.LANCZOS)
    return im


# ---------------------------------------------------------------- detourage

def a_deja_transparence(im):
    a = np.asarray(im.getchannel('A'))
    bord = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    return (bord < 200).mean() > 0.3


def detourer(im):
    """Retire un fond UNI touchant les bords. Rend (image RGBA, detouree ?)."""
    if a_deja_transparence(im):
        return im, True
    rgb = im.convert('RGB')
    arr = np.asarray(rgb).astype(np.int16)
    bord = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    if bord.std(axis=0).mean() > 22:          # fond charge : pas de detourage
        return im, False
    marque = (255, 0, 254)
    travail = rgb.copy()
    w, h = travail.size
    pas = max(4, min(w, h) // 60)
    graines = [(x, 0) for x in range(0, w, pas)] + [(x, h - 1) for x in range(0, w, pas)] \
        + [(0, y) for y in range(0, h, pas)] + [(w - 1, y) for y in range(0, h, pas)]
    ref = bord.mean(axis=0)
    for g in graines:
        px = travail.getpixel(g)
        if px == marque or np.abs(np.array(px) - ref).mean() > 30:
            continue
        ImageDraw.floodfill(travail, g, marque, thresh=34)
    t = np.asarray(travail)
    fond = (t[..., 0] == 255) & (t[..., 1] == 0) & (t[..., 2] == 254)
    garde = 1 - fond.mean()
    if garde < 0.08 or garde > 0.985:          # fuite ou rien retire
        return im, False
    alpha = Image.fromarray(np.where(fond, np.uint8(0), np.uint8(255)))
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = rgb.convert('RGBA')
    out.putalpha(alpha)
    return out, True


# ------------------------------------------------------------------- fond

def fond(centre, bord):
    y, x = np.mgrid[0:H, 0:L]
    d = np.sqrt(((x - L / 2) / (L / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / 1.3
    d = np.clip(d, 0, 1)[..., None]
    c = np.array(centre, float) * (1 - d) + np.array(bord, float) * d
    grain = np.random.default_rng(7).normal(0, 2.2, (H, L, 1))
    return Image.fromarray(np.clip(c + grain, 0, 255).astype('uint8'), 'RGB')


def composer(sujet, style, detoure):
    bbox = sujet.getchannel('A').getbbox() if detoure else None
    if bbox:
        sujet = sujet.crop(bbox)
    bw, bh = style['boite']
    r = min(bw / sujet.width, bh / sujet.height)
    sujet = sujet.resize((max(1, round(sujet.width * r)), max(1, round(sujet.height * r))),
                         Image.LANCZOS)
    toile = fond(*style['fond']).convert('RGBA')
    x, y = (L - sujet.width) // 2, (H - sujet.height) // 2
    if not detoure:
        # photo encadree : un liseré clair, pour qu'elle se detache du fond
        cadre = Image.new('RGBA', (sujet.width + 12, sujet.height + 12), (245, 242, 235, 255))
        cadre.paste(sujet, (6, 6))
        sujet, x, y = cadre, x - 6, y - 6
    # ombre portee
    a = sujet.getchannel('A')
    ombre = Image.new('RGBA', sujet.size, (0, 0, 0, 0))
    ombre.putalpha(a.point(lambda v: int(v * 0.45)))
    ombre = ombre.filter(ImageFilter.GaussianBlur(10))
    toile.alpha_composite(ombre, (x + 6, y + 10))
    toile.alpha_composite(sujet, (x, y))
    return toile.convert('RGB')


def composer_tuile(im, style):
    """Vignette carree de taille fixe, posee sur le fond.

    Pour les noeuds, le detourage laissait des debris gris ou blancs la ou la
    photo avait une ombre, et le melange de noeuds detoures et de photos
    encadrees manquait d'unite. Chaque noeud devient donc une tuile carree de
    meme taille : la photo y est centree et le vide est comble par la couleur
    de son propre bord, qui prolonge le fond de la photo."""
    rgb = im.convert('RGB')
    arr = np.asarray(rgb)
    bord = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    couleur = tuple(int(v) for v in np.median(bord, axis=0))
    cote = style['tuile']
    r = min(cote / rgb.width, cote / rgb.height)
    rgb = rgb.resize((max(1, round(rgb.width * r)), max(1, round(rgb.height * r))),
                     Image.LANCZOS)
    tuile = Image.new('RGB', (cote, cote), couleur)
    tuile.paste(rgb, ((cote - rgb.width) // 2, (cote - rgb.height) // 2))
    cadre = Image.new('RGBA', (cote + 12, cote + 12), (245, 242, 235, 255))
    cadre.paste(tuile, (6, 6))
    toile = fond(*style['fond']).convert('RGBA')
    x, y = (L - cadre.width) // 2, (H - cadre.height) // 2
    ombre = Image.new('RGBA', cadre.size, (0, 0, 0, 115)).filter(ImageFilter.GaussianBlur(10))
    toile.alpha_composite(ombre, (x + 6, y + 10))
    toile.alpha_composite(cadre, (x, y))
    return toile.convert('RGB')


# ------------------------------------------------------------------- pilote

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    essai = '--essai' in sys.argv
    seul = sys.argv[sys.argv.index('--seul') + 1] if '--seul' in sys.argv else None
    if seul:
        args = [a for a in args if a != seul]
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))

    for slug in args:
        style = STYLES[slug]
        cartes = json.loads(par_slug[slug].read_text(encoding='utf-8'))['cartes']
        if seul:
            cartes = [c for c in cartes if c['nom'] == seul]
        if '--forces' in sys.argv:           # ne reprendre que les cartes imposees
            cartes = [c for c in cartes if c['nom'] in FORCES]
        en = il.langlinks_en([c['titrePage'] for c in cartes])
        faites, rates = 0, []
        # Deux cartes d'une meme collection ne partagent jamais une source : le
        # noeud de pecheur et le noeud de pecheur double avaient recu le meme
        # fichier. Le second passe alors a la source suivante.
        deja = set()
        for c in cartes:
            page = en.get(c['titrePage'])
            f = fichier_force(c['nom'])
            if f:
                deja.add(f)
            elif page:
                for chercher in (lambda: fichier_infobox(page, style['cles']),
                                 lambda: fichier_image_de_tete(page),
                                 lambda: fichier_par_nom(page)):
                    f = chercher()
                    if f and f not in deja:
                        break
                    f = None
            if f:
                deja.add(f)
            im = charger(url_fichier(f)) if f else None
            origine = f
            if im is None:
                # repli : l'image actuelle de la carte, recomposee
                p = RACINE / c['imageUrl']
                if p.exists():
                    im, origine = Image.open(p).convert('RGBA'), '(image actuelle)'
                    im.thumbnail((1000, 1000), Image.LANCZOS)
            if im is None:
                rates.append(c['nom'])
                continue
            if style.get('tuile'):
                img, detoure = composer_tuile(im, style), False
            else:
                if c['nom'] in NE_PAS_DETOURER:
                    sujet, detoure = im, False
                else:
                    sujet, detoure = detourer(im)
                img = composer(sujet, style, detoure)
            print(f"  {c['nom']:<34} {'detoure' if detoure else 'encadre':<8} <- {str(origine)[:60]}")
            faites += 1
            if essai:
                continue
            brut = io.BytesIO(); img.save(brut, 'PNG')
            fu, th = il.to_full(brut.getvalue()), il.to_thumb(brut.getvalue())
            for rel, octets in ((c['imageUrl'], fu), (c['thumbUrl'], th)):
                p = RACINE / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(octets)
            sources[c['id']] = {'source': 'habillee', 'fichier': origine}
        print(f'{slug} : {faites} habillee(s), {len(rates)} ratee(s) {rates}')

    if not essai:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
