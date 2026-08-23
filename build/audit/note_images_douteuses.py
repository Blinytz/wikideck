#!/usr/bin/env python3
"""Consigne une note d'atelier sur les cartes dont l'image est peu sûre.

Le pipeline d'images va du plus fiable au moins fiable : correspondance memo,
source spécialisée, image de tête de la page Wikipédia, puis — faute de mieux —
une recherche de fichiers ou d'images sur le nom. Ces deux derniers recours
donnent le bon sujet une fois sur deux : Shangri-La y devient un hôtel de
Toronto, Yggdrasil une maison suédoise, Wendigo un lac.

Aucun contrôle automatique ne peut trancher — il faut un œil. On rassemble
donc ces cartes dans une note, que l'atelier affiche avec sa sélection : elles
sont vues, et non perdues dans 3 660 cartes.

Usage : python note_images_douteuses.py [--essai]
"""
import sys, json, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent

# sources dont le sujet n'est pas garanti, de la moins sûre à la moins pire
DOUTEUSES = ('bing', 'bing-retry', 'bing-retry2', 'wiki-sans-filtre')
ID_NOTE = 'n-audit-images-douteuses'


def main():
    essai = '--essai' in sys.argv
    sources = json.loads((RACINE / 'build' / 'images_sources.json')
                         .read_text(encoding='utf-8'))
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))

    # Une carte reprise dans l'atelier a un cadrage : c'est la trace du passage
    # de l'utilisateur. On la retire de la note — la reproposer effacerait son
    # travail de la selection et lui ferait relire ce qu'il a deja tranche.
    # (`images_sources.json` ne bouge pas lors d'un recadrage : le cadrage est
    #  le seul temoin fiable.)
    notes_deja = json.loads((RACINE / 'build' / 'notes_atelier.json')
                            .read_text(encoding='utf-8'))
    vues = set(notes_deja.get('cadrages', {})) | set(notes_deja.get('statuts', {}))

    cibles, par_collection, epargnees = [], {}, 0
    for c in idx['collections']:
        d = json.loads((RACINE / c['fichier']).read_text(encoding='utf-8'))
        for x in d['cartes']:
            src = (sources.get(x['id']) or {}).get('source', '')
            if src not in DOUTEUSES:
                continue
            if x['id'] in vues:
                epargnees += 1
                continue
            cibles.append(x['id'])
            par_collection[c['slug']] = par_collection.get(c['slug'], 0) + 1

    for slug, n in sorted(par_collection.items(), key=lambda kv: -kv[1]):
        print(f'  {slug:<34} {n:>4}')
    print(f'{len(cibles)} carte(s) à relire'
          f" ({epargnees} deja reprises dans l'atelier, laissees de cote)")

    if essai:
        return
    chemin = RACINE / 'build' / 'notes_atelier.json'
    notes = json.loads(chemin.read_text(encoding='utf-8'))
    maintenant = int(time.time() * 1000)
    note = next((n for n in notes['notes'] if n['id'] == ID_NOTE), None)
    texte = (
        "Images à relire après l'audit. Le pipeline n'a trouvé pour ces cartes "
        "ni correspondance memo, ni source spécialisée, ni image de tête sur la "
        "page Wikipédia : leur illustration vient d'une recherche par nom, qui "
        "donne le bon sujet une fois sur deux. Shangri-La y a hérité d'un hôtel "
        "de Toronto, Yggdrasil d'une maison suédoise. À reprendre à l'œil, par "
        "collection : ce sont les mythologies, le jeu vidéo et les empires qui "
        "en concentrent le plus.")
    if note is None:
        notes['notes'].append({
            'id': ID_NOTE, 'tags': ['mauvaise qualité'], 'texte': texte,
            'images': cibles, 'statut': 'ouverte',
            'creeLe': maintenant, 'majLe': maintenant})
    else:
        note.update(texte=texte, images=cibles, statut='ouverte', majLe=maintenant)
    chemin.write_text(json.dumps(notes, ensure_ascii=False, indent=1),
                      encoding='utf-8')
    print('note d\'atelier écrite')


if __name__ == '__main__':
    main()
