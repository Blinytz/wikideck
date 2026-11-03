// Objectifs (spec §6) : familles de paliers, récompense selon le rang du
// palier ; un palier obtenu reste obtenu ; paliers « toutes » dynamiques.

import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';
import { donnees } from './donnees.js';
import { estComplete, definirSurAcquisition, estLue } from './acquisition.js';
import { surReponse, journal, themesQuestions } from './questions.js';
import { donner } from './recompenses.js';

const TOUTES = 'toutes';

function compteQuestions(filtre) {
  return journal().filter(x => x.c && filtre(x)).length;
}
function possedees(f = () => true) {
  let n = 0;
  for (const [id, q] of Object.entries(etat.cartes)) if (q > 0 && donnees.parId.has(id) && f(donnees.parId.get(id))) n++;
  return n;
}
function total(f = () => true) { return [...donnees.parId.values()].filter(f).length; }
const themes = () => [...new Set(donnees.collections.map(c => c.theme).filter(Boolean))];
const themeTermine = t => donnees.collections.filter(c => c.theme === t).every(estComplete);
const st = () => (etat.stats ??= {});

export function familles() {
  const leg = c => c.rarete === 'legendaire', pan = c => c.rarete === 'pantheon';
  const f = [
    { cle: 'bonnes', nom: 'Bonnes réponses', paliers: [10, 100, 500, 1000, 2500, 5000, 10000], val: () => compteQuestions(() => true) },
    { cle: 'nobel', nom: 'Bonnes réponses Nobel', paliers: [10, 50, 200, 500], val: () => compteQuestions(x => x.d === 4) },
    { cle: 'omniscient', nom: 'Bonnes réponses Omniscient', paliers: [1, 10, 50, 100, 250], val: () => compteQuestions(x => x.d === 5) },
    ...themesQuestions().map(t => ({ cle: `specialiste:${t}`, nom: `Spécialiste : ${t}`, paliers: [25, 100, 250], val: () => compteQuestions(x => x.th === t) })),
    { cle: 'recordSuite', nom: 'Record de suite', paliers: [5, 10, 20, 30, 50], val: () => st().recordSuite || 0 },
    { cle: 'suitesExpert', nom: 'Suites de 5 en Expert ou plus', paliers: [1, 10, 50], val: () => st().suitesExpert || 0 },
    { cle: 'qdj', nom: 'Questions du jour réussies', paliers: [7, 30, 100, 365], val: () => compteQuestions(x => x.qdj) },
    { cle: 'cartes', nom: 'Cartes possédées', paliers: [100, 500, 1000, 2500, 5000, 7500, TOUTES], val: () => possedees(), toutes: () => total() },
    { cle: 'collections', nom: 'Collections terminées', paliers: [1, 5, 10, 25, 50, 100, TOUTES], val: () => donnees.collections.filter(estComplete).length, toutes: () => donnees.collections.length },
    { cle: 'themes', nom: 'Thèmes terminés', paliers: [1, 3, 5, TOUTES], val: () => themes().filter(themeTermine).length, toutes: () => themes().length },
    { cle: 'legendaires', nom: 'Légendaires possédées', paliers: [10, 50, 100, TOUTES], val: () => possedees(leg), toutes: () => total(leg) },
    { cle: 'pantheon', nom: 'Panthéon possédées', paliers: [1, 5, 10, 25, TOUTES], val: () => possedees(pan), toutes: () => total(pan) },
    { cle: 'lues', nom: 'Cartes lues', paliers: [10, 100, 500, 1000, 2500, 5000], val: () => Object.keys(etat.lues || {}).filter(estLue).length },
    { cle: 'paquets', nom: 'Paquets ouverts', paliers: [10, 100, 500, 1000], val: () => etat.paquets?.ouverts || 0 },
    { cle: 'resonances', nom: 'Résonances déclenchées', paliers: [1, 10, 50], val: () => st().resonances || 0 },
  ];
  return f;
}

export function seuil(fam, p) { return p === TOUTES ? fam.toutes() : p; }

export function recompenseRang(rang, toutes) {
  if (toutes) return { speciaux: ['sommet'] };
  if (rang === 0) return { paquets: 1 };
  if (rang === 1) return { paquets: 2 };
  if (rang === 2) return { speciaux: ['plancher'] };
  if (rang === 3) return { speciaux: ['inedit'] };
  return { speciaux: ['inedit'], eclats: config.get('eclatsObjectifAvance') };
}

export function obtenus(cle) { return (etat.objectifs ??= {})[cle] || 0; }

export function verifierObjectifs() {
  const o = (etat.objectifs ??= {});
  for (const fam of familles()) {
    const v = fam.val();
    while ((o[fam.cle] || 0) < fam.paliers.length) {
      const i = o[fam.cle] || 0;
      const p = fam.paliers[i];
      if (v < seuil(fam, p)) break;
      o[fam.cle] = i + 1;
      donner(recompenseRang(i, p === TOUTES), `Objectif ${fam.nom} : ${p === TOUTES ? 'toutes' : p.toLocaleString('fr-FR')}`);
    }
  }
  sauvegarder();
}

definirSurAcquisition(() => verifierObjectifs());
surReponse((entree, signe) => {
  const s = st();
  if (signe > 0 && !entree.qdj) {
    s.recordSuite = Math.max(s.recordSuite || 0, entree.suiteApres);
    s.suiteExpert = entree.correct && entree.difficulte >= 3 ? (s.suiteExpert || 0) + 1 : 0;
    if (s.suiteExpert === 5) s.suitesExpert = (s.suitesExpert || 0) + 1;
  }
  setTimeout(verifierObjectifs, 0);
});
