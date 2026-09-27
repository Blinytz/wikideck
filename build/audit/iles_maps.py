#!/usr/bin/env python3
"""Cartes des iles : une capture Google Maps de l'ile, avec un encart qui la
situe par rapport aux terres voisines.

C'est le style que l'utilisateur a pose a la main de l'ile de Skye a
Kerguelen : l'ile en gros plan avec son contour en pointilles rouges (le
trace que Google Maps dessine autour d'un lieu cherche), et dans un coin une
vue dezoomee qui la situe. A la main, c'etait tres long ; ce script le fait.

Par ile :
  1. Chrome (Playwright, sans fenetre, en double resolution pour que les noms
     restent lisibles sur la carte) cherche l'ile sur Google Maps ; le
     bandeau de consentement est refuse (« Tout refuser ») ;
  2. le panneau lateral est ferme, puis on zoome avec les boutons de la carte
     (recharger une adresse ferait perdre le contour rouge) jusqu'a ce que
     le contour occupe une bonne part de l'ecran ;
  3. on dezoome de quatre crans pour l'encart ;
  4. l'original est un 4:3 centre sur l'ile ; la carte en montre les 80 %
     du milieu, avec l'encart en bas a gauche. Le cadrage reste modifiable.

Usage : python iles_maps.py [--apercu] [<nom de carte>...]
"""
import io, re, sys, json, time, urllib.parse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
BROUILLON = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                 r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                 r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\iles')
VW, VH, ECHELLE = 2000, 1300, 2
# zone de carte exploitable (px CSS) : a droite du panneau lateral, hors des
# boutons et du logo
ZONE = (540, 90, 1900, 1200)     # fenetre en px CSS, rendue au double
MARGE = 80                          # px CSS rognes au bord (boutons, recherche)
PART_VISEE = (0.28, 0.5)           # place du contour dans la zone utile
DEZOOM_ENCART = 4


def attendre(s):
    time.sleep(s)


def refuser_consentement(pg):
    attendre(2.5)
    if 'consent' not in pg.url:
        return
    for txt in ('Tout refuser', 'Reject all'):
        b = pg.get_by_role('button', name=txt)
        if b.count():
            b.first.click()
            attendre(3)
            return


def bouton(pg, *noms):
    for n in noms:
        b = pg.get_by_role('button', name=n, exact=True)
        if b.count():
            return b.first
    return None


def capture(pg):
    pg.mouse.move(8, VH - 8)                 # hors carte : pas de fiche au survol
    attendre(0.6)
    return Image.open(io.BytesIO(pg.screenshot())).convert('RGB')


def contour(im):
    """Boite englobante du trace rouge (pointilles), en px de l'image, ou None."""
    a = np.asarray(im).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # le pointille est du rouge Google (234, 67, 53) ; les ecussons routiers
    # sont bruns ou rouge sombre, ils ne passent pas ce filtre
    m = (abs(r - 234) < 16) & (abs(g - 67) < 20) & (abs(b - 53) < 20)
    x0z, y0z, x1z, y1z = [v * ECHELLE for v in ZONE]
    m[:y0z, :] = m[y1z:, :] = False
    m[:, :x0z] = m[:, x1z:] = False
    # l'epingle rouge (quand Google ne trace pas de contour) est du meme rouge,
    # mais pleine : elle survit a une erosion, le pointille non. On la retire.
    masque = Image.fromarray((m * 255).astype('uint8'))
    plein = masque.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(41))
    m &= np.asarray(plein) == 0
    ys, xs = np.nonzero(m)
    if len(xs) < 40:
        return None
    # on ecarte les quelques pixels isoles (epingles, pictos)
    x0, x1 = np.percentile(xs, [1, 99])
    y0, y1 = np.percentile(ys, [1, 99])
    return x0, y0, x1, y1


def epingle(im):
    """Centre de l'epingle rouge (px), quand Google n'a pas trace de contour."""
    a = np.asarray(im).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (abs(r - 234) < 16) & (abs(g - 67) < 20) & (abs(b - 53) < 20)
    x0z, y0z, x1z, y1z = [v * ECHELLE for v in ZONE]
    m[:y0z, :] = m[y1z:, :] = False
    m[:, :x0z] = m[:, x1z:] = False
    plein = np.asarray(Image.fromarray((m * 255).astype('uint8')).filter(ImageFilter.MinFilter(9))) > 0
    ys, xs = np.nonzero(plein)
    if len(xs) < 20:
        return None
    # la pointe de l'epingle, sous la tete ronde, marque le lieu
    return float(np.median(xs)), float(ys.max()) + 12 * ECHELLE


def chercher(pg, requete):
    pg.goto('https://www.google.com/maps/search/' + urllib.parse.quote(requete),
            wait_until='domcontentloaded')
    refuser_consentement(pg)
    for i in range(25):
        attendre(1)
        if '/place/' in pg.url and '/@' in pg.url:
            return True
        if i == 8:
            lien = pg.locator('a[href*="/maps/place/"]')
            if lien.count():
                lien.first.click()
    # pas de fiche de lieu, mais une vue cadree sur le resultat : on s'en
    # contente si le contour rouge est la
    return '/@' in pg.url and contour(capture(pg)) is not None


def zoom_url(pg):
    m = re.search(r'/@-?[\d.]+,-?[\d.]+,([\d.]+)z', pg.url)
    return float(m.group(1)) if m else None


def ile_centre(boite):
    return ((boite[0] + boite[2]) / 2 / ECHELLE, (boite[1] + boite[3]) / 2 / ECHELLE)


def nettoyer(pg):
    """Retire les bandeaux qui se posent sur la carte (enquete « Aidez-nous a
    ameliorer Google Maps », invitations a se connecter...)."""
    pg.evaluate("""() => {
      for (const el of document.querySelectorAll('div, section')) {
        const t = el.innerText || '';
        if (t.length < 400 && /Aidez-nous|Help us improve|Vous voyez un affichage limité/.test(t)
            && getComputedStyle(el).position !== 'static') el.style.display = 'none';
      }
    }""")


def cran(pg, x, y, sens, fin=False):
    """Un cran de molette pointe sur (x, y). Gros cran = un niveau entier
    (attendu jusqu'au bout de l'animation) ; cran fin = ajustement."""
    pg.mouse.move(x, y)
    pg.mouse.wheel(0, (-1 if sens > 0 else 1) * (40 if fin else 100))
    attendre(1.6 if fin else 2.6)


def molette(pg, x, y, crans):
    """Dezoome (ou zoome) de `crans` niveaux entiers, point (x, y) fixe."""
    z0 = zoom_url(pg)
    for _ in range(abs(int(crans)) + 3):
        z = zoom_url(pg)
        if z0 is None or z is None or abs(z - z0) >= abs(crans) - 0.3:
            break
        cran(pg, x, y, crans)
    attendre(2)
    return (zoom_url(pg) or 0) - (z0 or 0)


def cadrer(pg):
    """Google Maps centre l'ile a droite du panneau lateral. On zoome a la
    molette pointee sur elle (elle reste en place) : gros crans tant qu'on est
    loin du but, crans fins ensuite, jusqu'a ce qu'elle occupe une part
    moyenne de la zone exploitable."""
    attendre(3)
    nettoyer(pg)
    utile_w = (ZONE[2] - ZONE[0]) * ECHELLE
    utile_h = (ZONE[3] - ZONE[1]) * ECHELLE
    im = capture(pg)
    boite = contour(im)
    if not boite:
        # pas de contour (archipel epars) : on zoome sur l'epingle, et on
        # rend une petite boite autour d'elle pour cadrer
        pin = epingle(im)
        if pin:
            for _ in range(2):
                cran(pg, pin[0] / ECHELLE, pin[1] / ECHELLE, 1)
            nettoyer(pg)
            im = capture(pg)
            boite = contour(im)
            if not boite:
                pin = epingle(im) or pin
                d = 260 * ECHELLE
                return im, (pin[0] - d, pin[1] - d * 0.75, pin[0] + d, pin[1] + d * 0.75)
    dernier = (im, boite)
    vise = sum(PART_VISEE) / 2
    for _ in range(30):
        if not boite:
            break
        dernier = (im, boite)
        part = max((boite[2] - boite[0]) / utile_w, (boite[3] - boite[1]) / utile_h)
        if PART_VISEE[0] <= part <= PART_VISEE[1]:
            break
        x, y = ile_centre(boite)
        # un niveau entier double la taille : gros cran si on reste du bon cote
        fin = (part * 2 > PART_VISEE[1]) if part < vise else (part / 2 < PART_VISEE[0])
        cran(pg, x, y, 1 if part < vise else -1, fin)
        nettoyer(pg)
        im = capture(pg)
        boite = contour(im)
    if not boite:                       # contour perdu : on garde le dernier etat vu
        return dernier
    return im, boite


def recadrer(im, centre, taille=None):
    """Un 4:3 centre sur `centre` (px), de hauteur `taille` (ou la plus
    grande possible), tenu dans la zone utile. Rend l'image et son origine."""
    x_min, y_min, x_max, y_max = [v * ECHELLE for v in ZONE]
    h_max = min(y_max - y_min, (x_max - x_min) * 3 // 4)
    h = int(min(taille or h_max, h_max))
    w = h * 4 // 3
    x0 = int(min(max(centre[0] - w / 2, x_min), x_max - w))
    y0 = int(min(max(centre[1] - h / 2, y_min), y_max - h))
    return im.crop((x0, y0, x0 + w, y0 + h)), (x0, y0)


def composer(gros, encart, ile=None):
    """Pose l'encart dans le coin de la carte qui recouvre le moins l'ile
    (`ile` : sa boite dans `gros`)."""
    im = gros.copy()
    W, H = im.size
    cw, ch = int(W * 0.8), int(H * 0.8)          # ce que la carte montre
    ew = int(cw * 0.36)
    e = encart.resize((ew, ew * 3 // 4), Image.LANCZOS)
    gx, gy = (W - cw) // 2 + int(cw * 0.025), (H - ch) // 2 + int(ch * 0.03)
    dx, dy = (W + cw) // 2 - int(cw * 0.025) - e.width, (H + ch) // 2 - int(ch * 0.03) - e.height
    coins = [(gx, dy), (dx, dy), (gx, gy), (dx, gy)]   # bas gauche d'abord

    def recouvrement(c):
        if not ile:
            return 0
        x0, y0 = c
        w = max(0, min(x0 + e.width, ile[2]) - max(x0, ile[0]))
        h = max(0, min(y0 + e.height, ile[3]) - max(y0, ile[1]))
        return w * h
    x0, y0 = min(coins, key=recouvrement)
    ombre = Image.new('L', (e.width + 60, e.height + 60), 0)
    ImageDraw.Draw(ombre).rectangle((30, 30, e.width + 30, e.height + 30), fill=120)
    ombre = ombre.filter(ImageFilter.GaussianBlur(12))
    im.paste(Image.new('RGB', ombre.size, (0, 0, 0)), (x0 - 24, y0 - 20), ombre)
    ImageDraw.Draw(im).rectangle((x0 - 6, y0 - 6, x0 + e.width + 5, y0 + e.height + 5), fill='white')
    im.paste(e, (x0, y0))
    return im


def webp(im, q):
    b = io.BytesIO()
    im.save(b, 'WEBP', quality=q)
    return b.getvalue()


# titres de page que Google Maps ne resout pas en un lieu unique
REQUETES = {'Îles Kerguelen': 'Grande Terre Kerguelen', 'Île Pitcairn': 'Pitcairn Island',
            'Atoll de Bikini': 'Bikini Atoll', 'Îles Marquises': 'Marquesas Islands',
            'Java (île)': 'Java Indonésie', 'Île de Pâques': 'Rapa Nui Easter Island',
            'Sainte-Hélène (île)': 'Saint Helena Island', 'Terre-Neuve (île)': 'Newfoundland island', 'Terre-Neuve': 'Île de Terre-Neuve Canada',
            'Komodo (île)': 'Komodo Island'}


# Iles que la recherche cadre mal (archipel epars, pas de contour, fiche
# pointee sur un lieu-dit) : centre et zoom donnes a la main.
COORDS = {'Groenland': (72.0, -41.0, 4.2), 'Île Maurice': (-20.28, 57.57, 10.4),
          'Palaos': (7.45, 134.55, 9.6), 'Maldives': (3.4, 73.35, 7.3),
          'Seychelles': (-4.62, 55.48, 10.6), 'Pitcairn': (-25.066, -130.1, 14.6),
          'Zanzibar': (-6.12, 39.38, 9.6), 'Fidji': (-17.75, 178.3, 8.2)}


def requete_de(c):
    t = c['titrePage']
    if t in REQUETES:
        return REQUETES[t]
    return t.replace(' (île)', '').replace(' (archipel)', ' archipel')


def main():
    from playwright.sync_api import sync_playwright
    apercu = '--apercu' in sys.argv
    noms = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--liste' in sys.argv:                  # un nom par ligne dans ce fichier
        f = Path(sys.argv[sys.argv.index('--liste') + 1])
        noms = [n.strip() for n in f.read_text(encoding='utf-8').splitlines() if n.strip()]
    cartes = json.loads((RACINE / 'data' / 'iles.json').read_text(encoding='utf-8'))['cartes']
    if noms:
        cartes = [c for c in cartes if c['nom'] in noms]
    BROUILLON.mkdir(exist_ok=True)
    fn = RACINE / 'build' / 'notes_atelier.json'
    fs = RACINE / 'build' / 'images_sources.json'
    with sync_playwright() as p:
        nav = p.chromium.launch(channel='chrome', headless=True)
        ctx = nav.new_context(viewport={'width': VW, 'height': VH}, device_scale_factor=ECHELLE,
                              locale='fr-FR')
        pg = ctx.new_page()
        for c in cartes:
            direct = COORDS.get(c['nom'])
            if direct:
                pg.goto('https://www.google.com/maps/@%s,%s,%sz' % direct, wait_until='domcontentloaded')
                refuser_consentement(pg)
                attendre(6)
                nettoyer(pg)
                url = pg.url
                im = capture(pg)
                ile = (VW / 2 * ECHELLE, VH / 2 * ECHELLE)
                h = 2 * (VW / 2 - ZONE[0]) * ECHELLE * 3 / 4 - 20   # symetrique autour du centre
                gros, _ = recadrer(im, ile, h)
                ile_gros = None
                molette(pg, VW / 2, VH / 2, -DEZOOM_ENCART)
                boite = True
                pos = ile
            elif not chercher(pg, requete_de(c)):
                print(f"  ✗ {c['nom']} : lieu introuvable ({pg.url[:70]})")
                continue
            if not direct:
              url = pg.url
              im, boite = cadrer(pg)
              zone_c = ((ZONE[0] + ZONE[2]) / 2 * ECHELLE, (ZONE[1] + ZONE[3]) / 2 * ECHELLE)
              if boite:
                  ile = ((boite[0] + boite[2]) / 2, (boite[1] + boite[3]) / 2)
                  bw, bh = boite[2] - boite[0], boite[3] - boite[1]
                  taille = max(bh / 0.5, bw / 0.5 * 3 / 4)        # l'ile ~50 % du cadre : de la mer autour, et la place de l'encart
              else:
                  ile, taille = zone_c, None
              gros, (gx0, gy0) = recadrer(im, ile, taille)
              ile_gros = (boite[0] - gx0, boite[1] - gy0, boite[2] - gx0, boite[3] - gy0) if boite else None
              # encart : quatre crans plus loin, a la molette pointee sur l'ile,
              # qui reste donc au meme endroit de l'ecran
              molette(pg, ile[0] / ECHELLE, ile[1] / ECHELLE, -DEZOOM_ENCART)
              pos = ile
            h_encart = h if direct else None
            nettoyer(pg)
            loin = capture(pg)
            # ile isolee : tant que l'encart n'est que de l'eau, on recule
            for _ in range(9):
                zone, _ = recadrer(loin, pos, h_encart)
                a = np.asarray(zone.resize((200, 150))).astype(int)
                eau = (abs(a[..., 0] - 144) < 30) & (abs(a[..., 1] - 212) < 30) & (abs(a[..., 2] - 232) < 30)
                if 1 - eau.mean() > 0.08:
                    break
                molette(pg, pos[0] / ECHELLE, pos[1] / ECHELLE, -1)
                nettoyer(pg)
                loin = capture(pg)
            encart, (ex0, ey0) = recadrer(loin, pos, h_encart)
            d = ImageDraw.Draw(encart)
            r = encart.width * 0.04
            cx, cy = pos[0] - ex0, pos[1] - ey0
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(220, 40, 40), width=max(5, int(r / 5)))
            im = composer(gros, encart, ile_gros)
            f = c['id'].split('_', 1)[1]
            etat = '' if boite else '  (contour rouge non trouve : centre de l ecran)'
            if apercu:
                im.save(BROUILLON / f'{f}.png')
                print(f"  {c['nom']:<30} apercu{etat}")
                continue
            W, H = im.size
            cw, ch = int(W * 0.8), int(H * 0.8)
            centre = im.crop(((W - cw) // 2, (H - ch) // 2, (W - cw) // 2 + cw, (H - ch) // 2 + ch))
            orig = im if max(im.size) <= 2400 else im.resize((2400, 1800), Image.LANCZOS)
            for rel, octets in ((f'images/originaux/iles/{f}.webp', webp(orig, 88)),
                                (c['imageUrl'], webp(centre.resize((800, 600), Image.LANCZOS), 90)),
                                (c['thumbUrl'], webp(centre.resize((213, 160), Image.LANCZOS), 82))):
                (RACINE / rel).write_bytes(octets)
            notes = json.loads(fn.read_text(encoding='utf-8'))
            notes['cadrages'][c['id']] = {'cx': 0.5, 'cy': 0.5, 'w': 0.8, 'original': True,
                                          'editeLe': 0, 'auto': True}
            fn.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
            sources = json.loads(fs.read_text(encoding='utf-8'))
            sources[c['id']] = {'source': 'google-maps', 'url': url}
            fs.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')
            print(f"  {c['nom']:<30} posee{etat}")
        nav.close()


if __name__ == '__main__':
    main()
