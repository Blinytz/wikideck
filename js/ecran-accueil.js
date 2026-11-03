// Accueil (spec §10) : paquet en cours, paquets prêts, inventaire, série,
// question du jour.

import { etat } from './etat.js';
import { formaterDuree, esc } from './ui.js';
import { initPaquets, secondesRestantes, ouvrirPaquet } from './paquets.js';
import { lancerOuverture } from './ouverture.js';
import { inventaire, ouvrirSpecial, libelle } from './speciaux.js';
import { s as serie, bonnesDuJour, prochainPalier } from './serie.js';
import { questionDuJour } from './questions.js';
import { config } from './config.js';

export function rendreEcranAccueil(section, options = {}) {
  initPaquets();
  const p = etat.paquets;
  const pct = Math.max(0, Math.min(100, Math.round(p.progression * 100)));
  if (options.tick && section.dataset.rendu === 'accueil') {
    section.querySelector('#temps-restant').textContent = formaterDuree(secondesRestantes());
    section.querySelector('#pct-paquet').textContent = `${pct}%`;
    section.querySelector('#cercle-progres').style.strokeDashoffset = String(283 * (1 - pct / 100));
    if (Number(section.querySelector('#nb-prets').textContent) !== p.prets) rendreEcranAccueil(section);
    return;
  }
  section.dataset.rendu = 'accueil';
  const inv = inventaire();
  const se = serie();
  const qdj = questionDuJour();
  section.innerHTML = `
    <div class="carte-panneau panneau-chargement">
      <div class="zone-progres">
        <svg viewBox="0 0 100 100" class="anneau-progres">
          <circle cx="50" cy="50" r="45" class="anneau-fond"/>
          <circle cx="50" cy="50" r="45" class="anneau-valeur" id="cercle-progres" style="stroke-dashoffset:${283 * (1 - pct / 100)}"/>
        </svg>
        <div class="centre-progres"><div class="paquet-emoji">🎁</div><div id="pct-paquet">${pct}%</div></div>
      </div>
      <p class="texte-doux centre"><b id="temps-restant">${formaterDuree(secondesRestantes())}</b></p>
      <button id="btn-ouvrir" class="btn btn-primaire btn-large" ${p.prets < 1 ? 'disabled' : ''}>
        Ouvrir · <span id="nb-prets">${p.prets}</span></button>
    </div>
    ${inv.length ? `<div class="carte-panneau"><h2>Inventaire</h2>
      ${inv.map(x => `<div class="ligne-inventaire"><span>${esc(x.type === 'mystere' ? 'Mystère' : libelle(x))}</span>
        <button class="btn" data-uid="${x.uid}">Ouvrir</button></div>`).join('')}</div>` : ''}
    <div class="carte-panneau ligne-accueil" data-aller="serie">
      <h2>Série · ${se.longueur} j</h2>
      <p class="texte-doux">${bonnesDuJour()} / ${config.get('bonnesParJour')} aujourd’hui · ${se.gels} Gel${se.gels > 1 ? 's' : ''} · palier ${prochainPalier()} j</p>
    </div>
    ${qdj && !qdj.faite ? `<div class="carte-panneau ligne-accueil" data-aller="questions"><h2>Question du jour</h2>
      <p class="texte-doux">${esc(qdj.theme || '')} · ${config.get('gainQuestionDuJour')} min</p></div>` : ''}`;

  section.querySelector('#btn-ouvrir').addEventListener('click', () => {
    const r = ouvrirPaquet();
    if (r) lancerOuverture(r, () => rendreEcranAccueil(section), { titre: 'Paquet standard' });
  });
  for (const b of section.querySelectorAll('[data-uid]')) {
    b.addEventListener('click', () => {
      const r = ouvrirSpecial(b.dataset.uid);
      if (r) lancerOuverture(r, () => rendreEcranAccueil(section), { titre: r.titre });
    });
  }
  for (const b of section.querySelectorAll('[data-aller]')) {
    b.addEventListener('click', () => document.dispatchEvent(new CustomEvent('wikideck:aller', { detail: b.dataset.aller })));
  }
}
