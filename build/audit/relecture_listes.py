#!/usr/bin/env python3
"""Page de relecture des listes Memo : une fiche par element, image comprise.

Lit les colonnes redigees (scratchpad/memo/liste_<slug>.json) et produit une
page HTML autonome (images incluses) ou les fiches a verifier passent en tete.

Usage : python relecture_listes.py <slug> [<slug>...]
"""
import sys, json, base64, html
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
MEMO = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
            r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
            r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad\memo')

COLONNES = {
    'philosophes': [('dates', 'Dates'), ('courant', 'Courant'), ('concepts', 'Concepts clés'),
                    ('oeuvres', 'Œuvres')],
    'tableaux-celebres': [('peintre', 'Peintre'), ('date', 'Date'), ('lieu', 'Conservé à'),
                          ('mouvement', 'Mouvement')],
    'plats-francais': [('region', 'Région'), ('ingredients', 'Ingrédients'), ('type', 'Type')],
}
ORDRE = ['legendaire', 'mythique', 'epique', 'rare', 'commune']
NIVEAU = {'commune': 'Facile', 'rare': 'Moyen', 'epique': 'Difficile',
          'mythique': 'Expert', 'legendaire': 'Expert'}


def vignette(c):
    p = RACINE / c['thumbUrl']
    return 'data:image/webp;base64,' + base64.b64encode(p.read_bytes()).decode() if p.exists() else ''


def page(sections):
    css = """
:root{--fond:#f6f4ef;--carte:#fff;--texte:#1d1b18;--doux:#6b665d;--trait:#e2ddd3;--alerte:#b4541a;--alerte-fond:#fdf0e6}
@media (prefers-color-scheme:dark){:root{--fond:#15140f;--carte:#1f1d18;--texte:#eeeae2;--doux:#a39e93;--trait:#34312a;--alerte:#f0a36b;--alerte-fond:#33241a}}
*{box-sizing:border-box}body{margin:0;background:var(--fond);color:var(--texte);font:15px/1.45 system-ui,sans-serif}
header{padding:24px 16px 8px;max-width:1100px;margin:auto}h1{margin:0 0 4px;font-size:24px}header p{margin:0;color:var(--doux)}
nav{position:sticky;top:0;background:var(--fond);border-bottom:1px solid var(--trait);padding:8px 16px;display:flex;gap:14px;flex-wrap:wrap;z-index:2}
nav a{color:var(--texte);text-decoration:none;font-weight:600}section{max-width:1100px;margin:auto;padding:8px 16px 32px}
h2{font-size:20px;margin:24px 0 4px}h2 small{color:var(--doux);font-weight:400;font-size:14px}
.fiche{display:grid;grid-template-columns:120px 1fr;gap:14px;background:var(--carte);border:1px solid var(--trait);border-radius:10px;padding:10px;margin:8px 0}
.fiche.doute{border-color:var(--alerte);background:var(--alerte-fond)}
.fiche img{width:120px;height:90px;object-fit:cover;border-radius:6px;background:#0002}
.nom{font-weight:700;font-size:16px}.niv{color:var(--doux);font-size:12px;margin-left:6px}
dl{display:grid;grid-template-columns:max-content 1fr;gap:2px 12px;margin:6px 0 0}dt{color:var(--doux)}dd{margin:0}
.note{color:var(--alerte);font-size:13px;margin-top:6px}
@media (max-width:560px){.fiche{grid-template-columns:1fr}.fiche img{width:100%;height:auto;aspect-ratio:4/3}}
"""
    nav = ''.join(f'<a href="#{s}">{html.escape(t)}</a>' for s, t, _ in sections)
    corps = ''.join(f'<section id="{s}">{h}</section>' for s, _, h in sections)
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Listes Mémo · relecture</title><style>{css}</style></head><body>'
            f'<header><h1>Listes Mémo · relecture</h1><p>Les fiches encadrées en orange sont '
            f'celles où le rédacteur a un doute : elles passent en tête de chaque liste.</p></header>'
            f'<nav>{nav}</nav>{corps}</body></html>')


def main():
    sections = []
    for slug in sys.argv[1:]:
        d = json.loads((RACINE / 'data' / f'{slug}.json').read_text(encoding='utf-8'))
        fiches = json.loads((MEMO / f'liste_{slug}.json').read_text(encoding='utf-8'))
        cartes = [c for c in d['cartes'] if c['id'] in fiches]
        cartes.sort(key=lambda c: (fiches[c['id']].get('confiance') != 'a_verifier',
                                   ORDRE.index(c['rarete']) if c['rarete'] in ORDRE else 9, c['nom']))
        doutes = sum(1 for c in cartes if fiches[c['id']].get('confiance') == 'a_verifier')
        blocs = [f'<h2>{html.escape(d["collection"])} <small>{len(cartes)} éléments · '
                 f'{doutes} à vérifier</small></h2>']
        for c in cartes:
            f = fiches[c['id']]
            doute = f.get('confiance') == 'a_verifier'
            lignes = ''.join(f'<dt>{html.escape(lib)}</dt><dd>{html.escape(f.get(k) or "·")}</dd>'
                             for k, lib in COLONNES[slug])
            note = f'<div class="note">{html.escape(f["note"])}</div>' if f.get('note') else ''
            blocs.append(f'<div class="fiche{" doute" if doute else ""}"><img src="{vignette(c)}" alt="">'
                         f'<div><span class="nom">{html.escape(c["nom"])}</span>'
                         f'<span class="niv">{NIVEAU.get(c["rarete"], "")}</span>'
                         f'<dl>{lignes}</dl>{note}</div></div>')
        sections.append((slug, d['collection'], ''.join(blocs)))
    sortie = MEMO / 'relecture.html'
    sortie.write_text(page(sections), encoding='utf-8')
    print(sortie, round(sortie.stat().st_size / 1e6, 1), 'Mo')


if __name__ == '__main__':
    main()
