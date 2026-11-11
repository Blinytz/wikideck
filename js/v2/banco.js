// Banco et Super Banco (novembre 2026) : deux carnets de questions ratées, propres à WikiDeck.
//
// - Toute question ratée (écran Questions, question du jour, défi, Banco, Super Banco)
//   entre dans les deux carnets : celui du jour (Banco du lendemain) et le carnet du Super Banco.
//   « J'avais bon » annule l'entrée qu'avait faite cette réponse.
// - Banco du jour : les ratées de la veille, 10 au plus, complétées si besoin par le carnet
//   du Super Banco. Une réussite au Banco ne sort pas la question du Super Banco.
// - Super Banco : 10 questions du carnet, dès qu'il en compte 10, prises en tête de pile.
//   Une première réussite marque la question et la renvoie en fin de pile ; une seconde
//   réussite (sans erreur entre les deux) la sort du carnet. Une erreur efface la marque.
// - Un essai de chaque par jour de jeu ; gains par paliers cumulés (fragments).

import { etat, sauvegarder } from '../etat.js';
import { toutesQuestions, estCorrecte, surReponse } from '../questions.js';
import { jourDeJeu, decalerJour } from '../jour.js';
import { compterBonne } from '../serie.js';
import { fragments } from './mecaniques.js';

export const TAILLE = 10;
export const PALIERS = [[5, 'commune', 3], [6, 'rare', 3], [7, 'epique', 3], [8, 'mythique', 2], [9, 'legendaire', 2], [10, 'pantheon', 1]];

const melanger = (t) => { const a = [...t]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const banque = () => new Map(toutesQuestions().map((q) => [q.id, q]));

/* ---------------- carnets ---------------- */
function carnets() {
  const c = (etat.carnets ??= {});
  c.jours ??= {};   // jour de jeu -> { id: nombre de ratés ce jour-là }
  c.super ??= {};   // id -> { n: ratés, depuis, pos: rang dans la pile (horodatage), justes: 0 | 1 }
  // seuls la veille et le jour même servent : le reste est oublié
  const garder = new Set([jourDeJeu(), decalerJour(jourDeJeu(), -1)]);
  for (const j of Object.keys(c.jours)) if (!garder.has(j)) delete c.jours[j];
  return c;
}

export function noterRatee(id, jour = jourDeJeu()) {
  if (!id) return;
  const c = carnets();
  const j = (c.jours[jour] ??= {});
  j[id] = (j[id] || 0) + 1;
  const s = (c.super[id] ??= { n: 0, depuis: Date.now(), pos: Date.now() });
  s.n += 1;
  s.justes = 0;   // une erreur efface la première réussite
  sauvegarder();
}
/* « J'avais bon » : la réponse n'était pas une erreur, on retire ce qu'elle avait ajouté. */
export function annulerRatee(id, jour = jourDeJeu()) {
  const c = carnets(), j = c.jours[jour];
  if (j?.[id]) { j[id] -= 1; if (j[id] <= 0) delete j[id]; }
  const s = c.super[id];
  if (s) { s.n -= 1; if (s.n <= 0) delete c.super[id]; }
  sauvegarder();
}

const valides = (ids, b = banque()) => ids.filter((id) => b.has(id));
export const carnetSuper = () => valides(Object.keys(carnets().super));
// la pile du Super Banco : les plus anciennes d'abord ; une question marquée repart à la fin
const pile = () => { const c = carnets().super; return carnetSuper().sort((a, b) => (c[a].pos || c[a].depuis) - (c[b].pos || c[b].depuis)); };
export const rateesVeille = () => valides(Object.keys(carnets().jours[decalerJour(jourDeJeu(), -1)] || {}));

// écran Questions et question du jour (le moteur annonce chaque réponse et chaque correction)
surReponse((entree, signe) => {
  if (entree.correct) return;
  if (signe > 0) noterRatee(entree.id, entree.jour);
  else annulerRatee(entree.id, entree.jour);
});

/* ---------------- parties ---------------- */
function partie(cle) {
  const j = jourDeJeu();
  if (etat[cle]?.jour !== j) etat[cle] = { jour: j, ids: null, rep: [], fini: false, gains: null };
  return etat[cle];
}
export const banco = () => preparer('banco');
export const superBanco = () => preparer('superBanco');

function preparer(cle) {
  const p = partie(cle);
  if (!p.ids) {
    const b = banque();
    if (!b.size) return p;
    let ids;
    if (cle === 'banco') {
      const veille = melanger(rateesVeille()).slice(0, TAILLE);
      const complement = melanger(carnetSuper().filter((id) => !veille.includes(id))).slice(0, TAILLE - veille.length);
      ids = veille.length ? [...veille, ...complement] : [];
    } else {
      const c = carnetSuper();
      ids = c.length >= TAILLE ? melanger(pile().slice(0, TAILLE)) : [];
    }
    if (!ids.length) return p;   // rien à jouer aujourd'hui (pas de ratées hier / carnet trop court)
    p.ids = ids;
    sauvegarder();
  }
  return p;
}

export const question = (p) => (p.ids && p.rep.length < p.ids.length ? banque().get(p.ids[p.rep.length]) : null);
export const score = (p) => p.rep.filter((r) => r.ok).length;

/* Réponse à la question en cours. */
export function repondre(cle, saisie) {
  const p = partie(cle), q = question(p);
  if (!q || p.fini) return null;
  const ok = estCorrecte(q, saisie);
  p.rep.push({ id: q.id, ok, saisie });
  const etape = appliquer(cle, q.id, ok, +1);
  sauvegarder();
  return { ok, q, etape, score: score(p), reste: p.ids.length - p.rep.length };
}
/* « J'avais bon / faux » sur la dernière réponse, tant que la partie n'est pas close. */
export function corriger(cle) {
  const p = partie(cle), r = p.rep.at(-1);
  if (!r || p.fini) return null;
  appliquer(cle, r.id, r.ok, -1);
  r.ok = !r.ok;
  const etape = appliquer(cle, r.id, r.ok, +1);
  sauvegarder();
  return { ok: r.ok, q: banque().get(r.id), etape, score: score(p), reste: p.ids.length - p.rep.length };
}
function appliquer(cle, id, ok, signe) {
  const p = partie(cle), jour = p.jour, sup = cle === 'superBanco', c = carnets();
  // Super Banco : l'entrée d'avant la réponse, pour pouvoir l'annuler (« J'avais bon / faux »)
  if (sup && signe > 0) { p.avant ??= {}; p.avant[id] = c.super[id] ? { ...c.super[id] } : null; }
  if (ok) compterBonne(jour, signe);
  else if (signe > 0) noterRatee(id, jour);
  else annulerRatee(id, jour);
  if (!sup) return null;
  if (signe < 0) {
    if (p.avant && id in p.avant) { if (p.avant[id]) c.super[id] = { ...p.avant[id] }; else delete c.super[id]; delete p.avant[id]; }
    return null;
  }
  if (!ok) return null;   // noterRatee a déjà compté l'erreur et effacé la marque
  const e = c.super[id];
  if (!e) return null;
  if (e.justes >= 1) { delete c.super[id]; return 'sortie'; }
  e.justes = 1; e.pos = Date.now();
  return 'marquee';
}

/* Fin de partie : gains des paliers atteints, cumulés. */
export function clore(cle) {
  const p = partie(cle);
  if (p.fini || !p.ids || p.rep.length < p.ids.length) return p.gains;
  const s = score(p), f = fragments();
  p.gains = PALIERS.filter(([n]) => s >= n).map(([n, r, k]) => { f[r] += k; return { n, r, k }; });
  p.fini = true;
  sauvegarder();
  return p.gains;
}
