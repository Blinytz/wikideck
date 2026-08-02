#!/usr/bin/env python3
"""Écriture des collections cibles dans data/ — l'étape qui touche le jeu.

Trois choses s'y passent :

1. Déménagement. L'`id` d'une carte porte le slug de sa collection, et l'atelier
   en déduit les chemins d'image, la clé de cadrage et l'entrée de sources. Une
   carte qui change de collection change donc d'id, et il faut suivre : ses
   fichiers full/thumb/original sont déplacés, son cadrage et sa source
   réindexés. Sans cela, la carte perdrait son image et son recadrage.

2. Création. Les cartes neuves reçoivent titre, extrait et lien de
   `resolution_pages.json`, puis leurs pageviews.

3. Rareté. Consigne 4 du document : rareté calculée depuis les pageviews, PUIS
   surcharges manuelles en dur. Le calcul est fait par collection, sur des
   pageviews TOUS rafraîchis sur la même fenêtre de 12 mois — mélanger deux
   fenêtres fausserait les quotas au profit des cartes neuves.

Usage : python creer_cartes.py --essai   # rapport, n'écrit rien
        python creer_cartes.py
"""
import sys, json, re, time, pickle, unicodedata, urllib.parse, urllib.request
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE / 'build'))
import rarete_pv
from plan_audit import norm

UA = 'wikideck-build/1.0 (projet perso; contact: claude.elk041@passmail.net)'
CACHE_PV = RACINE / 'build' / '.cache_pageviews.pkl'
_pv = pickle.loads(CACHE_PV.read_bytes()) if CACHE_PV.exists() else {}
_sale = 0


def periode():
    fin = date.today().replace(day=1) - timedelta(days=1)
    debut = (fin.replace(day=1) - timedelta(days=360)).replace(day=1)
    return debut.strftime('%Y%m%d'), fin.strftime('%Y%m%d')


DEBUT, FIN = periode()


def pageviews(titre):
    global _sale
    art = urllib.parse.quote(titre.replace(' ', '_'), safe='')
    url = ('https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/'
           f'fr.wikipedia/all-access/user/{art}/monthly/{DEBUT}/{FIN}')
    if url in _pv:
        return _pv[url]
    total = 0
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                total = sum(x.get('views', 0) for x in
                            json.loads(r.read().decode('utf-8')).get('items', []))
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:            # article sans statistiques
                break
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    _pv[url] = total
    _sale += 1
    if _sale >= 50:
        CACHE_PV.write_bytes(pickle.dumps(_pv))
        _sale = 0
    time.sleep(0.03)
    return total


def slugifier(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def titre_depuis_lien(lien):
    return urllib.parse.unquote((lien or '').split('/wiki/')[-1]).replace('_', ' ')


class Images:
    """Déplacement des fichiers image et report des index qui les référencent."""

    def __init__(self, essai):
        self.essai = essai
        self.notes = json.loads((RACINE / 'build' / 'notes_atelier.json')
                                .read_text(encoding='utf-8'))
        self.sources = json.loads((RACINE / 'build' / 'images_sources.json')
                                  .read_text(encoding='utf-8'))
        self.deplacees = 0

    def demenager(self, ancien_id, nouveau_id):
        if ancien_id == nouveau_id:
            return
        a_col, a_slug = ancien_id.split('_', 1)
        n_col, n_slug = nouveau_id.split('_', 1)
        for rep in ('full', 'thumbs', 'originaux'):
            src = RACINE / 'images' / rep / a_col / f'{a_slug}.webp'
            dst = RACINE / 'images' / rep / n_col / f'{n_slug}.webp'
            if not src.exists():
                continue
            self.deplacees += 1
            if self.essai:
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.replace(dst)
        if ancien_id in self.notes.get('cadrages', {}):
            self.notes['cadrages'][nouveau_id] = self.notes['cadrages'].pop(ancien_id)
        if ancien_id in self.sources:
            self.sources[nouveau_id] = self.sources.pop(ancien_id)
        for n in self.notes.get('notes', []):
            n['images'] = [nouveau_id if i == ancien_id else i
                           for i in n.get('images', [])]

    def ecrire(self):
        if self.essai:
            return
        (RACINE / 'build' / 'notes_atelier.json').write_text(
            json.dumps(self.notes, ensure_ascii=False, indent=1), encoding='utf-8')
        (RACINE / 'build' / 'images_sources.json').write_text(
            json.dumps(self.sources, ensure_ascii=False, indent=0), encoding='utf-8')


def main():
    essai = '--essai' in sys.argv
    plan = json.loads((ICI / 'plan_audit.json').read_text(encoding='utf-8'))
    restru = json.loads((ICI / 'restructuration.json').read_text(encoding='utf-8'))
    pages = json.loads((ICI / 'resolution_pages.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: c for c in plan['collections']}
    images = Images(essai)
    journal, collections = [], []

    for bloc in restru['collections']:
        slug, nom = bloc['slug'], bloc['nom']
        spec = par_slug[slug]
        cartes, pris = [], set()

        # --- cartes existantes : déménagement éventuel
        for c in bloc['cartes']:
            ancien_id = c['id']
            fslug = ancien_id.split('_', 1)[1]
            while f'{slug}_{fslug}' in pris:
                fslug += '-b'
            nouveau_id = f'{slug}_{fslug}'
            pris.add(nouveau_id)
            images.demenager(ancien_id, nouveau_id)
            c['id'] = nouveau_id
            c['collection'] = nom
            c['imageUrl'] = f'images/full/{slug}/{fslug}.webp'
            c['thumbUrl'] = f'images/thumbs/{slug}/{fslug}.webp'
            if c.pop('_regenerer', None) or c.pop('_aVerifier', None):
                cle = f'{slug}|{c["nom"]}'
                r = pages.get(cle)
                if r:
                    c['titrePage'], c['description'] = r['titre'], r['extrait']
                    c['lienWikipedia'] = r['lien']
                    c['_imageAJeter'] = True   # l'ancienne illustre un autre sujet
                else:
                    journal.append(f'{slug} · {c["nom"]} : page corrigée non résolue')
            cartes.append(c)

        # --- créations
        deja = {norm(c['nom']) for c in cartes}
        for n in spec['ajouts']:
            if norm(n) in deja:
                continue          # « ajout » qui était un transfert (§10.3, §26.8)
            r = pages.get(f'{slug}|{n}')
            if not r:
                journal.append(f'{slug} · {n} : page non résolue, carte non créée')
                continue
            fslug = slugifier(r['titre'])
            while f'{slug}_{fslug}' in pris:
                fslug += '-b'
            pris.add(f'{slug}_{fslug}')
            cartes.append({
                'id': f'{slug}_{fslug}', 'nom': n, 'titrePage': r['titre'],
                'imageUrl': f'images/full/{slug}/{fslug}.webp',
                'thumbUrl': f'images/thumbs/{slug}/{fslug}.webp',
                'description': r['extrait'], 'collection': nom,
                'lienWikipedia': r['lien'], 'tags': [], 'numero': 0,
            })

        collections.append({'collection': nom, 'slug': slug, 'cartes': cartes})

    # --- pageviews sur une fenêtre unique, pour tout le monde
    total = sum(len(c['cartes']) for c in collections)
    print(f'pageviews {DEBUT} -> {FIN} pour {total} cartes…')
    fait = 0
    for col in collections:
        for c in col['cartes']:
            c['pageviews'] = pageviews(titre_depuis_lien(c.get('lienWikipedia'))
                                       or c['titrePage'])
            fait += 1
            if fait % 250 == 0:
                print(f'  … {fait}/{total}')
    CACHE_PV.write_bytes(pickle.dumps(_pv))

    # --- rareté par quotas, puis surcharges du document
    for col in collections:
        spec = par_slug[col['slug']]
        vues = [c['pageviews'] for c in col['cartes']]
        paliers, rangs = rarete_pv.raretes(vues)
        for c, palier, rang in zip(col['cartes'], paliers, rangs):
            c['rarete'], c['pv'] = palier, rarete_pv.pv(rang)
        forcees = {norm(k): v for k, v in spec['raretes_forcees'].items()}
        vues_par_nom = {norm(c['nom']): c for c in col['cartes']}
        for nom, rar in spec['raretes_forcees'].items():
            c = vues_par_nom.get(norm(nom))
            if c is None:
                journal.append(f"{col['slug']} : rareté forcée pour « {nom} », "
                               'carte absente')
                continue
            c['rarete'], c['rareteManuel'] = rar, True
        for i, c in enumerate(col['cartes'], 1):
            c['numero'] = i

    print(f'\n{len(collections)} collections, {total} cartes, '
          f'{images.deplacees} fichier(s) image déplacé(s)')
    for s in journal:
        print(' •', s)

    if essai:
        return
    index = {'collections': []}
    intactes = ['merveilles-du-monde', 'pilotes-f1-champions-du-monde',
                'elements-chimiques']
    ancien = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    garde = {c['slug']: c for c in ancien['collections'] if c['slug'] in intactes}
    for col in collections:
        (RACINE / 'data' / f"{col['slug']}.json").write_text(
            json.dumps(col, ensure_ascii=False), encoding='utf-8')
        index['collections'].append({'slug': col['slug'], 'nom': col['collection'],
                                     'nbCartes': len(col['cartes']),
                                     'fichier': f"data/{col['slug']}.json"})
    index['collections'] += list(garde.values())
    (RACINE / 'data' / 'collections.json').write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')
    images.ecrire()
    # collections disparues (scindées)
    for slug in ('grands-dirigeants', 'dynasties-et-empires-historiques',
                 'auteurs-celebres', 'plus-grands-joueurs-de-football',
                 'mythologies-du-monde-hors-grece',
                 'personnages-de-fiction-celebres', 'films-cultes',
                 'jeux-video-cultes'):
        f = RACINE / 'data' / f'{slug}.json'
        if f.exists() and slug not in {c['slug'] for c in collections}:
            f.unlink()
    print(f"{len(index['collections'])} collections écrites")


if __name__ == '__main__':
    main()
