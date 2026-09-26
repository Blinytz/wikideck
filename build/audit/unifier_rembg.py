#!/usr/bin/env python3
"""Detoure les cartes d'une collection avec rembg et les pose sur son fond.

Generalisation de noeuds_unifier.py aux monnaies. Le detourage « maison »
laissait des bords manges, ou posait l'image dans un cadre blanc quand il
n'osait pas detourer (livre sterling, euro, peso chilien) : rembg, un
detoureur par reseau de neurones, isole billets et pieces quel que soit le
fond. Aucun cadre : chaque objet est pose directement sur le fond de la
collection, avec son inclinaison et son ombre.

La source est la photo d'origine (images_sources.json), jamais l'image deja
composee. Les cartes retouchees par l'utilisateur dans l'atelier (cadrage
enregistre) ne sont pas touchees : ce sont ses choix.

Usage : python unifier_rembg.py <slug> [<slug>...] [--apercu] [--seul "Nom"]
"""
import io, sys, json
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
sys.path.insert(0, str(ICI))
import images_lib as il
import habiller_images as hab
from rembg import remove, new_session

BROUILLON = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                 r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                 r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\unifier')


# Cartes retouchees dans l'atelier que l'utilisateur demande quand meme de
# refaire : la source est alors SA grande image.
# planches de plusieurs billets : l'enveloppe les souderait en un bloc
SANS_REPARATION = {'Dollar américain', 'Couronne tchèque', 'Dinar irakien'}
REFAIRE_RETOUCHEES = {'Florin', 'Thaler', 'Denier franc', 'Gros tournois', 'Aureus',
                      'Follis', 'Denier romain', 'Drachme', 'Taka', 'Riyal saoudien',
                      'Riyal qatarien'}


def source(c, sources, cad=()):
    # grand complement : l'image entiere choisie a l'oeil est dans originaux/,
    # l'image de la carte n'en est qu'un recadrage 4:3 qui couperait un billet
    if (sources.get(c['id']) or {}).get('source') == 'grand-complement':
        f = RACINE / 'images' / 'originaux' / c['id'].split('_', 1)[0] / (c['id'].split('_', 1)[1] + '.webp')
        if f.exists():
            return Image.open(f).convert('RGBA'), 'grand-complement'
    if c['id'] in cad:
        return Image.open(RACINE / c['imageUrl']).convert('RGBA'), 'atelier'
    f = (sources.get(c['id']) or {}).get('fichier')
    if f and f != '(image actuelle)' and not f.startswith('http'):
        im = hab.charger(hab.url_fichier(f, 1280))
        if im is not None:
            return im.convert('RGBA'), f
    return Image.open(RACINE / c['imageUrl']).convert('RGBA'), 'image actuelle'


def couverture(im, alpha):
    """Part de l'objet (tout ce qui differe du fond uni) gardee par rembg.

    Sur un billet, rembg ne garde souvent que les visages et jette le papier :
    la couverture s'effondre. Rend None si le fond n'est pas uni (on ne sait
    alors pas mesurer)."""
    import numpy as np
    arr = np.asarray(im.convert('RGB')).astype(np.int16)
    bord = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    if bord.std(axis=0).mean() > 18:
        return None
    objet = np.abs(arr - np.median(bord, axis=0)).max(axis=2) >= 26
    if objet.sum() < 100:
        return None
    garde = np.asarray(alpha) > 128
    return (objet & garde).sum() / objet.sum()


def reparer(im, alpha):
    """Complete un billet ronge par le detoureur.

    Un billet est convexe : quand l'image n'a qu'un objet principal, on
    remplace son masque par son enveloppe convexe, donc on rend au billet les
    zones que le reseau a prises pour du fond (papier clair, filigrane). Si les
    pixels ajoutes ressemblent au fond, c'est un eventail de billets et non un
    billet ronge : on ne touche a rien. Rend un masque 'L' ou None."""
    import numpy as np
    from PIL import ImageDraw, ImageFilter
    rgb = im.convert('RGB')
    arr = np.asarray(rgb).astype(np.int16)
    bord = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    ref = np.median(bord, axis=0)
    A = np.asarray(alpha) > 128
    if bord.std(axis=0).mean() <= 18:
        A = A | (np.abs(arr - ref).max(axis=2) >= 26)
    lw = 300; r = lw / rgb.width; lh = max(1, round(rgb.height * r))
    m = Image.fromarray(np.where(A, np.uint8(255), np.uint8(0))).resize((lw, lh), Image.NEAREST)
    m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    obj = np.asarray(m) > 0
    vus = np.zeros_like(obj); comps = []
    for y0 in range(lh):
        for x0 in range(lw):
            if obj[y0, x0] and not vus[y0, x0]:
                pile, pts = [(x0, y0)], []
                vus[y0, x0] = True
                while pile:
                    x, y = pile.pop(); pts.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < lw and 0 <= ny < lh and obj[ny, nx] and not vus[ny, nx]:
                            vus[ny, nx] = True; pile.append((nx, ny))
                comps.append(pts)
    if not comps:
        return None
    comps.sort(key=len, reverse=True)
    grand = comps[0]
    if len(grand) < 0.85 * sum(len(c) for c in comps):
        return None                                  # plusieurs objets
    h = hab._enveloppe(grand)
    if len(h) < 3:
        return None
    H = Image.new('L', (lw, lh), 0); ImageDraw.Draw(H).polygon(h, fill=255)
    Hn = np.asarray(H) > 0
    Ln = np.zeros_like(Hn)
    for x, y in grand:
        Ln[y, x] = True
    ajout = Hn & ~Ln
    if ajout.sum() < 0.02 * Hn.sum():
        return None                                  # rien a reparer
    petit = np.asarray(rgb.resize((lw, lh), Image.BILINEAR)).astype(np.int16)
    comme_fond = (np.abs(petit - ref).max(axis=2) < 26) & ajout
    if bord.std(axis=0).mean() <= 40 and comme_fond.sum() > 0.3 * ajout.sum():
        return None                                  # eventail : le vide est du fond
    return H.resize(rgb.size, Image.BILINEAR).point(lambda v: 255 if v >= 128 else 0)             .filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))


def rectangle(im, alpha):
    """Un billet seul, scanne droit : on le decoupe en rectangle exact.

    Masque = ce que garde le reseau + tout ce qui differe du fond. S'il n'y a
    qu'un objet et que son rectangle englobant ne contient presque pas de
    fond (le billet est droit), le billet EST ce rectangle : on recadre."""
    import numpy as np
    rgb = im.convert('RGB')
    arr = np.asarray(rgb).astype(np.int16)
    bord = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    if bord.std(axis=0).mean() > 40:
        return None
    ref = np.median(bord, axis=0)
    fond = np.abs(arr - ref).max(axis=2) < 26
    M = (np.asarray(alpha) > 128) | ~fond
    ys, xs = np.where(M)
    if not len(xs):
        return None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    boite = M[y0:y1, x0:x1]
    if boite.mean() < 0.94:                 # du fond dans la boite : pas droit, ou plusieurs objets
        return None
    if (x1 - x0) * (y1 - y0) < 0.15 * M.size:
        return None
    out = rgb.crop((int(x0), int(y0), int(x1), int(y1))).convert('RGBA')
    return out


def detourer_au_mieux(im, session, c, candidats):
    """Rend (sujet RGBA, origine, methode) ou None."""
    import numpy as np
    a = np.asarray(im.getchannel('A'))
    bord_a = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    if (bord_a < 20).mean() > 0.9 and (a > 128).mean() > 0.05:
        return im, None, 'transparent'      # la source est deja detouree
    im = im.convert('RGB')
    sujet = remove(im, session=session, post_process_mask=True)
    sujet.putalpha(sujet.getchannel('A').point(lambda v: 0 if v < 40 else v))
    if not sujet.getchannel('A').getbbox():
        return None
    if c['nom'] in SANS_REPARATION:
        return sujet, None, 'ia'
    r = rectangle(im, sujet.getchannel('A'))
    if r is not None:
        return r, None, 'rectangle'
    masque = reparer(im, sujet.getchannel('A'))
    if masque is not None:
        s2 = im.convert('RGBA'); s2.putalpha(masque)
        return s2, None, 'repare'
    cov = couverture(im, sujet.getchannel('A'))
    if cov is not None and cov < 0.75:
        return None
    return sujet, None, 'ia'


def main():
    apercu = '--apercu' in sys.argv
    seuls_neuves = '--neuves' in sys.argv       # grand complement seulement
    seuls = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == '--seul']
    slugs = [a for a in sys.argv[1:] if not a.startswith('--') and a not in seuls]
    session = new_session('birefnet-general')
    cad = json.loads((RACINE / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))['cadrages']
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    BROUILLON.mkdir(exist_ok=True)
    for slug in slugs:
        style = dict(hab.STYLES[slug])
        style.pop('tuile', None)
        cartes = json.loads(par_slug[slug].read_text(encoding='utf-8'))['cartes']
        fc = RACINE / 'data' / 'choix' / f'{slug}.json'
        candidats = json.loads(fc.read_text(encoding='utf-8')) if fc.exists() else {}
        if seuls:
            cartes = [c for c in cartes if c['nom'] in seuls]
        faites, epargnees = 0, 0
        for c in cartes:
            neuve = (sources.get(c['id']) or {}).get('source') == 'grand-complement'
            if seuls_neuves and not neuve:
                continue
            if c['id'] in cad and c['nom'] not in REFAIRE_RETOUCHEES and not neuve:
                epargnees += 1
                continue
            im, origine = source(c, sources, cad)
            im.thumbnail((1280, 1280), Image.LANCZOS)
            r = detourer_au_mieux(im, session, c, candidats)
            if r is None:
                print(f"  ✗ {c['nom']} : aucun detourage propre, image gardee")
                continue
            sujet, autre, methode = r
            if autre:
                origine = autre
            img = hab.composer(sujet, dict(style, _nom=c['nom']), True)
            faites += 1
            print(f"  {c['nom']:<34} {methode:<9} <- {str(origine)[:55]}")
            if apercu:
                img.save(BROUILLON / (c['id'].split('_', 1)[1] + '.png'))
                continue
            brut = io.BytesIO(); img.save(brut, 'PNG')
            for rel, octets in ((c['imageUrl'], il.to_full(brut.getvalue())),
                                (c['thumbUrl'], il.to_thumb(brut.getvalue()))):
                (RACINE / rel).write_bytes(octets)
            sources[c['id']] = dict(sources.get(c['id']) or {}, detourage=methode,
                                    fichier=origine)
        print(f'{slug} : {faites} detouree(s), {epargnees} retouchee(s) par toi epargnee(s)')
    if not apercu:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
