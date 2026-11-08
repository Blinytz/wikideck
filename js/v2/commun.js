// Outils partagés par les écrans v2 : sélecteurs, mouvement, toasts, teintes.
// Repris de l'essai de design (essais/design.html), sans données simulées.

import { RARETES } from './carte.js';

export const $ = (s, r = document) => r.querySelector(s);
export const vibrer = (ms = 8) => { try { if (navigator.userActivation?.hasBeenActive !== false) navigator.vibrate?.(ms); } catch {} };
export const fr = (n) => Math.round(n).toLocaleString('fr-FR');
export const transition = (fn) => (document.startViewTransition ? document.startViewTransition(fn) : (fn(), { finished: Promise.resolve() }));
export const RANG = (r) => RARETES.indexOf(r);
export const hasard = (t) => t[Math.floor(Math.random() * t.length)];
export const hash = (s) => { let h = 2166136261; for (const ch of s) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return (h >>> 0) / 4294967295; };
export const fmtTemps = (s) => `${String(Math.floor(s / 3600)).padStart(2, '0')}:${String(Math.floor(s / 60) % 60).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
export const fmtMin = (m) => (m >= 60 ? `${Math.floor(m / 60)} h${m % 60 ? ' ' + String(m % 60).padStart(2, '0') : ''}` : `${m} min`);
export const phrase = (d) => { const s = (d || '').replace(/\s*\([^)]*\)/g, '').replace(/\s+/g, ' ').trim(); const m = s.match(/^.{60,260}?[.!?](\s|$)/); return m ? m[0].trim() : s.slice(0, 220) + (s.length > 220 ? '…' : ''); };

// une teinte par thème : collections comme questions
const TEINTES = [
  [/gastro|cuisine|aliment|boisson/i, '#f0876a', 'ph-fork-knife'],
  [/relig|mytho|croyance/i, '#b79cff', 'ph-flower-lotus'],
  [/hist|politi|guerre/i, '#e5766a', 'ph-crown-simple'],
  [/scien|tech|math|physi|chimi|m[ée]dec|astro|invent/i, '#6ea8ff', 'ph-atom'],
  [/nature|anima|botan|zoo|oiseau/i, '#66d19e', 'ph-leaf'],
  [/g[ée]o|pays|ville|capital/i, '#4cc9c0', 'ph-globe-hemisphere-west'],
  [/[ée]cran|jeu|cin[ée]|t[ée]l[ée]|film|s[ée]rie|bande/i, '#ff7fc3', 'ph-film-slate'],
  [/art|peint|archi|musi|sculpt|op[ée]ra/i, '#f0b25a', 'ph-paint-brush-broad'],
  [/sport/i, '#ff9b52', 'ph-soccer-ball'],
  [/lettre|litt[ée]r|pens[ée]e|philo|langu/i, '#d8c49a', 'ph-feather'],
];
export const teinte = (t = '') => { const m = TEINTES.find(([r]) => r.test(t)); return m ? { c: m[1], ic: m[2] } : { c: '#a7a4ae', ic: 'ph-circles-four' }; };

export function cascade(z) { [...z.children].forEach((el, i) => { el.classList.add('entre'); el.style.setProperty('--i', i); }); }
const derniers = new Map();
export function compter(el, cle, vers, dur = 900) {
  if (!el) return;
  const de = derniers.get(cle) ?? 0; derniers.set(cle, vers);
  const t0 = performance.now(), suffixe = el.dataset.suffixe || '';
  const pas = (t) => { const p = Math.min(1, (t - t0) / dur), e = 1 - (1 - p) ** 3; el.innerHTML = fr(de + (vers - de) * e) + suffixe; if (p < 1) requestAnimationFrame(pas); };
  requestAnimationFrame(pas);
}
export function toast(ic, txt) { const t = document.createElement('div'); t.className = 'toast'; t.innerHTML = `<i class="ph-fill ${ic}"></i>${txt}`; document.body.append(t); setTimeout(() => t.remove(), 2500); }

// navigation entre écrans : jeu.js écoute cet événement
export const aller = (nom, options) => document.dispatchEvent(new CustomEvent('v2:aller', { detail: { nom, options } }));
// un écran demande à être redessiné (après un achat, une forge…)
export const rafraichir = () => document.dispatchEvent(new CustomEvent('v2:rafraichir'));

// overlay plein écran au style « fiche » ; renvoie l'élément et sa fermeture
export function ouvrirFeuille(classe = '', { surFermeture } = {}) {
  const f = document.createElement('div');
  f.className = 'fiche ' + classe;
  document.body.append(f);
  document.documentElement.style.overflow = 'hidden';
  const fermer = () => { f.remove(); if (!document.querySelector('.fiche')) document.documentElement.style.overflow = ''; surFermeture?.(); };
  return { f, fermer };
}
