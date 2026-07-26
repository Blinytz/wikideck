// Écran Éclats : compteur et barème de vente des doublons.
//
// Le taux fluctuant, sa courbe et la consommation manuelle ont été retirés le
// 26/07/2026 : une carte vaut un montant fixe selon sa rareté, et la conversion
// en euros se fait désormais dans Cagnottes.

import { etat } from './etat.js';
import { BAREME_VENTE } from './eclats.js';
import { formaterNombre, NOMS_RARETE } from './ui.js';

export function rendreEcranEclats(section) {
  const lignes = Object.entries(BAREME_VENTE).map(([rarete, valeur]) => `
    <li class="ligne-bareme">
      <span class="badge-rarete rarete-${rarete}">${NOMS_RARETE[rarete]}</span>
      <b>${formaterNombre(valeur)} ◆</b>
    </li>`).join('');

  section.innerHTML = `
    <div class="carte-panneau">
      <h2>Éclats</h2>
      <div class="ligne-eclats">
        <div class="total-eclats"><span class="gemme">◆</span>
          <b id="ecl-total">${formaterNombre(etat.eclats)}</b></div>
      </div>
      <p class="texte-doux">Les Éclats se gagnent en vendant les doublons de ta
      collection. Ils restent pour l'instant propres à WikiDeck.</p>
    </div>

    <div class="carte-panneau">
      <h2>Valeur d'un doublon</h2>
      <ul class="liste-bareme">${lignes}</ul>
      <p class="texte-doux">Montant fixe, connu d'avance : plus de taux à guetter.
      Le dernier exemplaire d'une carte n'est jamais vendable.</p>
    </div>`;
}

// Rafraîchissement léger appelé quand l'écran est visible.
export function majEclatsUI(section) {
  const total = section.querySelector('#ecl-total');
  if (total) total.textContent = formaterNombre(etat.eclats);
}
