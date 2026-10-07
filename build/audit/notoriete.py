#!/usr/bin/env python3
"""Mesures de notoriete stables, pour revoir les raretes.

Pour chaque carte :
  - vues mensuelles de la page francaise sur 36 mois (API Wikimedia) :
    total, mediane mensuelle, et pic (mois le plus vu / mediane) ;
  - nombre de langues ou l'article existe (sitelinks Wikidata), mesure de
    notoriete mondiale insensible a l'actualite.

Sortie : build/audit/notoriete.json  { id: {med, total, pic, langues} }
Reprise possible : les cartes deja mesurees ne sont pas redemandees.
"""
import sys, json, time, statistics, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
SORTIE = ICI / 'notoriete.json'
H = {'User-Agent': 'WikiDeck/1.0 (usage personnel ; mesure de notoriete)'}
DEBUT, FIN = '2023100100', '2026093000'


def vues(titre):
    u = ('https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/fr.wikipedia/all-access/user/'
         + urllib.parse.quote(titre.replace(' ', '_'), safe='') + f'/monthly/{DEBUT}/{FIN}')
    for essai in range(4):
        try:
            r = requests.get(u, headers=H, timeout=30)
            if r.status_code == 404:
                return []
            if r.status_code == 429:
                time.sleep(float(r.headers.get('Retry-After', 5 * (essai + 1)))); continue
            return [it['views'] for it in r.json().get('items', [])]
        except requests.RequestException:
            time.sleep(2)
    return None


def langues(titres):
    """{titre: nombre de langues}. Paquets de 20 (une URL trop longue est
    refusee) ; un paquet en echec est redemande titre par titre."""
    out = {}

    def paquet(lot):
        for essai in range(4):
            try:
                r = requests.post('https://www.wikidata.org/w/api.php', headers=H, timeout=60, data={
                    'action': 'wbgetentities', 'sites': 'frwiki', 'titles': '|'.join(lot),
                    'props': 'sitelinks', 'format': 'json'})
                if r.status_code == 429:
                    time.sleep(float(r.headers.get('Retry-After', 5))); continue
                return r.json()
            except Exception:
                time.sleep(3)
        return None
    for i in range(0, len(titres), 20):
        lot = titres[i:i + 20]
        js = [paquet(lot)]
        if js[0] is None:
            js = [paquet([t]) for t in lot]
        for j in js:
            for e in ((j or {}).get('entities') or {}).values():
                sl = e.get('sitelinks') or {}
                t = (sl.get('frwiki') or {}).get('title')
                if t:
                    out[t] = sum(1 for k in sl if k.endswith('wiki') and k not in ('commonswiki', 'specieswiki', 'metawiki'))
    return out


def main():
    res = json.loads(SORTIE.read_text(encoding='utf-8')) if SORTIE.exists() else {}
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    cartes = [c for e in idx['collections'] for c in json.loads((RACINE / e['fichier']).read_text(encoding='utf-8'))['cartes']]
    a_faire = [c for c in cartes if c['id'] not in res]
    print(len(cartes), 'cartes,', len(a_faire), 'a mesurer')
    # les langues sont lues a part, au rythme de Wikidata (langues_cartes.py)
    lg = json.loads((ICI / 'langues.json').read_text(encoding='utf-8'))

    def un(c):
        v = vues(c['titrePage'])
        if v is None:
            return c['id'], None
        med = statistics.median(v) if v else 0
        return c['id'], {'med': med, 'total': sum(v), 'pic': round(max(v) / med, 1) if v and med else 0,
                         'mois': len(v), 'langues': lg.get(c['titrePage'], 0)}
    with ThreadPoolExecutor(1) as ex:
        for k, (cid, m) in enumerate(ex.map(un, a_faire), 1):
            if m:
                res[cid] = m
            if k % 100 == 0:
                SORTIE.write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')
                print(k, 'faites')
    SORTIE.write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')
    print('fini :', len(res))


if __name__ == '__main__':
    main()
