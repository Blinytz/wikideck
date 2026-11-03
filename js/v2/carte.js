// Carte v2 : un seul composant pour la collection, la fiche et l'ouverture.
// Le dos est identique pour toutes les raretés : rien ne fuit avant le retournement.

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export const RARETES = ['commune', 'rare', 'epique', 'mythique', 'legendaire', 'pantheon'];
export const NOMS = { commune: 'Commune', rare: 'Rare', epique: 'Épique', mythique: 'Mythique', legendaire: 'Légendaire', pantheon: 'Panthéon' };
export const ICONES = { commune: 'ph-circle', rare: 'ph-diamond', epique: 'ph-star-four', mythique: 'ph-sparkle', legendaire: 'ph-crown-simple', pantheon: 'ph-sun-horizon' };

export function htmlDos() {
  return `<div class="k-dos"><div class="k-mono">W</div></div>`;
}

export function htmlCarte(c, { dos = false, neuve = false, desc = true, largeur, image = 'thumb' } = {}) {
  const src = (image === 'full' ? c.imageUrl : c.thumbUrl) + (c.imgV ? `?v=${c.imgV}` : '');
  const style = largeur ? ` style="--w:${largeur}px"` : '';
  return `<div class="k r-${c.rarete}${dos ? ' dos' : ''}${desc ? '' : ' sans-desc'}" data-id="${esc(c.id)}"${style}>
  <div class="k-in">
    <div class="k-face" style="--rar:var(--r-${c.rarete})">
      <div class="k-art"><img src="${esc(src)}" alt="" loading="lazy" onerror="this.remove()"><span class="k-init">${esc([...c.nom][0] ?? '?')}</span></div>
      <div class="k-corps">
        <div class="k-nom">${esc(c.nom)}</div>
        <div class="k-col">${esc(c.collection)}</div>
        <div class="k-desc">${esc((c.description || '').split('\n')[0])}</div>
        <div class="k-pied">
          <span class="k-rar"><i class="ph-fill ${ICONES[c.rarete]}"></i><span>${NOMS[c.rarete]}</span></span>
          <span class="k-pv">${c.pv}<small>PV</small></span>
        </div>
      </div>
      <div class="k-reflet"></div>
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
    el.style.setProperty('--ry', `${(px - .5) * force}deg`);
    el.style.setProperty('--rx', `${(.5 - py) * force}deg`);
    el.style.setProperty('--mx', `${px * 100}%`);
    el.style.setProperty('--my', `${py * 100}%`);
  };
  const repos = () => { el.style.setProperty('--rx', '0deg'); el.style.setProperty('--ry', '0deg'); };
  el.addEventListener('pointermove', (e) => maj(e.clientX, e.clientY));
  el.addEventListener('pointerleave', repos);
  el.addEventListener('pointerup', repos);
  el.addEventListener('pointercancel', repos);
}
