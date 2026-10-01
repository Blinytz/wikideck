# applique les choix des seules cartes encore sans image (jamais les retouchees)
for s in "$@"; do
  args=$(WIKIDECK_SANS_CACHE=1 PYTHONIOENCODING=utf-8 python -W ignore -c "
import sys,json; sys.path.insert(0,'.')
from candidats_images import cartes_sans_image
ch=json.load(open('choix_grand/$s.json',encoding='utf-8'))
print(' '.join('--seul '+c['id'] for c in cartes_sans_image('$s') if c['id'] in ch))")
  [ -n "$args" ] && WIKIDECK_SANS_CACHE=1 PYTHONIOENCODING=utf-8 python -W ignore appliquer_choix.py $s $args
done
