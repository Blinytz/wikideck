// Effets retenus sur le banc d'essai (08/11/2026) :
// - habillages : commune actuelle, rare Acier et verre, épique Néon, mythique Supernova,
//   légendaire Feuille d'or, panthéon Éclipse (classes posées sur <body>, styles dans css/effets.css) ;
// - révélation Cinéma pour toutes les raretés, anticipation à partir de l'épique.

import { RARETES } from './carte.js';
import { ouvrirPaquet } from './ouverture.js';
import { AMBIANCES, alea } from './particules.js';
import { son } from './son.js';

export const HABILLAGES = ['c-rare-a', 'c-epique-b', 'c-mythique-a', 'c-legendaire-b', 'c-pantheon-b'];
export const poserHabillages = () => document.body.classList.add(...HABILLAGES);

const RANG = (r) => RARETES.indexOf(r);
const COUL = { commune: '#d6d3dc', rare: '#cfdbe8', epique: '#b69cff', mythique: '#ff8fd6', legendaire: '#f2c66d', pantheon: '#ffffff' };
const DUREE_TENSION = { epique: 1000, mythique: 1500, legendaire: 2000, pantheon: 2800 };

async function tension(r, ctx) {
  const d = DUREE_TENSION[r]; if (!d) return;
  const c = COUL[r], k = RANG(r);
  ctx.slot.style.setProperty('--c', c); ctx.slot.style.setProperty('--d', d + 'ms');
  ctx.slot.classList.add('tension');
  if (k >= 3) ctx.ov.classList.add('sombre');
  const pas = 40, img = [];
  for (let i = 0; i <= pas; i++) { const a = (i / pas) ** 2 * (2 + k * 1.3); img.push({ transform: `translate(${alea(-a, a).toFixed(1)}px, ${alea(-a, a).toFixed(1)}px) rotate(${alea(-a, a) * .25}deg)` }); }
  ctx.el.animate(img, { duration: d, easing: 'linear' });
  const { x, y } = ctx.toile.centre, n = Math.round(d / 18);
  for (let i = 0; i < n; i++) {
    const a = Math.random() * 6.28, R = alea(150, 320), ret = Math.random() * d / 1000 * .55, t = d / 1000 - ret;
    ctx.toile.ajouter({ x: x + Math.cos(a) * R, y: y + Math.sin(a) * R, vx: -Math.cos(a) * R / (t * 60), vy: -Math.sin(a) * R / (t * 60), frein: 1, r: alea(.8, 2.4), duree: t, fin: .9, couleur: i % 3 ? c : '#fff', lueur: 10, retard: ret });
  }
  for (let t = 0; t < d; t += 260) setTimeout(() => ctx.vibrer(6 + k * 3), t);
  await ctx.attendre(d);
  ctx.slot.classList.remove('tension');
  ctx.flash(k >= 4 ? 700 : 350, k >= 4 ? .85 : .4);
}

function cinema(r, ctx) {
  const c = COUL[r], k = RANG(r);
  ctx.ajouter('fx-perso fx-fondart', { '--img': getComputedStyle(ctx.el).getPropertyValue('--img') });
  if (!k) return ctx.attendre(150);
  son(r); AMBIANCES[r]?.(ctx.toile);
  if (k >= 2) { const t = ctx.ajouter('fx-perso fx-titre', { '--c': c }); t.textContent = ctx.el.querySelector('.k-nom').textContent; }
  if (k >= 3) { ctx.ajouter('fx-perso fx-flare', { '--c': c }); ctx.vibrer([30, 40, 60]); }
  if (k >= 4) { ctx.flash(k === 5 ? 1000 : 500, k === 5 ? 1 : .4); ctx.onde(c); }
  return ctx.attendre(400 + k * 320);
}

export const OPTIONS_EFFETS = { avant: (r, ctx) => (RANG(r) >= 2 ? tension(r, ctx) : null), effet: cinema };

/* Ouvre un tirage [{carte, neuve}] avec les effets retenus. */
export function ouvrir(tirage, opts = {}) {
  return ouvrirPaquet(tirage, { ...OPTIONS_EFFETS, ...opts });
}

/* Résultat du moteur d'acquisition (js/acquisition.js) -> tirage de l'ouverture.
   Les cartes offertes par la Résonance s'ajoutent en fin de paquet. */
export function tirageDe(resultat) {
  const t = resultat.cartes.map(({ carte, nouvelle }) => ({ carte, neuve: nouvelle }));
  for (const s of resultat.resonances || []) for (const carte of s.declenchees) t.push({ carte, neuve: true });
  return t;
}
