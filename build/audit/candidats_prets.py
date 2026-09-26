#!/usr/bin/env python3
"""Dit si toutes les cartes sans image d'une collection ont leurs candidates.

Sortie 0 si la collection est prete (planches regenerees au passage), 1 sinon.

Usage : python candidats_prets.py <slug>
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from candidats_images import CAND, cartes_sans_image, planches

slug = sys.argv[1]
cartes = cartes_sans_image(slug)
manque = [c for c in cartes if not (CAND / slug / f"{c['id'].split('_', 1)[1]}.json").exists()]
if manque:
    print(f'{slug} : {len(manque)} carte(s) encore en collecte')
    sys.exit(1)
for f in planches(slug, cartes):
    print(f)
sys.exit(0)
