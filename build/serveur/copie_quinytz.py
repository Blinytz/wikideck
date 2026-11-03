#!/usr/bin/env python3
"""Copie hebdomadaire des questions Quinytz dans le Supabase Éclats (spec §3.1).

Lit la table `questions` du projet Quinytz (clé secrète Quinytz), puis upsert
dans `wikideck_questions` ; une question retirée de Quinytz (absente ou
inactive) est désactivée, jamais supprimée. Aucune dépendance entre les deux
projets à l'exécution du jeu.

Variables : QUINYTZ_SUPABASE_URL, QUINYTZ_SERVICE_KEY,
            ECLATS_SUPABASE_URL, ECLATS_SERVICE_KEY.
"""
import json, os, sys, urllib.request


def client(url, cle):
    url = url.rstrip('/')
    h = {'apikey': cle, 'Authorization': f'Bearer {cle}', 'Content-Type': 'application/json'}

    def appel(chemin, methode='GET', corps=None, entetes=None):
        req = urllib.request.Request(f'{url}/rest/v1/{chemin}', method=methode,
                                     data=json.dumps(corps).encode() if corps is not None else None,
                                     headers={**h, **(entetes or {})})
        with urllib.request.urlopen(req, timeout=60) as r:
            t = r.read().decode()
            return json.loads(t) if t else None
    return appel


def tout_lire(appel, chemin):
    out = []
    for debut in range(0, 1_000_000, 1000):
        lot = appel(chemin, entetes={'Range': f'{debut}-{debut + 999}'})
        out += lot
        if len(lot) < 1000:
            return out


def main():
    quinytz = client(os.environ['QUINYTZ_SUPABASE_URL'], os.environ['QUINYTZ_SERVICE_KEY'])
    eclats = client(os.environ['ECLATS_SUPABASE_URL'], os.environ['ECLATS_SERVICE_KEY'])
    source = tout_lire(quinytz, 'questions?select=id,question,reponse,type,theme,difficulte,actif&order=id')
    lignes = []
    for q in source:
        d = q.get('difficulte') or 2
        lignes.append({'id': str(q['id']), 'question': q['question'], 'reponse': q['reponse'],
                       'variantes': [], 'theme': q.get('theme') or 'Culture générale',
                       'difficulte': max(1, min(5, int(d))),
                       'actif': bool(q.get('actif', True)) and q.get('type', 'reponse_courte') == 'reponse_courte'})
    for i in range(0, len(lignes), 500):
        eclats('wikideck_questions?on_conflict=id', 'POST', lignes[i:i + 500],
               {'Prefer': 'resolution=merge-duplicates,return=minimal'})
    ids = {l['id'] for l in lignes}
    presentes = tout_lire(eclats, 'wikideck_questions?select=id,actif&order=id')
    retirees = [x['id'] for x in presentes if x['id'] not in ids and x['actif']]
    for i in range(0, len(retirees), 100):
        lot = ','.join(f'"{x}"' for x in retirees[i:i + 100])
        eclats(f'wikideck_questions?id=in.({lot})', 'PATCH', {'actif': False}, {'Prefer': 'return=minimal'})
    actives = sum(1 for l in lignes if l['actif'])
    print(f'{len(lignes)} questions copiées ({actives} actives), {len(retirees)} désactivées')


if __name__ == '__main__':
    sys.exit(main())
