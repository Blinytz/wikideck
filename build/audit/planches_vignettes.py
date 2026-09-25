#!/usr/bin/env python3
"""Assemble les vignettes de chaque collection en une seule planche.

L'atelier affiche plus de 5 500 vignettes. Une requete par vignette, c'est
soit lent (170 ms chacune, quatre a la fois), soit refuse par GitHub Pages
(429 « trop de requetes ») des qu'on va plus vite. Une planche par
collection ramene le tout a une centaine de requetes : la collection
s'affiche d'un coup.

Chaque case fait 160 x 120 (le 4:3 de la grille), la vignette y est recadree
au centre, comme le faisait `object-fit: cover`. L'index `data/planches.json`
donne pour chaque collection l'ordre des cartes, la geometrie et la date de
fabrication : une carte recadree dans l'atelier APRES cette date reprend sa
vignette individuelle, pour que le travail de l'utilisateur se voie tout de
suite, sans attendre une nouvelle planche.

Une planche n'est reecrite que si son contenu a change (empreinte), pour ne
pas grossir le depot a chaque passage.

Usage : python planches_vignettes.py [<slug>...]   (toutes par defaut)
"""
import io, sys, json, time, hashlib
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent

CL, CH, COLS = 160, 120, 10
FOND = (13, 13, 22)          # le fond des cases vides, celui de la grille


def case(chemin):
    try:
        im = Image.open(chemin).convert('RGB')
    except Exception:
        return Image.new('RGB', (CL, CH), FOND)
    r = max(CL / im.width, CH / im.height)            # couvrir la case
    im = im.resize((max(CL, round(im.width * r)), max(CH, round(im.height * r))),
                   Image.LANCZOS)
    x, y = (im.width - CL) // 2, (im.height - CH) // 2
    return im.crop((x, y, x + CL, y + CH))


def main():
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    demandes = [a for a in sys.argv[1:] if not a.startswith('--')]
    fi = RACINE / 'data' / 'planches.json'
    index = json.loads(fi.read_text(encoding='utf-8')) if fi.exists() else {}
    dossier = RACINE / 'images' / 'planches'
    dossier.mkdir(parents=True, exist_ok=True)
    slugs_vivants = {c['slug'] for c in idx['collections']}
    ecrites = inchangees = 0

    for col in idx['collections']:
        slug = col['slug']
        if demandes and slug not in demandes:
            continue
        donnees = json.loads((RACINE / col['fichier']).read_text(encoding='utf-8'))
        cartes = donnees['cartes']
        # Empreinte de chaque vignette : elle entre dans l'adresse de l'image
        # (?v=...), si bien qu'une image regeneree a une adresse neuve et que
        # le navigateur ne peut plus servir l'ancienne depuis son cache.
        change = False
        for c in cartes:
            t = RACINE / c['thumbUrl']
            v = hashlib.sha1(t.read_bytes()).hexdigest()[:8] if t.exists() else None
            if v and c.get('imgV') != v:
                c['imgV'] = v
                change = True
        if change:
            (RACINE / col['fichier']).write_text(json.dumps(donnees, ensure_ascii=False),
                                                 encoding='utf-8')
        lignes = (len(cartes) + COLS - 1) // COLS
        planche = Image.new('RGB', (CL * COLS, CH * max(1, lignes)), FOND)
        for i, c in enumerate(cartes):
            planche.paste(case(RACINE / c['thumbUrl']), ((i % COLS) * CL, (i // COLS) * CH))
        tampon = io.BytesIO()
        planche.save(tampon, 'WEBP', quality=78, method=6)
        octets = tampon.getvalue()
        empreinte = hashlib.sha1(octets).hexdigest()[:10]
        ids = [c['id'] for c in cartes]
        ancien = index.get(slug)
        if ancien and ancien.get('v') == empreinte and ancien.get('ids') == ids:
            # Contenu identique, verifie a l'instant : la planche reflete les
            # vignettes actuelles. On avance sa date, sans quoi une vignette
            # restauree a l'identique (fichier plus recent, meme image) la
            # ferait passer pour perimee.
            ancien['genereLe'] = int(time.time() * 1000)
            inchangees += 1
            continue
        (dossier / f'{slug}.webp').write_bytes(octets)
        index[slug] = {'v': empreinte, 'genereLe': int(time.time() * 1000),
                       'cols': COLS, 'lignes': lignes, 'ids': ids}
        ecrites += 1
        print(f'  {slug:<40} {len(cartes):>4} cartes  {len(octets) // 1024:>4} Ko')

    # planches de collections disparues
    for slug in [s for s in index if s not in slugs_vivants]:
        index.pop(slug)
        (dossier / f'{slug}.webp').unlink(missing_ok=True)
        print(f'  x {slug} (collection disparue)')

    fi.write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')),
                  encoding='utf-8')
    total = sum(p.stat().st_size for p in dossier.glob('*.webp'))
    print(f'{ecrites} planche(s) ecrite(s), {inchangees} inchangee(s), '
          f'{len(index)} au total, {total / 1e6:.1f} Mo')


if __name__ == '__main__':
    main()
