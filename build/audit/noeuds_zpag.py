#!/usr/bin/env python3
"""Illustre les noeuds avec les images de zpag.net, a la demande de l'utilisateur.

Source : https://zpag.net/Noeuds/liste_noeuds.htm, un site francais de
matelotage qui montre chaque noeud en photo, sur fond neutre et dans un style
constant. C'est ce qui manquait a la collection : les images de Wikipedia
melangeaient schemas, photos de cordes d'escalade et vues d'ensemble.

Le site est ancien et ses images sont petites (220 a 300 px). Pour chaque
noeud, on retient sur sa page l'image de plus grande surface, qui est en
general le noeud termine ; l'apercu de survol (150 px) ne sert qu'en dernier
recours. L'image est ensuite posee en tuile sur le fond ardoise de la
collection, comme les autres noeuds.

La correspondance carte -> page est ecrite a la main : les intitules du site
ne suivent pas ceux de Wikipedia (« Tete alouette », « Noeud demi-cle »,
« Amarrage a fouet »...). Les noeuds absents du site gardent leur image.

Usage : python noeuds_zpag.py [--apercu]
"""
import io, re, sys, json, time, urllib.request
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
sys.path.insert(0, str(ICI))
import images_lib as il
import habiller_images as hab

BASE = 'https://zpag.net/Noeuds/'
UA = {'User-Agent': 'Mozilla/5.0 (wikideck, usage personnel)'}

# nom de carte -> intitule exact sur la liste du site
CORRESPONDANCE = {
    'Demi-nœud': 'Demi-nœud',
    'Nœud plat': 'Noeud pla',               # intitule tronque sur le site
    'Nœud en huit': 'Noeud en huit',
    'Nœud en huit en double': 'Nœud en huit double',
    "Nœud d'écoute": 'Noeud écoute',
    'Nœud de Carrick': 'Noeud de Carrick',
    'Nœud de Zeppelin': 'Noeud zeppelin',
    'Nœud de pêcheur': 'Noeud du pêcheur',
    'Nœud de pêcheur double': 'Noeud du pêcheur double',
    'Nœud double': 'Simple double',
    'Nœud de chaise': 'Noeud de chaise',
    'Nœud de chaise double sur son double': 'Noeud de chaise en double',
    'Nœud de papillon alpin': 'Noeud papillon',
    'Nœud de plein poing': 'Noeud de plein poing',
    'Nœud coulant': 'Nœud coulant simple',
    'Nœud de pendu': 'Noeud de pendu',
    'Demi-clef': 'Noeud demi-clé',
    'Nœud de cabestan': 'Noeud de cabestan',
    'Nœud de demi-cabestan': 'Demi-cabestan',
    'Nœud de taquet': 'Noeud de taquet',
    'Nœud de grappin': 'Noeud de grappin',
    "Nœud en tête d'alouette": 'Tête alouette',
    "Nœud d'élingue": 'Nœud élingue',
    'Nœud de ride': 'Nœud de ride',
    'Nœud de laguis': 'Noeud de laguis',
    'Nœud de galère': 'Noeud de galère',
    'Nœud de jambe de chien': 'Noeud de jambe de chien',
    'Nœud de fouet': 'Amarrage à fouet',
    'Nœud de bois': 'Noeud de bois',
    'Nœud de Prusik': 'Noeud de prusik',
    'Nœud de Machard': 'Noeud de machard',
    # le « noeud de cravate » du site est un noeud marin, pas une cravate :
    # la carte garde son image
    'Nœud de franciscain': 'Noeud de capucin',   # capucin = franciscain
}


# Images imposees (page, fichier) quand la plus grande image de la page n'est
# pas le bon noeud : la page du noeud plat montre en grand le noeud de vache,
# qui est justement le noeud en queue de cochon.
IMPOSEES = {
    'Nœud plat': ('noeud_plat.htm', 'images9/plat3.jpg'),
    'Nœud en queue de cochon': ('noeud_plat.htm', 'images9/vache.jpg'),
}
# En dessous de cette taille, l'image serait floue une fois agrandie : la
# carte garde alors son image actuelle.
COTE_MIN = 200


def lire(url):
    for essai in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read()
        except Exception:
            time.sleep(2 * (essai + 1))
    return None


def index_du_site():
    h = lire(BASE + 'liste_noeuds.htm').decode('cp1252', 'replace')
    site = {}
    for attrs, txt in re.findall(r'<a([^>]*)>(.*?)</a>', h, re.S | re.I):
        href = re.search(r'href="([^"]+)"', attrs)
        apercu = re.search(r"img src=([^ '>]+)", attrs)
        t = re.sub(r'<[^>]+>', '', txt).split("'")[0]
        t = re.sub(r'\s+', ' ', t).replace('&nbsp;', ' ').strip()
        if href and apercu and t and t not in site:
            site[t] = (href.group(1), apercu.group(1))
    return site


def meilleure_image(page):
    """L'image de plus grande surface de la page du noeud."""
    h = lire(BASE + page)
    if not h:
        return None, None
    h = h.decode('cp1252', 'replace')
    dossier = page.rsplit('/', 1)[0] + '/' if '/' in page else ''
    meilleure, surface = None, 0
    for src in re.findall(r'<img[^>]+src="([^"]+)"', h, re.I):
        if src.startswith('http') or src.lower().endswith('.gif'):
            continue
        data = lire(BASE + dossier + src)
        if not data:
            continue
        try:
            im = Image.open(io.BytesIO(data)).convert('RGB')
        except Exception:
            continue
        if im.width * im.height > surface:
            meilleure, surface = (im, src), im.width * im.height
        time.sleep(0.15)
    return meilleure if meilleure else (None, None)


def main():
    apercu = '--apercu' in sys.argv
    site = index_du_site()
    cartes = json.loads((RACINE / 'data' / 'noeuds.json').read_text(encoding='utf-8'))['cartes']
    style = dict(hab.STYLES['noeuds'], tuile=420)
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))
    brouillon = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                     r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                     r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\zpag')
    brouillon.mkdir(exist_ok=True)
    faits, absents = 0, []
    for c in cartes:
        if c['nom'] in IMPOSEES:
            page, src = IMPOSEES[c['nom']]
            data = lire(BASE + src)
            im = Image.open(io.BytesIO(data)).convert('RGB') if data else None
        else:
            intitule = CORRESPONDANCE.get(c['nom'])
            if not intitule or intitule not in site:
                absents.append(c['nom'])
                continue
            page, _ = site[intitule]
            im, src = meilleure_image(page)
        if im is None or max(im.size) < COTE_MIN:
            absents.append(c['nom'] + (' (image du site trop petite)' if im else ''))
            continue
        img = hab.composer_tuile(im.convert('RGBA'), style)
        print(f"  {c['nom']:<36} <- {page} : {src} {im.size}")
        faits += 1
        if apercu:
            img.save(brouillon / (c['id'].split('_', 1)[1] + '.png'))
            continue
        brut = io.BytesIO(); img.save(brut, 'PNG')
        for rel, octets in ((c['imageUrl'], il.to_full(brut.getvalue())),
                            (c['thumbUrl'], il.to_thumb(brut.getvalue()))):
            (RACINE / rel).write_bytes(octets)
        sources[c['id']] = {'source': 'zpag.net', 'fichier': BASE + page}
    if not apercu:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'{faits} noeud(s) illustre(s) depuis zpag.net ; gardent leur image : {absents}')


if __name__ == '__main__':
    main()
