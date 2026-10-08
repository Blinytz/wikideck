#!/usr/bin/env python3
"""Donnees compactes du prototype du Musee (essais/musee.html).

Une ligne par carte : id, nom, collection, theme, rarete, vignette, titre de
page, annee et pays (faits Wikidata, quand la collection a ete lue).
Sortie : essais/musee_cartes.json
"""
import json, re
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
faits = {}
for f in (ICI / 'faits').glob('*.json'):
    faits.update(json.loads(f.read_text(encoding='utf-8')))


def annee(fx):
    for p in ('P569', 'P571', 'P577'):
        for v in fx.get(p) or []:
            m = re.match(r'^-?\d+', str(v))
            if m:
                return int(m.group())
    return None


def pays(fx):
    for p in ('P27', 'P17', 'P495'):
        if fx.get(p):
            return fx[p][0]
    return None


cols, cartes = [], []
for i, e in enumerate(idx['collections']):
    cols.append([e['slug'], e['nom'], idx['themes'].index(e['theme'])])
    for c in json.loads((RACINE / e['fichier']).read_text(encoding='utf-8'))['cartes']:
        fx = faits.get(c['id'], {})
        cartes.append([c['id'], c['nom'], i, c['rarete'], c['thumbUrl'], c['titrePage'],
                       annee(fx), pays(fx)])
out = {'themes': idx['themes'], 'collections': cols, 'cartes': cartes}
(RACINE / 'essais' / 'musee_cartes.json').write_text(
    json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(len(cartes), 'cartes,', sum(1 for c in cartes if c[6] is not None), 'datees,',
      sum(1 for c in cartes if c[7]), 'avec pays')
