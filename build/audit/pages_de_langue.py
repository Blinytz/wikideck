#!/usr/bin/env python3
"""Illustre une carte de langue par une page de texte ecrite DANS la langue.

Le style est celui que l'utilisateur a choisi a la main pour les 28 premieres
langues : un gros plan de vrai texte, page imprimee ou manuscrite, qui remplit
toute la carte. Pour les langues restantes, on compose la page nous-memes.

Le texte est celui de la Declaration universelle des droits de l'homme, qui
existe dans presque toutes les langues : les traductions viennent du projet
« UDHR in Unicode » (depot d'Eric Muller, qui le maintient). Ce n'est donc
jamais un texte invente, et chaque langue a son vrai systeme d'ecriture.

La page est composee par Chrome sans fenetre, et non par la bibliotheque
d'images de Python : celle-ci ne sait pas lier les lettres du tamoul, du
thai ou de l'amharique. Chrome les compose correctement, dans les polices
Windows adaptees a chaque ecriture.

Usage : python pages_de_langue.py [--apercu] [<nom de carte>...]
        --apercu : ecrit dans le brouillon, sans toucher aux cartes
"""
import io, re, sys, json, html, random, subprocess, tempfile, urllib.request
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(RACINE / 'build'))
import images_lib as il

NOTES = RACINE / 'build' / 'notes_atelier.json'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
SOURCE = 'https://raw.githubusercontent.com/eric-muller/udhr/main/data/udhr/udhr_{}.xml'

# nom de carte -> (code UDHR, police, sens d'ecriture)
LANGUES = {
    # (code UDHR, polices CSS, sens d'ecriture)
    'Latin': ('lat', "'Georgia'", 'ltr'),
    'Grec ancien': ('ell_polytonic', "'Palatino Linotype','Cambria'", 'ltr'),
    'Sanskrit': ('san', "'Nirmala UI'", 'ltr'),
    'Hébreu': ('heb', "'David Libre','Times New Roman'", 'rtl'),
    'Arabe': ('arb', "'Arial','Segoe UI'", 'rtl'),
    'Langues chinoises': ('cmn_hant', "'Microsoft JhengHei','Microsoft YaHei','SimSun'", 'ltr'),
    'Mandarin standard': ('cmn_hans', "'SimSun','Microsoft YaHei'", 'ltr'),
    'Japonais': ('jpn', "'Yu Mincho','MS Mincho','Yu Gothic'", 'ltr'),
    'Coréen': ('kor', "'Batang','Malgun Gothic'", 'ltr'),
    'Hindi': ('hin', "'Nirmala UI'", 'ltr'),
    'Bengali': ('ben', "'Nirmala UI'", 'ltr'),
    'Ourdou': ('urd', "'Arial','Segoe UI'", 'rtl'),
    'Persan (langue)': ('pes_1', "'Arial','Segoe UI'", 'rtl'),
    'Turc': ('tur', "'Georgia'", 'ltr'),
    'Russe': ('rus', "'Georgia'", 'ltr'),
    'Polonais': ('pol', "'Georgia'", 'ltr'),
    'Allemand': ('deu_1996', "'Georgia'", 'ltr'),
    'Anglais': ('eng', "'Georgia'", 'ltr'),
    'Français': ('fra', "'Georgia'", 'ltr'),
    'Espagnol': ('spa', "'Georgia'", 'ltr'),
    'Portugais': ('por_PT', "'Georgia'", 'ltr'),
    'Italien': ('ita', "'Georgia'", 'ltr'),
    'Néerlandais': ('nld', "'Georgia'", 'ltr'),
    'Suédois': ('swe', "'Georgia'", 'ltr'),
    'Finnois': ('fin', "'Georgia'", 'ltr'),
    'Hongrois': ('hun', "'Georgia'", 'ltr'),
    'Basque': ('eus', "'Georgia'", 'ltr'),
    'Breton': ('bre', "'Georgia'", 'ltr'),
    'Gallois': ('cym', "'Georgia'", 'ltr'),
    'Irlandais': ('gle', "'Georgia'", 'ltr'),
    'Islandais': ('isl', "'Georgia'", 'ltr'),
    'Swahili': ('swh', "'Georgia'", 'ltr'),
    'Yoruba': ('yor', "'Cambria'", 'ltr'),
    'Zoulou': ('zul', "'Georgia'", 'ltr'),
    'Amharique': ('amh', "'Ebrima'", 'ltr'),
    'Haoussa': ('hau_NG', "'Cambria'", 'ltr'),
    'Quechua': ('quz', "'Georgia'", 'ltr'),
    'Guarani': ('gug', "'Cambria'", 'ltr'),
    'Nahuatl': ('nhn', "'Georgia'", 'ltr'),
    'Langues maories': ('mri', "'Georgia'", 'ltr'),
    'Hawaïen': ('haw', "'Cambria'", 'ltr'),
    'Espéranto': ('epo', "'Georgia'", 'ltr'),
    'Tamoul': ('tam', "'Nirmala UI'", 'ltr'),
    'Vietnamien': ('vie', "'Cambria'", 'ltr'),
    'Thaï': ('tha', "'Leelawadee UI'", 'ltr'),
    # grand complement du 26/09/2026
    'Catalan': ('cat', "'Georgia'", 'ltr'),
    'Occitan': ('oci_1', "'Georgia'", 'ltr'),
    'Grec moderne': ('ell_monotonic', "'Palatino Linotype','Cambria'", 'ltr'),
    'Ukrainien': ('ukr', "'Georgia'", 'ltr'),
    'Roumain': ('ron_2006', "'Georgia'", 'ltr'),
    'Tchèque': ('ces', "'Georgia'", 'ltr'),
    'Serbo-croate': ('srp_cyrl', "'Georgia'", 'ltr'),
    'Albanais': ('als', "'Georgia'", 'ltr'),
    'Yiddish': ('ydd', "'David Libre','Times New Roman'", 'rtl'),
    'Romani': ('rmn_1', "'Georgia'", 'ltr'),
    'Wolof': ('wol', "'Georgia'", 'ltr'),
    'Afrikaans': ('afr', "'Georgia'", 'ltr'),
    'Malgache': ('plt', "'Georgia'", 'ltr'),
    'Berbère': ('tzm_tfng', "'Ebrima'", 'ltr'),
    'Lingala': ('lin', "'Georgia'", 'ltr'),
    'Arménien': ('hye', "'Sylfaen'", 'ltr'),
    'Géorgien': ('kat', "'Sylfaen'", 'ltr'),
    'Kurde': ('kmr', "'Georgia'", 'ltr'),
    'Pachto': ('pbu', "'Arial','Segoe UI'", 'rtl'),
    'Tibétain': ('bod', "'Microsoft Himalaya'", 'ltr'),
    'Mongol': ('khk', "'Georgia'", 'ltr'),
    'Pendjabi': ('pan', "'Nirmala UI'", 'ltr'),
    'Télougou': ('tel', "'Nirmala UI'", 'ltr'),
    'Tagalog': ('tgl', "'Georgia'", 'ltr'),
    'Indonésien': ('ind', "'Georgia'", 'ltr'),
    'Khmer': ('khm', "'Khmer UI','Leelawadee UI'", 'ltr'),
    'Créole haïtien': ('hat_popular', "'Georgia'", 'ltr'),
    'Inuktitut': ('ike', "'Gadugi','Euphemia'", 'ltr'),
    'Navajo': ('nav', "'Cambria'", 'ltr'),
    'Cherokee': ('chr_cased', "'Gadugi'", 'ltr'),
    'Maya yucatèque': ('yua', "'Georgia'", 'ltr'),
    'Aymara': ('ayr', "'Georgia'", 'ltr'),
}


def texte_udhr(code):
    with urllib.request.urlopen(SOURCE.format(code), timeout=30) as r:
        xml = r.read().decode('utf-8')
    titre = re.search(r'<title>(.*?)</title>', xml, re.S)
    paras = [html.unescape(re.sub(r'<[^>]+>', '', p)).strip()
             for p in re.findall(r'<para>(.*?)</para>', xml, re.S)]
    paras = [p for p in paras if p]
    return (html.unescape(titre.group(1)).strip() if titre else ''), paras[:6]


PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#2a2320}}
.feuille{{position:absolute;left:{fx}px;top:{fy}px;width:940px;height:760px;
  transform:rotate({angle}deg);transform-origin:50% 50%;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(255,255,255,.35), transparent 60%),
    radial-gradient(ellipse at 80% 90%, rgba(120,90,50,.18), transparent 55%),
    linear-gradient(180deg,#f4ecd8,#ead9b8);
  box-shadow: inset 0 0 120px rgba(90,60,20,.35);
  padding:70px 90px;box-sizing:border-box;direction:{sens};
  font-family:{police},serif;color:#2b2118;}}
h1{{font-size:44px;margin:0 0 22px;font-weight:700;letter-spacing:.5px}}
p{{font-size:31px;line-height:1.42;margin:0 0 16px;text-align:justify}}
.grain{{position:absolute;inset:0;opacity:.18;mix-blend-mode:multiply;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>")}}
.ombre{{position:absolute;left:{dx}px;top:{dy}px;width:800px;height:600px;background:radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(0,0,0,.28) 100%)}}
</style></head><body><div class="feuille"><h1>{titre}</h1>{paras}</div>
<div class="grain"></div><div class="ombre"></div></body></html>"""


def composer(nom, code, police, sens, dossier):
    titre, paras = texte_udhr(code)
    rng = random.Random(nom)                  # meme carte, meme angle
    # La page est composee sur une table deux fois plus grande que la carte :
    # la carte en est le centre (identique a l'ancienne composition), et
    # l'atelier peut deplacer ou dezoomer le cadrage sans tomber dans le vide.
    page = PAGE.format(angle=round(rng.uniform(-3.5, 3.5), 2), sens=sens, police=police,
                       W=1600, H=1200, dx=400, dy=300, fx=340, fy=230,
                       titre=html.escape(titre),
                       paras=''.join(f'<p>{html.escape(p)}</p>' for p in paras))
    f_html = dossier / f'{code}.html'
    f_png = dossier / f'{code}.png'
    f_html.write_text(page, encoding='utf-8')
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                    f'--user-data-dir={dossier / "chrome"}', '--window-size=1600,1200',
                    f'--screenshot={f_png}', f_html.as_uri()],
                   capture_output=True, timeout=90)
    return Image.open(f_png).convert('RGB') if f_png.exists() else None


def main():
    apercu = '--apercu' in sys.argv
    noms = [a for a in sys.argv[1:] if not a.startswith('--')] or list(LANGUES)
    dossier = Path(tempfile.mkdtemp(prefix='pages_langue_'))
    brouillon = Path(r'C:\Users\flxjr\AppData\Local\Temp\claude'
                     r'\C--Users-flxjr-OneDrive-Documents-Ecosyst-me-Eclats'
                     r'\c09b28ae-d115-4d67-acb5-b72ec6b0313a\scratchpad')
    cartes = {c['nom']: c for c in json.loads(
        (RACINE / 'data' / 'langues-du-monde.json').read_text(encoding='utf-8'))['cartes']}
    sf = RACINE / 'build' / 'images_sources.json'
    sources = json.loads(sf.read_text(encoding='utf-8'))
    for nom in noms:
        code, police, sens = LANGUES[nom]
        try:
            img = composer(nom, code, police, sens, dossier)
        except Exception as e:
            print(f'  ✗ {nom} : {e}')
            continue
        if img is None:
            print(f'  ✗ {nom} : capture ratee')
            continue
        if apercu:
            img.save(brouillon / f'langue_{code}.png')
            print(f'  {nom:<18} apercu ecrit')
            continue
        c = cartes[nom]
        # la carte = le centre 800 x 600 ; la page entiere devient l'original,
        # avec un cadrage qui retombe exactement sur ce centre
        brut = io.BytesIO(); img.crop((400, 300, 1200, 900)).save(brut, 'PNG')
        for rel, octets in ((c['imageUrl'], il.to_full(brut.getvalue())),
                            (c['thumbUrl'], il.to_thumb(brut.getvalue()))):
            (RACINE / rel).write_bytes(octets)
        orig = RACINE / 'images' / 'originaux' / 'langues-du-monde' / (c['id'].split('_', 1)[1] + '.webp')
        orig.parent.mkdir(parents=True, exist_ok=True)
        img.save(orig, 'WEBP', quality=88)
        notes = json.loads(NOTES.read_text(encoding='utf-8'))
        if not (notes['cadrages'].get(c['id']) or {}).get('editeLe'):     # jamais une retouche
            notes['cadrages'][c['id']] = {'cx': 0.5, 'cy': 0.5, 'w': 0.5, 'original': True,
                                          'editeLe': 0, 'auto': True}
            NOTES.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
        sources[c['id']] = {'source': 'page-udhr', 'code': code}
        print(f'  {nom:<18} <- DUDH [{code}]')
    if not apercu:
        sf.write_text(json.dumps(sources, ensure_ascii=False, indent=0), encoding='utf-8')


if __name__ == '__main__':
    main()
