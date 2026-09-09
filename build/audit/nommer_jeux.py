#!/usr/bin/env python3
"""Renomme les cartes d'edition olympique sur le modele ville + annee.

« Ete 1972 » devient « JO Munich 1972 », « Hiver 1992 » devient « JO d'hiver
Albertville 1992 ». Seul le `nom` change : l'`id` est derive du titre de page,
donc les fichiers image, les cadrages et les entrees de provenance ne bougent
pas.

La ville est ecrite ici a la main, mais elle n'est pas crue sur parole : le
script verifie que chaque ville apparait bien dans le resume de la page, et
refuse d'ecrire si une seule ne colle pas. Une table de 55 lignes tapee de
memoire contient toujours une faute, et une carte qui annonce la mauvaise
ville est pire qu'une carte mal nommee.

Usage : python nommer_jeux.py [--essai]
"""
import sys, json, re, unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent

ETE = {
    1896: 'Athènes', 1900: 'Paris', 1904: 'Saint-Louis', 1908: 'Londres',
    1912: 'Stockholm', 1920: 'Anvers', 1924: 'Paris', 1928: 'Amsterdam',
    1932: 'Los Angeles', 1936: 'Berlin', 1948: 'Londres', 1952: 'Helsinki',
    1956: 'Melbourne', 1960: 'Rome', 1964: 'Tokyo', 1968: 'Mexico',
    1972: 'Munich', 1976: 'Montréal', 1980: 'Moscou', 1984: 'Los Angeles',
    1988: 'Séoul', 1992: 'Barcelone', 1996: 'Atlanta', 2000: 'Sydney',
    2004: 'Athènes', 2008: 'Pékin', 2012: 'Londres', 2016: 'Rio de Janeiro',
    2020: 'Tokyo', 2024: 'Paris',
}
HIVER = {
    1924: 'Chamonix', 1928: 'Saint-Moritz', 1932: 'Lake Placid',
    1936: 'Garmisch-Partenkirchen', 1948: 'Saint-Moritz', 1952: 'Oslo',
    1956: "Cortina d'Ampezzo", 1960: 'Squaw Valley', 1964: 'Innsbruck',
    1968: 'Grenoble', 1972: 'Sapporo', 1976: 'Innsbruck', 1980: 'Lake Placid',
    1984: 'Sarajevo', 1988: 'Calgary', 1992: 'Albertville',
    1994: 'Lillehammer', 1998: 'Nagano', 2002: 'Salt Lake City',
    2006: 'Turin', 2010: 'Vancouver', 2014: 'Sotchi', 2018: 'Pyeongchang',
    2022: 'Pékin', 2026: 'Milan-Cortina',
}
# La graphie du resume ne colle pas toujours a celle qu'on veut afficher.
# A gauche ce qu'on ecrit sur la carte, a droite ce qu'on accepte de trouver
# dans le resume comme preuve que la ville est la bonne.
PREUVES = {
    'Saint-Louis': ['saint-louis', 'st. louis'],
    'Saint-Moritz': ['saint-moritz', 'st-moritz', 'st. moritz'],
    'Squaw Valley': ['squaw valley', 'olympic valley'],
    'Milan-Cortina': ['milan', 'cortina'],
    'Pyeongchang': ['pyeongchang', 'pyongchang'],
    'Mexico': ['mexico'],
    'Sotchi': ['sotchi'],
}


def sans_accent(s):
    s = unicodedata.normalize('NFD', s)
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()


def main():
    essai = '--essai' in sys.argv
    idx = json.loads((RACINE / 'data' / 'collections.json').read_text(encoding='utf-8'))
    par_slug = {c['slug']: RACINE / c['fichier'] for c in idx['collections']}

    lots = [('jeux-olympiques', ETE, 'JO {ville} {annee}'),
            ('jeux-olympiques-hiver', HIVER, "JO d'hiver {ville} {annee}")]
    ecrits, ecarts = {}, []

    for slug, villes, motif in lots:
        d = json.loads(par_slug[slug].read_text(encoding='utf-8'))
        for c in d['cartes']:
            m = re.search(r'(\d{4})', c['titrePage'])
            if not m:
                ecarts.append(f"{slug} · {c['nom']} : pas d'annee dans le titre")
                continue
            annee = int(m.group(1))
            ville = villes.get(annee)
            if not ville:
                ecarts.append(f'{slug} · {annee} : ville inconnue de la table')
                continue
            # controle : la ville doit apparaitre dans le resume de la page
            resume = sans_accent(c.get('description', ''))
            preuves = [sans_accent(p) for p in PREUVES.get(ville, [ville])]
            if not any(p in resume for p in preuves):
                ecarts.append(f'{slug} · {annee} : « {ville} » absente du resume')
                continue
            c['nom'] = motif.format(ville=ville, annee=annee)
        # Tri par annee, pas par titre : « Jeux olympiques de 1896 » et
        # « Jeux olympiques d'ete de 1924 » ne se suivent pas alphabetiquement,
        # et la collection d'ete commencait donc en 1924 pour finir en 1920.
        d['cartes'].sort(key=lambda c: int(re.search(r'(\d{4})', c['titrePage']).group(1)))
        for i, c in enumerate(d['cartes'], 1):
            c['numero'] = i
        ecrits[slug] = d

    if ecarts:
        print(f'{len(ecarts)} controle(s) en echec, rien ecrit :')
        for e in ecarts:
            print('  ✗', e)
        return 1

    for slug, d in ecrits.items():
        print(f'  {slug:<24} ' + ', '.join(c['nom'] for c in d['cartes'][:3])
              + ' … ' + d['cartes'][-1]['nom'])
        if not essai:
            par_slug[slug].write_text(json.dumps(d, ensure_ascii=False),
                                      encoding='utf-8')
    print('[essai] rien écrit' if essai
          else f'{sum(len(d["cartes"]) for d in ecrits.values())} cartes renommees')
    return 0


if __name__ == '__main__':
    sys.exit(main())
