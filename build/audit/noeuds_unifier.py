#!/usr/bin/env python3
"""Unifie les 35 noeuds : chaque corde detouree, posee sur le meme fond.

Demande de l'utilisateur : plus d'homogeneite, plus de fonds blancs, un fond
unique. Ses 11 cartes retouchees etaient de belles photos, mais sur des fonds
varies (blanc, bois, papier quadrille, tissu rose). Le detourage par couleur
ne suffisait pas : il perdait les cordes blanches ou sombres et gardait les
fonds colores.

On utilise rembg (modele isnet-general-use), un detoureur par reseau de
neurones, qui isole l'objet quel que soit le fond.

Sources : pour les cartes retouchees par l'utilisateur, SA grande image, qui
porte son choix de photo et son cadrage ; pour les autres, la photo Commons
d'origine, plus nette qu'une image deja composee.

Le noeud est ensuite recadre au plus pres, agrandi pour remplir la meme
surface sur chaque carte, et pose sur le fond ardoise avec une ombre douce.

Usage : python noeuds_unifier.py [--apercu] [<nom de carte>...]
"""
import io, sys, json
from pathlib import Path
from PIL import Image, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
sys.path.insert(0, str(ICI))
import images_lib as il
import habiller_images as hab
from rembg import remove, new_session

GARDER = {'Nœud de ride'}
STYLE = dict(hab.STYLES['noeuds'], boite=(660, 480), ombre=(0.55, 14, 8, 14))
STYLE.pop('tuile', None)


def source(c, cad, sources):
    if c['id'] in cad:                       # le choix et le cadrage de l'utilisateur
        return Image.open(RACINE / c['imageUrl']).convert('RGB'), 'atelier'
    f = (sources.get(c['id']) or {}).get('fichier')
    if f and not f.startswith('http'):
        im = hab.charger(hab.url_fichier(f, 1280))
        if im is not None:
            return im.convert('RGB'), f
    return Image.open(RACINE / c['imageUrl']).convert('RGB'), 'image actuelle'


def main():
    apercu = '--apercu' in sys.argv
    seuls = [a for a in sys.argv[1:] if not a.startswith('--')]
    session = new_session('isnet-general-use')
    cad = json.loads((RACINE / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))['cadrages']
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))
    cartes = json.loads((RACINE / 'data' / 'noeuds.json').read_text(encoding='utf-8'))['cartes']
    if seuls:
        cartes = [c for c in cartes if c['nom'] in seuls]
    # rembg ampute le noeud de ride (tresse tenue en main) : son detourage par
    # couleur etait deja propre, la carte le garde
    cartes = [c for c in cartes if c['nom'] not in GARDER]
    brouillon = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                     r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                     r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\unifier')
    brouillon.mkdir(exist_ok=True)
    for c in cartes:
        im, origine = source(c, cad, sources)
        im.thumbnail((1280, 1280), Image.LANCZOS)
        sujet = remove(im, session=session, post_process_mask=True)
        a = sujet.getchannel('A')
        # les pixels a peine opaques sont du bruit de fond : on les coupe
        sujet.putalpha(a.point(lambda v: 0 if v < 40 else v))
        if not sujet.getchannel('A').getbbox():
            print(f"  ✗ {c['nom']} : rien de detoure")
            continue
        img = hab.composer(sujet, dict(STYLE, _nom=c['nom']), True)
        print(f"  {c['nom']:<38} <- {str(origine)[:60]}")
        if apercu:
            img.save(brouillon / (c['id'].split('_', 1)[1] + '.png'))
            continue
        brut = io.BytesIO(); img.save(brut, 'PNG')
        for rel, octets in ((c['imageUrl'], il.to_full(brut.getvalue())),
                            (c['thumbUrl'], il.to_thumb(brut.getvalue()))):
            (RACINE / rel).write_bytes(octets)
        s = sources.get(c['id']) or {}
        sources[c['id']] = dict(s, detourage='rembg')
    if not apercu:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
