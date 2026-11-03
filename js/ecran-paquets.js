// Écran Paquets : chargement en cours, file de paquets prêts, ouverture
// avec révélation carte par carte façon gacha.

import { etat } from './etat.js';
import { donnees } from './donnees.js';
import { formaterDuree, esc, NOMS_RARETE, htmlImageCarte } from './ui.js';
import { initPaquets, rattraperPaquets, secondesRestantes, ouvrirPaquet,
         getVitesseTotale } from './paquets.js';
import { config } from './config.js';
import { lancerOuverture } from './ouverture.js';

export function tickPaquets() {
  rattraperPaquets();
}

export function rendreEcranPaquets(section, options = {}) {
  initPaquets();
  const p = etat.paquets;
  const reste = secondesRestantes();
  const pct = Math.round(p.progression * 100);

  // Pendant le tick 1s, ne rafraîchir que les valeurs (pas de re-render DOM
  // complet, sinon les clics/animations seraient interrompus).
  if (options.tick && section.dataset.rendu === 'v7') {
    section.querySelector('#temps-restant').textContent = formaterDuree(reste);
    const vit = section.querySelector('#vitesse-paquets');
    if (vit) vit.textContent = `×${getVitesseTotale().toFixed(2)}`;
    section.querySelector('#pct-paquet').textContent = `${pct}%`;
    const cercle = section.querySelector('#cercle-progres');
    cercle.style.strokeDashoffset = String(283 * (1 - p.progression));
    section.querySelector('#nb-prets').textContent = p.prets;
    section.querySelector('#btn-ouvrir').disabled = p.prets < 1;
    section.querySelector('#file-prets').classList.toggle('vide', p.prets === 0);
    return;
  }
  section.dataset.rendu = 'v7';

  section.innerHTML = `
    <div class="carte-panneau panneau-chargement">
      <h2>Prochain paquet</h2>
      <div class="zone-progres">
        <svg viewBox="0 0 100 100" class="anneau-progres">
          <circle cx="50" cy="50" r="45" class="anneau-fond"/>
          <circle cx="50" cy="50" r="45" class="anneau-valeur" id="cercle-progres"
                  style="stroke-dashoffset:${283 * (1 - p.progression)}"/>
        </svg>
        <div class="centre-progres">
          <div class="paquet-emoji">🎁</div>
          <div id="pct-paquet">${pct}%</div>
        </div>
      </div>
      <p class="texte-doux centre">
        Prêt dans <b id="temps-restant">${formaterDuree(reste)}</b>
        ${config.get('stationActive') ? `<br>Vitesse de recherche : <b id="vitesse-paquets">×${getVitesseTotale().toFixed(2)}</b>` : ''}
      </p>
    </div>

    <div class="carte-panneau" id="file-prets" ${p.prets === 0 ? 'class-vide' : ''}>
      <h2>File d'attente</h2>
      <p class="texte-doux"><b id="nb-prets">${p.prets}</b> paquet(s) prêt(s) à ouvrir</p>
      <button id="btn-ouvrir" class="btn btn-primaire btn-large"
              ${p.prets < 1 ? 'disabled' : ''}>✨ Ouvrir un paquet</button>
    </div>`;

  section.querySelector('#btn-ouvrir').addEventListener('click', () => {
    const resultat = ouvrirPaquet();
    if (resultat) lancerOuverture(resultat, () => rendreEcranPaquets(section, {}), { titre: 'Paquet standard' });
  });
}
