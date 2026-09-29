#!/usr/bin/env python3
"""Faits structures Wikidata pour les cartes d'une collection.

Premiere brique des listes Memo (build/audit/listes_memo.md) : pour chaque
carte, on retrouve son element Wikidata par le titre de sa page francaise,
puis on lit les proprietes utiles (dates, createur, lieu, pays...), avec les
libelles en francais.

Sortie : build/audit/faits/<slug>.json
  { "<id carte>": {"qid": "Q...", "P569": ["1724"], "P170": ["Leonard de Vinci"], ...} }

Usage : python wikidata_faits.py <slug> [<slug>...]
"""
import sys, json, time
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
SORTIE = ICI / 'faits'
API = 'https://www.wikidata.org/w/api.php'
ENTETES = {'User-Agent': 'WikiDeck/1.0 (usage personnel ; listes de culture generale)'}

# proprietes lues pour toutes les collections ; chaque liste prend ce qui la sert
PROPRIETES = {
    'P569': 'naissance', 'P570': 'deces', 'P27': 'nationalite', 'P135': 'mouvement',
    'P800': 'oeuvres', 'P101': 'domaine', 'P170': 'createur', 'P571': 'creation',
    'P276': 'lieu', 'P195': 'collection', 'P131': 'territoire', 'P495': 'pays_origine',
    'P17': 'pays', 'P50': 'auteur', 'P577': 'publication', 'P136': 'genre',
    'P186': 'materiau', 'P527': 'composants', 'P2079': 'technique',
}


def get(params):
    for essai in range(5):
        try:
            r = requests.get(API, params={**params, 'format': 'json'}, headers=ENTETES, timeout=30)
            if r.status_code == 429:
                time.sleep(5 * (essai + 1))
                continue
            return r.json()
        except requests.RequestException:
            time.sleep(3)
    return {}


def entites_par_titres(titres):
    """{titre frwiki: entite} par paquets de 50."""
    sortie = {}
    for i in range(0, len(titres), 50):
        lot = titres[i:i + 50]
        j = get({'action': 'wbgetentities', 'sites': 'frwiki', 'titles': '|'.join(lot),
                 'props': 'claims|sitelinks', 'sitefilter': 'frwiki'})
        for e in (j.get('entities') or {}).values():
            t = ((e.get('sitelinks') or {}).get('frwiki') or {}).get('title')
            if t:
                sortie[t] = e
    return sortie


def libelles(qids):
    out = {}
    qids = sorted(set(qids))
    for i in range(0, len(qids), 50):
        j = get({'action': 'wbgetentities', 'ids': '|'.join(qids[i:i + 50]),
                 'props': 'labels', 'languages': 'fr|en'})
        for q, e in (j.get('entities') or {}).items():
            l = e.get('labels') or {}
            out[q] = (l.get('fr') or l.get('en') or {}).get('value', q)
    return out


def valeur(snak):
    dv = (snak.get('mainsnak') or {}).get('datavalue') or {}
    v = dv.get('value')
    if dv.get('type') == 'wikibase-entityid':
        return ('Q', v['id'])
    if dv.get('type') == 'time':
        t = v['time']                       # +1724-04-22T00:00:00Z
        an = t[1:].split('-')[0].lstrip('0') or '0'
        return ('T', ('-' if t[0] == '-' else '') + an)
    if dv.get('type') == 'quantity':
        return ('T', v['amount'].lstrip('+'))
    if isinstance(v, str):
        return ('T', v)
    return None


def main():
    SORTIE.mkdir(exist_ok=True)
    for slug in sys.argv[1:]:
        cartes = json.loads((RACINE / 'data' / f'{slug}.json').read_text(encoding='utf-8'))['cartes']
        titres = [c['titrePage'] for c in cartes]
        ents = entites_par_titres(titres)
        brut, a_nommer = {}, []
        for c in cartes:
            e = ents.get(c['titrePage'])
            if not e:
                continue
            faits = {'qid': e['id']}
            for p in PROPRIETES:
                vals = []
                # rang « preferred » d'abord, puis « normal » ; « deprecated » ecarte
                claims = [x for x in (e.get('claims') or {}).get(p, []) if x.get('rank') != 'deprecated']
                claims.sort(key=lambda x: x.get('rank') != 'preferred')
                for cl in claims:
                    v = valeur(cl)
                    if v:
                        vals.append(v)
                        if v[0] == 'Q':
                            a_nommer.append(v[1])
                if vals:
                    faits[p] = vals
            brut[c['id']] = faits
        noms = libelles(a_nommer)
        propre = {cid: {k: ([noms.get(v[1], v[1]) if v[0] == 'Q' else v[1] for v in vs] if k != 'qid' else vs)
                        for k, vs in f.items()} for cid, f in brut.items()}
        (SORTIE / f'{slug}.json').write_text(json.dumps(propre, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'{slug} : {len(propre)}/{len(cartes)} cartes trouvees dans Wikidata')


if __name__ == '__main__':
    main()
