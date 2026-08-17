#!/usr/bin/env python3
"""Dernier recours pour les cartes que `fetch_images.py` laisse sans image.

Le pipeline écarte volontairement drapeaux, blasons et cartes de position :
sur une carte de personnage ou de monument, ce serait une illustration ratée.
Mais pour un État, un conflit ou une dynastie, c'est justement l'image que
l'encyclopédie propose, et souvent la seule. Cinq cartes restaient vides pour
cette raison — Union soviétique, Dynastie Shang, les deux guerres en cours,
Nergal.

On reprend donc l'image principale de la page SANS le filtre, fr puis en, et
on ne garde que ce qui passe le contrôle de taille habituel. Une carte
toujours vide après ça est signalée : consigne 10, aucune carte ne doit être
livrée sans image.

Second usage, `--reprendre-recherche` : reprendre les cartes illustrees par
la recherche d'images du web. C'est le dernier maillon de la chaine, et il se
trompe souvent de sujet — Horus s'y etait vu attribuer un plan du metro
parisien, Marduk un logo, Terraria une emission de television italienne. Quand
l'encyclopedie a une image de la page, meme ecartee par le filtre (drapeau,
carte, blason), elle vaut mieux : elle est au moins du bon sujet. La recherche
n'est conservee que pour les pages qui n'ont aucune image.

Usage : python images_manquantes.py [--essai] [--reprendre-recherche]
"""
import sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
import images_lib as il

# Quatre pages n'exposent aucune image principale exploitable en français.
# Plutot que de prendre au hasard la premiere image de la page — qui est,
# par ordre alphabetique, « Armenian cotton.jpg » pour l'URSS —, le fichier
# est choisi ici, et dit pourquoi.
CHOISIES = {
    # l'embleme d'Etat : c'est l'image que la carte d'un Etat appelle
    'Union des républiques socialistes soviétiques':
        ('commons', 'Flag of the Soviet Union.svg'),
    # un bronze rituel : l'objet par lequel la dynastie est connue, la page
    # anglaise ne proposant qu'une carte de territoire
    'Dynastie Shang': ('commons', '18th cent BC wine vessel.jpg'),
    # photographies de tete des pages anglaises correspondantes
    'Guerre civile syrienne':
        ('url', 'https://upload.wikimedia.org/wikipedia/commons/5/59/'
                'Bombed_out_vehicles_Aleppo.jpg'),
    # la page « An (dieu) » n'expose aucune image ; la stele de Shamash montre
    # le pantheon mesopotamien dont Anu fait partie
    'An (dieu)': ('commons', 'Tablet of Shamash.jpg'),
    'Guerre russo-ukrainienne':
        ('url', 'https://upload.wikimedia.org/wikipedia/commons/9/9c/'
                'Anti-terrorist_operation_in_eastern_Ukraine_%28War_Ukraine%29'
                '_%2827843153986%29.jpg'),
    # Lieux légendaires : ces pages n'ont pas d'image de tête, et la recherche
    # par nom leur donnait un téléphone pliant, un évêque et un fond d'écran
    # Alienware. Fichiers repérés un par un sur Commons.
    'Tour de Babel': ('commons', 'Pieter Bruegel the Elder - The Tower of '
                                 'Babel (Vienna) - Google Art Project - edited.jpg'),
    # « Cibola.jpg » sur Commons est un vapeur qui porte ce nom.
    # La marche de Coronado a la recherche des sept cites, elle, est du sujet.
    "Cités d'or": ('commons', 'Frederic Remington - Coronado sets out to the north.jpg'),
    'Mu (continent)': ('commons', 'Golden-age-mu-map.jpg'),
    'Kitej': ('commons', 'Kitezh.jpg'),
    'Shambhala (mythe)': ('commons', 'Shambhala.jpg'),
    'Pays de Pount': ('commons', "Relief of Hatshepsut's expedition to the "
                                 'Land of Punt by Σταύρος.jpg'),
}


def commons(titre):
    """Premier fichier de Commons dont le NOM contient le titre de la page.

    Dernier filet avant la recherche d'images generaliste, et bien plus sur
    qu'elle : le mediatheque de Wikipedia est thematisee, et un fichier
    nomme « Horus.svg » parle d'Horus, la ou une recherche web sur « Horus »
    rend un plan du metro parisien."""
    d = il.api('commons.wikimedia.org', dict(
        action='query', list='search', srsearch=f'intitle:"{titre}"',
        srnamespace=6, srlimit=8))
    for hit in ((d or {}).get('query') or {}).get('search', []):
        nom = hit['title'].split(':', 1)[-1]
        if il.MAUVAIS_FICHIERS.search(nom):
            continue
        if not nom.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.svg')):
            continue
        u = il.commons_thumb(nom)
        if u:
            return u
    return None


def choisie(titre):
    mode_valeur = CHOISIES.get(titre)
    if not mode_valeur:
        return None
    mode, valeur = mode_valeur
    return il.commons_thumb(valeur) if mode == 'commons' else valeur


def main():
    essai = '--essai' in sys.argv
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    sources_f = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sources_f.read_text(encoding='utf-8'))

    reprendre = '--reprendre-recherche' in sys.argv
    filtre = (sys.argv[sys.argv.index('--collection') + 1]
              if '--collection' in sys.argv else None)
    vides = []
    for c in idx['collections']:
        if filtre and c['slug'] != filtre:
            continue
        d = json.loads((RACINE / c['fichier']).read_text(encoding='utf-8'))
        for x in d['cartes']:
            venue_du_web = (sources.get(x['id']) or {}).get('source', '').startswith('bing')
            if not (RACINE / x['imageUrl']).exists() or (reprendre and venue_du_web):
                vides.append((c['slug'], x))
    print(f'{len(vides)} carte(s) à illustrer')
    if not vides:
        return 0

    titres = [x['titrePage'] for _, x in vides]
    fr = il.wiki_images_batch(titres, 'fr.wikipedia.org', filtrer=False)
    manquants = [t for t in titres if t not in fr]
    en_par_fr = il.langlinks_en(manquants) if manquants else {}
    en = il.wiki_images_batch(list(en_par_fr.values()), 'en.wikipedia.org',
                              filtrer=False) if en_par_fr else {}

    restent = []
    for slug, x in vides:
        url = (choisie(x['titrePage']) or fr.get(x['titrePage'])
               or en.get(en_par_fr.get(x['titrePage'], ''))
               or commons(x['titrePage']))
        data = il.telecharger_image(url, min_cote=300, navigateur=False) if url else None
        if not data:
            restent.append(f"{slug} · {x['nom']}")
            continue
        th, fu = il.to_thumb(data), il.to_full(data)
        if not (th and fu):
            restent.append(f"{slug} · {x['nom']}")
            continue
        print(f"  {slug:<30} {x['nom']:<28} <- {url.rsplit('/', 1)[-1][:52]}")
        if essai:
            continue
        for rel, octets in ((x['imageUrl'], fu), (x['thumbUrl'], th)):
            f = RACINE / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(octets)
        sources[x['id']] = {'source': 'wiki-sans-filtre'}

    if not essai:
        sources_f.write_text(json.dumps(sources, ensure_ascii=False, indent=0),
                             encoding='utf-8')
        il.save_cache(force=True)
    print(f"{len(vides) - len(restent)} illustrée(s) par l'encyclopédie, "
          f"{len(restent)} laissée(s) en l'état")
    for r in restent[:40]:
        print(' •', r)
    return 0 if reprendre else (1 if restent else 0)


if __name__ == '__main__':
    sys.exit(main())
