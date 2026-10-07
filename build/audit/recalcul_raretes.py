#!/usr/bin/env python3
"""Recalcul des raretes et des PV (07/10/2026), decide avec l'utilisateur.

Notoriete d'une carte (stable, insensible aux pics d'actualite) :
  G = moyenne de deux rangs sur tout le jeu : nombre de langues de l'article
      (build/audit/langues.json) et vues MEDIANES mensuelles sur 3 ans
      (build/audit/notoriete.json ; a defaut, les vues sur 12 mois de la carte).
Rarete, par collection (quotas inchanges : 2 % legendaire, 6 % mythique,
  16 % epique, 26 % rare, le reste commun) sur S = 0,75 x rang de G dans la
  collection + 0,25 x G : chaque collection a ses vedettes, mais Napoleon
  reste au-dessus du meilleur noeud marin.
Pantheon : liste fixee avec l'utilisateur, hors quotas, PV 1001 a 1200.
PV : la fourchette de la rarete (commune 1-399, rare 400-599, epique 600-799,
  mythique 800-899, legendaire 900-1000), la carte y etant placee selon G
  parmi toutes les cartes de meme rarete du jeu.
Les cartes marquees rareteManuel / pvManuel (retouches de l'utilisateur,
  par exemple via le tableau Excel) gardent leur valeur.

Usage : python recalcul_raretes.py            (calcul + rapport, rien d'ecrit)
        python recalcul_raretes.py --appliquer
"""
import sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent

QUOTAS = [('legendaire', 0.02), ('mythique', 0.06), ('epique', 0.16), ('rare', 0.26)]
FOURCHETTES = {'commune': (1, 399), 'rare': (400, 599), 'epique': (600, 799),
               'mythique': (800, 899), 'legendaire': (900, 1000), 'pantheon': (1001, 1200)}
# Pantheon : (collection, titre de page)
PANTHEON = [
    ('figures-religieuses', 'Jésus de Nazareth'), ('figures-religieuses', 'Mahomet'), ('figures-religieuses', 'Siddhartha Gautama'),
    ('dieux-et-figures-mythologiques-grecques', 'Zeus'),
    ('souverains-et-conquerants', 'Napoléon Ier'), ('souverains-et-conquerants', 'Jules César'),
    ('souverains-et-conquerants', 'Alexandre le Grand'), ('souverains-et-conquerants', 'Cléopâtre VII'),
    ('presidents-de-la-republique-francaise', 'Charles de Gaulle'), ('dirigeants-contemporains', 'Nelson Mandela'),
    ('figures-emancipation', 'Martin Luther King'),
    ('scientifiques-celebres', 'Albert Einstein'), ('scientifiques-celebres', 'Isaac Newton'),
    ('scientifiques-celebres', 'Charles Darwin'), ('scientifiques-celebres', 'Marie Curie'),
    ('philosophes', 'Aristote'), ('philosophes', 'Socrate'), ('philosophes', 'Platon'),
    ('grands-peintres', 'Léonard de Vinci'), ('grands-peintres', 'Michel-Ange'),
    ('grands-compositeurs', 'Wolfgang Amadeus Mozart'), ('auteurs-classiques', 'William Shakespeare'),
    ('auteurs-classiques', 'Homère'), ('auteurs-classiques', 'Victor Hugo'),
    ('tableaux-celebres', 'La Joconde'), ('oeuvres-litteraires', 'Iliade'),
    ('musique-populaire', 'Michael Jackson'), ('musique-populaire', 'The Beatles'),
    ('realisateurs', 'Charlie Chaplin'), ('acteurs-et-actrices', 'Marilyn Monroe'),
    ('legendes-du-football', 'Pelé'),
    ('grandes-guerres', 'Seconde Guerre mondiale'), ('grandes-guerres', 'Première Guerre mondiale'),
    ('grandes-guerres', 'Révolution française'), ('empires-et-civilisations', 'Empire romain'),
    ('corps-celestes', 'Terre'), ('corps-celestes', 'Soleil'), ('corps-celestes', 'Lune'),
    ('villes-du-monde', 'Paris'), ('villes-du-monde', 'Rome'), ('monuments-emblematiques', 'Tour Eiffel'),
    ('textes-sacres', 'Bible'), ('textes-sacres', 'Coran'), ('inventions-importantes', 'Internet'),
]


def rangs(valeurs):
    """Rang percentile (0..1) de chaque valeur, ex-aequo au rang moyen."""
    n = len(valeurs)
    ordre = sorted(range(n), key=lambda i: valeurs[i])
    r = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and valeurs[ordre[j + 1]] == valeurs[ordre[i]]:
            j += 1
        for k in range(i, j + 1):
            r[ordre[k]] = ((i + j) / 2) / max(1, n - 1)
        i = j + 1
    return r


def calculer():
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    lg = json.loads((ICI / 'langues.json').read_text(encoding='utf-8'))
    v60 = json.loads((ICI / 'vues_60j.json').read_text(encoding='utf-8'))
    cartes = []
    for e in idx['collections']:
        for c in json.loads((RACINE / e['fichier']).read_text(encoding='utf-8'))['cartes']:
            # vues : moyenne geometrique entre la moyenne quotidienne sur 12 mois
            # et la mediane quotidienne des 60 derniers jours. Un pic passe ne
            # pese que sur la premiere, un pic present presque pas sur la mediane.
            an = (c.get('pageviews') or 0) / 365
            med = v60.get(c['titrePage'], an)
            vues = (max(an, 0.1) * max(med, 0.1)) ** 0.5
            cartes.append(dict(c=c, col=e['slug'], colnom=e['nom'], theme=e.get('theme', ''),
                               langues=lg.get(c['titrePage'], 0), vues=vues, an=an, med=med, pic=None))
    rl = rangs([x['langues'] for x in cartes])
    rv = rangs([x['vues'] for x in cartes])
    for x, a, b in zip(cartes, rl, rv):
        x['G'] = (a + b) / 2
    panth = set(PANTHEON)
    trouves = set()
    for x in cartes:
        if (x['col'], x['c']['titrePage']) in panth:
            x['nouvelle'] = 'pantheon'
            trouves.add((x['col'], x['c']['titrePage']))
    manquants = panth - trouves
    # rarete par collection
    par_col = {}
    for x in cartes:
        par_col.setdefault(x['col'], []).append(x)
    for col, xs in par_col.items():
        libres = [x for x in xs if 'nouvelle' not in x]
        rc = rangs([x['G'] for x in libres])
        for x, r in zip(libres, rc):
            x['S'] = 0.75 * r + 0.25 * x['G']
        n = len(libres)
        ordre = sorted(libres, key=lambda x: -x['S'])
        q = [(p, max(1, round(n * s))) for p, s in QUOTAS]
        while sum(k for _, k in q) > n and any(k > 0 for _, k in q[1:]):
            for i in range(len(q) - 1, 0, -1):
                if q[i][1] > 0 and sum(k for _, k in q) > n:
                    q[i] = (q[i][0], q[i][1] - 1)
        it = iter(ordre)
        for p, k in q:
            for _ in range(k):
                x = next(it, None)
                if x:
                    x['nouvelle'] = p
        for x in it:
            x['nouvelle'] = 'commune'
    # retouches manuelles : on garde
    for x in cartes:
        if x['c'].get('rareteManuel') and x['nouvelle'] != 'pantheon':
            x['nouvelle'] = x['c']['rarete']
    # PV : position de G parmi les cartes de meme rarete, sur tout le jeu
    par_r = {}
    for x in cartes:
        par_r.setdefault(x['nouvelle'], []).append(x)
    for r, xs in par_r.items():
        lo, hi = FOURCHETTES[r]
        for x, p in zip(xs, rangs([x['G'] for x in xs])):
            x['pv'] = x['c']['pv'] if x['c'].get('pvManuel') else round(lo + p * (hi - lo))
    return idx, cartes, manquants


def main():
    idx, cartes, manquants = calculer()
    from collections import Counter
    print('cartes :', len(cartes))
    print('Pantheon introuvables :', sorted(manquants))
    print('raretes :', dict(Counter(x['nouvelle'] for x in cartes)))
    print('changements de rarete :', sum(1 for x in cartes if x['nouvelle'] != x['c']['rarete']))
    if '--appliquer' in sys.argv:
        par_fichier = {}
        for x in cartes:
            x['c']['rarete'], x['c']['pv'] = x['nouvelle'], x['pv']
        for e in idx['collections']:
            f = RACINE / e['fichier']
            d = json.loads(f.read_text(encoding='utf-8'))
            maj = {x['c']['id']: x['c'] for x in cartes if x['col'] == e['slug']}
            d['cartes'] = [maj.get(c['id'], c) for c in d['cartes']]
            f.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
        print('ecrit')
    return cartes


if __name__ == '__main__':
    main()
