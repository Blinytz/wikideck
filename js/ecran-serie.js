// Écran Série : série en cours, record, prochain palier, calendrier, Gels,
// bonnes réponses du jour.

import { config } from './config.js';
import { jourDeJeu, decalerJour } from './jour.js';
import { s as serie, bonnesDuJour, prochainPalier } from './serie.js';

export function rendreEcranSerie(section) {
  const e = serie();
  const auj = jourDeJeu();
  const jours = Array.from({ length: 35 }, (_, i) => decalerJour(auj, i - 34));
  section.innerHTML = `
    <div class="entete-ecran"><h2>Série</h2><span class="texte-doux">record ${e.record} j</span></div>
    <div class="carte-panneau">
      <div class="chiffres-serie">
        <div><b>${e.longueur}</b><span>jours</span></div>
        <div><b>${bonnesDuJour()} / ${config.get('bonnesParJour')}</b><span>aujourd’hui</span></div>
        <div><b>${e.gels}</b><span>Gels</span></div>
        <div><b>${prochainPalier()}</b><span>prochain palier</span></div>
      </div>
    </div>
    <div class="carte-panneau">
      <div class="calendrier">${jours.map(j => `<span class="jour ${e.calendrier[j] || (j === auj ? 'aujourdhui' : '')}" title="${j}">${Number(j.slice(8))}</span>`).join('')}</div>
    </div>`;
}
