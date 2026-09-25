#!/usr/bin/env python3
"""Noeuds : de vraies photos, homogenes, detourees sur un meme fond.

L'utilisateur a juge la collection trop heterogene (photos sur fonds de
couleur, dessins, schemas) et ne veut pas d'images creees. On s'appuie donc
sur deux series de PHOTOGRAPHIES faites en studio sur fond uni :

  - la serie de l'US Coast Guard sur Commons (« ... ABoK nnn ... USCG »),
    cordes rouges ou bleues sur fond blanc, 1280 px, numerotee d'apres
    l'Ashley Book of Knots ;
  - la serie « WPK », cordes rouges sur fond gris, pour les noeuds
    d'escalade qui manquent a la premiere.

Sur un fond aussi propre, le detourage est net. Chaque noeud est pose en
grand, sans cadre, sur le fond ardoise de la collection : les deux series se
fondent en une seule. Pour les noeuds absents des deux series, on cherche une
photo sur fond uni ; une image qui ne se detoure pas proprement est
refusee, et la carte garde alors son image, plutot que de reintroduire un
style different.

Usage : python noeuds_series.py [--apercu]
"""
import io, re, sys, json
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
sys.path.insert(0, str(ICI))
import images_lib as il
import habiller_images as hab

# carte -> recherches Commons, dans l'ordre : (requete, fragment du nom de fichier)
USCG = lambda frag: ('intitle:USCG intitle:ABoK', frag)
CARTES = {
    'Demi-nœud': [USCG('Knot-overhand-ABoK')],
    'Nœud plat': [USCG('Knot-square-ABoK 1204-USCG (cropped)'), USCG('Knot-square')],
    'Nœud en huit': [('intitle:"figure eight knot"', 'knot'), ('intitle:"figure-eight knot"', 'knot')],
    'Nœud en huit en double': [USCG('Loop-figure 8')],
    "Nœud d'écoute": [USCG('Sheet Bend - ABoK')],
    'Nœud de Carrick': [USCG('Carrick Bend')],
    'Nœud de Zeppelin': [('intitle:"Zeppelin bend"', 'eppelin')],
    'Nœud de pêcheur': [USCG('Knot-fishermans')],
    'Nœud de pêcheur double': [('intitle:WPK', "Double fisherman")],
    'Nœud double': [('intitle:"double overhand"', 'verhand')],
    'Nœud double gansé': [('intitle:"double overhand noose"', 'oose')],
    'Nœud en queue de cochon': [('intitle:"granny knot"', 'ranny')],
    'Nœud de chaise': [USCG('Knot-bowline-ABoK 1010')],
    'Nœud de chaise double en huit': [('intitle:Karash', 'arash')],
    'Nœud de chaise double sur son double': [USCG('Knot-bowline bight')],
    'Nœud de papillon alpin': [('intitle:WPK', 'Alpine butterfly')],
    'Nœud de plein poing': [USCG('Loop-overhand')],
    'Nœud coulant': [USCG('Knot-noose')],
    'Nœud de pendu': [('intitle:"hangman" knot', 'angman')],
    'Demi-clef': [USCG('Hitch-half-ABoK')],
    'Nœud de cabestan': [USCG('Clove Hitch - ABoK')],
    'Nœud de demi-cabestan': [USCG('Hitch-munter')],
    'Nœud de taquet': [('intitle:"cleat hitch"', 'leat')],
    'Nœud de grappin': [('intitle:"anchor bend"', 'nchor')],
    "Nœud en tête d'alouette": [USCG('Cow Hitch')],
    "Nœud d'élingue": [('intitle:"bottle sling"', 'ling'), ('intitle:"jug sling"', 'ling')],
    'Nœud de ride': [('intitle:"Matthew Walker"', 'alker')],
    'Nœud de laguis': [('intitle:"running bowline"', 'owline')],
    # le noeud de galere est le noeud simple gance : le « slip knot » de l'USCG
    'Nœud de galère': [USCG('Knot-slip-ABoK')],
    'Nœud de jambe de chien': [USCG('Knot-sheepshank')],
    # le noeud de fouet est le « taut-line hitch »
    'Nœud de fouet': [USCG('Hitch-taut line')],
    'Nœud de bois': [('intitle:"timber hitch" knot', 'imber hitch')],
    'Nœud de Prusik': [('intitle:WPK', 'Prusik')],
    'Nœud de Machard': [('intitle:WPK', 'Klemheist')],
    'Nœud de franciscain': [('intitle:"capuchin knot"', 'apuchin'), ('intitle:"barrel knot"', 'arrel')],
}
# dessins et schemas : l'utilisateur veut des photos
PAS_PHOTO = re.compile(r'\.(svg|png|gif|pdf|djvu|tif)$|EB1911|PSF|ABOK-\d|diagram|drawing|scouting|'
                       r'animation|USNS|skater|book|page|scan',
                       re.I)
STYLE = dict(hab.STYLES['noeuds'], boite=(600, 470))
STYLE.pop('tuile', None)


def detourer_corde(im):
    """Detoure une corde de couleur vive par sa SATURATION.

    Le detourage par remplissage depuis les bords laissait des taches
    blanches : les ombres du studio sont grises, et l'interieur des boucles,
    enferme par la corde, n'est pas atteint depuis le bord. Ici, la corde est
    tout ce qui est sature (rouge, bleu, vert) ; les fils blancs tresses dans
    la corde sont reboucles par une fermeture morphologique. Rend None si le
    resultat n'a pas l'air d'une corde (trop peu ou trop de pixels gardes)."""
    import numpy as np
    from PIL import ImageFilter
    hsv = np.asarray(im.convert('RGB').convert('HSV')).astype(np.int16)
    s, v = hsv[..., 1], hsv[..., 2]
    corde = (s > 70) & (v > 40)
    garde = corde.mean()
    if garde < 0.02 or garde > 0.6:
        return None
    masque = Image.fromarray(np.where(corde, np.uint8(255), np.uint8(0)))
    masque = masque.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))
    masque = masque.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1))
    out = im.convert('RGBA')
    out.putalpha(masque)
    return out


def fichiers(requete, frag):
    d = il.api('commons.wikimedia.org', dict(action='query', list='search', srsearch=requete,
                                              srnamespace=6, srlimit=40))
    for h in ((d or {}).get('query') or {}).get('search', []):
        f = h['title'].split(':', 1)[1]
        if frag.lower() in f.lower() and not PAS_PHOTO.search(f):
            yield f


# Choix faits a l'oeil parmi les candidats (noeuds_candidats.json, rang dans la
# liste). Sans eux, la recherche automatique prenait parfois une photo hors
# sujet : un corbeau pour le noeud de pendu, un portrait pour le noeud de
# chaise double en huit, un schema pour le noeud de franciscain.
CHOIX = {
    'Nœud de Zeppelin': 1, 'Nœud de pêcheur double': 1, 'Nœud double': 0,
    'Nœud de chaise double en huit': 1, 'Nœud de pendu': 1, 'Nœud de grappin': 1,
    'Nœud de ride': 1, 'Nœud de laguis': 0, 'Nœud de bois': 0, 'Nœud de Machard': 0,
}
# Aucune photo propre et juste n'existe pour ceux-ci : ils gardent leur image,
# plutot qu'un noeud voisin (le « figure 8 bend » n'est pas le noeud en huit,
# le « blood knot » n'est pas le noeud de franciscain) ou un detourage sale.
GARDER = {'Nœud en huit', 'Nœud double gansé', 'Nœud en queue de cochon',
          'Nœud de papillon alpin', 'Nœud de taquet', 'Nœud de franciscain'}


def main():
    apercu = '--apercu' in sys.argv
    cartes = json.loads((RACINE / 'data' / 'noeuds.json').read_text(encoding='utf-8'))['cartes']
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))
    brouillon = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                     r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                     r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\series')
    brouillon.mkdir(exist_ok=True)
    deja, faits, gardees = set(), 0, []
    candidats = json.loads((ICI / 'noeuds_candidats.json').read_text(encoding='utf-8'))
    for c in cartes:
        retenu = None
        if c['nom'] in GARDER:
            gardees.append(c['nom'])
            continue
        if c['nom'] in CHOIX:
            f = candidats[c['nom']][CHOIX[c['nom']]]
            im = hab.charger(hab.url_fichier(f, 1200))
            sujet = detourer_corde(im) if im is not None else None
            retenu = (f, sujet) if sujet is not None else None
        for requete, frag in ([] if retenu else CARTES.get(c['nom'], [])):
            for f in fichiers(requete, frag):
                if f in deja:
                    continue
                im = hab.charger(hab.url_fichier(f, 1200))
                if im is None or max(im.size) < 500:
                    continue
                sujet = detourer_corde(im)
                if sujet is not None:
                    retenu = (f, sujet)
                    break
            if retenu:
                break
        if not retenu:
            gardees.append(c['nom'])
            continue
        f, sujet = retenu
        deja.add(f)
        img = hab.composer(sujet, dict(STYLE, _nom=c['nom']), True)
        print(f"  {c['nom']:<38} <- {f[:60]}")
        faits += 1
        if apercu:
            img.save(brouillon / (c['id'].split('_', 1)[1] + '.png'))
            continue
        brut = io.BytesIO(); img.save(brut, 'PNG')
        for rel, octets in ((c['imageUrl'], il.to_full(brut.getvalue())),
                            (c['thumbUrl'], il.to_thumb(brut.getvalue()))):
            (RACINE / rel).write_bytes(octets)
        sources[c['id']] = {'source': 'commons-serie', 'fichier': f}
    if not apercu:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'{faits} noeud(s) en photo detouree ; gardent leur image : {gardees}')


if __name__ == '__main__':
    main()
