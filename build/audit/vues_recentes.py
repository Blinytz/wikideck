"""Vues quotidiennes medianes sur les 60 derniers jours (API de Wikipedia,
50 pages par requete) : une mesure insensible aux pics passes. Sortie
build/audit/vues_60j.json {titre de page: mediane}."""
import json, time, statistics, sys
from pathlib import Path
import requests
sys.stdout.reconfigure(encoding='utf-8')
R = Path(__file__).resolve().parent.parent.parent
F = Path(__file__).resolve().parent / 'vues_60j.json'
idx = json.loads((R / 'data/collections.json').read_text(encoding='utf-8'))
T = sorted({c['titrePage'] for e in idx['collections'] for c in json.loads((R / e['fichier']).read_text(encoding='utf-8'))['cartes']})
out = json.loads(F.read_text(encoding='utf-8')) if F.exists() else {}
T = [t for t in T if not out.get(t)]
s = requests.Session(); s.headers['User-Agent'] = 'WikiDeckCartes/1.1 (https://blinytz.github.io/wikideck/) python-requests'
print(len(T), 'a lire', flush=True)
for i in range(0, len(T), 50):
    lot = T[i:i + 50]
    # l'API ne rend les vues que d'une partie des pages a la fois : on suit
    # « continue » jusqu'au bout et on fusionne
    q = {'pages': [], 'normalized': [], 'redirects': []}
    vues_par_page = {}
    suite = {}
    while True:
        for essai in range(6):
            r = s.get('https://fr.wikipedia.org/w/api.php', timeout=60, params={
                'action': 'query', 'titles': '|'.join(lot), 'prop': 'pageviews', 'pvipdays': 60,
                'redirects': 1, 'format': 'json', 'formatversion': 2, **suite})
            if r.status_code == 429:
                time.sleep(float(r.headers.get('Retry-After', 10)) + 1); continue
            j = r.json(); break
        qq = j.get('query', {})
        for k in ('normalized', 'redirects'):
            q[k] += qq.get(k, [])
        for pg in qq.get('pages', []):
            if pg.get('pageviews'):
                vues_par_page[pg['title']] = pg['pageviews']
        if 'continue' not in j:
            break
        suite = j['continue']
        time.sleep(0.5)
    q['pages'] = [{'title': t, 'pageviews': v} for t, v in vues_par_page.items()]
    # titre demande -> titre final (normalisation, redirection)
    alias = {}
    for k in ('normalized', 'redirects'):
        for a in q.get(k, []):
            alias[a['to']] = alias.get(a['from'], a['from'])
    for p in q.get('pages', []):
        v = [x for x in (p.get('pageviews') or {}).values() if x is not None]
        med = statistics.median(v) if v else 0
        out[p['title']] = med
        t = p['title']
        while t in alias:
            t = alias[t]; out[t] = med
    time.sleep(1)
    if i % 1000 == 0:
        F.write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8'); print(i, flush=True)
F.write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
print('fini', len(out))
