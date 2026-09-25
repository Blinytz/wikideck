#!/usr/bin/env python3
"""Cartes des elements : une case de tableau periodique, sans photo.

Les photos d'echantillon ne s'accordaient pas entre elles (fonds, echelles,
detourages). Chaque carte devient une grande case de tableau periodique sur
fond sombre, liseree de la couleur de sa famille : numero atomique, masse,
symbole, nom, famille, etat, periode et groupe, configuration electronique,
electrons par couche, electronegativite, et une petite carte du tableau qui
situe l'element.

Tout tient dans le carre central (x 100 a 700) : la grille du jeu recadre
les cartes en carre.

Donnees : build/audit/tableau_periodique.json (Bowserinator,
Periodic-Table-JSON). Noms francais : ceux des cartes.

Usage : python elements_tuiles.py [--apercu] [Z...]
"""
import io, re, sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
import images_lib as il

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
ETATS = {'Solid': 'solide', 'Liquid': 'liquide', 'Gas': 'gazeux'}
# sans isotope stable : masse du plus stable, entre crochets
SANS_STABLE = {43, 61} | set(range(84, 90)) | set(range(93, 119))
GRAS = r'C:\Windows\Fonts\segoeuib.ttf'
FIN = r'C:\Windows\Fonts\segoeui.ttf'
SEMI = r'C:\Windows\Fonts\seguisb.ttf'
L, H = 800, 600
X0, Y0, X1, Y1 = 104, 28, 696, 572          # la case, dans le carre central
BLANC, GRIS = (246, 246, 250), (160, 164, 180)


def police(chemin, t):
    return ImageFont.truetype(chemin, t)


def famille(z):
    for nom, coul, zs in FAMILLES:
        if z in zs:
            return nom, coul
    return 'Élément', (200, 200, 200)


def nombre(x, dec):
    return f'{x:.{dec}f}'.rstrip('0').rstrip('.').replace('.', ',')


def masse(z, m):
    return f'[{round(m)}]' if z in SANS_STABLE else nombre(m, 3)


def position(e):
    """(periode, groupe) ; groupe None pour les lanthanides et actinides."""
    if e['ypos'] >= 9:
        return e['ypos'] - 3, None
    return e['ypos'], e['xpos']


def config(e):
    s = e['electron_configuration_semantic'].lstrip('*')
    coeur = re.match(r'\[\w+\]', s)
    morceaux = re.findall(r'(\d[spdf])(1[0-4]|\d)', s)
    return (coeur.group(0) if coeur else None), morceaux


def texte_centre(dr, x, y, s, f, coul):
    dr.text((x - dr.textlength(s, font=f) / 2, y), s, font=f, fill=coul)


def dessiner_config(dr, xc, y, e, coul):
    """[Ar] 3d⁶ 4s², exposants dessines en petit et en haut."""
    coeur, morceaux = config(e)
    f, fe = police(SEMI, 32), police(GRAS, 21)
    parts = ([(coeur + ' ', f, 0, GRIS)] if coeur else [])
    for orb, n in morceaux:
        parts += [(orb, f, 0, BLANC), (n, fe, -6, coul), ('  ', fe, 0, coul)]
    larg = sum(dr.textlength(t, font=p) for t, p, _, _ in parts)
    x = xc - larg / 2
    for t, p, dy, c in parts:
        dr.text((x, y + dy), t, font=p, fill=c)
        x += dr.textlength(t, font=p)


def mini_tableau(dr, x, y, e, coul, cote=11, pas=13):
    """Le tableau en miniature, l'element allume."""
    for f in DONNEES:
        cx, cy = f['xpos'], f['ypos']
        if cy >= 9:
            cy -= 0.6                                 # lanthanides et actinides decolles
        px, py = x + (cx - 1) * pas, y + (cy - 1) * pas
        moi = f['number'] == e['number']
        _, c = famille(f['number'])
        terne = tuple(int(v * .28 + 20) for v in c)
        dr.rounded_rectangle((px, py, px + cote, py + cote), radius=2,
                             fill=coul if moi else terne)
        if moi:
            dr.rounded_rectangle((px - 3, py - 3, px + cote + 3, py + cote + 3), radius=4,
                                 outline=BLANC, width=2)


def carte(e, nom):
    z = e['number']
    fam, coul = famille(z)
    y, x = [a.astype('float32') for a in np.mgrid[0:H, 0:L]]
    d = np.clip(np.sqrt(((x - 400) / 520) ** 2 + ((y - 300) / 420) ** 2), 0, 1)[..., None]
    fond = np.array((30, 33, 44)) * (1 - d) + np.array((9, 10, 15)) * d
    toile = Image.fromarray(fond.astype('uint8'), 'RGB').convert('RGBA')

    # halo de la famille derriere la case
    halo = Image.new('RGBA', (L, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).rounded_rectangle((X0 + 30, Y0 + 30, X1 - 30, Y1 - 30), radius=40,
                                           fill=coul + (60,))
    toile.alpha_composite(halo.filter(ImageFilter.GaussianBlur(40)))

    calque = Image.new('RGBA', (L, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(calque)
    dr.rounded_rectangle((X0, Y0, X1, Y1), radius=30, fill=(17, 19, 27, 235),
                         outline=coul + (255,), width=5)
    # bandeau de famille en bas de case
    dr.rounded_rectangle((X0 + 3, Y1 - 64, X1 - 3, Y1 - 3), radius=27, fill=coul + (40,))
    dr.rectangle((X0 + 3, Y1 - 64, X1 - 3, Y1 - 36), fill=coul + (40,))
    toile.alpha_composite(calque)
    dr = ImageDraw.Draw(toile)

    # en haut a gauche : numero atomique ; a droite : masse et electronegativite
    dr.text((X0 + 30, Y0 + 18), str(z), font=police(GRAS, 64), fill=coul)
    fm = police(SEMI, 30)
    m = masse(z, e['atomic_mass'])
    dr.text((X1 - 30 - dr.textlength(m, font=fm), Y0 + 26), m, font=fm, fill=BLANC)
    fp = police(FIN, 19)
    t = 'masse atomique'
    dr.text((X1 - 30 - dr.textlength(t, font=fp), Y0 + 64), t, font=fp, fill=GRIS)
    en = e.get('electronegativity_pauling')
    if en:
        t = f'χ {nombre(en, 2)}'
        dr.text((X1 - 30 - dr.textlength(t, font=fm), Y0 + 92), t, font=fm, fill=BLANC)
        t = 'électronégativité'
        dr.text((X1 - 30 - dr.textlength(t, font=fp), Y0 + 130), t, font=fp, fill=GRIS)

    # a gauche, sous le numero : le tableau miniature
    mini_tableau(dr, 400 - 9 * 9.2, Y0 + 26, e, coul, cote=7.6, pas=9.2)

    # electrons par couche, en colonne a droite, comme sur les vrais tableaux
    fc = police(SEMI, 21)
    couches = e['shells']
    yc = Y0 + 186
    for n in couches:
        s = str(n)
        dr.text((X1 - 30 - dr.textlength(s, font=fc), yc), s, font=fc, fill=GRIS)
        yc += 25

    # le symbole, grand et lumineux
    s = e['symbol']
    fs = police(GRAS, 170 if len(s) < 2 else 150)
    ys = Y0 + 112 if len(s) < 2 else Y0 + 128
    if re.search('[gpy]', s):                 # jambage : le symbole remonte
        ys -= 22
    lueur = Image.new('RGBA', (L, H), (0, 0, 0, 0))
    texte_centre(ImageDraw.Draw(lueur), 400, ys, s, fs, coul + (255,))
    toile.alpha_composite(lueur.filter(ImageFilter.GaussianBlur(22)))
    dr = ImageDraw.Draw(toile)
    texte_centre(dr, 400, ys, s, fs, BLANC)

    # nom, puis etat, periode et groupe
    fn = police(GRAS, 46 if len(nom) <= 12 else 38)
    texte_centre(dr, 400, Y0 + 310, nom, fn, BLANC)
    periode, groupe = position(e)
    etat = ETATS.get(e['phase'], '?') if z < 100 else 'état inconnu'
    infos = [etat, f'période {periode}'] + ([f'groupe {groupe}'] if groupe else [])
    texte_centre(dr, 400, Y0 + 368, '  ·  '.join(infos), police(FIN, 24), GRIS)
    dr.line((250, Y0 + 408, 550, Y0 + 408), fill=coul + (255,), width=1)

    dessiner_config(dr, 400, Y0 + 422, e, coul)
    texte_centre(dr, 400, Y1 - 55, fam.upper(), police(GRAS, 26), coul)
    return toile.convert('RGB')


DONNEES = [e for e in json.loads((ICI / 'tableau_periodique.json').read_text(encoding='utf-8'))
           ['elements'] if e['number'] <= 118]


def main():
    apercu = '--apercu' in sys.argv
    zs = {int(a) for a in sys.argv[1:] if a.isdigit()}
    cartes = json.loads((RACINE / 'data' / 'elements-chimiques.json')
                        .read_text(encoding='utf-8'))['cartes']
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))
    brouillon = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                     r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                     r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\elements')
    brouillon.mkdir(exist_ok=True)
    for z, c in enumerate(cartes, 1):
        if zs and z not in zs:
            continue
        img = carte(DONNEES[z - 1], c['nom'])
        if apercu:
            img.save(brouillon / f'{z:03d}.png')
            continue
        brut = io.BytesIO(); img.save(brut, 'PNG')
        for rel, o in ((c['imageUrl'], il.to_full(brut.getvalue())),
                       (c['thumbUrl'], il.to_thumb(brut.getvalue()))):
            (RACINE / rel).write_bytes(o)
        sources[c['id']] = {'source': 'tuile-element'}
    if not apercu:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'{len(zs) or len(cartes)} case(s)')


if __name__ == '__main__':
    main()
