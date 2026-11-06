#!/usr/bin/env python3
"""Repère les cartes dont l'image d'origine (images/originaux) ne correspond
plus à l'illustration publiée (images/full) : image remplacée depuis, encart
ajouté après coup... Pour elles, l'atelier ne doit pas partir de l'origine.

Écrit build/originaux_divergents.json : liste des identifiants de carte.
Usage : python originaux_divergents.py
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
RACINE = Path(__file__).resolve().parent.parent.parent
notes = json.loads((RACINE / 'build' / 'notes_atelier.json').read_text(encoding='utf-8'))['cadrages']
idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
divergents, vus = [], 0
for e in idx['collections']:
    for c in json.loads((RACINE / e['fichier']).read_text(encoding='utf-8'))['cartes']:
        a = notes.get(c['id'])
        slug = c['id'].split('_', 1)[1]
        o = RACINE / 'images' / 'originaux' / e['slug'] / f'{slug}.webp'
        f = RACINE / c['imageUrl']
        if not (a and a.get('original') and a.get('w') and o.exists() and f.exists()):
            continue
        vus += 1
        src = Image.open(o).convert('L'); iw, ih = src.size
        wi = a['w'] * iw; hi = wi * 3 / 4
        x0, y0 = a['cx'] * iw - wi / 2, a['cy'] * ih - hi / 2
        A = np.asarray(src.crop((round(x0), round(y0), round(x0 + wi), round(y0 + hi))).resize((160, 120))).astype(float)
        B = np.asarray(Image.open(f).convert('L').resize((160, 120))).astype(float)
        best = min(abs(A[10:110, 10:150] - B[10 + dy:110 + dy, 10 + dx:150 + dx]).mean()
                   for dx in range(-6, 7, 2) for dy in range(-6, 7, 2))
        centre = abs(A[10:110, 10:150] - B[10:110, 10:150]).mean()
        if centre > best + 1.5 or centre > 14:
            divergents.append(c['id'])
(RACINE / 'build' / 'originaux_divergents.json').write_text(json.dumps(sorted(divergents), ensure_ascii=False, indent=0), encoding='utf-8')
print(f'{vus} cartes comparées, {len(divergents)} originaux divergents')
