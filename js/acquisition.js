// Acquisition de cartes : point de passage unique de toute carte obtenue,
// quelle que soit sa source (paquet passif, questions, boutique, récompense,
// Résonance). Tient l'historique d'ouverture, la Résonance des collections
// et le décompte de progression des collections.

import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';
import { donnees } from './donnees.js';

export const SOURCES = {
  passif: 'Paquet passif', questions: 'Questions', boutique: 'Boutique',
  recompense: 'Récompense', resonance: 'Résonance',
};

function initEtat() {
  etat.historique ??= [];      // [{t, source, type, cartes: [{id, r, n}]}]
  etat.resonance ??= {};       // slug -> {jauge, n}
  etat.lues ??= {};            // id -> horodatage de la première lecture
}

export function collectionDe(id) {
  return donnees.colDe.get(id);
}

export function nbPossedees(col) {
  let n = 0;
  for (const c of col.cartes) if (etat.cartes[c.id] > 0) n++;
  return n;
}

export function estComplete(col) {
  return nbPossedees(col) === col.cartes.length;
}

export function seuilResonance(n) {
  return Math.round(config.get('resonanceSeuilBase') * config.get('resonanceFacteur') ** n);
}

export function etatResonance(slug) {
  initEtat();
  const r = etat.resonance[slug] ?? { jauge: 0, n: 0 };
  return { ...r, seuil: seuilResonance(r.n) };
}

function enregistrer(source, type, cartes) {
  etat.historique.push({
    t: Date.now(), source, type,
    cartes: cartes.map(({ carte, nouvelle }) => ({ id: carte.id, r: carte.rarete, n: nouvelle ? 1 : 0 })),
  });
}

// Un doublon charge la jauge de sa collection ; jauge pleine : une carte
// manquante de la collection est ajoutée. Collection complète : jauge en pause.
function chargerResonance(col, suivi) {
  if (estComplete(col)) return;
  const r = (etat.resonance[col.slug] ??= { jauge: 0, n: 0 });
  let s = suivi.get(col.slug);
  if (!s) {
    s = { slug: col.slug, nom: col.nom, avant: r.jauge, seuilAvant: seuilResonance(r.n), declenchees: [] };
    suivi.set(col.slug, s);
  }
  r.jauge += 1;
  if (r.jauge >= seuilResonance(r.n)) {
    const manquantes = col.cartes.filter(c => !(etat.cartes[c.id] > 0));
    const carte = manquantes[Math.floor(Math.random() * manquantes.length)];
    etat.cartes[carte.id] = 1;
    enregistrer('resonance', 'resonance', [{ carte, nouvelle: true }]);
    s.declenchees.push(carte);
    r.jauge = 0;
    r.n += 1;
  }
  s.apres = r.jauge;
  s.seuil = seuilResonance(r.n);
}

/*
 * Ajoute des cartes à la collection. `ids` : identifiants tirés.
 * Retourne de quoi animer l'ouverture et dresser son récapitulatif.
 */
export function acquerir(ids, { source = 'passif', type = 'standard' } = {}) {
  initEtat();
  const avant = new Map();
  const cartes = [];
  const resonances = new Map();
  for (const id of ids) {
    const carte = donnees.parId.get(id);
    if (!carte) continue;
    const col = collectionDe(id);
    if (col && !avant.has(col.slug)) avant.set(col.slug, nbPossedees(col));
    const nouvelle = !(etat.cartes[id] > 0);
    etat.cartes[id] = (etat.cartes[id] || 0) + 1;
    cartes.push({ carte, nouvelle });
    if (!nouvelle && col) chargerResonance(col, resonances);
  }
  // l'historique de l'ouverture précède celui des cartes de Résonance
  const entree = { t: Date.now(), source, type,
    cartes: cartes.map(({ carte, nouvelle }) => ({ id: carte.id, r: carte.rarete, n: nouvelle ? 1 : 0 })) };
  const iRes = etat.historique.length - [...resonances.values()].reduce((a, s) => a + s.declenchees.length, 0);
  etat.historique.splice(iRes, 0, entree);

  const progres = [];
  for (const [slug, n] of avant) {
    const col = donnees.collections.find(c => c.slug === slug);
    const apres = nbPossedees(col);
    if (apres > n) progres.push({ slug, nom: col.nom, avant: n, apres, total: col.cartes.length });
  }
  progres.sort((a, b) => (b.apres - b.avant) - (a.apres - a.avant));
  sauvegarder();
  return { cartes, progres, resonances: [...resonances.values()], source, type };
}

export function marquerLue(id) {
  initEtat();
  if (!etat.lues[id]) { etat.lues[id] = Date.now(); sauvegarder(); }
}

export function estLue(id) {
  return !!etat.lues?.[id];
}

export function historique() {
  initEtat();
  return etat.historique;
}
