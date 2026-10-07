"""Nombre de langues de chaque page (sitelinks Wikidata), au rythme permis
par Wikimedia : paquets de 10, Retry-After respecte. Reprise possible."""
import json, time, sys
from pathlib import Path
import requests
sys.stdout.reconfigure(encoding='utf-8')
R = Path(__file__).resolve().parent.parent.parent
F = Path(__file__).resolve().parent / 'langues.json'
out = json.loads(F.read_text(encoding='utf-8')) if F.exists() else {}
idx = json.loads((R / 'data/collections.json').read_text(encoding='utf-8'))
T = sorted({c['titrePage'] for e in idx['collections'] for c in json.loads((R / e['fichier']).read_text(encoding='utf-8'))['cartes']})
fait = set(json.loads((F.parent / 'langues_vus.json').read_text(encoding='utf-8'))) if (F.parent / 'langues_vus.json').exists() else set()
T = [t for t in T if t not in fait]
s = requests.Session(); s.headers['User-Agent'] = 'WikiDeck/1.0 (usage personnel ; mesure de notoriete)'
print(len(T), 'titres a lire')
for i in range(0, len(T), 10):
    lot = T[i:i + 10]
    while True:
        try:
            r = s.post('https://www.wikidata.org/w/api.php', timeout=40, data={
                'action': 'wbgetentities', 'sites': 'frwiki', 'titles': '|'.join(lot), 'props': 'sitelinks',
                'format': 'json', 'maxlag': 5})
            if r.status_code == 429 or 'maxlag' in r.text[:200]:
                time.sleep(float(r.headers.get('Retry-After', 5)) + 1); continue
            j = r.json(); break
        except Exception:
            time.sleep(5)
    for e in (j.get('entities') or {}).values():
        sl = e.get('sitelinks') or {}
        t = (sl.get('frwiki') or {}).get('title')
        if t:
            out[t] = sum(1 for k in sl if k.endswith('wiki') and k not in ('commonswiki', 'specieswiki', 'metawiki'))
    fait.update(lot)
    time.sleep(0.6)
    if i % 500 == 0:
        F.write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
        (F.parent / 'langues_vus.json').write_text(json.dumps(sorted(fait), ensure_ascii=False), encoding='utf-8')
        print(i, len(out), flush=True)
F.write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
(F.parent / 'langues_vus.json').write_text(json.dumps(sorted(fait), ensure_ascii=False), encoding='utf-8')
print('fini', len(out))
