// Série (v2, écran secondaire sous Plus) : chiffres de la série et calendrier
// mois par mois, navigable jusqu'au premier jour joué.

import { etat } from '../../etat.js';
import { config } from '../../config.js';
import { jourDeJeu } from '../../jour.js';
import { s as serie, bonnesDuJour, prochainPalier, recompensePalier } from '../../serie.js';
import { $, vibrer } from '../commun.js';
import { son } from '../son.js';

const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
const pad = (n) => String(n).padStart(2, '0');

function premierMois(e) {
  const jours = [...Object.keys(e.calendrier), ...Object.keys(e.jours)];
  if (etat.creeLe) jours.push(jourDeJeu(etat.creeLe));
  return (jours.sort()[0] || jourDeJeu()).slice(0, 7);
}

function libellePalier(j) {
  const r = recompensePalier(j);
  if (!r) return '';
  const p = [];
  if (r.paquets) p.push(`${r.paquets} paquet${r.paquets > 1 ? 's' : ''}`);
  if (r.gels) p.push(`${r.gels} gel`);
  if (r.speciaux) p.push(`${r.speciaux.length} paquet${r.speciaux.length > 1 ? 's' : ''} spécia${r.speciaux.length > 1 ? 'ux' : 'l'}`);
  if (r.pantheon) p.push('une Panthéon');
  return p.join(' · ');
}

let mois = null;

export function rendre(z) {
  const e = serie(), auj = jourDeJeu(), objectif = config.get('bonnesParJour'), bonnes = bonnesDuJour();
  const debut = premierMois(e), fin = auj.slice(0, 7);
  if (!mois || mois > fin || mois < debut) mois = fin;
  const [a, m] = mois.split('-').map(Number);
  const nbJours = new Date(Date.UTC(a, m, 0)).getUTCDate();
  const decalage = (new Date(Date.UTC(a, m - 1, 1)).getUTCDay() + 6) % 7; // lundi en premier
  const palier = prochainPalier();
  const cases = [];
  for (let i = 0; i < decalage; i++) cases.push('<span></span>');
  for (let d = 1; d <= nbJours; d++) {
    const j = `${mois}-${pad(d)}`, etatJ = e.calendrier[j] || (j === auj ? (bonnes >= objectif ? 'valide' : 'encours') : j > auj ? 'futur' : '');
    const n = e.jours[j] || 0;
    cases.push(`<span class="cj ${etatJ}${j === auj ? ' auj' : ''}"><b>${d}</b>${n && etatJ !== 'futur' ? `<i>${n}</i>` : ''}</span>`);
  }
  z.innerHTML = `
    <div class="bloc serie2-tete">
      <div class="s2-grand"><i class="ph-fill ph-fire"></i><b>${e.longueur}</b><span>jour${e.longueur > 1 ? 's' : ''}</span></div>
      <div class="s2-chiffres">
        <div><b>${e.record}</b><span>record</span></div>
        <div><b>${e.gels}</b><span>gel${e.gels > 1 ? 's' : ''}</span></div>
        <div><b>${palier}</b><span>palier</span></div>
      </div>
    </div>
    <div class="bloc s2-jour${bonnes >= objectif ? ' fait' : ''}">
      <div class="s2-ligne"><span class="surtitre">Aujourd’hui</span><b>${bonnes} / ${objectif}</b></div>
      <div class="barre2"><i style="width:${Math.min(100, bonnes / objectif * 100)}%"></i></div>
    </div>
    <div class="bloc s2-palier"><span class="surtitre">${palier} jours</span><b>${libellePalier(palier)}</b></div>
    <div class="bloc s2-cal">
      <div class="s2-nav">
        <button class="retour" id="m-prec" ${mois <= debut ? 'disabled' : ''} aria-label="Mois précédent"><i class="ph-bold ph-caret-left"></i></button>
        <h3>${MOIS[m - 1]} ${a}</h3>
        <button class="retour" id="m-suiv" ${mois >= fin ? 'disabled' : ''} aria-label="Mois suivant"><i class="ph-bold ph-caret-right"></i></button>
      </div>
      <div class="s2-semaine">${['L', 'M', 'M', 'J', 'V', 'S', 'D'].map((x) => `<span>${x}</span>`).join('')}</div>
      <div class="s2-grille">${cases.join('')}</div>
    </div>`;
  const aller = (k) => {
    const d = new Date(Date.UTC(a, m - 1 + k, 1));
    mois = `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}`;
    vibrer(); son('tap'); rendre(z);
  };
  $('#m-prec', z).addEventListener('click', () => aller(-1));
  $('#m-suiv', z).addEventListener('click', () => aller(1));
}
