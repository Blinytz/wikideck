#!/usr/bin/env python3
"""Moteur d'application de `plan_audit.json` sur data/.

Restructuration incrémentale : on part des collections telles qu'elles sont
AUJOURD'HUI — l'atelier les a éditées depuis la génération d'origine — et on
les déplace, jamais on ne les régénère. Une carte existante conserve son image,
son cadrage, ses réglages manuels ; seule sa collection d'accueil change.

Les appariements se font sur le `nom` : c'est la seule clé que le document
d'audit manipule. Tout nom du plan qui ne retrouve pas sa carte, et toute carte
qu'aucune règle ne réclame, sont signalés — jamais devinés.

Étapes (l'ordre compte, cf. plan_audit.py) :
    renommages → corrections de page → fusions → suppressions → transferts
    → répartition → contrôle des restes

Usage : python appliquer_audit.py --essai    # rapport, n'écrit rien
        python appliquer_audit.py            # applique la restructuration
"""
import sys, json, re, unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI))
from plan_audit import norm, norm_sans_article


class Pool:
    """Les cartes existantes, indexées par collection et par nom normalisé.

    Chaque carte n'est délivrée qu'une fois : `prendre` la retire de l'index,
    ce qui rend visible à la fin ce que personne n'a réclamé."""

    def __init__(self, alias):
        self.alias = {norm(k): norm(v) for k, v in alias.items()}
        self.cartes = {}
        idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
        self.noms_collections = {}
        for c in idx['collections']:
            d = json.loads((RACINE / c['fichier']).read_text(encoding='utf-8'))
            self.cartes[c['slug']] = list(d['cartes'])
            self.noms_collections[c['slug']] = d['collection']
        self.index = {s: self._indexer(v) for s, v in self.cartes.items()}
        self.orphelines = defaultdict(list)      # slug destination -> cartes

    @staticmethod
    def _indexer(cartes):
        idx = {}
        for c in cartes:
            idx.setdefault(norm(c['nom']), c)
            idx.setdefault(norm_sans_article(c['nom']), c)
        return idx

    def reindexer(self, slug):
        self.index[slug] = self._indexer(self.cartes[slug])

    def chercher(self, slug, nom):
        idx = self.index.get(slug, {})
        for cle in (norm(nom), norm_sans_article(nom),
                    self.alias.get(norm(nom), '')):
            if cle and cle in idx:
                return idx[cle]
        return None

    def prendre(self, slug, nom):
        c = self.chercher(slug, nom)
        if c is None:
            return None
        self.cartes[slug] = [x for x in self.cartes[slug] if x is not c]
        self.reindexer(slug)
        return c

    def reste(self, slug):
        out = self.cartes[slug]
        self.cartes[slug] = []
        self.reindexer(slug)
        return out


def slugifier(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def appliquer(plan, journal):
    pool = Pool(plan['alias'])
    sig = journal.append

    # 1. renommages — le nom seul, la page reste la même
    for r in plan['renommages']:
        c = pool.chercher(r['slug'], r['de'])
        if c is None:
            sig(f"renommage {r['slug']} : « {r['de']} » introuvable  [{r['raison']}]")
            continue
        c['nom'] = r['vers']
        pool.reindexer(r['slug'])

    # 2. corrections de page — changement de sujet : la fiche est à refaire
    for r in plan['corrections_page']:
        c = pool.chercher(r['slug'], r['nom'])
        if c is None:
            sig(f"correction {r['slug']} : « {r['nom']} » introuvable  [{r['raison']}]")
            continue
        c['titrePage'] = r['titrePage']
        if r.get('nouveau_nom'):
            c['nom'] = r['nouveau_nom']
        c['_regenerer'] = r['raison']
        pool.reindexer(r['slug'])

    for r in plan['a_verifier']:
        c = pool.chercher(r['slug'], r['nom'])
        if c is None:
            sig(f"à vérifier {r['slug']} : « {r['nom']} » introuvable")
            continue
        c['_aVerifier'] = r['hypotheses']
        c['_regenerer'] = r['raison']

    for r in plan['corrections_tags']:
        c = pool.chercher(r['slug'], r['nom'])
        if c is None:
            sig(f"tags {r['slug']} : « {r['nom']} » introuvable")
            continue
        c['tags'] = r['tags']
        c['tagsManuel'] = True

    # 3. fusions — on garde la carte la plus consultée, l'autre disparaît
    for f in plan['fusions']:
        trouvees = [pool.chercher(f['slug'], n) for n in f['noms']]
        trouvees = [c for c in trouvees if c]
        if len(trouvees) < 2:
            sig(f"fusion {f['slug']} {f['noms']} : {len(trouvees)} carte(s) trouvée(s)")
            continue
        garde = max(trouvees, key=lambda c: c.get('pageviews', 0))
        garde['nom'] = f['vers']
        for c in trouvees:
            if c is not garde:
                pool.cartes[f['slug']].remove(c)
        pool.reindexer(f['slug'])

    # 4. suppressions
    for slug, noms in plan['suppressions'].items():
        for n in noms:
            if pool.prendre(slug, n) is None:
                sig(f'suppression {slug} : « {n} » introuvable')

    # 5. transferts vers une collection qui n'est pas la scission de la source
    for t in plan['transferts']:
        for n in t['noms']:
            c = pool.prendre(t['de'], n)
            if c is None:
                sig(f"transfert {t['de']} -> {t['vers']} : « {n} » introuvable")
                continue
            pool.orphelines[t['vers']].append(c)

    # 6. répartition — DEUX passes. « Toutes les autres cartes existantes »
    # (§4.2, §10.1, §11.1…) ne peut se calculer qu'une fois toutes les listes
    # nominatives servies, y compris celles de collections décrites plus loin
    # dans le document.
    resultat = {c['slug']: list(pool.orphelines.pop(c['slug'], []))
                for c in plan['collections']}
    for col in plan['collections']:
        for src in col['prend']:
            if src.get('reste'):
                continue
            for n in src['noms']:
                c = pool.prendre(src['de'], n)
                if c is None:
                    sig(f"répartition {src['de']} -> {col['slug']} : « {n} » introuvable")
                    continue
                resultat[col['slug']].append(c)
    for col in plan['collections']:
        for src in col['prend']:
            if src.get('reste'):
                resultat[col['slug']] += pool.reste(src['de'])

    # 6bis. un « ajout » qui est en fait un transfert. §10.3 liste Terechkova,
    # Michael Collins et Baumgartner comme des créations alors que la
    # correction du lot 3 en fait des transferts depuis les Aviateurs ; §26.8
    # inscrit Gilgamesh et Didon dans ses listes d'ajouts alors que §3.1 les
    # transfère. Sans ce filtre la carte existerait deux fois.
    for col in plan['collections']:
        deja = {norm(c['nom']) for c in resultat[col['slug']]}
        garde = [n for n in col['ajouts'] if norm(n) not in deja]
        for n in col['ajouts']:
            if norm(n) in deja:
                sig(f"{col['slug']} : « {n} » listé en ajout mais déjà transféré "
                    f'— création annulée')
        col['ajouts'] = garde

    # 7. ce que personne n'a réclamé
    intactes = {'merveilles-du-monde', 'pilotes-f1-champions-du-monde',
                'elements-chimiques'}
    for slug, restantes in pool.cartes.items():
        if restantes and slug not in intactes:
            sig(f'{slug} : {len(restantes)} carte(s) non réparties — '
                + ', '.join(c['nom'] for c in restantes[:8])
                + ('…' if len(restantes) > 8 else ''))
    for slug, cs in pool.orphelines.items():
        sig(f'transfert vers {slug} : collection cible absente du plan '
            f'({len(cs)} carte(s))')

    return pool, resultat


def main():
    plan = json.loads((ICI / 'plan_audit.json').read_text(encoding='utf-8'))
    journal = []
    pool, resultat = appliquer(plan, journal)

    intactes = {'merveilles-du-monde', 'pilotes-f1-champions-du-monde',
                'elements-chimiques'}
    print(f'{len(resultat) + len(intactes)} collections après restructuration\n')
    total = 0
    for col in plan['collections']:
        n_ex, n_new = len(resultat[col['slug']]), len(col['ajouts'])
        total += n_ex + n_new
        print(f"  {col['slug']:<38} {n_ex:>4} existantes + {n_new:>3} à créer "
              f"= {n_ex + n_new:>4}")
    print(f'\n  (+ {len(intactes)} collections inchangées)')
    print(f'  {total} cartes dans les collections touchées, '
          f"dont {sum(len(c['ajouts']) for c in plan['collections'])} à créer")

    print(f'\n---- signalements ({len(journal)}) ----')
    for s in journal:
        print(' •', s)

    if '--essai' not in sys.argv:
        (ICI / 'restructuration.json').write_text(json.dumps(
            {'collections': [{'slug': c['slug'], 'nom': c['nom'],
                              'role_source': c['role_source'],
                              'cartes': resultat[c['slug']]}
                             for c in plan['collections']],
             'signalements': journal}, ensure_ascii=False, indent=1), encoding='utf-8')
        print('\nrestructuration.json écrit')


if __name__ == '__main__':
    main()
