#!/usr/bin/env python3
"""Consigne 5 : aucun `nom` identique dans deux collections.

Le contrôle final en relève 19 après restructuration. La consigne donne la
règle de résolution — suffixer avec le type entre parenthèses, « Charon
(lune) » — mais pas lequel des deux suffixer. Le choix retenu ici, à chaque
fois : c'est le sens SECOND qui prend la parenthèse, le sens usuel gardant le
nom nu.

  - Les constellations portent des noms d'emprunt (Lion, Sextant, Pégase) :
    c'est la constellation qui est qualifiée, pas l'animal ni le héros.
  - Un personnage qui porte le nom de son oeuvre (Pac-Man, Shrek) prend
    « (personnage) » : l'oeuvre garde le nom nu. §28.10 demandait justement
    qu'aucune carte n'existe des deux côtés du registre ; le document lui-même
    inscrit pourtant ces quatre-là dans les deux, la parenthèse tranche.
  - Francis Bacon est peintre d'un côté, philosophe de l'autre : deux
    personnes différentes, les deux sont qualifiées.
  - Mercure garde son nom nu chez les éléments chimiques, collection que
    l'audit ne touche pas.
  - « Hades » (le jeu) et « Hadès » (le dieu) ne sont PAS le même nom : la
    consigne parle de noms exactement identiques, et c'est bien ainsi que le
    jeu s'écrit. Rien n'est qualifié, le contrôle final se contente de le
    signaler.

`titrePage` et `lienWikipedia` ne bougent jamais : seul le nom affiché change.

Usage : python lever_homonymes.py [--essai]
"""
import sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent

SUFFIXES = [
    # (slug, nom actuel, nouveau nom)
    ('constellations', 'Boussole', 'Boussole (constellation)'),
    ('constellations', 'Licorne', 'Licorne (constellation)'),
    ('constellations', 'Lion', 'Lion (constellation)'),
    ('constellations', 'Microscope', 'Microscope (constellation)'),
    ('constellations', 'Persée', 'Persée (constellation)'),
    ('constellations', 'Phénix', 'Phénix (constellation)'),
    ('constellations', 'Poisson volant', 'Poisson volant (constellation)'),
    ('constellations', 'Pégase', 'Pégase (constellation)'),
    ('constellations', 'Scorpion', 'Scorpion (constellation)'),
    ('constellations', 'Sextant', 'Sextant (constellation)'),
    ('corps-celestes', 'Ariel', 'Ariel (lune)'),
    ('corps-celestes', 'Mercure', 'Mercure (planète)'),
    ('personnages-jeu-video', 'Crash Bandicoot', 'Crash Bandicoot (personnage)'),
    ('personnages-jeu-video', 'Donkey Kong', 'Donkey Kong (personnage)'),
    ('personnages-jeu-video', 'Pac-Man', 'Pac-Man (personnage)'),
    ('personnages-jeu-video', 'Sonic the Hedgehog', 'Sonic the Hedgehog (personnage)'),
    ('personnages-jeu-video', 'Scorpion', 'Scorpion (Mortal Kombat)'),
    ('personnages-animation', 'Shrek', 'Shrek (personnage)'),
    ('personnages-animation', 'Ariel', 'Ariel (La Petite Sirène)'),
    ('grands-peintres', 'Francis Bacon', 'Francis Bacon (peintre)'),
    ('scientifiques-celebres', 'Francis Bacon', 'Francis Bacon (philosophe)'),
]


def main():
    essai = '--essai' in sys.argv
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    faits, absents = 0, []
    charges = {}

    for slug, ancien, nouveau in SUFFIXES:
        chemin = par_slug.get(slug)
        if chemin is None:
            absents.append(f'{slug} : collection absente')
            continue
        if slug not in charges:
            charges[slug] = json.loads(chemin.read_text(encoding='utf-8'))
        carte = next((c for c in charges[slug]['cartes'] if c['nom'] == ancien), None)
        if carte is None:
            absents.append(f'{slug} · {ancien} : carte absente')
            continue
        carte['nom'] = nouveau
        faits += 1
        print(f'  {slug:<28} {ancien}  ->  {nouveau}')

    if not essai:
        for slug, d in charges.items():
            par_slug[slug].write_text(json.dumps(d, ensure_ascii=False),
                                      encoding='utf-8')
    print(f'{faits} nom(s) qualifié(s)' + ('  [essai]' if essai else ''))
    for a in absents:
        print(' •', a)


if __name__ == '__main__':
    main()
