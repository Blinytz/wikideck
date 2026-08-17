#!/usr/bin/env python3
"""Renumérote les collections et resynchronise les effectifs de l'index.

Supprimer une carte depuis l'atelier la retirait du fichier de collection sans
renuméroter le reste ni corriger `nbCartes` dans `collections.json`. Chaque
suppression laissait donc un trou dans la numérotation et un effectif annoncé
faux — les deux que le contrôle final réclame.

La cause est corrigée dans l'atelier ; ce script rattrape l'existant, et reste
utile comme filet après toute manipulation directe des fichiers.

Usage : python reparer_numerotation.py [--essai]
"""
import sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
RACINE = Path(__file__).resolve().parent.parent.parent


def main():
    essai = '--essai' in sys.argv
    chemin_idx = RACINE / 'data' / 'collections.json'
    idx = json.loads(chemin_idx.read_text(encoding='utf-8'))
    corriges = 0

    for entree in idx['collections']:
        chemin = RACINE / entree['fichier']
        d = json.loads(chemin.read_text(encoding='utf-8'))
        nums = [c.get('numero') for c in d['cartes']]
        attendu = list(range(1, len(d['cartes']) + 1))
        renumerote = nums != attendu
        effectif = entree['nbCartes'] != len(d['cartes'])
        if not (renumerote or effectif):
            continue
        corriges += 1
        details = []
        if renumerote:
            details.append('numérotation')
            for i, c in enumerate(d['cartes'], 1):
                c['numero'] = i
        if effectif:
            details.append(f"effectif {entree['nbCartes']} -> {len(d['cartes'])}")
            entree['nbCartes'] = len(d['cartes'])
        print(f"  {entree['slug']:<40} {', '.join(details)}")
        if not essai:
            chemin.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')

    if not essai and corriges:
        chemin_idx.write_text(json.dumps(idx, ensure_ascii=False, indent=1),
                              encoding='utf-8')
    print(f'{corriges} collection(s) corrigée(s)' + ('  [essai]' if essai else ''))


if __name__ == '__main__':
    main()
