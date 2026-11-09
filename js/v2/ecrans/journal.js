// Journal des paquets (v2, écran secondaire sous Plus) : d'où vient chaque paquet,
// jour par jour, du plus récent au plus ancien.

import { journalPaquets } from '../../paquets.js';
import { jourDeJeu } from '../../jour.js';
import { esc } from '../carte.js';
import { fmtMin } from '../commun.js';

const SOURCES = {
  minuteur: ['ph-timer', 'Minuteur', 'var(--texte-2)'],
  question: ['ph-lightbulb', 'Question', '#ffd36b'],
  qdj: ['ph-star', 'Question du jour', 'var(--or)'],
  correction: ['ph-arrow-counter-clockwise', 'Correction', 'var(--texte-3)'],
  ticket: ['ph-ticket', 'Ticket', 'var(--or)'],
  ouverture: ['ph-package', 'Ouverture', 'var(--texte-3)'],
  temps: ['ph-timer', 'Temps', 'var(--texte-2)'],
  recompense: ['ph-gift', 'Récompense', 'var(--vert)'],
};
const source = (src) => SOURCES[src] || ['ph-gift', src, 'var(--vert)'];
const heure = (t) => new Date(t).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Paris' });
const fmtJour = (j) => new Date(`${j}T12:00:00Z`).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC' });

export function rendre(z) {
  const j = journalPaquets();
  if (!j.length) { z.innerHTML = '<div class="vide-etat"><i class="ph ph-package"></i>Aucun paquet</div>'; return; }
  const jours = new Map();
  for (const x of [...j].reverse()) {
    const d = jourDeJeu(x.t);
    if (!jours.has(d)) jours.set(d, []);
    jours.get(d).push(x);
  }
  const auj = jourDeJeu();
  z.innerHTML = [...jours].map(([d, l]) => {
    const gagnes = l.filter((x) => x.src !== 'ouverture').reduce((s, x) => s + (x.n || 0), 0);
    return `<div class="jp-jour"><span class="surtitre">${d === auj ? 'Aujourd’hui' : fmtJour(d)}</span>${gagnes > 0 ? `<span class="jp-total">+${gagnes}</span>` : ''}</div>
    <div class="bloc groupe">${l.map((x) => {
      const [ic, lib, coul] = source(x.src);
      const tps = x.sec ? `<span class="jp-tps${x.sec < 0 ? ' neg' : ''}">${x.sec < 0 ? '+' : '−'}${fmtMin(Math.round(Math.abs(x.sec) / 60))}</span>` : '';
      const pk = x.n ? `<span class="jp-n${x.n < 0 ? ' neg' : ''}">${x.n > 0 ? '+' : '−'}${Math.abs(x.n)}<i class="ph-fill ph-package"></i></span>` : '';
      return `<div class="rangee jp"><span class="ic" style="color:${coul}"><i class="ph-fill ${ic}"></i></span><span class="lib">${esc(lib)}<small>${heure(x.t)}</small></span>${tps}${pk}</div>`;
    }).join('')}</div>`;
  }).join('');
}
