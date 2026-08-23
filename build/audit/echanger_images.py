#!/usr/bin/env python3
"""Échange les images de deux cartes (note atelier n1786210673307).

Ulysse et Thésée portaient l'illustration l'un de l'autre. Ce qui suit l'image
doit suivre avec elle : les trois fichiers (full, vignette, original), le
cadrage — qui décrit comment CETTE image est recadrée, pas la carte — et
l'entrée de provenance.

Usage : python echanger_images.py <id carte A> <id carte B> [--essai]
"""
import sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
RACINE = Path(__file__).resolve().parent.parent.parent


def chemins(cid):
    col, slug = cid.split('_', 1)
    return {rep: RACINE / 'images' / rep / col / f'{slug}.webp'
            for rep in ('full', 'thumbs', 'originaux')}


def main():
    ids = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(ids) != 2:
        sys.exit('deux identifiants de carte attendus')
    a, b = ids
    essai = '--essai' in sys.argv

    ca, cb = chemins(a), chemins(b)
    for rep in ('full', 'thumbs', 'originaux'):
        fa, fb = ca[rep], cb[rep]
        if not fa.exists() and not fb.exists():
            continue
        print(f'  {rep:<10} {"<->" if fa.exists() and fb.exists() else "->"} '
              f'{fa.name} / {fb.name}')
        if essai:
            continue
        tmp = fa.with_suffix('.echange')
        if fa.exists():
            fa.replace(tmp)
        if fb.exists():
            fb.replace(fa)
        if tmp.exists():
            tmp.replace(fb)

    fn = RACINE / 'build' / 'notes_atelier.json'
    notes = json.loads(fn.read_text(encoding='utf-8'))
    cad = notes.get('cadrages', {})
    va, vb = cad.get(a), cad.get(b)
    for cle, val in ((a, vb), (b, va)):
        if val is None:
            cad.pop(cle, None)
        else:
            cad[cle] = val
    print(f'  cadrage    {"oui" if va else "aucun"} <-> {"oui" if vb else "aucun"}')

    fs = RACINE / 'build' / 'images_sources.json'
    src = json.loads(fs.read_text(encoding='utf-8'))
    sa, sb = src.get(a), src.get(b)
    for cle, val in ((a, sb), (b, sa)):
        if val is None:
            src.pop(cle, None)
        else:
            src[cle] = val

    if essai:
        print('[essai] rien écrit')
        return
    fn.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding='utf-8')
    fs.write_text(json.dumps(src, ensure_ascii=False, indent=0), encoding='utf-8')
    print('échangé')


if __name__ == '__main__':
    main()
