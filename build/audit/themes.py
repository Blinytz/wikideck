#!/usr/bin/env python3
"""Grands themes des collections (champ « theme » de data/collections.json).

L'atelier groupe ses filtres et sa grille par theme, dans l'ordre de THEMES.
Rejouable : python build/audit/themes.py (signale toute collection sans theme).
"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
RACINE = Path(__file__).resolve().parent.parent.parent

THEMES = {
    'Histoire et politique': ['souverains-et-conquerants', 'dirigeants-contemporains', 'presidents-des-etats-unis',
        'monarques-anglais-et-britanniques', 'papes', 'dynasties-regnantes', 'empires-et-civilisations',
        'grandes-batailles-historiques', 'grandes-guerres', 'traites-et-textes-fondateurs', 'figures-emancipation',
        'figures-resistance', 'organisations-internationales', 'crises-economiques', 'monnaies-historiques',
        'grands-explorateurs'],
    'Géographie': ['villes-du-monde', 'iles', 'montagnes-et-volcans', 'fleuves-mers-et-oceans', 'lacs', 'deserts',
        'regions-francaises', 'micro-etats', 'monuments-emblematiques', 'merveilles-du-monde', 'sites-antiques', 'langues-du-monde',
        'monnaies-du-monde'],
    'Sciences et techniques': ['scientifiques-celebres', 'inventeurs-et-ingenieurs', 'inventions-importantes',
        'elements-chimiques', 'theoremes-et-lois', 'corps-humain', 'maladies-et-epidemies', 'corps-celestes',
        'constellations', 'conquete-spatiale', 'astronautes-et-cosmonautes', 'aviateurs-celebres',
        'pionniers-de-lextreme', 'vehicules-celebres', 'noeuds'],
    'Nature': ['mammiferes', 'oiseaux', 'reptiles-et-amphibiens', 'poissons-et-vie-marine', 'insectes',
        'dinosaures-celebres', 'creatures-prehistoriques', 'races-de-chien', 'races-de-chat', 'races-de-cheval',
        'arbres', 'fleurs', 'champignons', 'plantes-cultivees', 'mineraux-et-pierres'],
    'Arts': ['grands-peintres', 'tableaux-celebres', 'sculptures-celebres', 'photographies-celebres', 'architectes',
        'styles-architecturaux', 'mode-et-couturiers', 'grands-compositeurs', 'oeuvres-musicales',
        'musique-populaire', 'instruments-de-musique'],
    'Lettres et pensée': ['auteurs-classiques', 'auteurs-modernes', 'oeuvres-litteraires', 'personnages-litterature',
        'mouvements-litteraires', 'genres-litteraires', 'philosophes'],
    'Religions et mythologies': ['figures-religieuses', 'religions-du-monde', 'textes-sacres', 'fetes-religieuses',
        'croyances-et-notions-sacrees', 'dieux-et-figures-mythologiques-grecques', 'mythologie-nordique',
        'mythologie-egyptienne', 'mythologie-hindoue', 'mythologie-celtique', 'mythologie-finnoise',
        'mythologies-asie-est', 'mythologies-mesoamericaines', 'mythologies-proche-orient', 'mythologies-slaves',
        'mythologies-africaines', 'mythologies-oceanie-ameriques', 'creatures-et-legendes', 'lieux-legendaires',
        'objets-mythiques', 'evenements-mythiques', 'vehicules-mythiques'],
    'Écrans et jeux': ['classiques-du-cinema', 'cinema-moderne', 'realisateurs', 'acteurs-et-actrices',
        'series-televisees', 'festivals-et-recompenses-cinema', 'personnages-cinema-serie', 'personnages-animation',
        'personnages-bd-comics', 'personnages-manga-anime', 'age-dor-du-jeu-video', 'jeu-video-moderne',
        'personnages-jeu-video', 'jeux-de-societe'],
    'Sport': ['legendes-du-sport', 'legendes-du-football', 'football-ere-moderne', 'coupes-du-monde-fifa',
        'jeux-olympiques', 'jeux-olympiques-hiver', 'champions-olympiques', 'pilotes-f1-champions-du-monde',
        'disciplines-sportives', 'grandes-competitions'],
    'Gastronomie': ['plats-francais', 'cuisines-du-monde', 'fromages', 'cepages'],
}

def main():
    f = RACINE / 'data' / 'collections.json'
    idx = json.loads(f.read_text(encoding='utf-8'))
    theme_de = {s: t for t, ss in THEMES.items() for s in ss}
    ordre = {s: i for i, s in enumerate(s for ss in THEMES.values() for s in ss)}
    sans = []
    for e in idx['collections']:
        e['theme'] = theme_de.get(e['slug'])
        if not e['theme']:
            sans.append(e['slug'])
    idx['themes'] = list(THEMES)
    idx['collections'].sort(key=lambda e: ordre.get(e['slug'], 10 ** 6))
    f.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding='utf-8')
    inconnus = [s for s in theme_de if s not in {e['slug'] for e in idx['collections']}]
    print(len(idx['collections']), 'collections ; sans theme :', sans, '; slugs inconnus :', inconnus)

if __name__ == '__main__':
    main()
