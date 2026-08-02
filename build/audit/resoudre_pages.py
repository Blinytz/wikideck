#!/usr/bin/env python3
"""Résolution des pages fr.wikipedia des cartes à créer et des pages corrigées.

L'annexe CSV est donnée comme source de vérité des titres, mais elle propose
très souvent le nom de la carte tel quel : « Min », « Sif », « Règle »,
« Iris ». Sur fr.wikipedia ces titres mènent à une page d'homonymie, à un
autre sujet, ou nulle part. Une recherche en texte intégral sur le seul nom
est pire encore — elle rend Suga pour Min et Jaimie Alexander pour Sif.

D'où une résolution en entonnoir, du plus fiable au moins fiable :

  1. le titre du CSV tel quel ;
  2. « Nom (qualificatif) », la forme de désambiguïsation de fr.wikipedia
     (« Min (dieu) », « Règle (constellation) ») ;
  3. les liens de la page d'homonymie, quand c'en est une — c'est
     l'encyclopédie elle-même qui énumère les sens possibles ;
  4. la recherche, mais enrichie du domaine de la collection
     (« Sif mythologie nordique » et non « Sif »).

Et surtout un JUGE, appliqué à toutes les étapes sauf la première : le résumé
de la page doit contenir un mot du domaine de la collection (domaines.py).
Une page qui ne parle pas du bon sujet est refusée, quel que soit son rang.
Si rien ne passe, la carte est SIGNALÉE — consigne 1 du document : ne jamais
remplacer par un choix arbitraire.

Sorties : resolution_pages.json, pages_a_signaler.txt.
Le cache disque rend le script rejouable sans refaire un appel.

Usage : python resoudre_pages.py [--limite N] [--slug <slug>]
"""
import sys, json, time, pickle, re, unicodedata, urllib.parse, urllib.request, urllib.error
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
from plan_audit import norm, charger
import domaines

UA = 'wikideck-build/1.0 (projet perso; contact: claude.elk041@passmail.net)'
API = 'https://fr.wikipedia.org/w/api.php'
CACHE = ICI / '.cache_pages.pkl'
LOT = 20                       # exlimit=20, plafond anonyme des extraits

_cache = pickle.loads(CACHE.read_bytes()) if CACHE.exists() else {}
_sale = 0
INDICES = {}      # nom de carte -> commentaire du document, rempli par main()

# Titres que l'entonnoir ne peut pas trouver seul, tranchés à la main après
# lecture des signalements. Chacun a été vérifié sur fr.wikipedia.
SURCHARGES = {
    "sites-antiques|Ziggourat d'Our": "Ziggurat d'Ur",
    'sites-antiques|Volubilis': 'Volubilis (site archéologique)',
    'sites-antiques|Lascaux': 'Grotte de Lascaux',
    "monuments-emblematiques|Palais des Papes": "Palais des papes d'Avignon",
    "monuments-emblematiques|Temple d'Or d'Amritsar": 'Harmandir Sahib',
    'monuments-emblematiques|Grand Palais de Bangkok': 'Grand Palais (Bangkok)',
    'creatures-prehistoriques|Lion des cavernes': 'Panthera spelaea',
    'creatures-prehistoriques|Moa': 'Dinornithiformes',
    'grands-explorateurs|Ahmad ibn Fadlan': 'Ibn Fadlan',
    'scientifiques-celebres|Fibonacci': 'Leonardo Fibonacci',
    'inventeurs-et-ingenieurs|Isaac Singer': 'Isaac Merritt Singer',
    'inventeurs-et-ingenieurs|Frères Lumière': 'Auguste et Louis Lumière',
    'aviateurs-celebres|Louis Breguet': 'Louis Charles Breguet',
    'aviateurs-celebres|Donald Douglas': 'Donald Wills Douglas',
    'insectes|Scarabée Hercule': 'Dynastes hercules',
    'insectes|Phasme feuille': 'Phylliidae',
    'races-de-chien|Braque hongrois': 'Braque hongrois à poil court',
    'races-de-chat|Van turc': 'Turc de Van',
    'races-de-chat|Highland fold': 'Scottish fold',
    'jeu-video-moderne|Sekiro': 'Sekiro: Shadows Die Twice',
    'mythologies-asie-est|Yanluo': 'Yanluo Wang',
    'inventions-importantes|Outil de pierre taillée': 'Industrie lithique',
    'inventions-importantes|Métallurgie du bronze': 'Âge du bronze',
    'inventions-importantes|Conserve alimentaire': 'Appertisation',
    "inventions-importantes|Réseau d'égouts": 'Égout',
    'coupes-du-monde-fifa|Coupe du monde 2026': 'Coupe du monde de football 2026',
    'tableaux-celebres|La Cathédrale de Rouen': 'Série des Cathédrales de Rouen',
    'tableaux-celebres|Washington traversant le Delaware':
        'Washington Crossing the Delaware',
    'tableaux-celebres|La Ville qui monte': 'La Città che sale',
    'tableaux-celebres|Un plus grand plongeon': 'A Bigger Splash',
    'tableaux-celebres|No. 61 (Rust and Blue)': 'Mark Rothko',
    # Trouvés à la main après une passe de sondage sur les signalements.
    'mythologies-slaves|Dazhbog': 'Dajbog',
    'mythologies-africaines|Yemoja': 'Iemanja',
    'mythologies-africaines|Legba': 'Papa Legba',
    'mythologies-oceanie-ameriques|Hina': 'Hina (divinité)',
    'personnages-cinema-serie|Doc Brown': 'Emmett Brown',
    'personnages-jeu-video|Joel': 'Joel Miller',
    'mythologie-nordique|Sigurd': 'Siegfried (mythologie)',
    'personnages-manga-anime|Lupin III': 'Arsène Lupin III',
}


def sauver(force=False):
    global _sale
    if force or _sale >= 60:
        CACHE.write_bytes(pickle.dumps(_cache))
        _sale = 0


def marquer(n=1):
    global _sale
    _sale += n
    sauver()


def get(params):
    url = API + '?' + urllib.parse.urlencode({**params, 'format': 'json'})
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read().decode('utf-8'))
            time.sleep(0.05)
            return d
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None


def sans_accents(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


# Collections du vivant : voir bien_la_carte.
VIVANT = {'mammiferes', 'oiseaux', 'reptiles-et-amphibiens', 'insectes',
          'poissons-et-vie-marine', 'races-de-chien', 'races-de-chat',
          'dinosaures-celebres', 'creatures-prehistoriques'}


# ------------------------------------------------------------------- le juge

def du_domaine(fiche, slug):
    """Le résumé parle-t-il du sujet de la collection ?"""
    mots = domaines.MOTS.get(slug)
    if not mots:
        return True
    texte = re.sub(r"['’]", ' ', sans_accents(fiche.get('extrait', '')))
    titre = re.sub(r"['’]", ' ', sans_accents(fiche.get('titre', '')))
    return any(re.search(r'\b' + re.escape(sans_accents(m)), texte + ' ' + titre)
               for m in mots)


def bien_la_carte(fiche, nom, slug_vivant=False):
    """Le titre désigne-t-il bien CE sujet ?

    Le juge de domaine ne suffit pas : « Demon Slayer » parle bien de manga,
    « Michael Shanks » bien d'un rôle de série — mais ce ne sont ni Tanjiro
    Kamado ni Shanks. fr.wikipedia n'a tout simplement pas d'article pour
    beaucoup de personnages ; mieux vaut signaler la carte que lui coller
    l'article de l'oeuvre ou celui de l'acteur.

    Seule l'étape 1 en est dispensée : le titre y vient du CSV, et une
    redirection suivie (Ammit -> Ammout) est une bonne réponse."""
    sans_paren = lambda x: re.sub(r'\s*\([^)]*\)$', '', sans_accents(x)).strip()
    base, plein = sans_paren(fiche['titre']), sans_accents(fiche['titre']).strip()
    n, n_nu = sans_accents(nom).strip(), sans_paren(nom)
    # La parenthèse doit tomber des DEUX côtés : beaucoup de cartes en portent
    # une (« Arc (arme) », « Souris (informatique) », « Sirène (mythologie
    # grecque) »), et les comparer à un titre déjà dénudé les condamnait.
    for a in (n, n_nu):
        for b in (base, plein):
            if a == b or SequenceMatcher(None, a, b).ratio() >= 0.78:
                return True
    # Espèces : fr.wikipedia titre au nom scientifique ou normalisé (Ursus
    # spelaeus, Poule domestique) et le nom courant n'est qu'une redirection.
    # Le résumé, lui, le cite toujours. Réservé aux collections du vivant :
    # ailleurs ce test laisserait passer la page de l'oeuvre pour un personnage.
    if slug_vivant:
        mots = [m for m in re.split(r'\W+', n_nu) if len(m) >= 4]
        texte = sans_accents(fiche.get('extrait', ''))
        if mots and all(re.search(r'\b' + re.escape(m), texte) for m in mots):
            return True
    # Cartes doubles — « Timon et Pumbaa », « Vil Coyote et Bip Bip » : quand
    # l'encyclopédie ne titre que l'un des deux, sa page reste la bonne.
    return ' et ' in n and base in [m.strip() for m in n.split(' et ')]


def note(fiche, nom, slug):
    """Départage les candidats du domaine : proximité du titre, malus aux
    pages qui ne sont pas un sujet (listes, homonymie)."""
    t, n = sans_accents(fiche['titre']), sans_accents(nom)
    base = re.sub(r'\s*\([^)]*\)$', '', t)
    score = SequenceMatcher(None, n, base).ratio()
    if base == n:
        score += 0.5
    if re.match(r'^(liste|catégorie|categorie|univers|personnages) d', t):
        score -= 0.6
    if len(fiche.get('extrait', '')) < 120:
        score -= 0.2
    return score


# ------------------------------------------------------- accès à l'encyclopédie

def fiches(titres):
    """{titre demandé -> fiche} en lots. Le rattachement passe par les tables
    `normalized`/`redirects` renvoyées, jamais par l'ordre des pages."""
    out = {}
    d = get({'action': 'query', 'redirects': 1,
             'prop': 'extracts|pageprops|pageimages|links',
             'explaintext': 1, 'exintro': 1, 'exlimit': 'max',
             'piprop': 'original', 'pllimit': 'max', 'plnamespace': 0,
             'titles': '|'.join(titres)})
    if not d or 'query' not in d:
        return out
    q = d['query']
    vers = {t: t for t in titres}
    for r in q.get('normalized', []) + q.get('redirects', []):
        vers[r['to']] = vers.get(r['from'], r['from'])
    for page in q.get('pages', {}).values():
        demande = vers.get(page['title'], page['title'])
        if 'missing' in page:
            out[demande] = {'statut': 'introuvable'}
            continue
        homonymie = 'disambiguation' in (page.get('pageprops') or {})
        out[demande] = {
            'statut': 'homonymie' if homonymie else 'ok',
            'titre': page['title'],
            'extrait': (page.get('extract') or '')[:500],
            'illustration': (page.get('original') or {}).get('source', ''),
            'liens': [l['title'] for l in page.get('links', [])][:40],
        }
    return out


def charger_fiches(titres):
    """Interroge ce qui n'est pas déjà en cache.

    Une fiche d'homonymie sans liste de liens vient d'un cache antérieur à
    l'ajout de `prop=links` : elle est réinterrogée, sinon l'étape 3 ne verrait
    jamais un seul candidat."""
    for t in list(titres):
        f = _cache.get('fiche:' + t)
        if f and f.get('statut') == 'homonymie' and 'liens' not in f:
            del _cache['fiche:' + t]
    manquants = sorted({t for t in titres if t and 'fiche:' + t not in _cache})
    for i in range(0, len(manquants), LOT):
        for t, f in fiches(manquants[i:i + LOT]).items():
            _cache['fiche:' + t] = f
        for t in manquants[i:i + LOT]:            # mémorise aussi les absences
            _cache.setdefault('fiche:' + t, {'statut': 'introuvable'})
        marquer(LOT)
    sauver(force=True)
    return len(manquants)


def rechercher(terme, n=6):
    cle = f'rech{n}:' + terme
    if cle in _cache:
        return _cache[cle]
    d = get({'action': 'query', 'list': 'search', 'srsearch': terme,
             'srlimit': n, 'srnamespace': 0})
    titres = [h['title'] for h in ((d or {}).get('query') or {}).get('search', [])]
    _cache[cle] = titres
    marquer()
    return titres


# ------------------------------------------------------------------- entonnoir

def candidats_etape(etape, slug, nom, titre):
    indice = INDICES.get(nom, '')
    surcharge = SURCHARGES.get(f'{slug}|{nom}')
    if etape == 0:
        return [surcharge] if surcharge else []
    if etape == 1:
        return [titre]
    if etape == 2:
        qualifs = list(domaines.QUALIFS.get(slug, []))
        if indice:
            qualifs.insert(0, indice)     # « Les Trois Grâces (Rubens) »
        return [f'{titre} ({q})' for q in qualifs]
    if etape == 3:
        f = _cache.get('fiche:' + titre) or {}
        return f.get('liens', []) if f.get('statut') == 'homonymie' else []
    if etape == 4:
        ctx = domaines.CONTEXTE.get(slug, '')
        req = [f'{nom} {indice} {ctx}'.strip()] if indice else []
        return [t for r in req + [f'{nom} {ctx}'.strip(), titre]
                for t in rechercher(r)]
    if etape == 5:
        # Repêchage : le titre du CSV, juge de domaine écarté. Beaucoup de
        # bonnes pages n'emploient simplement aucun mot de la liste (Monnaie,
        # Savon, Sun Yat-sen). Mais PAS pour les personnages : là, le juge est
        # tout ce qui distingue la fiche du personnage de celle de l'oeuvre,
        # et sans lui « Meursault » devient la commune viticole, « Travis
        # Bickle » le film Taxi Driver, « Denji » la série Chainsaw Man.
        return [] if slug.startswith('personnages-') else [titre]
    return []


def retenir(etape, slug, nom, titre):
    """Meilleur candidat du domaine à cette étape, ou None."""
    retenus = []
    for c in candidats_etape(etape, slug, nom, titre):
        f = _cache.get('fiche:' + c)
        if not f or f['statut'] != 'ok' or not f.get('extrait'):
            continue
        if etape not in (0, 5) and not du_domaine(f, slug):
            continue                     # l'étape 5 est justement le repêchage
        if etape not in (0, 1, 5) and not bien_la_carte(f, nom, slug in VIVANT):
            continue                     # l'étape 5 est déjà signalée « à relire »
        retenus.append((note(f, nom, slug), f))
    if not retenus:
        return None
    return max(retenus, key=lambda x: x[0])[1]


def main():
    limite = int(sys.argv[sys.argv.index('--limite') + 1]) \
        if '--limite' in sys.argv else None
    slug_filtre = sys.argv[sys.argv.index('--slug') + 1] \
        if '--slug' in sys.argv else None

    plan = json.loads((ICI / 'plan_audit.json').read_text(encoding='utf-8'))
    INDICES.update(plan.get('indices') or {})
    restru = json.loads((ICI / 'restructuration.json').read_text(encoding='utf-8'))
    _, _, csv_par_nom = charger()
    deja = {c['slug']: {norm(x['nom']) for x in c['cartes']}
            for c in restru['collections']}

    demandes = []                       # (slug, nom, titre proposé, méfiance)
    for col in plan['collections']:
        for nom in col['ajouts']:
            if norm(nom) in deja.get(col['slug'], set()):
                continue
            ligne = csv_par_nom.get(norm(nom))
            demandes.append((col['slug'], nom,
                             (ligne or {}).get('titrePage') or nom,
                             ligne is None or ligne.get('statut') == 'à vérifier'))
    for r in plan['corrections_page']:
        demandes.append((r['slug'], r.get('nouveau_nom') or r['nom'],
                         r['titrePage'], False))
    for r in plan['a_verifier']:
        demandes.append((r['slug'], r['nom'], r['hypotheses'][0], True))
    if slug_filtre:
        demandes = [d for d in demandes if d[0] == slug_filtre]
    if limite:
        demandes = demandes[:limite]
    print(f'{len(demandes)} pages à résoudre')

    resolution, signalements, par_etape = {}, [], {}
    restants = list(demandes)
    for etape, libelle in ((0, 'tranché à la main'), (1, 'titre du CSV'),
                           (2, 'titre qualifié'),
                           (3, "page d'homonymie"), (4, 'recherche'),
                           (5, 'CSV hors domaine — à relire')):
        if not restants:
            break
        besoins = []
        if etape == 3:      # rafraîchir les pages d'homonymie avant d'en lire les liens
            charger_fiches([t for _, _, t, _ in restants])
        for slug, nom, titre, mefiance in restants:
            if etape == 1 and mefiance:
                continue                 # « à vérifier » : le titre n'est qu'une piste
            besoins += candidats_etape(etape, slug, nom, titre)
        n = charger_fiches(besoins)
        encore = []
        for d in restants:
            slug, nom, titre, mefiance = d
            f = None if (etape == 1 and mefiance) else retenir(etape, slug, nom, titre)
            if f is None:
                encore.append(d)
                continue
            resolution[f'{slug}|{nom}'] = {
                'slug': slug, 'nom': nom, 'titre': f['titre'],
                'extrait': f['extrait'], 'illustration': f['illustration'],
                'lien': 'https://fr.wikipedia.org/wiki/'
                        + urllib.parse.quote(f['titre'].replace(' ', '_')),
                'etape': libelle,
            }
            par_etape[libelle] = par_etape.get(libelle, 0) + 1
        print(f'  étape {etape} ({libelle}) : {n} pages interrogées, '
              f'{len(restants) - len(encore)} résolues, {len(encore)} restent')
        restants = encore

    for slug, nom, titre, _ in restants:
        etat = (_cache.get('fiche:' + titre) or {}).get('statut', 'introuvable')
        signalements.append(f'{slug} · {nom} · titre proposé « {titre} » · {etat}')

    (ICI / 'resolution_pages.json').write_text(
        json.dumps(resolution, ensure_ascii=False, indent=1), encoding='utf-8')
    (ICI / 'pages_a_signaler.txt').write_text(
        '\n'.join(signalements), encoding='utf-8')
    sauver(force=True)
    print(f'\n{len(resolution)} pages résolues {par_etape}, '
          f'{len(signalements)} signalée(s)')
    for s in signalements[:40]:
        print(' •', s)


if __name__ == '__main__':
    main()
