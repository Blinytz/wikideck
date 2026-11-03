// Jour de jeu : fuseau Europe/Paris, le jour commence à 4 h (paramètre).

import { config } from './config.js';

const FMT = new Intl.DateTimeFormat('fr-CA', {
  timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23',
});

function parties(t) {
  const p = Object.fromEntries(FMT.formatToParts(new Date(t)).map(x => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, heure: Number(p.hour) };
}

/* Identifiant du jour de jeu (AAAA-MM-JJ) d'un instant. */
export function jourDeJeu(t = Date.now()) {
  const decale = t - config.get('heureDebutJour') * 3600e3;
  return parties(decale).date;
}

/* Jour suivant / précédent d'un identifiant AAAA-MM-JJ. */
export function decalerJour(j, n) {
  const d = new Date(`${j}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export function joursEntre(a, b) {
  return Math.round((new Date(`${b}T12:00:00Z`) - new Date(`${a}T12:00:00Z`)) / 864e5);
}

export function heureParis(t = Date.now()) {
  return parties(t).heure;
}
