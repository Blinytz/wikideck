// Carte v3 : un seul composant pour la collection, la fiche et l'ouverture.
// Le dos est identique pour toutes les raretés : rien ne fuit avant le retournement.

export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export const RARETES = ['commune', 'rare', 'epique', 'mythique', 'legendaire', 'pantheon'];
export const NOMS = { commune: 'Commune', rare: 'Rare', epique: 'Épique', mythique: 'Mythique', legendaire: 'Légendaire', pantheon: 'Panthéon' };
export const ICONES = { commune: 'ph-circle', rare: 'ph-diamond', epique: 'ph-star-four', mythique: 'ph-sparkle', legendaire: 'ph-crown-simple', pantheon: 'ph-sun-horizon' };

export function htmlDos() {
  return `<div class="k-dos"><div class="k-mono">W</div></div>`;
}

export function htmlCarte(c, { dos = false, neuve = false, total = c.total, image = 'thumb', attrs = '' } = {}) {
  const src = (image === 'full' ? c.imageUrl : c.thumbUrl) + (c.imgV ? `?v=${c.imgV}` : '');
  const num = c.numero != null ? `<span class="k-num">${String(c.numero).padStart(3, '0')}${total ? `<small>/${total}</small>` : ''}</span>` : '<span></span>';
  return `<div class="k r-${c.rarete}${dos ? ' dos' : ''}" data-id="${esc(c.id)}" style="--img:url('${esc(src)}');--rar:var(--r-${c.rarete})" ${attrs}>
  <div class="k-in">
    <div class="k-face">
      <div class="k-fond"></div>
      <div class="k-art"><img src="${esc(src)}" alt="" loading="lazy" decoding="async" onerror="this.remove()"><span class="k-init">${esc([...c.nom][0] ?? '?')}</span></div>
      <div class="k-holo"></div>
      <div class="k-haut">${num}<span class="k-ico"><i class="ph-fill ${ICONES[c.rarete]}"></i></span></div>
      <div class="k-bas">
        <div class="k-col">${esc(c.collection)}</div>
        <div class="k-nom">${esc(c.nom)}</div>
        <div class="k-pied"><span class="k-rarnom">${NOMS[c.rarete]}</span><span class="k-pv">${c.pv}<small>PV</small></span></div>
      </div>
      <div class="k-glare"></div>
      <div class="k-cadre"></div>
    </div>
    ${htmlDos()}
  </div>
  ${neuve ? '<span class="k-neuve">Nouvelle</span>' : ''}
</div>`;
}

// Inclinaison 3D au doigt ou à la souris ; revient à plat au relâchement.
export function brancherInclinaison(el, force = 14) {
  const maj = (x, y) => {
    const r = el.getBoundingClientRect();
    const px = Math.min(1, Math.max(0, (x - r.left) / r.width));
    const py = Math.min(1, Math.max(0, (y - r.top) / r.height));
    el.classList.add('tilt');
    el.style.setProperty('--ry', `${(px - .5) * force}deg`);
    el.style.setProperty('--rx', `${(.5 - py) * force}deg`);
    el.style.setProperty('--mx', `${px * 100}%`);
    el.style.setProperty('--my', `${py * 100}%`);
  };
  const repos = () => {
    el.classList.remove('tilt');
    el.style.setProperty('--rx', '0deg'); el.style.setProperty('--ry', '0deg');
  };
  el.addEventListener('pointermove', (e) => maj(e.clientX, e.clientY));
  el.addEventListener('pointerleave', repos);
  el.addEventListener('pointerup', repos);
  el.addEventListener('pointercancel', repos);
}
