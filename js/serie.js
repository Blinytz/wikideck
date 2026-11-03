// Série quotidienne (spec §4) : 10 bonnes réponses par jour de jeu (hors
// question du jour), paliers récompensés, Gels consommés automatiquement.

import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';
import { jourDeJeu, decalerJour } from './jour.js';
import { surReponse } from './questions.js';
import { donner } from './recompenses.js';

const PALIERS = [
  [3, { paquets: 1 }],
  [7, { paquets: 2, gels: 1 }],
  [14, { speciaux: ['plancher'] }],
  [30, { speciaux: ['inedit'] }],
  [60, { speciaux: ['grand'], eclats: 50000 }],
  [100, { speciaux: ['sommet'] }],
  [182, { speciaux: ['inedit', 'inedit'] }],
  [365, { pantheon: true }],
];

export function s() {
  const e = (etat.serie ??= {});
  e.jours ??= {}; e.calendrier ??= {}; e.paliers ??= [];
  e.longueur ??= 0; e.validesSerie ??= 0; e.record ??= 0; e.gels ??= 0;
  e.dernierJourTraite ??= decalerJour(jourDeJeu(), -1);
  return e;
}

export function prochainPalier(longueur = s().longueur) {
  for (const [j] of PALIERS) if (j > longueur) return j;
  return (Math.floor(longueur / 365) + 1) * 365;
}
export function recompensePalier(j) {
  const p = PALIERS.find(x => x[0] === j);
  return p ? p[1] : (j > 365 && j % 365 === 0 ? { speciaux: ['sommet'] } : null);
}

function franchir() {
  const e = s();
  const j = e.longueur;
  e.record = Math.max(e.record, j);
  const r = recompensePalier(j);
  if (r && !e.paliers.includes(j)) { e.paliers.push(j); donner(r, `Série de ${j} jours`); }
}

function valider(jour) {
  const e = s();
  if (e.calendrier[jour] === 'valide') return;
  e.calendrier[jour] = 'valide';
  e.longueur += 1;
  e.validesSerie += 1;
  if (e.validesSerie % config.get('gelTousLes') === 0) donner({ gels: 1 }, `${e.validesSerie} jours validés`);
  franchir();
}

/* Jours écoulés depuis le dernier passage : Gel ou remise à zéro. */
export function traiterJours() {
  const e = s();
  const hier = decalerJour(jourDeJeu(), -1);
  let j = e.dernierJourTraite;
  while (j < hier) {
    j = decalerJour(j, 1);
    if (e.calendrier[j] === 'valide') continue;
    if (e.gels > 0) {
      e.gels -= 1;
      e.calendrier[j] = 'gele';
      e.longueur += 1;
      franchir();
    } else {
      e.calendrier[j] = 'manque';
      e.longueur = 0;
      e.validesSerie = 0;
      e.paliers = [];
    }
  }
  e.dernierJourTraite = hier;
  sauvegarder();
}

export function bonnesDuJour() { return s().jours[jourDeJeu()] || 0; }

surReponse((entree, signe) => {
  if (entree.qdj || !entree.correct) return;
  const e = s();
  const n = (e.jours[entree.jour] || 0) + signe;
  e.jours[entree.jour] = Math.max(0, n);
  if (n >= config.get('bonnesParJour')) valider(entree.jour);
  sauvegarder();
});
