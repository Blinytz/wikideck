#!/usr/bin/env python3
"""Cartes des elements : la vraie photo de l'echantillon, en case de tableau.

Les schemas d'atome se ressemblaient tous, a la couleur pres. Chaque carte
devient une case de tableau periodique sur fond sombre : a gauche le numero,
le symbole et la famille ; au centre la PHOTO de l'element (image de tete de
la page anglaise, detouree par rembg) ; un liseré de la couleur de sa
famille. Les elements synthetiques, qui n'ont jamais ete vus a l'oeil nu,
n'ont pas de photo : leur symbole occupe alors le centre, en grand.

Usage : python elements_tuiles.py [--apercu] [Z...]
"""
import io, re, sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build')); sys.path.insert(0, str(ICI))
import images_lib as il
import habiller_images as hab

SYMB = ('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn '
        'Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce '
        'Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn '
        'Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl '
        'Mc Lv Ts Og').split()
FAMILLES = [
    ('Métal alcalin', (255, 107, 107), {3, 11, 19, 37, 55, 87}),
    ('Alcalino-terreux', (255, 170, 80), {4, 12, 20, 38, 56, 88}),
    ('Lanthanide', (240, 120, 200), set(range(57, 72))),
    ('Actinide', (220, 110, 255), set(range(89, 104))),
    ('Métal de transition', (255, 205, 90), set(range(21, 31)) | set(range(39, 49))
     | set(range(72, 81)) | set(range(104, 113))),
    ('Métal pauvre', (150, 200, 230), {13, 31, 49, 50, 81, 82, 83, 84, 113, 114, 115, 116}),
    ('Métalloïde', (110, 220, 190), {5, 14, 32, 33, 51, 52}),
    ('Non-métal', (120, 230, 120), {1, 6, 7, 8, 15, 16, 34}),
    ('Halogène', (90, 220, 255), {9, 17, 35, 53, 85, 117}),
    ('Gaz noble', (170, 150, 255), {2, 10, 18, 36, 54, 86, 118}),
]
# photos d'echantillon choisies quand l'image de tete n'en est pas une
FORCES = {79: 'Gold-crystals.jpg', 83: 'Bismuth crystals and 1cm3 cube.jpg'}
POLICE = r'C:\Windows\Fonts\segoeuib.ttf'
POLICE_FINE = r'C:\Windows\Fonts\segoeui.ttf'
L, H = 800, 600


def famille(z):
    for nom, coul, zs in FAMILLES:
        if z in zs:
            return nom, coul
    return 'Élément', (200, 200, 200)


def photo(z, page_en):
    f = FORCES.get(z)
    if not f:
        d = il.api('en.wikipedia.org', dict(action='query', titles=page_en, prop='pageimages',
                                             piprop='name', redirects=1))
        for p in hab.pages_de(d):
            f = p.get('pageimage')
    if not f or re.search(r'\.svg$|shell|diagram|spectr|orbital|structure|lattice', f, re.I):
        return None, None
    return hab.charger(hab.url_fichier(f, 1280)), f


def carte(z, nom, sujet):
    fam, coul = famille(z)
    y, x = [a.astype('float32') for a in __import__('numpy').mgrid[0:H, 0:L]]
    np = __import__('numpy')
    d = np.clip(np.sqrt(((x - 520) / 520) ** 2 + ((y - 300) / 420) ** 2), 0, 1)[..., None]
    fond = np.array((34, 38, 50)) * (1 - d) + np.array((10, 11, 16)) * d
    toile = Image.fromarray(fond.astype('uint8'), 'RGB').convert('RGBA')
    dr = ImageDraw.Draw(toile)
    # halo de la couleur de famille derriere le sujet
    halo = Image.new('RGBA', (L, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse((330, 90, 750, 510), fill=coul + (70,))
    toile.alpha_composite(halo.filter(ImageFilter.GaussianBlur(70)))
    if sujet is not None:
        bb = sujet.getchannel('A').getbbox()
        sujet = sujet.crop(bb)
        r = min(430 / sujet.width, 430 / sujet.height)
        sujet = sujet.resize((round(sujet.width * r), round(sujet.height * r)), Image.LANCZOS)
        x0, y0 = 545 - sujet.width // 2, 300 - sujet.height // 2
        om = Image.new('RGBA', sujet.size, (0, 0, 0, 0))
        om.putalpha(sujet.getchannel('A').point(lambda v: int(v * .6)))
        toile.alpha_composite(om.filter(ImageFilter.GaussianBlur(14)), (x0 + 8, y0 + 16))
        toile.alpha_composite(sujet, (x0, y0))
    else:
        f = ImageFont.truetype(POLICE, 260)
        s = SYMB[z - 1]
        w = dr.textlength(s, font=f)
        lueur = Image.new('RGBA', (L, H), (0, 0, 0, 0))
        ImageDraw.Draw(lueur).text((545 - w / 2, 150), s, font=f, fill=coul + (255,))
        toile.alpha_composite(lueur.filter(ImageFilter.GaussianBlur(18)))
        dr.text((545 - w / 2, 150), s, font=f, fill=(245, 245, 250))
    # colonne de gauche : numero, symbole, famille
    dr.rounded_rectangle((34, 34, 250, 566), radius=26, outline=coul + (255,), width=5,
                         fill=(18, 20, 28, 210))
    dr.text((62, 58), str(z), font=ImageFont.truetype(POLICE, 58), fill=coul)
    f = ImageFont.truetype(POLICE, 150 if len(SYMB[z - 1]) < 2 else 118)
    dr.text((142 - dr.textlength(SYMB[z - 1], font=f) / 2, 180), SYMB[z - 1], font=f,
            fill=(250, 250, 252))
    fn = ImageFont.truetype(POLICE, 34 if len(nom) < 11 else 26)
    dr.text((142 - dr.textlength(nom, font=fn) / 2, 410), nom, font=fn, fill=(235, 235, 240))
    ff = ImageFont.truetype(POLICE_FINE, 22)
    dr.text((142 - dr.textlength(fam, font=ff) / 2, 470), fam, font=ff, fill=coul)
    return toile.convert('RGB')


def main():
    apercu = '--apercu' in sys.argv
    zs = {int(a) for a in sys.argv[1:] if a.isdigit()}
    from rembg import remove, new_session
    ses = new_session('isnet-general-use')
    cartes = json.loads((RACINE / 'data' / 'elements-chimiques.json').read_text(encoding='utf-8'))['cartes']
    en = il.langlinks_en([c['titrePage'] for c in cartes])
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))
    brouillon = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                     r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                     r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\elements')
    brouillon.mkdir(exist_ok=True)
    for z, c in enumerate(cartes, 1):
        if zs and z not in zs:
            continue
        im, f = photo(z, en.get(c['titrePage'], c['nom']))
        sujet = None
        if im is not None:
            im.thumbnail((1280, 1280))
            sujet = remove(im.convert('RGB'), session=ses, post_process_mask=True)
            sujet.putalpha(sujet.getchannel('A').point(lambda v: 0 if v < 40 else v))
            if not sujet.getchannel('A').getbbox():
                sujet = None
        img = carte(z, c['nom'], sujet)
        print(f"  {z:>3} {c['nom']:<16} {'photo ' + f[:50] if sujet else 'symbole'}")
        if apercu:
            img.save(brouillon / f'{z:03d}.png'); continue
        brut = io.BytesIO(); img.save(brut, 'PNG')
        for rel, o in ((c['imageUrl'], il.to_full(brut.getvalue())), (c['thumbUrl'], il.to_thumb(brut.getvalue()))):
            (RACINE / rel).write_bytes(o)
        sources[c['id']] = {'source': 'tuile-element', 'fichier': f if sujet else None}
    if not apercu:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
