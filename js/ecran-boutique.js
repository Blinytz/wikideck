// Écran Boutique : 3 offres, prix barré, remise, temps restant, achat unique.

import { etat } from './etat.js';
import { esc, formaterNombre, formaterDuree, confirmer } from './ui.js';
import { majBoutique, prix, remiseEffective, libelleOffre, acheter } from './boutique.js';

export function rendreEcranBoutique(section, options = {}) {
  const t = Date.now();
  const emps = majBoutique(t);
  if (options.tick && section.dataset.rendu === 'boutique') {
    for (const el of section.querySelectorAll('[data-fin]')) el.textContent = formaterDuree((Number(el.dataset.fin) - t) / 1000);
    const solde = section.querySelector('#solde-boutique');
    if (solde) solde.textContent = `◆ ${formaterNombre(etat.eclats)}`;
    // une offre apparue ou expirée : on redessine
    if (emps.map(e => e.offre?.uid || '').join() !== section.dataset.offres) rendreEcranBoutique(section);
    return;
  }
  section.dataset.rendu = 'boutique';
  section.dataset.offres = emps.map(e => e.offre?.uid || '').join();
  section.innerHTML = `
    <div class="entete-ecran"><h2>Boutique</h2><span class="texte-doux" id="solde-boutique">◆ ${formaterNombre(etat.eclats)}</span></div>
    ${emps.map(em => {
      if (!em.offre) return `<div class="carte-panneau offre vide"><span class="texte-doux">Prochaine offre dans
        <b data-fin="${em.prochaine}">${formaterDuree((em.prochaine - t) / 1000)}</b></span></div>`;
      const o = em.offre;
      const r = remiseEffective(o, t);
      const p = prix(o, t);
      return `<div class="carte-panneau offre ${o.flash ? 'flash' : ''}">
        <div class="offre-tete"><b>${esc(libelleOffre(o))}</b>${o.flash ? '<span class="pastille-flash">Flash</span>' : ''}</div>
        <div class="offre-prix">${r ? `<s>${formaterNombre(o.base)}</s> <span class="remise">-${r} %</span>` : ''}
          <b>◆ ${formaterNombre(p)}</b></div>
        <div class="offre-pied"><span class="texte-doux">⏱ <span data-fin="${o.fin}">${formaterDuree((o.fin - t) / 1000)}</span></span>
          <button class="btn btn-primaire" data-uid="${o.uid}" ${etat.eclats < p ? 'disabled' : ''}>Acheter</button></div>
      </div>`;
    }).join('')}`;
  for (const b of section.querySelectorAll('[data-uid]')) {
    b.addEventListener('click', () => {
      const em = emps.find(x => x.offre?.uid === b.dataset.uid);
      if (!em || !confirmer(`Acheter « ${libelleOffre(em.offre)} » pour ${formaterNombre(prix(em.offre))} Éclats ?`)) return;
      const r = acheter(b.dataset.uid);
      if (!r.ok) alert(r.raison);
      rendreEcranBoutique(section);
    });
  }
}
