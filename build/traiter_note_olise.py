#!/usr/bin/env python3
"""Note atelier n1785510213567 — la carte Jamal Musiala devient Michael Olise.

C'est un REMPLACEMENT, pas un renommage d'affichage : la carte change de sujet.
L'image a déjà été remplacée dans l'atelier ; il reste tout le reste — id,
nom, titrePage, lienWikipedia, description, pageviews, noms de fichiers image,
clé de cadrage, index des sources — plus la rareté, qui est attribuée par
quotas sur toute la collection et bouge donc avec les pageviews.

Les fichiers de build qui alimentent une régénération (resolution.json,
noms_cartes.json) sont mis à jour eux aussi, sinon Musiala reviendrait au
prochain `generate_cards.py`. Les rapports (audit.*, rapport_images.csv,
contact_sheets/) sont des sorties : ils se réécrivent d'eux-mêmes.

Usage : python traiter_note_olise.py
"""
import sys, json, re, unicodedata, urllib.request, urllib.parse
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'build'))
import rarete_pv

UA = 'wikideck-build/1.0 (projet perso; contact: claude.elk041@passmail.net)'
COL_SLUG = 'plus-grands-joueurs-de-football'
ANCIEN, NOUVEAU = 'jamal-musiala', 'michael-olise'
TITRE = 'Michael Olise'


def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def periode():
    fin = date.today().replace(day=1) - timedelta(days=1)
    debut = (fin.replace(day=1) - timedelta(days=360)).replace(day=1)
    return debut.strftime('%Y%m%d'), fin.strftime('%Y%m%d')


def fiche_wikipedia(titre):
    d = get_json('https://fr.wikipedia.org/w/api.php?action=query&format=json'
                 '&redirects=1&prop=extracts|pageprops|pageimages&explaintext=1'
                 '&exintro=1&piprop=original&titles=' + urllib.parse.quote(titre))
    page = next(iter(d['query']['pages'].values()))
    if 'missing' in page:
        raise SystemExit(f'Page introuvable : {titre}')
    if 'disambiguation' in (page.get('pageprops') or {}):
        raise SystemExit(f'Page d\'homonymie : {titre}')
    return (page['title'], (page.get('extract') or '')[:500],
            (page.get('original') or {}).get('source', ''))


def pageviews(titre):
    debut, fin = periode()
    art = urllib.parse.quote(titre.replace(' ', '_'), safe='')
    d = get_json('https://wikimedia.org/api/rest_v1/metrics/pageviews/'
                 f'per-article/fr.wikipedia/all-access/user/{art}/monthly/{debut}/{fin}')
    return sum(x.get('views', 0) for x in d.get('items', []))


def renommer_fichier(rel_dir):
    a = ROOT / rel_dir / f'{ANCIEN}.webp'
    b = ROOT / rel_dir / f'{NOUVEAU}.webp'
    if a.exists():
        if b.exists():
            b.unlink()
        a.rename(b)
        print(f'  image  {rel_dir}/{ANCIEN}.webp -> {NOUVEAU}.webp')


def main():
    titre, extrait, illustration = fiche_wikipedia(TITRE)
    vues = pageviews(titre)
    print(f'{titre} — {vues:,} vues sur 12 mois'.replace(',', ' '))

    # --- data/<collection>.json : la carte, puis les raretés de la collection
    fic = ROOT / 'data' / f'{COL_SLUG}.json'
    d = json.loads(fic.read_text(encoding='utf-8'))
    carte = next(c for c in d['cartes'] if c['id'] == f'{COL_SLUG}_{ANCIEN}')
    carte.update({
        'id': f'{COL_SLUG}_{NOUVEAU}',
        'nom': TITRE,
        'titrePage': titre,
        'imageUrl': f'images/full/{COL_SLUG}/{NOUVEAU}.webp',
        'thumbUrl': f'images/thumbs/{COL_SLUG}/{NOUVEAU}.webp',
        'description': extrait,
        'lienWikipedia': 'https://fr.wikipedia.org/wiki/'
                         + urllib.parse.quote(titre.replace(' ', '_')),
        'pageviews': vues,
    })
    # tags/pouvoir/pvCombat dépendent du sujet : ils seront réattribués par
    # generer_combat.py, qui repart du lien Wikipédia.
    for champ in ('tags', 'liensSortants'):
        carte.pop(champ, None)

    # Rareté de la seule carte remplacée. On ne recalcule PAS toute la
    # collection : les quotas y sont déjà périmés (147 cartes aujourd'hui, mais
    # les raretés datent d'un effectif plus grand — l'atelier a supprimé des
    # cartes sans les rejouer), et un recalcul rétrograderait au passage Pelé,
    # Platini ou Messi, ce que la note ne demande pas. La collection est de
    # toute façon scindée et recalculée en entier par le lot 6 de l'audit.
    vues_col = sorted((c.get('pageviews', 0) for c in d['cartes']), reverse=True)
    rang = vues_col.index(vues) + 1
    voisins = [c['rarete'] for c in sorted(d['cartes'], key=lambda c: -c['pageviews'])
               if c['id'] != carte['id']][max(0, rang - 3):rang + 2]
    carte['rarete'] = max(set(voisins), key=voisins.count)
    carte['pv'] = rarete_pv.pv(1 - (rang - 1) / max(1, len(vues_col) - 1))
    fic.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
    print(f'  carte  {carte["id"]} — rang {rang}/{len(vues_col)} en notoriété '
          f'-> {carte["rarete"]}, {carte["pv"]} PV')

    for rep in ('images/full', 'images/thumbs', 'images/originaux'):
        renommer_fichier(f'{rep}/{COL_SLUG}')

    # --- notes_atelier.json : cadrage + référence de la note
    fn = ROOT / 'build' / 'notes_atelier.json'
    notes = json.loads(fn.read_text(encoding='utf-8'))
    ancien_id, nouvel_id = f'{COL_SLUG}_{ANCIEN}', f'{COL_SLUG}_{NOUVEAU}'
    if ancien_id in notes.get('cadrages', {}):
        notes['cadrages'][nouvel_id] = notes['cadrages'].pop(ancien_id)
        print('  cadrage reporté sur le nouvel id')
    for n in notes.get('notes', []):
        n['images'] = [nouvel_id if i == ancien_id else i for i in n.get('images', [])]
    fn.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')

    # --- index des sources d'images
    fs = ROOT / 'build' / 'images_sources.json'
    src = json.loads(fs.read_text(encoding='utf-8'))
    if ancien_id in src:
        src[nouvel_id] = {'source': 'atelier'}
        del src[ancien_id]
        fs.write_text(json.dumps(src, ensure_ascii=False, indent=0), encoding='utf-8')

    # --- entrées de build qui alimentent une régénération
    fr_ = ROOT / 'build' / 'resolution.json'
    rs = json.loads(fr_.read_text(encoding='utf-8'))
    for r in rs:
        if r.get('titre') == 'Jamal Musiala' or r.get('nom') == 'Jamal Musiala':
            r['nom'] = TITRE
            r['titre'] = titre
            r['extrait'] = extrait
            r['url'] = carte['lienWikipedia']
            r['thumb'] = illustration        # sinon la photo de Musiala reviendrait
            r['image_absente'] = not illustration
            r['note'] = 'remplacement demandé (note atelier n1785510213567)'
    fr_.write_text(json.dumps(rs, ensure_ascii=False, indent=1), encoding='utf-8')

    fnc = ROOT / 'build' / 'noms_cartes.json'
    nc = json.loads(fnc.read_text(encoding='utf-8'))
    for cle in [k for k in nc if 'Musiala' in k]:
        nc[f'{cle.split("|")[0]}|{TITRE}'] = {**nc.pop(cle), 'nomCarte': TITRE}
    fnc.write_text(json.dumps(nc, ensure_ascii=False, indent=1), encoding='utf-8')

    reste = [f for f in (fic, fn, fs, fr_, fnc)
             if 'musiala' in f.read_text(encoding='utf-8').lower()]
    print('  reste des références Musiala :', [f.name for f in reste] or 'aucune')


if __name__ == '__main__':
    main()
