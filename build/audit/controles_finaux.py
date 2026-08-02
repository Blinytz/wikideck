#!/usr/bin/env python3
"""Les contrôles que le document exige après implémentation.

Trois de la section « Contrôles finaux » :
  1. aucun `nom` dupliqué entre deux collections (consigne 5) ;
  2. `numero` continu de 1 à N sur chaque collection ;
  3. aucune carte sans imageUrl, sans rareté, sans pouvoir (consigne 10).

Deux de cohérence croisée :
  4. consigne 7 — tout tableau implique son peintre dans Grands peintres ;
  5. §28.10 — un même sujet ne peut exister à la fois comme personnage et
     comme œuvre.

Plus deux contrôles de cohérence interne du jeu :
  6. le fichier image annoncé existe réellement ;
  7. les effectifs de `collections.json` collent aux fichiers.

Sort en code 1 s'il reste un manquement bloquant.

Usage : python controles_finaux.py
"""
import sys, json, re, unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent

RARETES = {'commune', 'rare', 'epique', 'mythique', 'legendaire'}
# §28.10 — les six collections de personnages contre les deux d'œuvres
PERSONNAGES = {'personnages-litterature', 'personnages-cinema-serie',
               'personnages-bd-comics', 'personnages-jeu-video',
               'personnages-animation', 'personnages-manga-anime'}
OEUVRES = {'classiques-du-cinema', 'cinema-moderne',
           'age-dor-du-jeu-video', 'jeu-video-moderne'}
PARTICULES = {'van', 'von', 'der', 'den', 'dos', 'del', 'della', 'jean',
              'saint', 'pierre', 'louis', 'anne', 'marie', 'jose', 'juan'}


def norm(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '', s)


def charger():
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    cols = []
    for c in idx['collections']:
        d = json.loads((RACINE / c['fichier']).read_text(encoding='utf-8'))
        d['_annonce'] = c['nbCartes']
        cols.append(d)
    return cols


def main():
    cols = charger()
    dur, doux = [], []

    # 1. homonymes inter-collections
    par_nom = defaultdict(list)
    for d in cols:
        for c in d['cartes']:
            par_nom[norm(c['nom'])].append((d['slug'], c['nom']))
    for cle, occ in sorted(par_nom.items()):
        slugs = {s for s, _ in occ}
        if len(slugs) < 2:
            continue
        # La consigne vise les noms EXACTEMENT identiques. « Hades » le jeu et
        # « Hadès » le dieu n'en sont pas : l'un s'écrit ainsi, et les qualifier
        # serait corriger une collision qui n'existe que pour l'accent.
        exact = len({n.casefold() for _, n in occ}) == 1
        msg = 'homonyme « {} » dans {}'.format(occ[0][1], ', '.join(sorted(slugs)))
        (dur if exact else doux).append(
            msg if exact else msg + "  (les noms ne diffèrent que par l'accent)")

    # 2. numérotation
    for d in cols:
        nums = [c.get('numero') for c in d['cartes']]
        if nums != list(range(1, len(nums) + 1)):
            trous = sorted(set(range(1, len(nums) + 1)) - set(n for n in nums if n))
            dur.append(f"{d['slug']} : numérotation non continue "
                       f"({len(nums)} cartes, {len(trous)} trou(s))")

    # 3. complétude + 6. l'image existe vraiment
    for d in cols:
        for c in d['cartes']:
            if c.get('rarete') not in RARETES:
                dur.append(f"{d['slug']} · {c['nom']} : rareté « {c.get('rarete')} »")
            if not (c.get('pouvoir') or {}).get('texte'):
                dur.append(f"{d['slug']} · {c['nom']} : sans pouvoir")
            if not c.get('imageUrl'):
                dur.append(f"{d['slug']} · {c['nom']} : sans imageUrl")
            elif not (RACINE / c['imageUrl']).exists():
                dur.append(f"{d['slug']} · {c['nom']} : image absente du dépôt")

    # 4. tout tableau implique son peintre
    # Le nom du peintre peut porter une parenthèse (« Léonard de Vinci
    # (peintre) », consigne 8) : c'est le nom nu qui figure dans le résumé.
    # On cherche le PATRONYME, pas le nom complet : le résumé d'un tableau dit
    # « Hokusai » là où la carte s'appelle « Katsushika Hokusai », et le nom
    # complet ne s'y retrouve jamais tel quel.
    peintres = set()
    for d in cols:
        if d['slug'] != 'grands-peintres':
            continue
        for c in d['cartes']:
            nu = re.sub(r'\s*\([^)]*\)$', '', c['nom'])
            for mot in re.split(r"[\s'’-]+", nu):
                # « Jan van Eyck » n'a aucun mot de 5 lettres : on descend à 4,
                # en écartant les particules, qui ne désignent personne.
                if len(mot) >= 4 and norm(mot) not in PARTICULES:
                    peintres.add(norm(mot))
    tableaux = next((d for d in cols if d['slug'] == 'tableaux-celebres'), None)
    if tableaux and peintres:
        for c in tableaux['cartes']:
            resume = norm((c.get('description') or '')[:500])
            if not any(p in resume for p in peintres):
                doux.append(f"tableau orphelin ? « {c['nom']} » — aucun peintre "
                            'de Grands peintres nommé dans son résumé')

    # 5. personnage ↔ œuvre
    noms_perso = {norm(c['nom']): c['nom'] for d in cols if d['slug'] in PERSONNAGES
                  for c in d['cartes']}
    for d in cols:
        if d['slug'] not in OEUVRES:
            continue
        for c in d['cartes']:
            if norm(c['nom']) in noms_perso:
                dur.append(f"collision personnage/œuvre : « {c['nom']} » "
                           f"({d['slug']})")

    # 7. effectifs annoncés
    for d in cols:
        if d['_annonce'] != len(d['cartes']):
            dur.append(f"{d['slug']} : collections.json annonce {d['_annonce']} "
                       f"cartes pour {len(d['cartes'])}")

    total = sum(len(d['cartes']) for d in cols)
    print(f'{len(cols)} collections, {total} cartes\n')
    print(f'---- manquements bloquants ({len(dur)}) ----')
    for s in dur[:60]:
        print(' •', s)
    if len(dur) > 60:
        print(f'   … et {len(dur) - 60} autres')
    print(f'\n---- à regarder ({len(doux)}) ----')
    for s in doux[:30]:
        print(' •', s)
    if len(doux) > 30:
        print(f'   … et {len(doux) - 30} autres')
    return 1 if dur else 0


if __name__ == '__main__':
    sys.exit(main())
