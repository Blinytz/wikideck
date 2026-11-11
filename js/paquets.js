// Moteur des paquets : chargement horodaté, file d'attente illimitée,
// rattrapage hors-ligne, tirage équiprobable dans le pool global.

import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';
import { donnees } from './donnees.js';
import { acquerir } from './acquisition.js';
import { vitesseTotale, rejouerStation } from './station.js';

// Point d'entrée UNIQUE de la vitesse : produit des boosts des 3 modules de
// la Station de Recherche (chacun ≥ 1).
/* Journal des paquets : chaque gain (temps ou paquet) et chaque ouverture, avec sa source.
   sec : temps retiré au minuteur (négatif s'il est rendu) ; n : paquets prêts en plus ou en moins. */
const MAX_JOURNAL = 400;
export function noter(src, { sec = 0, n = 0 } = {}) {
  if (!sec && !n) return;
  const j = (etat.journalPaquets ??= []);
  j.push({ t: Date.now(), src, ...(sec ? { sec: Math.round(sec) } : {}), ...(n ? { n } : {}) });
  if (j.length > MAX_JOURNAL) j.splice(0, j.length - MAX_JOURNAL);
  if (n > 0) document.dispatchEvent(new CustomEvent('wikideck:paquet', { detail: { src, n } }));
}
export const journalPaquets = () => etat.journalPaquets || [];

export function getVitesseTotale() {
  return config.get('stationActive') ? vitesseTotale() : 1;
}

export function initPaquets() {
  if (!etat.paquets || typeof etat.paquets.progression !== 'number') {
    etat.paquets = { progression: 0, lastTs: Date.now(), prets: 0, ouverts: 0 };
  }
  rattraperPaquets();
}

// Fait avancer le chargement en suivant le replay de la Station : chaque pas
// simulé applique la vitesse RÉELLE de ce pas (les boosts évoluent pendant
// l'absence — stock qui s'épuise, instances qui expirent…). La vitesse
// s'applique à la progression restante : jamais de retour à zéro.
export function rattraperPaquets() {
  const p = etat.paquets;
  if (!p) return;
  const avant = p.prets;
  try { avancer(p); } finally { if (p.prets > avant) noter('minuteur', { n: p.prets - avant }); }
  // l'horloge avance toute seule : on n'enregistre que si un paquet est sorti
  // (sinon chaque seconde « modifiait » la partie et l'appareil écrasait le serveur)
  if (p.prets !== avant) sauvegarder();
}
function avancer(p) {
  const duree = config.get('dureeBaseSecondes');
  if (!config.get('stationActive')) {
    // Station désactivée : vitesse fixe ×1, simple temps écoulé.
    const maintenant = Date.now();
    p.progression += Math.max(0, (maintenant - (p.lastTs || maintenant)) / 1000) / duree;
    while (p.progression >= 1) { p.prets += 1; p.progression -= 1; }
    p.lastTs = maintenant;
    return;
  }
  rejouerStation((dt, vitesse) => {
    p.progression += dt * vitesse / duree;
    while (p.progression >= 1) {
      p.prets += 1;               // le suivant démarre automatiquement derrière
      p.progression -= 1;
    }
  });
  p.lastTs = Date.now();
}

/* Gain (ou retrait, si négatif) de temps sur le paquet passif en cours ;
   le surplus déborde sur les paquets suivants, sans plafond. */
export function crediterTemps(secondes, source = 'temps') {
  initPaquets();
  const p = etat.paquets, avant = p.prets;
  p.progression += secondes / config.get('dureeBaseSecondes');
  while (p.progression >= 1) { p.prets += 1; p.progression -= 1; }
  while (p.progression < 0 && p.prets > 0) { p.prets -= 1; p.progression += 1; }
  noter(source, { sec: secondes, n: p.prets - avant });
  sauvegarder();
}

export function secondesRestantes() {
  const p = etat.paquets;
  const duree = config.get('dureeBaseSecondes');
  return Math.max(0, (1 - p.progression) * duree / getVitesseTotale());
}

// Tire un paquet standard depuis la file : cartes équiprobables sur le pool
// global, doublons conservés. Retourne le résultat d'acquisition ou null.
export function tirerIds(n) {
  const ids = [];
  for (let i = 0; i < n; i++) ids.push(donnees.pool[Math.floor(Math.random() * donnees.pool.length)]);
  return ids;
}

export function ouvrirPaquet() {
  rattraperPaquets();
  const p = etat.paquets;
  if (p.prets < 1) return null;
  p.prets -= 1;
  p.ouverts += 1;
  noter('ouverture', { n: -1 });
  return acquerir(tirerIds(config.get('tailleDuPaquet')), { source: 'passif', type: 'standard' });
}
