#!/usr/bin/env python3
"""Remet « Jeux olympiques » sur une regle unique : une carte = une edition.

La collection melangeait quatre natures : des editions, des institutions
(CIO, Jeux paralympiques), des symboles (flamme, drapeau), des epreuves
(marathon, decathlon), un lieu (stade de Berlin) et une personne (Coubertin).
Meme probleme que le Valhalla chez les divinites nordiques : ce qui n'est pas
de la meme nature ne partage pas la collection.

Ce que fait le script :

  1. sort de la collection tout ce qui n'est pas une edition ;
  2. RECASE ce qui a une maison ailleurs plutot que de le supprimer :
     Coubertin chez les legendes du sport, le stade olympique de Berlin chez
     les monuments. Les fichiers image, le cadrage et l'entree de provenance
     suivent, puisque l'`id` porte le slug de la collection ;
  3. SUPPRIME le reste, faute de collection d'accueil : la page generale des
     Jeux, les Jeux antiques, les Jeux paralympiques, la flamme, le drapeau,
     le CIO, le marathon et le decathlon ;
  4. complete les editions d'ete manquantes, de 1896 a 2024 ;
  5. cree « Jeux olympiques d'hiver » avec les 25 editions, dont les deux
     qui etaient rangees a tort dans la collection d'ete.

Les editions annulees par les guerres (1916, 1940, 1944 pour l'ete ; 1940 et
1944 pour l'hiver) ne sont PAS des cartes : elles n'ont jamais eu lieu.

Usage : python jeux_olympiques.py [--essai]
"""
import sys, json, shutil, re, time, pickle, unicodedata, urllib.parse, urllib.request
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE / 'build'))
import rarete_pv
import resoudre_pages as R

UA = 'wikideck-build/1.0 (projet perso; contact: claude.elk041@passmail.net)'
CACHE_PV = RACINE / 'build' / '.cache_pageviews.pkl'
_pv = pickle.loads(CACHE_PV.read_bytes()) if CACHE_PV.exists() else {}

ETE = [1896, 1900, 1904, 1908, 1912, 1920, 1924, 1928, 1932, 1936, 1948, 1952,
       1956, 1960, 1964, 1968, 1972, 1976, 1980, 1984, 1988, 1992, 1996, 2000,
       2004, 2008, 2012, 2016, 2020, 2024]
HIVER = [1924, 1928, 1932, 1936, 1948, 1952, 1956, 1960, 1964, 1968, 1972,
         1976, 1980, 1984, 1988, 1992, 1994, 1998, 2002, 2006, 2010, 2014,
         2018, 2022, 2026]

# nom de carte a deplacer -> collection d'accueil
RECASER = {
    'Pierre de Coubertin': 'legendes-du-sport',
    'Stade olympique de Berlin': 'monuments-emblematiques',
}
# noms a supprimer : aucune collection du jeu ne les accueille
SUPPRIMER = ['Jeux olympiques', 'Jeux olympiques antiques', 'Jeux paralympiques',
             'Comité international olympique', 'Flamme olympique',
             'Drapeau olympique', 'Marathon', 'Décathlon']

SLUG_ETE, SLUG_HIVER = 'jeux-olympiques', 'jeux-olympiques-hiver'


def periode():
    fin = date.today().replace(day=1) - timedelta(days=1)
    return ((fin.replace(day=1) - timedelta(days=360)).replace(day=1).strftime('%Y%m%d'),
            fin.strftime('%Y%m%d'))


DEBUT, FIN = periode()


def pageviews(titre):
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
            if e.code == 404:
                break
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    _pv[url] = total
    time.sleep(0.03)
    return total


def slugifier(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


class Images:
    """Deplace ou supprime les trois fichiers d'une carte, son cadrage et sa
    provenance. L'`id` porte le slug de la collection : sans ce menage,
    l'atelier chercherait l'image a l'ancienne adresse."""

    def __init__(self, essai):
        self.essai = essai
        self.fn = RACINE / 'build' / 'notes_atelier.json'
        self.fs = RACINE / 'build' / 'images_sources.json'
        self.notes = json.loads(self.fn.read_text(encoding='utf-8'))
        self.src = json.loads(self.fs.read_text(encoding='utf-8'))

    def _chemins(self, cid):
        col, fslug = cid.split('_', 1)
        return {rep: RACINE / 'images' / rep / col / f'{fslug}.webp'
                for rep in ('full', 'thumbs', 'originaux')}

    def demenager(self, ancien, neuf):
        for rep, src in self._chemins(ancien).items():
            dst = self._chemins(neuf)[rep]
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not self.essai:
                    shutil.move(str(src), str(dst))
        for d in (self.notes.get('cadrages', {}), self.src):
            if ancien in d:
                d[neuf] = d.pop(ancien)

    def supprimer(self, cid):
        for p in self._chemins(cid).values():
            if p.exists() and not self.essai:
                p.unlink()
        self.notes.get('cadrages', {}).pop(cid, None)
        self.src.pop(cid, None)

    def ecrire(self):
        if self.essai:
            return
        self.fn.write_text(json.dumps(self.notes, ensure_ascii=False, indent=1),
                           encoding='utf-8')
        self.fs.write_text(json.dumps(self.src, ensure_ascii=False, indent=0),
                           encoding='utf-8')


def carte(slug, nom, fiche, collection, pris_ids):
    fslug = slugifier(fiche['titre'])
    while f'{slug}_{fslug}' in pris_ids:
        fslug += '-b'
    pris_ids.add(f'{slug}_{fslug}')
    return {
        'id': f'{slug}_{fslug}', 'nom': nom, 'titrePage': fiche['titre'],
        'imageUrl': f'images/full/{slug}/{fslug}.webp',
        'thumbUrl': f'images/thumbs/{slug}/{fslug}.webp',
        'description': fiche['extrait'], 'collection': collection,
        'lienWikipedia': 'https://fr.wikipedia.org/wiki/'
                         + urllib.parse.quote(fiche['titre'].replace(' ', '_')),
        'pageviews': pageviews(fiche['titre']), 'tags': [], 'numero': 0,
    }


def main():
    essai = '--essai' in sys.argv
    idx_f = RACINE / 'data' / 'collections.json'
    idx = json.loads(idx_f.read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    charges = {}

    def charger(slug):
        if slug not in charges:
            charges[slug] = json.loads(par_slug[slug].read_text(encoding='utf-8'))
        return charges[slug]

    im = Images(essai)
    ete = charger(SLUG_ETE)

    # ---- 1 et 2 : ce qui n'est pas une edition sort
    for nom, dest in RECASER.items():
        c = next((x for x in ete['cartes'] if x['nom'] == nom), None)
        if not c:
            continue
        d = charger(dest)
        ancien = c['id']
        fslug = ancien.split('_', 1)[1]
        pris = {x['id'] for x in d['cartes']}
        while f'{dest}_{fslug}' in pris:
            fslug += '-b'
        c['id'] = f'{dest}_{fslug}'
        c['collection'] = d['collection']
        c['imageUrl'] = f'images/full/{dest}/{fslug}.webp'
        c['thumbUrl'] = f'images/thumbs/{dest}/{fslug}.webp'
        im.demenager(ancien, c['id'])
        d['cartes'].append(c)
        ete['cartes'].remove(c)
        print(f'  -> {dest:<28} {nom}')

    for nom in SUPPRIMER:
        c = next((x for x in ete['cartes'] if x['nom'] == nom), None)
        if not c:
            continue
        im.supprimer(c['id'])
        ete['cartes'].remove(c)
        print(f'  x  supprimee                    {nom}')

    # ---- 5 : les editions d'hiver quittent la collection d'ete
    hiver_cartes = []
    for c in list(ete['cartes']):
        if "d'hiver" in c['titrePage']:
            ancien = c['id']
            fslug = ancien.split('_', 1)[1]
            c['id'] = f'{SLUG_HIVER}_{fslug}'
            c['imageUrl'] = f'images/full/{SLUG_HIVER}/{fslug}.webp'
            c['thumbUrl'] = f'images/thumbs/{SLUG_HIVER}/{fslug}.webp'
            c['collection'] = "Jeux olympiques d'hiver"
            im.demenager(ancien, c['id'])
            ete['cartes'].remove(c)
            hiver_cartes.append(c)
            print(f'  -> {SLUG_HIVER:<28} {c["nom"]}')

    # ---- 4 et 5 : completer les deux series
    titres = (["Jeux olympiques d'été de %d" % a for a in ETE]
              + ["Jeux olympiques d'hiver de %d" % a for a in HIVER])
    R.charger_fiches(titres)

    # 1896 et 1900 n'ont pas « d'ete » dans leur titre : il n'y avait pas
    # encore de Jeux d'hiver. On compare donc sur le titre CANONIQUE rendu par
    # le resolveur, pas sur le titre demande, sans quoi ces deux editions
    # seraient creees en double.
    manquants = []
    pris_ete = {x['id'] for x in ete['cartes']}
    deja_ete = {x['titrePage'] for x in ete['cartes']}
    for a in ETE:
        t = "Jeux olympiques d'été de %d" % a
        f = R._cache.get('fiche:' + t)
        if not f or f['statut'] != 'ok' or not f.get('extrait'):
            manquants.append(t)
            continue
        if f['titre'] in deja_ete:
            continue
        ete['cartes'].append(carte(SLUG_ETE, 'Été %d' % a, f,
                                   ete['collection'], pris_ete))

    pris_hiver = {x['id'] for x in hiver_cartes}
    deja_hiver = {x['titrePage'] for x in hiver_cartes}
    for a in HIVER:
        t = "Jeux olympiques d'hiver de %d" % a
        f = R._cache.get('fiche:' + t)
        if not f or f['statut'] != 'ok' or not f.get('extrait'):
            manquants.append(t)
            continue
        if f['titre'] in deja_hiver:
            continue
        hiver_cartes.append(carte(SLUG_HIVER, 'Hiver %d' % a, f,
                                  "Jeux olympiques d'hiver", pris_hiver))

    # les cartes d'edition deja presentes portaient le titre long : on aligne
    for c in ete['cartes']:
        m = re.search(r"de (\d{4})$", c['titrePage'])
        if m:
            c['nom'] = 'Été %s' % m.group(1)
    for c in hiver_cartes:
        m = re.search(r"d'hiver de (\d{4})", c['titrePage'])
        if m:
            c['nom'] = 'Hiver %s' % m.group(1)

    ete['cartes'].sort(key=lambda c: c['titrePage'])
    hiver_cartes.sort(key=lambda c: c['titrePage'])
    # `slug` est obligatoire : generer_combat et controles_finaux le lisent
    # dans le fichier de collection, pas seulement dans l'index.
    charges[SLUG_HIVER] = {'collection': "Jeux olympiques d'hiver",
                           'slug': SLUG_HIVER, 'cartes': hiver_cartes}

    CACHE_PV.write_bytes(pickle.dumps(_pv))

    for slug, d in charges.items():
        paliers, rangs = rarete_pv.raretes([c.get('pageviews', 0) for c in d['cartes']])
        for c, p, r in zip(d['cartes'], paliers, rangs):
            if not c.get('rareteManuel'):
                c['rarete'], c['pv'] = p, rarete_pv.pv(r)
        for i, c in enumerate(d['cartes'], 1):
            c['numero'] = i
        print(f'  {slug:<32} {len(d["cartes"])} cartes')
    for m in manquants:
        print('  ✗ page non resolue :', m)

    if essai:
        print('[essai] rien écrit')
        return

    im.ecrire()
    for slug, d in charges.items():
        f = par_slug.get(slug) or (RACINE / 'data' / f'{slug}.json')
        f.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
        e = next((x for x in idx['collections'] if x['slug'] == slug), None)
        if e:
            e['nbCartes'] = len(d['cartes'])
        else:
            apres = next(i for i, x in enumerate(idx['collections'])
                         if x['slug'] == SLUG_ETE)
            idx['collections'].insert(apres + 1, {
                'slug': slug, 'nom': d['collection'],
                'fichier': f'data/{slug}.json', 'nbCartes': len(d['cartes'])})
    idx_f.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{len(idx['collections'])} collections")


if __name__ == '__main__':
    main()
