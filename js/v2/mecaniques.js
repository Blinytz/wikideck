// Mécaniques ajoutées par la refonte (novembre 2026), branchées sur l'état réel :
// tout vit dans `etat`, donc tout est sauvegardé et synchronisé avec le serveur
// comme le reste de la partie.
//
// - fragments : un doublon s'échange (au choix) contre 1 fragment de sa rareté ;
//   10 fragments d'une rareté forgent une carte manquante de cette rareté ;
// - doublons : vendre (Éclats, barème de js/eclats.js) ou fragmenter, carte par carte ou en lot ;
// - carte du jour : une carte qu'on n'a pas, gagnée par une série sans faute de
//   questions imposées (3 à 15 selon la rareté) ; essais illimités ;
// - ticket du jour : 9 cases, 3 à gratter, chaque case est un lot
//   (temps de paquet, fragments, carte, paquet).

import { etat, sauvegarder } from '../etat.js';
import { donnees } from '../donnees.js';
import { acquerir } from '../acquisition.js';
import { crediterTemps, tirerIds } from '../paquets.js';
import { ajouterStandard } from '../speciaux.js';
import { valeurVente } from '../eclats.js';
import { crediterEclats } from '../portefeuille.js';
import { toutesQuestions, estCorrecte } from '../questions.js';
import { jourDeJeu } from '../jour.js';
import { RARETES } from './carte.js';

const RANG = (r) => RARETES.indexOf(r);
const hash = (s) => { let h = 2166136261; for (const ch of s) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return (h >>> 0) / 4294967295; };
const hasard = (t) => t[Math.floor(Math.random() * t.length)];
const carteDe = (id) => donnees.parId.get(id);
export const possede = (id) => (etat.cartes[id] || 0) > 0;
export const quantite = (id) => etat.cartes[id] || 0;
const actives = () => donnees.pool.map(carteDe);

/* ---------------- fragments et forge ---------------- */
export const PRIX_FORGE = 10;
export function fragments() {
  const f = (etat.fragments ??= {});
  for (const r of RARETES) f[r] ??= 0;
  return f;
}
export const manquantes = (r) => actives().filter((c) => c.rarete === r && !possede(c.id));
export const forgeable = (r) => fragments()[r] >= PRIX_FORGE && manquantes(r).length > 0;

/* Forge : retire 10 fragments, ajoute une carte manquante de la rareté. Renvoie le résultat d'acquisition. */
export function forger(r) {
  if (!forgeable(r)) return null;
  fragments()[r] -= PRIX_FORGE;
  const c = hasard(manquantes(r));
  return acquerir([c.id], { source: 'forge', type: 'forge' });
}

/* ---------------- doublons : vendre ou fragmenter ---------------- */
export const lesDoublons = () => actives().filter((c) => quantite(c.id) > 1);
export const nbDoublons = (cartes = lesDoublons()) => cartes.reduce((s, c) => s + quantite(c.id) - 1, 0);
export const valeurDoublons = (cartes = lesDoublons()) => cartes.reduce((s, c) => s + valeurVente(c) * (quantite(c.id) - 1), 0);

/* Vend tous les doublons de ces cartes (le dernier exemplaire reste). Renvoie le total d'Éclats. */
export function vendre(cartes) {
  let total = 0;
  for (const c of cartes) {
    const k = quantite(c.id) - 1;
    if (k <= 0) continue;
    etat.cartes[c.id] = 1;
    total += k * valeurVente(c);
  }
  sauvegarder();
  if (total) crediterEclats(total, cartes.length === 1 ? `Revente de doublons : ${cartes[0].nom}` : 'Revente groupée de doublons', 'revente');
  return total;
}
/* Échange tous les doublons de ces cartes contre des fragments (1 par doublon). Renvoie le nombre de fragments. */
export function fragmenter(cartes) {
  const f = fragments();
  let n = 0;
  for (const c of cartes) {
    const k = quantite(c.id) - 1;
    if (k <= 0) continue;
    etat.cartes[c.id] = 1;
    f[c.rarete] += k; n += k;
  }
  sauvegarder();
  return n;
}

/* ---------------- carte du jour : le défi ---------------- */
export const SERIE_DEFI = { commune: 3, rare: 5, epique: 8, mythique: 10, legendaire: 12, pantheon: 15 };
export function defi() {
  const j = jourDeJeu();
  if (etat.defi?.jour !== j) etat.defi = { jour: j, id: null, suite: 0, record: 0, gagne: false, vues: [] };
  return etat.defi;
}
/* La carte du jour : tirée de façon stable dans les cartes qu'on n'a pas. */
export function carteDuJour() {
  const d = defi();
  let c = d.id && carteDe(d.id);
  if (!c) {
    const pool = actives().filter((x) => !possede(x.id)).sort((a, b) => (a.id < b.id ? -1 : 1));
    if (!pool.length) return null;
    c = pool[Math.floor(hash(d.jour + 'cdj') * pool.length)];
    d.id = c.id; sauvegarder();
  }
  return c;
}
/* Question imposée, au hasard, sans répétition dans la journée. */
export function questionDefi() {
  const d = defi(), banque = toutesQuestions();
  if (!banque.length) return null;
  let pool = banque.filter((q) => !d.vues.includes(q.id));
  if (!pool.length) { d.vues = []; pool = banque; }
  const q = hasard(pool);
  d.vues.push(q.id); sauvegarder();
  return q;
}
/* Réponse au défi : renvoie { ok, suite, gagne, resultat } ; la carte est ajoutée à la victoire. */
export function repondreDefi(q, saisie) {
  const d = defi(), c = carteDuJour();
  const ok = estCorrecte(q, saisie);
  d.suite = ok ? d.suite + 1 : 0;
  d.record = Math.max(d.record, d.suite);
  let resultat = null;
  if (ok && !d.gagne && d.suite >= SERIE_DEFI[c.rarete]) {
    d.gagne = true;
    resultat = acquerir([c.id], { source: 'defi', type: 'carte-du-jour' });
  }
  sauvegarder();
  return { ok, suite: d.suite, gagne: d.gagne, resultat };
}

/* ---------------- ticket à gratter ---------------- */
export const A_GRATTER = 3;
const LOTS = [
  [20, { t: 'temps', h: 1 }], [12, { t: 'temps', h: 2 }], [8, { t: 'temps', h: 3 }], [4, { t: 'temps', h: 6 }], [1, { t: 'temps', h: 12 }],
  [15, { t: 'frag', r: 'commune' }], [10, { t: 'frag', r: 'rare' }], [6, { t: 'frag', r: 'epique' }], [3, { t: 'frag', r: 'mythique' }], [1.5, { t: 'frag', r: 'legendaire' }], [.5, { t: 'frag', r: 'pantheon' }],
  [14, { t: 'carte' }], [5, { t: 'paquet' }],
];
const CHANCES_CARTE = { commune: 55, rare: 30, epique: 11, mythique: 3, legendaire: .9, pantheon: .1 };
const rngDe = (s) => { let a = Math.floor(hash(s) * 4294967295) >>> 0; return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
function tirerLot(rng) {
  let x = rng() * LOTS.reduce((s, [p]) => s + p, 0), l = LOTS[0][1];
  for (const [p, lot] of LOTS) { x -= p; if (x <= 0) { l = lot; break; } }
  l = { ...l };
  if (l.t === 'frag') { const y = rng(); l.n = y < .55 ? 1 : y < .85 ? 2 : 3; }
  if (l.t === 'carte') { let y = rng() * 100; l.r = RARETES.find((r) => (y -= CHANCES_CARTE[r]) <= 0) || 'commune'; }
  return l;
}
export function ticket() {
  const j = jourDeJeu();
  if (etat.ticket?.jour !== j) {
    const rng = rngDe(j + 'ticket' + (etat.creeLe || ''));
    etat.ticket = { jour: j, cases: Array.from({ length: 9 }, () => tirerLot(rng)), choisies: [], grattees: [] };
    sauvegarder();
  }
  return etat.ticket;
}
export const estGros = (l) => (l.t === 'temps' && l.h >= 6) || ((l.t === 'frag' || l.t === 'carte') && RANG(l.r) >= 3) || l.t === 'paquet';
export function choisirCase(i) {
  const tk = ticket();
  if (tk.grattees.includes(i)) return false;
  if (tk.choisies.includes(i)) return true;
  if (tk.choisies.length >= A_GRATTER) return false;
  tk.choisies.push(i); sauvegarder();
  return true;
}
/* Case grattée : le lot est appliqué tout de suite (les cartes, elles, s'ouvrent à la fin). */
export function gratter(i) {
  const tk = ticket();
  if (tk.grattees.includes(i)) return null;
  tk.grattees.push(i);
  const l = tk.cases[i];
  if (l.t === 'temps') crediterTemps(l.h * 3600);
  else if (l.t === 'frag') fragments()[l.r] += l.n;
  else if (l.t === 'paquet') ajouterStandard(1);
  else {
    const pool = actives().filter((c) => c.rarete === l.r);
    const c = hasard(pool.length ? pool : actives());
    l.id = c.id; l.neuve = !possede(c.id);
  }
  sauvegarder();
  return l;
}
/* Cartes gagnées au ticket et pas encore reçues : on les acquiert d'un coup. */
export function encaisserTicket() {
  const tk = ticket();
  const l = tk.grattees.map((i) => tk.cases[i]).filter((x) => x.t === 'carte' && x.id && !x.recu);
  if (!l.length) return null;
  const neuves = new Map(l.map((x) => [x.id, x.neuve]));
  l.forEach((x) => (x.recu = true));
  const r = acquerir(l.map((x) => x.id), { source: 'ticket', type: 'ticket' });
  // la nouveauté se juge au moment du grattage, pas après les cartes déjà reçues
  r.cartes.forEach((x) => { if (neuves.has(x.carte.id)) x.nouvelle = neuves.get(x.carte.id); });
  return r;
}
export const cartesEnAttente = () => { const tk = ticket(); return tk.grattees.map((i) => tk.cases[i]).filter((x) => x.t === 'carte' && x.id && !x.recu); };
