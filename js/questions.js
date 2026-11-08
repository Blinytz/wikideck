// Questions (spec §3) : tirage de 3 propositions, réponse libre tolérante,
// verdict corrigeable, gains de temps avec suite, retour espacé, question du jour.
//
// Les questions viennent de la copie Quinytz (Supabase Éclats, étape serveur).
// `definirSource` reçoit la liste ; tant qu'elle est vide, l'écran l'indique.

import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';
import { jourDeJeu } from './jour.js';
import { crediterTemps } from './paquets.js';

export const NIVEAUX = ['', 'Débutant', 'Confirmé', 'Expert', 'Nobel', 'Omniscient'];
const CLES_GAIN = ['', 'gainDebutant', 'gainConfirme', 'gainExpert', 'gainNobel', 'gainOmniscient'];
const JOUR = 864e5;

let source = [];          // [{id, question, reponse, variantes, theme, difficulte}]
const crochets = [];
export function surReponse(fn) { crochets.push(fn); }
export function definirSource(liste) { source = liste.filter(q => q.actif !== false); }
export function nbQuestions() { return source.length; }
/* Toute la banque (défi de la carte du jour, v2) : lecture seule. */
export function toutesQuestions() { return source; }
export function themesQuestions() { return [...new Set(source.map(q => q.theme).filter(Boolean))].sort(); }

function q() {
  return (etat.quiz ??= { suivi: {}, propositions: null, suite: 0, derniere: null, qdj: null, journal: [] });
}
function parId(id) { return source.find(x => x.id === id); }

/* ---------- validation ---------- */
const ARTICLES = /^(le|la|les|l|un|une|des|du|de|d|au|aux|the|a|an)\s+/;
export function normaliser(s) {
  return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[’'`]/g, ' ').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim()
    .replace(ARTICLES, '').replace(ARTICLES, '');
}
function levenshtein(a, b) {
  const m = a.length, n = b.length;
  let prec = Array.from({ length: n + 1 }, (_, j) => j);
  for (let i = 1; i <= m; i++) {
    const cur = [i];
    for (let j = 1; j <= n; j++) cur[j] = Math.min(prec[j] + 1, cur[j - 1] + 1, prec[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    prec = cur;
  }
  return prec[n];
}
/* Réponses acceptées : la réponse, ses variantes, la réponse sans sa parenthèse. */
function acceptees(qu) {
  const brut = [qu.reponse, ...(qu.variantes || [])];
  for (const r of [...brut]) {
    const sans = r.replace(/\s*\([^)]*\)\s*/g, ' ').trim();
    if (sans !== r) brut.push(sans);
  }
  const norm = brut.map(normaliser).filter(Boolean);
  // un nom propre en deux ou trois mots : le dernier suffit (« Picasso » pour « Pablo Picasso »)
  for (const r of [...norm]) {
    const mots = r.split(' ');
    if (mots.length >= 2 && mots.length <= 3 && mots.at(-1).length >= 4) norm.push(mots.at(-1));
  }
  return norm;
}
export function estCorrecte(qu, saisie) {
  const s = normaliser(saisie);
  if (!s) return false;
  return acceptees(qu).some(r => levenshtein(s, r) <= Math.floor(r.length * config.get('toleranceLevenshtein')));
}

/* ---------- multiplicateur de suite ---------- */
export function multiplicateur(suite) {
  if (suite >= 20) return 4;
  if (suite >= 10) return 3;
  if (suite >= 5) return 2;
  if (suite >= 3) return 1.5;
  return 1;
}
export function gainMinutes(qu, suite) {
  return config.get(CLES_GAIN[qu.difficulte] || 'gainDebutant') * multiplicateur(suite);
}

/* ---------- retour espacé ---------- */
function eligible(id, t) { return (q().suivi[id]?.prochaine || 0) <= t; }
function programmer(id, correct, t) {
  const s = q().suivi[id] ??= { reussites: 0, prochaine: 0 };
  if (correct) {
    s.reussites += 1;
    s.prochaine = t + config.get('delaiReussie') * 2 ** (s.reussites - 1) * JOUR;
  } else {
    s.reussites = 0;
    s.prochaine = t + config.get('delaiRatee') * JOUR;
  }
}

/* ---------- tirage de 3 propositions (pas de relance possible) ---------- */
export function propositions() {
  const etatQ = q();
  if (etatQ.propositions?.length) return etatQ.propositions.map(parId).filter(Boolean);
  if (!source.length) return [];
  const t = Date.now();
  const qdjId = etatQ.qdj?.id;
  const pool = source.filter(x => x.id !== qdjId && eligible(x.id, t));
  const n = config.get('propositions');
  const choix = [];
  while (choix.length < n && pool.length) choix.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0]);
  if (choix.length < n) {
    // pas assez d'éligibles : celles dont le délai expire le plus tôt
    const reste = source.filter(x => x.id !== qdjId && !choix.includes(x))
      .sort((a, b) => (etatQ.suivi[a.id]?.prochaine || 0) - (etatQ.suivi[b.id]?.prochaine || 0));
    choix.push(...reste.slice(0, n - choix.length));
  }
  etatQ.propositions = choix.map(x => x.id);
  sauvegarder();
  return choix;
}

/* Le joueur choisit une proposition : les autres sont défaussées. */
export function choisir(id) {
  const etatQ = q();
  etatQ.propositions = null;
  etatQ.enCours = { id, qdj: false };
  sauvegarder();
  return parId(id);
}
export function questionEnCours() {
  const e = q().enCours;
  return e ? { ...parId(e.id), qdj: e.qdj } : null;
}

/* ---------- question du jour ---------- */
export function questionDuJour() {
  const etatQ = q();
  const jour = jourDeJeu();
  if (etatQ.qdj?.jour === jour) return { ...parId(etatQ.qdj.id), faite: etatQ.qdj.faite };
  if (!source.length) return null;
  const t = Date.now();
  let pool = source.filter(x => x.difficulte === 5 && eligible(x.id, t));
  if (!pool.length) pool = source.filter(x => x.difficulte === 4 && eligible(x.id, t));
  if (!pool.length) return null;
  const choisie = pool[Math.floor(Math.random() * pool.length)];
  etatQ.qdj = { jour, id: choisie.id, faite: false };
  sauvegarder();
  return { ...choisie, faite: false };
}
export function commencerQuestionDuJour() {
  const etatQ = q();
  if (!etatQ.qdj || etatQ.qdj.faite) return null;
  etatQ.enCours = { id: etatQ.qdj.id, qdj: true };
  sauvegarder();
  return questionEnCours();
}

/* ---------- réponse, verdict et correction ---------- */
function appliquer(entree, signe) {
  // signe = +1 applique, -1 annule (pour la correction)
  const etatQ = q();
  if (entree.correct) crediterTemps(signe * entree.gain * 60);
  if (!entree.qdj) etatQ.suite = signe > 0 ? entree.suiteApres : entree.suiteAvant;
  for (const fn of crochets) fn(entree, signe);
}

export function repondre(saisie) {
  const etatQ = q();
  const enCours = etatQ.enCours;
  if (!enCours) return null;
  const qu = parId(enCours.id);
  const t = Date.now();
  const correct = estCorrecte(qu, saisie);
  const entree = construire(qu, enCours.qdj, correct, saisie, t, etatQ.suite);
  entree.suiviAvant = { ...(etatQ.suivi[qu.id] || { reussites: 0, prochaine: 0 }) };
  etatQ.journal.push({ id: qu.id, t, c: correct ? 1 : 0, qdj: enCours.qdj ? 1 : 0, d: qu.difficulte, th: qu.theme });
  appliquer(entree, +1);
  programmer(qu.id, correct, t);
  if (enCours.qdj) etatQ.qdj.faite = true;
  etatQ.enCours = null;
  etatQ.derniere = entree;
  sauvegarder();
  return entree;
}

function construire(qu, qdj, correct, saisie, t, suiteAvant) {
  const suiteApres = qdj ? suiteAvant : (correct ? suiteAvant + 1 : 0);
  const gain = !correct ? 0 : qdj ? config.get('gainQuestionDuJour') : gainMinutes(qu, suiteApres);
  return { id: qu.id, question: qu.question, reponse: qu.reponse, saisie, theme: qu.theme,
    difficulte: qu.difficulte, qdj, correct, gain, suiteAvant, suiteApres, t, jour: jourDeJeu(t) };
}

/* « En fait j'avais bon / faux » : recalcule gain, suite et compteurs. */
export function corriger() {
  const etatQ = q();
  const e = etatQ.derniere;
  if (!e) return null;
  appliquer(e, -1);
  const qu = parId(e.id) || e;
  const nouveau = construire(qu, e.qdj, !e.correct, e.saisie, e.t, e.suiteAvant);
  nouveau.corrigee = true;
  nouveau.suiviAvant = e.suiviAvant;
  const j = etatQ.journal.findLast(x => x.id === e.id && x.t === e.t);
  if (j) j.c = nouveau.correct ? 1 : 0;
  appliquer(nouveau, +1);
  etatQ.suivi[e.id] = { ...e.suiviAvant };
  programmer(e.id, nouveau.correct, e.t);
  etatQ.derniere = nouveau;
  sauvegarder();
  return nouveau;
}

export function suite() { return q().suite; }
export function journal() { return q().journal; }
