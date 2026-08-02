#!/usr/bin/env python3
"""Le SENS du document d'audit : quelle liste va où, et pour quoi faire.

`lire_audit.py` extrait les listes ; ce module leur donne une intention et
produit `plan_audit.json`, seul fichier que le moteur d'application consomme.
Tout ce qui n'est pas dérivable d'une liste (renommages, corrections de page,
fusions, raretés forcées) est écrit ici en toutes lettres, avec le renvoi vers
le paragraphe du document.

Ordre imposé au moteur, et raison de cet ordre :
  1. renommages et corrections de page — les listes de répartition citent les
     cartes sous leur nom d'APRÈS correction (« Élisabeth Ire de Russie »,
     « Coyote (mythologie) », « King Kong (film) ») ;
  2. fusions puis suppressions — pour ne pas répartir une carte condamnée ;
  3. répartition — listes nominatives, ou « reste » de la collection source ;
  4. ajouts, renumérotation, raretés.

Usage : python plan_audit.py            # écrit plan_audit.json + rapport
        python plan_audit.py --verifier # rapport seul
"""
import sys, json, csv, re, unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import lire_audit as L

RACINE = ICI.parent.parent

# ---------------------------------------------------------------- appariement

ARTICLES = ('le ', 'la ', 'les ', "l'", 'un ', 'une ', 'des ', 'du ')


def norm(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '', s)


def norm_sans_article(s):
    """Les cartes existantes ont été importées d'un tableur qui a mangé les
    articles initiaux : « Le Parrain » y est « Parrain ». Le document, lui,
    les écrit. On compare donc aussi sans article."""
    t = str(s).lower().lstrip('« ').strip()
    for a in ARTICLES:
        if t.startswith(a):
            return norm(t[len(a):])
    return norm(t)


# Écarts qu'aucune règle ne rattrape : le document et la carte ne s'écrivent
# simplement pas pareil. Chaque ligne est une décision, pas une heuristique.
ALIAS = {
    '8½': '8 1/2',
    'Pokémon Rouge et Bleu': 'Pokémon Rouge/Bleu',
    'Wernher von Braun': 'Werner von Braun',   # la carte a une coquille
    # §26.11 cite la carte sous son nom d'avant le renommage de §26.11 lui-même
    'Coyote': 'Coyote (mythologie)',
}

# ------------------------------------------------------- corrections préalables
# (§1.2, §2.1, §3.2, §3.3, §14.1, §15.1, §15.2, §18.1, §20.1, §22.1, §26.11,
#  §27.2, §28.3, §29, §30.1, §12.1, §16.2, §11.3)

RENOMMAGES = [
    # (slug source, nom actuel, nom cible, raison)
    ('corps-celestes', 'Charon', 'Charon (lune)', '§1.2 homonyme mythologie'),
    ('corps-celestes', 'Éris', 'Éris (planète naine)', '§1.2 homonyme mythologie'),
    ('corps-celestes', 'Rhéa', 'Rhéa (lune)', '§1.2 homonyme Titanide'),
    ('corps-celestes', 'Titan', 'Titan (lune)', '§1.2 ambiguïté Titans'),
    ('corps-celestes', 'Europe', 'Europe (lune)', '§1.2 ambiguïté continent'),
    ('grands-dirigeants', 'Elizabeth Ire', 'Élisabeth Ire de Russie', '§3.2 page réelle'),
    ('tableaux-celebres', 'Autoportrait', 'Autoportrait de Rembrandt', '§14.1'),
    ('poissons-et-vie-marine', 'Poulpe', 'Pieuvre commune', '§20.1'),
    ('races-de-chien', 'Pitbull', 'American Pit Bull Terrier', '§22.1 race non reconnue'),
    ('mythologies-du-monde-hors-grece', 'Coyote', 'Coyote (mythologie)', '§26.11 homonyme mammifère'),
    ('creatures-et-legendes', 'Sirène', 'Sirène (folklore)', '§27.2'),
    ('creatures-et-legendes', 'Basilic', 'Basilic (créature)', '§27.2'),
    ('personnages-de-fiction-celebres', 'Nemo', 'Nemo (Le Monde de Nemo)', '§28.3'),
    ('scientifiques-celebres', 'Léonard de Vinci', 'Léonard de Vinci (inventeur)', '§12.1'),
    ('aviateurs-celebres', 'Antoine de Saint-Exupéry', 'Antoine de Saint-Exupéry (aviateur)', '§16.2'),
    ('inventions-importantes', 'Péniciline', 'Pénicilline', '§15.2'),
    ('inventions-importantes', 'Ampoule Electrique', 'Ampoule électrique', '§15.2'),
    # §29 — collisions personnage ↔ œuvre, titrePage inchangé
    ('films-cultes', 'Batman', 'Batman (film)', '§29'),
    ('films-cultes', 'King Kong', 'King Kong (film)', '§29'),
    ('films-cultes', 'Terminator', 'Terminator (film)', '§29'),
    ('films-cultes', "E.T., l'extra-terrestre", "E.T., l'extra-terrestre (film)", '§29'),
    ('films-cultes', 'Forrest Gump', 'Forrest Gump (film)', '§29'),
    ('films-cultes', 'Joker', 'Joker (film)', '§29'),
]

# Changement de sujet : la page visée n'est pas la bonne. Le moteur régénère
# description, pageviews et image (l'ancienne illustre un autre sujet).
CORRECTIONS_PAGE = [
    ('dieux-et-figures-mythologiques-grecques', 'Chronos', 'Cronos', 'Cronos',
     '§2.1 la carte visait le dieu primordial, pas le Titan'),
    ('inventions-importantes', 'Télégraphe', 'Télégraphe électrique', None, '§15.1'),
    ('inventions-importantes', 'Téléphone', 'Téléphone', None, '§15.1 pointait le groupe de rock'),
    ('inventions-importantes', 'Machine à écrire', 'Machine à écrire', None, '§15.1 pointait la pièce de Cocteau'),
    ('inventions-importantes', 'GPS', 'Global Positioning System', None, '§15.1'),
    ('inventions-importantes', 'Intelligence Artificielle', 'Intelligence artificielle', None, '§15.1'),
    ('oiseaux', 'Corbeau', 'Grand Corbeau', 'Grand Corbeau', '§18.1 terme ambigu'),
    ('films-cultes', 'Seigneur des Anneaux',
     'Le Seigneur des anneaux : La Communauté de l\'anneau',
     'Le Seigneur des anneaux : La Communauté de l\'anneau',
     '§30.1 une carte = un film'),
]

# §18.1 — deux cartes dont le document demande de VÉRIFIER la page avant de
# trancher. Elles sont traitées par le résolveur, pas décidées ici.
A_VERIFIER = [
    ('oiseaux', 'Aigle pêcheur', ['Balbuzard pêcheur', 'Pygargue vocifer'],
     '§18.1 nom ambigu, retenir la page réellement visée'),
    ('oiseaux', 'Pigeon voyageur', ['Tourte voyageuse', 'Pigeon voyageur'],
     '§18.1 l\'oiseau disparu emblématique est la Tourte voyageuse'),
]

# §22.1 — deux races décrites deux fois. On garde une carte, la plus notoire
# des deux gardant son image ; l'autre disparaît.
FUSIONS = [
    ('races-de-chien', ['Papillon', 'Épagneul nain continental'],
     'Épagneul nain continental (Papillon)', '§22.1 même race'),
    ('races-de-chien', ['Spitz nain', 'Spitz allemand'], 'Spitz allemand',
     '§22.1 le nain est une variété de l\'allemand'),
]

# §3.3 — les tags disent Espagne/Europe pour un libérateur vénézuélien.
CORRECTIONS_TAGS = [
    ('grands-dirigeants', 'Simón Bolívar',
     ['Venezuela', 'Amérique du Sud', 'XVIIIe siècle', 'XIXe siècle'], '§3.3'),
]

# ------------------------------------------------------------------ transferts
# Cartes qui changent de collection sans que leur collection source soit
# scindée (§3.1, §15.3, §16.1, §26.x, §27.1, §12.1).

TRANSFERTS = [
    ('grands-dirigeants', ['Gilgamesh', 'Didon'], 'mythologies-proche-orient',
     '§3.1 figures légendaires, pas des dirigeants historiques'),
    ('inventions-importantes', ['Tunnel sous la Manche'], 'monuments-emblematiques',
     '§15.3 ouvrage d\'art, pas une invention'),
    ('aviateurs-celebres',
     ['Valentina Terechkova', 'Michael Collins', 'Sally Ride', 'Eileen Collins',
      'Chris Hadfield', 'Felix Baumgartner'], 'pionniers-de-lextreme',
     '§16.1 vol spatial et saut extrême, pas de l\'aviation'),
]


# --------------------------------------------------------------------- lecture

def charger():
    secs = L.sections(L.MD.read_text(encoding='utf-8'))
    lignes = list(csv.DictReader(L.CSV.open(encoding='utf-8')))
    csv_par_nom = {}
    for r in lignes:
        csv_par_nom.setdefault(norm(L.nettoyer(r['nom_carte'])), r)
    return secs, lignes, csv_par_nom


def ajouts(secs, num, cible=None):
    """Puces d'ajout d'une section, éventuellement du seul bloc `cible`."""
    blocs = L.groupes_ajouts(secs[num])
    if cible is None:
        return [n for b in blocs for n in b['noms']]
    for b in blocs:
        if b['cible'].lower().startswith(cible.lower()):
            return b['noms']
    raise KeyError(f'§{num} : bloc d\'ajouts « {cible} » introuvable')


def suppressions(secs, num):
    for b in L.groupes_ajouts(secs[num], 'suppressions'):
        return b['noms']
    # forme tabulaire : première colonne
    rows = secs[num].tableau('suppressions')
    if rows:
        return [r[0] for r in rows]
    return []


def flechee(secs, num, cible):
    d = L.listes_flechees(secs[num]) or {}
    d.update(L.repartitions_vers(secs[num]))
    for k, v in d.items():
        if k.lower().startswith(cible.lower()):
            return v['noms']
    raise KeyError(f'§{num} : répartition « {cible} » introuvable')


def etiquetee(secs, num, bloc, etiquette):
    """Liste étiquetée d'un sous-bloc précis (sections 26 et 28)."""
    out = []
    for titre, lab, _, noms in L.listes_etiquetees(secs[num]):
        if titre.startswith(bloc) and lab.lower().startswith(etiquette.lower()):
            out += noms
    if not out:
        raise KeyError(f'§{num} bloc {bloc} : « {etiquette} » introuvable')
    return out


def raretes(secs, num, colonne_collection=False):
    """Tableau « Raretés à forcer » -> {nom: (rareté, collection|None)}."""
    out = {}
    for r in secs[num].tableau('rareté'):
        if len(r) < 2:
            continue
        nom = r[0]
        rar = r[-1].split()[0].lower() if r[-1] else ''
        col = r[1] if colonne_collection and len(r) >= 3 else None
        if rar in ('commune', 'rare', 'epique', 'mythique', 'legendaire'):
            out[nom] = (rar, col)
    return out


# ------------------------------------------------------------------- la cible
# Une entrée par collection d'arrivée. `prend` décrit d'où viennent les cartes
# existantes : une liste nominative, ou « reste » (tout ce que la collection
# source n'a pas donné ailleurs). `role_source` indique de quelle collection
# hériter la configuration de combat quand la collection est nouvelle.

def cibles(secs):
    A = lambda n, c=None: ajouts(secs, n, c)
    F = lambda n, c: flechee(secs, n, c)
    E = lambda n, b, e: etiquetee(secs, n, b, e)
    R = lambda n, **kw: raretes(secs, n, **kw)

    return [
        # ---- lot 1
        dict(slug='corps-celestes', nom='Corps celestes',
             prend=[('corps-celestes', 'reste')], ajouts=A(1), raretes=R(1)),
        dict(slug='dieux-et-figures-mythologiques-grecques',
             nom='Dieux et figures mythologiques grecques',
             prend=[('dieux-et-figures-mythologiques-grecques', 'reste')],
             ajouts=A(2), raretes=R(2)),
        dict(slug='souverains-et-conquerants', nom='Souverains et conquérants',
             role_source='grands-dirigeants',
             prend=[('grands-dirigeants', F(3, 'Souverains'))],
             ajouts=A(3, 'Souverains'), raretes=R(3, colonne_collection=True),
             filtre_rarete='A'),
        dict(slug='dirigeants-contemporains', nom="Dirigeants de l'ère contemporaine",
             role_source='grands-dirigeants',
             prend=[('grands-dirigeants', F(3, 'Dirigeants'))],
             ajouts=A(3, 'Dirigeants'), raretes=R(3, colonne_collection=True),
             filtre_rarete='B'),
        dict(slug='sites-antiques', nom='Sites antiques et archéologiques',
             role_source='monuments-emblematiques',
             prend=[('monuments-emblematiques', F(4, 'Sites'))],
             ajouts=A(4, 'Sites'), raretes=R(4)),
        dict(slug='monuments-emblematiques', nom='Monuments et architecture',
             prend=[('monuments-emblematiques', 'reste')],
             ajouts=A(4, 'Monuments'), raretes=R(4)),
        dict(slug='constellations', nom='Constellations',
             prend=[('constellations', 'reste')], ajouts=A(5)),
        # ---- lot 2
        dict(slug='empires-et-civilisations', nom='Empires et civilisations',
             role_source='dynasties-et-empires-historiques',
             prend=[('dynasties-et-empires-historiques', F(6, 'Empires'))],
             ajouts=A(6, 'Empires'), raretes=R(6, colonne_collection=True),
             filtre_rarete='A'),
        dict(slug='dynasties-regnantes', nom='Dynasties et maisons régnantes',
             role_source='dynasties-et-empires-historiques',
             prend=[('dynasties-et-empires-historiques', F(6, 'Dynasties'))],
             ajouts=A(6, 'Dynasties'), raretes=R(6, colonne_collection=True),
             filtre_rarete='B'),
        dict(slug='grandes-batailles-historiques', nom='Grandes batailles historiques',
             prend=[('grandes-batailles-historiques', 'reste')],
             ajouts=A(7), raretes=R(7)),
        dict(slug='grandes-guerres', nom='Grandes guerres',
             prend=[('grandes-guerres', 'reste')], ajouts=A(8), raretes=R(8)),
        dict(slug='dinosaures-celebres', nom='Dinosaures celebres',
             prend=[('dinosaures-celebres', 'reste')], ajouts=A(9, 'Dinosaures')),
        dict(slug='creatures-prehistoriques', nom='Créatures préhistoriques',
             role_source='dinosaures-celebres', prend=[],
             ajouts=L.puces_apres(secs[9], '9.4'), raretes=R(9)),
        dict(slug='grands-explorateurs', nom='Grands explorateurs',
             prend=[('grands-explorateurs', 'reste')],
             ajouts=A(10, 'Grands explorateurs'),
             raretes=R(10, colonne_collection=True), filtre_rarete='A'),
        dict(slug='pionniers-de-lextreme', nom="Pionniers de l'extrême",
             role_source='grands-explorateurs',
             prend=[('grands-explorateurs', F(10, 'Pionniers'))],
             ajouts=A(10, 'Pionniers'), raretes=R(10, colonne_collection=True),
             filtre_rarete='B'),
        # ---- lot 3
        dict(slug='auteurs-classiques', nom='Auteurs classiques',
             role_source='auteurs-celebres',
             prend=[('auteurs-celebres', F(11, 'Auteurs classiques'))],
             ajouts=A(11, 'Auteurs classiques'),
             raretes=R(11, colonne_collection=True), filtre_rarete='A'),
        dict(slug='auteurs-modernes', nom='Auteurs modernes et contemporains',
             role_source='auteurs-celebres', prend=[('auteurs-celebres', 'reste')],
             ajouts=A(11, 'Auteurs modernes'),
             raretes=R(11, colonne_collection=True), filtre_rarete='B'),
        dict(slug='scientifiques-celebres', nom='Scientifiques celebres',
             prend=[('scientifiques-celebres', 'reste')],
             ajouts=A(12, 'Scientifiques'), raretes=R(12, colonne_collection=True),
             filtre_rarete='A'),
        dict(slug='inventeurs-et-ingenieurs', nom='Inventeurs et ingénieurs',
             role_source='inventions-importantes',
             prend=[('scientifiques-celebres', L.bloc_puces(secs[12], '12.1')
                     + ['Léonard de Vinci (inventeur)'])],
             ajouts=A(12, 'Inventeurs'), raretes=R(12, colonne_collection=True),
             filtre_rarete='B'),
        dict(slug='grands-peintres', nom='Grands peintres',
             prend=[('grands-peintres', 'reste')], ajouts=A(13), raretes=R(13)),
        dict(slug='tableaux-celebres', nom='Tableaux celebres',
             prend=[('tableaux-celebres', 'reste')], ajouts=A(14), raretes=R(14)),
        # ---- lot 4
        dict(slug='inventions-importantes', nom='Inventions importantes',
             prend=[('inventions-importantes', 'reste')], ajouts=A(15), raretes=R(15)),
        dict(slug='aviateurs-celebres', nom='Aviateurs celebres',
             prend=[('aviateurs-celebres', 'reste')], ajouts=A(16), raretes=R(16)),
        # ---- lot 5
        dict(slug='mammiferes', nom='Mammiferes',
             prend=[('mammiferes', 'reste')], ajouts=A(17)),
        dict(slug='oiseaux', nom='Oiseaux', prend=[('oiseaux', 'reste')], ajouts=A(18)),
        dict(slug='reptiles-et-amphibiens', nom='Reptiles et amphibiens',
             prend=[('reptiles-et-amphibiens', 'reste')], ajouts=A(19)),
        dict(slug='poissons-et-vie-marine', nom='Poissons et vie marine',
             prend=[('poissons-et-vie-marine', 'reste')], ajouts=A(20)),
        dict(slug='insectes', nom='Insectes', prend=[('insectes', 'reste')], ajouts=A(21)),
        dict(slug='races-de-chien', nom='Races de chien',
             prend=[('races-de-chien', 'reste')], ajouts=A(22)),
        dict(slug='races-de-chat', nom='Races de chat', role_source='races-de-chien',
             prend=[], ajouts=L.toutes_puces(secs[23])),
        # ---- lot 6
        dict(slug='coupes-du-monde-fifa', nom='Coupes du monde FIFA',
             prend=[('coupes-du-monde-fifa', 'reste')], ajouts=['Coupe du monde 2026']),
        dict(slug='legendes-du-football', nom='Légendes du football',
             role_source='plus-grands-joueurs-de-football',
             prend=[('plus-grands-joueurs-de-football', F(25, 'Légendes'))],
             ajouts=A(25, 'Légendes')),
        dict(slug='football-ere-moderne', nom='Football, ère moderne',
             role_source='plus-grands-joueurs-de-football',
             prend=[('plus-grands-joueurs-de-football', 'reste')],
             ajouts=L.bloc_puces(secs[25], 'Ajouts')),
        dict(slug='creatures-et-legendes', nom='Creatures et legendes',
             prend=[('creatures-et-legendes', 'reste')], ajouts=A(27)),
        # ---- lot 8
        dict(slug='classiques-du-cinema', nom='Classiques du cinéma',
             role_source='films-cultes',
             prend=[('films-cultes', F(30, 'Classiques'))], ajouts=A(30, 'Classiques'),
             raretes=R(30, colonne_collection=True), filtre_rarete='A'),
        dict(slug='cinema-moderne', nom='Cinéma moderne', role_source='films-cultes',
             prend=[('films-cultes', 'reste')], ajouts=A(30, 'Cinéma moderne'),
             raretes=R(30, colonne_collection=True), filtre_rarete='B'),
        dict(slug='age-dor-du-jeu-video', nom="Âge d'or du jeu vidéo",
             role_source='jeux-video-cultes',
             prend=[('jeux-video-cultes', F(31, "Âge d'or"))],
             ajouts=A(31, "Âge d'or"), raretes=R(31, colonne_collection=True),
             filtre_rarete='A'),
        dict(slug='jeu-video-moderne', nom='Jeu vidéo moderne',
             role_source='jeux-video-cultes', prend=[('jeux-video-cultes', 'reste')],
             ajouts=A(31, 'Jeu vidéo moderne'), raretes=R(31, colonne_collection=True),
             filtre_rarete='B'),
    ] + mythologies(secs) + personnages(secs)


def mythologies(secs):
    """§26 — dix collections taillées dans `mythologies-du-monde-hors-grece`,
    plus les créatures que §27.1 leur rend."""
    src = 'mythologies-du-monde-hors-grece'
    rar = raretes(secs, 26, colonne_collection=True)
    plan = [
        ('26.2', 'mythologie-nordique', 'Mythologie nordique', 'nordique'),
        ('26.3', 'mythologie-egyptienne', 'Mythologie égyptienne', 'égyptienne'),
        ('26.4', 'mythologie-hindoue', 'Mythologie hindoue', 'hindoue'),
        ('26.5', 'mythologie-celtique', 'Mythologie celtique', 'celtique'),
        ('26.6', 'mythologies-asie-est', "Mythologies d'Asie de l'Est", "Asie de l'Est"),
        ('26.7', 'mythologies-mesoamericaines',
         'Mythologies mésoaméricaines et andines', 'mésoaméricaine'),
        ('26.8', 'mythologies-proche-orient',
         'Mythologies du Proche-Orient ancien', 'Proche-Orient'),
        ('26.9', 'mythologies-slaves', 'Mythologies slaves et baltes', 'slave'),
        ('26.10', 'mythologies-africaines', 'Mythologies africaines', 'africaine'),
        ('26.11', 'mythologies-oceanie-ameriques',
         'Mythologies océaniennes et amérindiennes', 'Océanie'),
    ]
    out = []
    for bloc, slug, nom, cle_rarete in plan:
        existantes, ajout, transferts = [], [], []
        for titre, lab, _, noms in L.listes_etiquetees(secs[26]):
            if not titre.startswith(bloc + ' '):
                continue
            l = lab.lower()
            if l.startswith('existante'):
                existantes += noms
            elif l.startswith('transfert'):
                transferts += noms
            else:                      # « Ajouts », ou un intitulé d'aire (26.8)
                ajout += noms
        prend = []
        if existantes:
            prend.append((src, existantes))
        if transferts:
            prend.append(('creatures-et-legendes', transferts))
        out.append(dict(slug=slug, nom=nom, role_source=src, prend=prend,
                        ajouts=ajout,
                        raretes={k: v for k, v in rar.items()
                                 if v[1] and cle_rarete.lower() in v[1].lower()}))
    return out


def personnages(secs):
    """§28 — six collections taillées dans `personnages-de-fiction-celebres`."""
    src = 'personnages-de-fiction-celebres'
    plan = [
        ('28.4', 'personnages-litterature', 'Personnages de littérature'),
        ('28.5', 'personnages-cinema-serie', 'Personnages de cinéma et de série'),
        ('28.6', 'personnages-bd-comics', 'Personnages de bande dessinée et de comics'),
        ('28.7', 'personnages-jeu-video', 'Personnages de jeu vidéo'),
        ('28.8', 'personnages-animation', "Personnages d'animation"),
        ('28.9', 'personnages-manga-anime', "Personnages de manga et d'anime"),
    ]
    out = []
    for bloc, slug, nom in plan:
        existantes, ajout = [], []
        for titre, lab, _, noms in L.listes_etiquetees(secs[28]):
            if not titre.startswith(bloc + ' '):
                continue
            l = lab.lower()
            if l.startswith('existante'):
                existantes += noms
            elif l.startswith('slug'):
                continue
            else:
                ajout += noms
        out.append(dict(slug=slug, nom=nom, role_source=src,
                        prend=[(src, existantes)], ajouts=ajout))
    return out


# --------------------------------------------------------- suppressions sèches
# Cartes retirées sans destination (§9.1, §15.3, §17.1, §18.2, §19.1, §20.2,
# §21.1, §25.3, §27.1, §28.2, §4.1).

def suppressions_seches(secs):
    out = {
        'dinosaures-celebres': suppressions(secs, 9),
        'inventions-importantes': ['Machine électrique'],        # §15.3
        'mammiferes': [r[0] for r in secs[17].tableau('suppressions')],
        'oiseaux': suppressions(secs, 18) ,
        'reptiles-et-amphibiens': suppressions(secs, 19),
        'poissons-et-vie-marine': suppressions(secs, 20),
        'insectes': suppressions(secs, 21),
        'plus-grands-joueurs-de-football': L.bloc_puces(secs[25], 'Suppressions'),
        'monuments-emblematiques': ['Table Mountain'],           # §4.1
        'personnages-de-fiction-celebres': ['Thor'],             # §28.2
        # §27.1 — déjà présentes chez les Grecs, on ne les duplique pas
        'creatures-et-legendes': ['Chimère', 'Hydre de Lerne', 'Minotaure', 'Pégase'],
    }
    return {k: v for k, v in out.items() if v}


def construire():
    secs, lignes_csv, csv_par_nom = charger()
    plan = {
        'renommages': [dict(zip(('slug', 'de', 'vers', 'raison'), r)) for r in RENOMMAGES],
        'corrections_page': [dict(zip(('slug', 'nom', 'titrePage', 'nouveau_nom', 'raison'), r))
                             for r in CORRECTIONS_PAGE],
        'a_verifier': [dict(zip(('slug', 'nom', 'hypotheses', 'raison'), r)) for r in A_VERIFIER],
        'fusions': [dict(zip(('slug', 'noms', 'vers', 'raison'), r)) for r in FUSIONS],
        'corrections_tags': [dict(zip(('slug', 'nom', 'tags', 'raison'), r))
                             for r in CORRECTIONS_TAGS],
        'transferts': [dict(zip(('de', 'noms', 'vers', 'raison'), r)) for r in TRANSFERTS],
        'suppressions': suppressions_seches(secs),
        'alias': ALIAS,
        'collections': [],
    }
    for c in cibles(secs):
        rar = c.get('raretes') or {}
        f = c.get('filtre_rarete')
        plan['collections'].append({
            'slug': c['slug'], 'nom': c['nom'],
            'role_source': c.get('role_source', c['slug']),
            'prend': [{'de': d, 'noms': n} if n != 'reste' else {'de': d, 'reste': True}
                      for d, n in c['prend']],
            'ajouts': c['ajouts'],
            'raretes_forcees': {k: v[0] for k, v in rar.items()
                                if f is None or v[1] is None or v[1] == f},
        })
    return plan, secs, csv_par_nom


def main():
    plan, secs, csv_par_nom = construire()
    cartes_cibles = sum(len(c['ajouts']) for c in plan['collections'])
    print(f"{len(plan['collections'])} collections cibles, "
          f"{cartes_cibles} cartes à créer")

    hors_csv = {}
    for c in plan['collections']:
        manque = [n for n in c['ajouts'] if norm(n) not in csv_par_nom]
        if manque:
            hors_csv[c['slug']] = manque
    total_hors = sum(len(v) for v in hors_csv.values())
    print(f'{total_hors} carte(s) absente(s) de l\'annexe CSV :')
    for slug, noms in hors_csv.items():
        print(f'   {slug} ({len(noms)}) : ' + ', '.join(noms[:6])
              + ('…' if len(noms) > 6 else ''))

    doublons = {}
    for c in plan['collections']:
        for n in c['ajouts']:
            doublons.setdefault(norm(n), []).append(c['slug'])
    rep = {k: v for k, v in doublons.items() if len(v) > 1}
    if rep:
        print(f'{len(rep)} nom(s) ajouté(s) dans plusieurs collections :')
        for k, v in list(rep.items())[:10]:
            print(f'   {k} -> {v}')

    if '--verifier' not in sys.argv:
        (ICI / 'plan_audit.json').write_text(
            json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
        print('plan_audit.json écrit')


if __name__ == '__main__':
    main()
