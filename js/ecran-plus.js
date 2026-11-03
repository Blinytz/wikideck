// Menu « Plus » : écrans secondaires.

const ENTREES = [
  ['historique', '🕘', 'Historique'],
  ['serie', '🔥', 'Série'],
  ['objectifs', '🎯', 'Objectifs'],
  ['eclats', '◆', 'Éclats'],
  ['reglages', '⚙️', 'Réglages'],
];

export function rendreEcranPlus(section) {
  section.innerHTML = `<div class="menu-plus">${ENTREES.map(([e, ico, nom]) =>
    `<button class="carte-panneau entree-plus" data-aller="${e}"><span class="ico">${ico}</span>${nom}</button>`).join('')}</div>`;
  for (const b of section.querySelectorAll('[data-aller]')) {
    b.addEventListener('click', () => document.dispatchEvent(new CustomEvent('wikideck:aller', { detail: b.dataset.aller })));
  }
}
