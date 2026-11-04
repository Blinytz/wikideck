// Carte v4 : un objet en 3D (deux faces et une tranche) qu'on fait tourner au doigt.
// Le dos est identique pour toutes les raretés : rien ne fuit avant le retournement.
// Chaque rareté a sa matière ; les reflets suivent l'angle de la carte, pas le pointeur.

export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export const RARETES = ['commune', 'rare', 'epique', 'mythique', 'legendaire', 'pantheon'];
export const NOMS = { commune: 'Commune', rare: 'Rare', epique: 'Épique', mythique: 'Mythique', legendaire: 'Légendaire', pantheon: 'Panthéon' };
export const ICONES = { commune: 'ph-circle', rare: 'ph-diamond', epique: 'ph-star-four', mythique: 'ph-sparkle', legendaire: 'ph-crown-simple', pantheon: 'ph-sun-horizon' };

// paillettes : chacune a sa place, sa taille et l'angle sous lequel elle s'allume
const PAILLETTES = { epique: 10, mythique: 26, legendaire: 30, pantheon: 34 };
function graine(s) { let h = 2166136261; for (const ch of s) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return () => ((h = Math.imul(h ^ (h >>> 15), 2246822507) >>> 0) / 4294967295); }
function htmlPaillettes(c) {
  const n = PAILLETTES[c.rarete]; if (!n) return '';
  const r = graine(c.id);
  let h = '';
  for (let i = 0; i < n; i++) {
    const t = 3 + r() * (c.rarete === 'pantheon' ? 9 : 6);
    h += `<i style="left:${(r() * 100).toFixed(1)}%;top:${(r() * 100).toFixed(1)}%;--t:${t.toFixed(1)}px;--ph:${(r() * 6.28).toFixed(2)};--d:${(2 + r() * 4).toFixed(2)}s;--dl:${(-r() * 6).toFixed(2)}s"></i>`;
  }
  return `<div class="k-paillettes">${h}</div>`;
}

// le nom et la collection doivent toujours tenir : la taille suit la longueur
const echelleNom = (n) => (n.length > 34 ? .62 : n.length > 26 ? .72 : n.length > 18 ? .84 : 1);
const echelleCol = (n) => (n.length > 34 ? .8 : 1);

export function htmlDos() {
  return `<div class="k-dos"><div class="k-mono">W</div></div>`;
}

// une image qui échoue est relancée deux fois, puis remplacée par la vignette
window.__kErreur ??= (img) => {
  const n = +(img.dataset.essais || 0);
  if (n < 2) { img.dataset.essais = n + 1; setTimeout(() => { img.src = img.src.replace(/([?&])r=\d+/, '') + (img.src.includes('?') ? '&' : '?') + 'r=' + (n + 1); }, 600 * (n + 1)); return; }
  if (img.dataset.secours && !img.src.includes(img.dataset.secours.split('?')[0])) { img.src = img.dataset.secours; return; }
  img.remove();
};

export function htmlCarte(c, { dos = false, neuve = false, total = c.total, image = 'full', attrs = '' } = {}) {
  const v = c.imgV ? `?v=${c.imgV}` : '';
  const src = (image === 'full' ? c.imageUrl : c.thumbUrl) + v;
  const num = c.numero != null ? `<span class="k-num">${String(c.numero).padStart(3, '0')}${total ? `<small>/${total}</small>` : ''}</span>` : '<span></span>';
  return `<div class="k r-${c.rarete}${dos ? ' dos' : ''}" data-id="${esc(c.id)}" style="--img:url('${esc(src)}');--rar:var(--r-${c.rarete});--en:${echelleNom(c.nom)};--ec:${echelleCol(c.collection || '')}" ${attrs}>
  <div class="k-in">
    <div class="k-face">
      <div class="k-fond"></div>
      <div class="k-art"><img src="${esc(src)}" data-secours="${esc(c.thumbUrl + v)}" alt="" decoding="async" onerror="__kErreur(this)"><span class="k-init">${esc([...c.nom][0] ?? '?')}</span></div>
      <div class="k-matiere"></div>
      <div class="k-holo"></div>
      ${htmlPaillettes(c)}
      <div class="k-haut">${num}<span class="k-ico"><i class="ph-fill ${ICONES[c.rarete]}"></i></span></div>
      <div class="k-bas">
        <div class="k-col">${esc(c.collection)}</div>
        <div class="k-nom">${esc(c.nom)}</div>
        <div class="k-pied"><span class="k-rarnom">${NOMS[c.rarete]}</span><span class="k-pv">${c.pv}<small>PV</small></span></div>
      </div>
      <div class="k-glare"></div>
      <div class="k-cadre"></div>
    </div>
    <div class="k-tranche t1"></div><div class="k-tranche t2"></div><div class="k-tranche t3"></div>
    ${htmlDos()}
    ${neuve ? '<span class="k-neuve">Nouvelle</span>' : ''}
  </div>
</div>`;
}

/* ---------- lumière : calculée depuis l'orientation de la carte ---------- */
function eclairer(el, rx, ry) {
  const a = ry * Math.PI / 180, b = rx * Math.PI / 180;
  el.style.setProperty('--lx', `${50 + Math.sin(a) * 60}%`);
  el.style.setProperty('--ly', `${50 - Math.sin(b) * 60}%`);
  el.style.setProperty('--lum', Math.min(1, (Math.abs(Math.sin(a)) + Math.abs(Math.sin(b))) * 2.2).toFixed(3));
  const ps = el.querySelectorAll('.k-paillettes i');
  for (const p of ps) {
    const ph = +p.style.getPropertyValue('--ph');
    // chaque paillette s'allume sous un angle qui lui est propre
    const v = Math.cos(a * 3.2 + ph) * Math.cos(b * 2.6 + ph * 1.7);
    p.style.opacity = Math.max(0, v) ** 6;
  }
}

/* Inclinaison douce et automatique : la carte respire, ses reflets bougent seuls. */
function flotter(el, etat) {
  const t = performance.now() / 1000;
  return { rx: Math.sin(t * .7 + etat.p) * 3.5, ry: Math.sin(t * .5 + etat.p * 2) * 6 };
}

// Manipulation 3D : glisser fait tourner la carte (avec élan), relâcher la ramène
// sur la face la plus proche ; un toucher sans glissé appelle `surTap`.
export function brancherManipulation(el, { surTap, libre = true, flotte = true } = {}) {
  const etat = { rx: 0, ry: 0, vx: 0, vy: 0, prise: null, p: Math.random() * 6, actif: true, retour: false };
  el.classList.add('manip');
  const appliquer = () => {
    el.style.setProperty('--rx', `${etat.rx}deg`);
    el.style.setProperty('--ry', `${etat.ry}deg`);
    const base = el.classList.contains('dos') ? 180 : 0;
    eclairer(el, etat.rx, etat.ry + base);
  };
  const boucle = () => {
    if (!etat.actif || !el.isConnected) return;
    if (!etat.prise) {
      // élan puis rappel à ressort vers la face visible (+ flottement)
      const cible = flotte ? flotter(el, etat) : { rx: 0, ry: 0 };
      etat.vy += (cible.ry - etat.ry) * .06; etat.vx += (cible.rx - etat.rx) * .06;
      etat.vy *= .82; etat.vx *= .82;
      etat.ry += etat.vy; etat.rx += etat.vx;
    }
    appliquer();
    requestAnimationFrame(boucle);
  };
  el.addEventListener('pointerdown', (e) => {
    if (!libre) return;
    etat.prise = { x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, t: performance.now(), bouge: false };
    try { el.setPointerCapture(e.pointerId); } catch {}
  });
  el.addEventListener('pointermove', (e) => {
    const p = etat.prise; if (!p) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y;
    if (Math.hypot(e.clientX - p.x0, e.clientY - p.y0) > 6) { p.bouge = true; el.classList.add('tenue'); }
    etat.ry += dx * .55; etat.rx -= dy * .35;
    etat.rx = Math.max(-35, Math.min(35, etat.rx));
    etat.vy = dx * .55; etat.vx = -dy * .35;
    p.x = e.clientX; p.y = e.clientY;
  });
  const lacher = () => {
    const p = etat.prise; if (!p) return;
    etat.prise = null; el.classList.remove('tenue');
    if (!p.bouge) { surTap?.(); return; }
    // au-delà d'un quart de tour, la carte se pose sur l'autre face
    const tot = etat.ry + etat.vy * 4;
    const demi = Math.round(tot / 180);
    if (demi % 2) { el.classList.toggle('dos'); etat.ry -= demi * 180; el.dispatchEvent(new CustomEvent('retournee', { detail: { dos: el.classList.contains('dos') } })); }
    else etat.ry -= demi * 180;
  };
  el.addEventListener('pointerup', lacher);
  el.addEventListener('pointercancel', lacher);
  requestAnimationFrame(boucle);
  return {
    etat,
    arreter: () => { etat.actif = false; },
    // retournement animé par le ressort : on bascule la face et on part d'un demi-tour
    retourner: (sens = 1) => { el.classList.toggle('dos'); etat.ry -= 180 * sens; etat.vy = 0; },
    verrouiller: (oui) => { libre = !oui; },
  };
}

// Compatibilité : les petites cartes gardent une simple inclinaison au survol.
export function brancherInclinaison(el) { return brancherManipulation(el, { flotte: false }); }
