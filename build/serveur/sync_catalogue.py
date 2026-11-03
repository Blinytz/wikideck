#!/usr/bin/env python3
"""Synchronise le catalogue des cartes (data/) dans le Supabase Éclats.

Lancé par la GitHub Action « catalogue » à chaque push qui modifie data/.
Upsert de toutes les cartes ; une carte absente des données n'est jamais
supprimée : elle passe archivee = true (spec §5.6).

Variables : ECLATS_SUPABASE_URL, ECLATS_SERVICE_KEY.
"""
import json, os, sys, urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
URL = os.environ['ECLATS_SUPABASE_URL'].rstrip('/')
CLE = os.environ['ECLATS_SERVICE_KEY']
# les nouvelles clés secrètes (sb_secret_…) ne s'envoient que dans apikey
H = {'apikey': CLE, 'Content-Type': 'application/json',
     **({} if CLE.startswith('sb_') else {'Authorization': f'Bearer {CLE}'})}


def appel(chemin, methode='GET', corps=None, entetes=None):
    req = urllib.request.Request(f'{URL}/rest/v1/{chemin}', method=methode,
                                 data=json.dumps(corps).encode() if corps is not None else None,
                                 headers={**H, **(entetes or {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read().decode()
        return json.loads(t) if t else None


def main():
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    lignes = []
    for e in idx['collections']:
        for c in json.loads((RACINE / e['fichier']).read_text(encoding='utf-8'))['cartes']:
            lignes.append({'id': c['id'], 'nom': c['nom'], 'collection': e['slug'],
                           'rarete': c['rarete'], 'archivee': bool(c.get('archivee'))})
    ids = {l['id'] for l in lignes}
    for i in range(0, len(lignes), 500):
        appel('wikideck_cartes?on_conflict=id', 'POST', lignes[i:i + 500],
              {'Prefer': 'resolution=merge-duplicates,return=minimal'})
    existants = []
    for debut in range(0, 100000, 1000):
        lot = appel('wikideck_cartes?select=id,archivee&order=id', entetes={'Range': f'{debut}-{debut + 999}'})
        existants += lot
        if len(lot) < 1000:
            break
    a_archiver = [x['id'] for x in existants if x['id'] not in ids and not x['archivee']]
    for i in range(0, len(a_archiver), 100):
        lot = ','.join(f'"{x}"' for x in a_archiver[i:i + 100])
        appel(f'wikideck_cartes?id=in.({lot})', 'PATCH', {'archivee': True}, {'Prefer': 'return=minimal'})
    print(f'{len(lignes)} cartes synchronisées, {len(a_archiver)} archivées')


if __name__ == '__main__':
    sys.exit(main())
