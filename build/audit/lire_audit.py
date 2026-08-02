#!/usr/bin/env python3
"""Extraction des listes du document d'audit (audit_collections.md).

Le document est rédigé pour un humain : les listes y prennent quatre formes
(puces, paragraphes séparés par « · », tableaux, titres de groupe). Plutôt
qu'un parseur général — impossible à garder honnête sur 2 700 lignes — on
extrait ces quatre formes telles quelles et on vérifie systématiquement les
effectifs annoncés entre parenthèses. Toute liste dont le compte ne tombe pas
juste est signalée : c'est le garde-fou contre une lecture silencieusement
fausse.

Le sens (quelle liste va dans quelle collection, et pour quoi faire) est
décrit à part dans plan_audit.py — ici, on ne fait que lire.

Usage : python lire_audit.py          # rapport de lecture
        python lire_audit.py --json   # dump complet
"""
import sys, re, json, csv
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ICI = Path(__file__).resolve().parent
MD = ICI / 'audit_collections.md'
CSV = ICI / 'annexe_liens_wikipedia.csv'

# « Nom *(commentaire)* » -> « Nom » ; « **Nom** *(x)* » -> « Nom »
RE_COMMENT = re.compile(r'\s*\*\([^)]*\)\*\s*$')
RE_GRAS = re.compile(r'\*\*(.+?)\*\*')
RE_ITAL = re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)')
# « (48) » comme « (48 cartes) » : le document alterne les deux formes
EFFECTIF = r'\((\d+)(?:\s+cartes?)?\)'


# Le commentaire en italique d'une puce est souvent la clé de la page :
# « Les Trois Grâces *(Rubens)* » ne se résout pas sans « Rubens », fr.wikipedia
# ayant aussi celles de Raphaël et de Canova. On le retient donc au lieu de le
# jeter — d'où ce registre, rempli au fil du nettoyage.
COMMENTAIRES = {}


def nettoyer(s):
    s = s.strip()
    commentaire = RE_COMMENT.search(s)
    s = RE_COMMENT.sub('', s)
    s = RE_GRAS.sub(r'\1', s)
    s = RE_ITAL.sub(r'\1', s)
    s = re.sub(r'\s*\*\([^)]*\)\s*$', '', s)      # commentaire non fermé
    s = re.sub(r'`', '', s)
    # « Nanotyrannus — taxon contesté… », « Coyote → renommer … » : le document
    # accroche motif ou consigne au nom lui-même. Le nom s'arrête au tiret.
    s = re.split(r'\s+[—→]\s+', s)[0]
    s = s.strip(' .·')
    if commentaire and s:
        COMMENTAIRES.setdefault(s, commentaire.group(0).strip(' *()'))
    return s


def noms_dune_ligne(ligne):
    """Paragraphe « A · B · C » -> [A, B, C]."""
    return [n for n in (nettoyer(x) for x in ligne.split('·')) if n]


class Section:
    """Un chapitre « # N. TITRE » du document."""

    def __init__(self, numero, titre, lignes):
        self.numero, self.titre, self.lignes = numero, titre, lignes
        self.slug = None
        m = re.search(r'\*\*Slug :\*\*\s*`([^`]+)`', '\n'.join(lignes))
        if m:
            self.slug = m.group(1)
        self.blocs = self._blocs()

    def _blocs(self):
        """{titre de sous-titre (## ou ###) : [lignes]} dans l'ordre."""
        blocs, courant, cle = [], [], None
        for l in self.lignes:
            if re.match(r'^#{2,4} ', l):
                if cle is not None:
                    blocs.append((cle, courant))
                cle, courant = l.lstrip('# ').strip(), []
            else:
                courant.append(l)
        if cle is not None:
            blocs.append((cle, courant))
        return blocs

    def puces(self, filtre):
        """Puces « - X » de tous les blocs dont le titre contient `filtre`."""
        out = []
        for titre, lignes in self.blocs:
            if filtre.lower() not in titre.lower():
                continue
            out += [nettoyer(l[2:]) for l in lignes if l.startswith('- ')]
        return out

    def tableau(self, filtre):
        """Lignes d'un tableau markdown -> [[cellules]] (en-tête exclu)."""
        for titre, lignes in self.blocs:
            if filtre.lower() not in titre.lower():
                continue
            rows = []
            for l in lignes:
                if not l.startswith('|') or set(l) <= set('|-: '):
                    continue
                cells = [nettoyer(c) for c in l.strip('|').split('|')]
                rows.append(cells)
            if rows:
                return rows[1:]          # sans l'en-tête
        return []


def sections(texte):
    out, courant, entete = [], [], None
    for l in texte.splitlines():
        m = re.match(r'^# (\d+)\. (.+)$', l)
        if m:
            if entete:
                out.append(Section(entete[0], entete[1], courant))
            entete, courant = (int(m.group(1)), m.group(2)), []
        elif entete:
            courant.append(l)
    if entete:
        out.append(Section(entete[0], entete[1], courant))
    return {s.numero: s for s in out}


def listes_flechees(sec):
    """« ### → Collection (n) » suivi d'un paragraphe « A · B · C »."""
    out = {}
    for titre, lignes in sec.blocs:
        m = re.match(r'^→\s*(.+?)\s*' + EFFECTIF + r'$', titre)
        if not m:
            continue
        noms = []
        for l in lignes:
            if l.strip() and not l.startswith(('>', '|', '#')):
                noms += noms_dune_ligne(l)
        out[m.group(1)] = {'attendu': int(m.group(2)), 'noms': noms}
    return out


def repartitions_vers(sec):
    """« ## X.Y Répartition … vers <Cible> (n) » + paragraphe « A · B · C ».

    Variante de `listes_flechees` employée par les sections 25, 30 et 31."""
    out = {}
    for titre, lignes in sec.blocs:
        m = re.match(r'^\d+\.\d+\s+Répartition.*?\bvers\s+(.+?)\s*' + EFFECTIF + r'$',
                     titre, re.I)
        if not m:
            continue
        noms = []
        for l in lignes:
            if ' · ' in l and not l.startswith(('|', '>', '#')):
                noms += noms_dune_ligne(l)
        out[m.group(1)] = {'attendu': int(m.group(2)), 'noms': noms}
    return out


def groupes_ajouts(sec, filtre='ajouts'):
    """« ## X.Y Ajouts — Collection (n) » puis « ### Groupe (n) » + puces.

    Retourne [{cible, attendu, noms}] — cible = ce qui suit « — », sinon ''."""
    out, courant = [], None
    for titre, lignes in sec.blocs:
        m = re.match(r'^\d+\.\d+\s+' + filtre + r'\b(?:\s*—\s*(.+?))?\s*(?:' + EFFECTIF + r')?$',
                     titre, re.I)
        if m:
            courant = {'cible': (m.group(1) or '').strip(),
                       'attendu': int(m.group(2)) if m.group(2) else None,
                       'noms': []}
            out.append(courant)
        elif courant is None or re.match(r'^\d+\.\d+\s', titre):
            courant = None                      # on a quitté le bloc Ajouts
        puces = [nettoyer(l[2:]) for l in lignes if l.startswith('- ')]
        if courant is not None:
            courant['noms'] += puces
            # certains ajouts sont donnés en paragraphe « A · B · C »
            if not puces:
                for l in lignes:
                    if ' · ' in l and not l.startswith(('|', '>', '*')):
                        courant['noms'] += noms_dune_ligne(l)
    return [b for b in out if b['noms']]


# « **Ajouts (23) :** A · B » et « *Comics américains (13)* — A · B » :
# les deux formes de liste étiquetée en ligne des sections 26 et 28.
RE_ETIQ = re.compile(r'^(?:\*\*(?P<l1>[^*]+?)\s*(?:\((?P<n1>\d+)\))?\s*:\*\*'
                     r'|\*(?P<l2>[^*]+?)\s*\((?P<n2>\d+)\)\*\s*—)\s*(?P<reste>.*)$')


def listes_etiquetees(sec, etiquette=None):
    """[(titre du bloc, étiquette, attendu, [noms])] dans l'ordre du document.

    `etiquette` filtre sur le début du libellé (« Ajouts », « Existantes »…)."""
    out = []
    for titre, lignes in sec.blocs:
        for l in lignes:
            m = RE_ETIQ.match(l.strip())
            if not m:
                continue
            lab = (m.group('l1') or m.group('l2') or '').strip()
            n = m.group('n1') or m.group('n2')
            noms = noms_dune_ligne(m.group('reste'))
            if not noms:
                continue
            if etiquette and not lab.lower().startswith(etiquette.lower()):
                continue
            out.append((titre, lab, int(n) if n else None, noms))
    return out


def paragraphes_gras(sec, etiquette):
    """Compatibilité : listes_etiquetees sans le libellé."""
    return [(t, n, noms) for t, _, n, noms in listes_etiquetees(sec, etiquette)]


def toutes_puces(sec):
    return [nettoyer(l[2:]) for _, lignes in sec.blocs
            for l in lignes if l.startswith('- ')]


def puces_apres(sec, titre_depart):
    """Puces des blocs « ### » qui suivent un bloc « ## X.Y … » donné.

    Sert aux sections où la liste d'ajouts n'a pas d'en-tête « Ajouts » à elle
    (nouvelles collections des sections 9.4 et 23)."""
    noms, actif = [], False
    for titre, lignes in sec.blocs:
        if titre_depart.lower() in titre.lower():
            actif = True
            continue
        if actif and re.match(r'^\d+\.\d+\s', titre):
            break                                # bloc « ## » suivant : on sort
        if actif:
            noms += [nettoyer(l[2:]) for l in lignes if l.startswith('- ')]
    return noms


def lire_csv():
    rows = list(csv.DictReader(CSV.open(encoding='utf-8')))
    par_nom = {}
    for r in rows:
        par_nom.setdefault(nettoyer(r['nom_carte']), []).append(r)
    return rows, par_nom


def main():
    secs = sections(MD.read_text(encoding='utf-8'))
    rows, par_nom = lire_csv()
    rapport, anomalies = [], []

    rapport.append(f'{len(secs)} sections, {len(rows)} lignes de CSV\n')
    for n, s in sorted(secs.items()):
        rapport.append(f'== {n}. {s.titre}' + (f'  [{s.slug}]' if s.slug else ''))
        for cible, d in listes_flechees(s).items():
            ok = len(d['noms']) == d['attendu']
            rapport.append(f'   répartition → {cible} : {len(d["noms"])}/{d["attendu"]}'
                           + ('' if ok else '   ⚠'))
            if not ok:
                anomalies.append(f'{n}. répartition {cible} : '
                                 f'{len(d["noms"])} lus pour {d["attendu"]} annoncés')
        for b in groupes_ajouts(s):
            att = b['attendu']
            ok = att is None or len(b['noms']) == att
            rapport.append(f'   ajouts {b["cible"] or "(section)"} : '
                           f'{len(b["noms"])}/{att}' + ('' if ok else '   ⚠'))
            if not ok:
                anomalies.append(f'{n}. ajouts {b["cible"]} : '
                                 f'{len(b["noms"])} lus pour {att} annoncés')
            inconnus = [x for x in b['noms'] if x not in par_nom]
            if inconnus:
                anomalies.append(f'{n}. absents du CSV ({len(inconnus)}) : '
                                 + ', '.join(inconnus[:8])
                                 + ('…' if len(inconnus) > 8 else ''))
        for sup in groupes_ajouts(s, 'suppressions'):
            rapport.append(f'   suppressions : {len(sup["noms"])}/{sup["attendu"]}')

    print('\n'.join(rapport))
    print('\n---- anomalies ----')
    for a in anomalies:
        print(' •', a)
    print(f'{len(anomalies)} anomalie(s)')

    if '--json' in sys.argv:
        (ICI / 'lecture_audit.json').write_text(json.dumps(
            {str(n): {'titre': s.titre, 'slug': s.slug,
                      'repartitions': listes_flechees(s),
                      'ajouts': groupes_ajouts(s)}
             for n, s in secs.items()}, ensure_ascii=False, indent=1), encoding='utf-8')
        print('lecture_audit.json écrit')


if __name__ == '__main__':
    main()


def bloc_puces(sec, prefixe):
    """Puces d'un bloc « ### <prefixe>… » — sections 25.3 et suivantes, où la
    liste n'a pas d'en-tête « ## X.Y » à elle."""
    for titre, lignes in sec.blocs:
        if titre.lower().startswith(prefixe.lower()):
            noms = [nettoyer(l[2:]) for l in lignes if l.startswith('- ')]
            if noms:
                return noms
            for l in lignes:
                if ' · ' in l and not l.startswith(('|', '>', '#')):
                    noms += noms_dune_ligne(l)
            if noms:
                return noms
    return []
