#!/usr/bin/env python3
"""Illustre les cartes d'edition olympique avec une photo de l'edition.

Une page d'edition n'expose que son embleme, qui est sous droits : la carte
reste donc vide. Commons, en revanche, a des photos libres de chaque edition,
rangees sous un titre stable en anglais, « 1952 Summer Olympics ».

Le script cherche donc `intitle:"<annee> Summer|Winter Olympics"` et prend le
premier fichier qui passe trois filtres : une vraie photo, pas un embleme ni
une carte de participation, et une taille lisible en vignette. Le choix reste
arbitraire parmi les photos de l'edition, donc la provenance est marquee
`choisie-faute-de-mieux` et la carte part dans la note a relire.

Usage : python images_jeux.py [--essai]
"""
import sys, re, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
import images_lib as il

SLUGS = {'jeux-olympiques': 'Summer', 'jeux-olympiques-hiver': 'Winter'}

# Ce qui n'illustre pas l'evenement : symboles, cartes, timbres, tableaux.
# Les motifs sont des PREFIXES, sans limite de mot a droite : « boycotting »,
# « stamps » et « countries » doivent tomber comme « boycott », « stamp » et
# « country ». Le premier jet fermait chaque motif par une limite de mot, et
# la carte des pays boycotteurs de 1976 est passee au travers.
ECARTER = re.compile(
    r'\b(logo|emblem|pictogram|poster|philatel|stamp|sheetlet|souvenir'
    r'|medal|boycot|participat|candidate cit|countr|team number|team size'
    r'|venue|calendar|coin|flag|map|route|bid book)', re.I)


def photo_edition(annee, saison):
    for requete in ('intitle:"%d %s Olympics"' % (annee, saison),
                    '"%d %s Olympics"' % (annee, saison)):
        d = il.api('commons.wikimedia.org', dict(
            action='query', list='search', srsearch=requete,
            srnamespace=6, srlimit=30))
        for h in (d or {}).get('query', {}).get('search', []):
            nom = h['title'].split(':', 1)[1]
            if not nom.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            if ECARTER.search(nom) or il.MAUVAIS_FICHIERS.search(nom):
                continue
            u = il.commons_thumb(nom)
            if not u:
                continue
            data = il.telecharger_image(u, min_cote=400, navigateur=False)
            if data:
                return nom, data
    return None, None


def main():
    essai = '--essai' in sys.argv
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}
    sources_f = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sources_f.read_text(encoding='utf-8'))

    faits, restent = 0, []
    for slug, saison in SLUGS.items():
        if slug not in par_slug:
            continue
        d = json.loads(par_slug[slug].read_text(encoding='utf-8'))
        for c in d['cartes']:
            if (RACINE / c['imageUrl']).exists():
                continue
            m = re.search(r'(\d{4})', c['titrePage'])
            if not m:
                restent.append(f"{slug} · {c['nom']}")
                continue
            nom, data = photo_edition(int(m.group(1)), saison)
            if not data:
                restent.append(f"{slug} · {c['nom']}")
                continue
            th, fu = il.to_thumb(data), il.to_full(data)
            if not (th and fu):
                restent.append(f"{slug} · {c['nom']}")
                continue
            print(f"  {c['nom']:<14} <- {nom[:64]}")
            faits += 1
            if essai:
                continue
            for rel, octets in ((c['imageUrl'], fu), (c['thumbUrl'], th)):
                p = RACINE / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(octets)
            sources[c['id']] = {'source': 'choisie-faute-de-mieux'}

    if not essai:
        sources_f.write_text(json.dumps(sources, ensure_ascii=False, indent=0),
                             encoding='utf-8')
        il.save_cache(force=True)
    print(f'{faits} illustree(s), {len(restent)} laissee(s)')
    for r in restent:
        print('  •', r)


if __name__ == '__main__':
    main()
