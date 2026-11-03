// Écran Historique : toutes les ouvertures, de la plus récente à la plus
// ancienne, avec filtres « nouvelles uniquement » et « non lues ».

import { donnees } from './donnees.js';
import { esc, NOMS_RARETE, htmlImageCarte } from './ui.js';
import { ouvrirDetailCarte } from './carte.js';
import { historique, estLue, SOURCES } from './acquisition.js';
import { detailOptions } from './ecran-collection.js';

const TYPES = { standard: 'Standard', resonance: 'Résonance' };
const PAR_PAGE = 40;
let filtres = { nouvelles: false, nonLues: false };
let limite = PAR_PAGE;

function date(t) {
  return new Date(t).toLocaleString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

export function rendreEcranHistorique(section) {
  const toutes = historique();
  const lignes = [];
  for (let i = toutes.length - 1; i >= 0 && lignes.length < limite; i--) {
    const e = toutes[i];
    const cartes = e.cartes.filter(c => (!filtres.nouvelles || c.n) && (!filtres.nonLues || !estLue(c.id)));
    if (!cartes.length) continue;
    lignes.push(`
      <div class="entree-histo">
        <div class="tete"><span><b>${esc(SOURCES[e.source] || e.source)}</b> · ${esc(TYPES[e.type] || e.type)}</span><span>${date(e.t)}</span></div>
        <div class="histo-cartes">${cartes.map(c => {
          const carte = donnees.parId.get(c.id);
          if (!carte) return '';
          return `<button class="mini-carte rarete-${c.r}" data-id="${esc(c.id)}">
            ${htmlImageCarte(carte)}
            <span class="nom-mini">${esc(carte.nom)}</span>
            <span class="rarete-mini">${NOMS_RARETE[c.r]}</span>
            ${c.n ? '<span class="pastille-nouvelle">★</span>' : ''}
            ${estLue(c.id) ? '<span class="indicateur-lue">lue</span>' : ''}
          </button>`;
        }).join('')}</div>
      </div>`);
  }
  section.innerHTML = `
    <div class="entete-ecran"><h2>Historique</h2><span class="texte-doux">${toutes.length} ouverture${toutes.length > 1 ? 's' : ''}</span></div>
    <div class="filtres">
      <button class="filtre ${filtres.nouvelles ? 'actif' : ''}" data-f="nouvelles">Nouvelles uniquement</button>
      <button class="filtre ${filtres.nonLues ? 'actif' : ''}" data-f="nonLues">Non lues</button>
    </div>
    ${lignes.join('') || '<p class="texte-doux">Rien à afficher.</p>'}
    ${toutes.length > limite ? '<button class="btn btn-discret btn-plus">Plus ancien</button>' : ''}`;
  for (const b of section.querySelectorAll('.filtre')) {
    b.addEventListener('click', () => { filtres[b.dataset.f] = !filtres[b.dataset.f]; limite = PAR_PAGE; rendreEcranHistorique(section); });
  }
  section.querySelector('.btn-plus')?.addEventListener('click', () => { limite += PAR_PAGE; rendreEcranHistorique(section); });
  for (const b of section.querySelectorAll('.mini-carte[data-id]')) {
    b.addEventListener('click', () => {
      const carte = donnees.parId.get(b.dataset.id);
      ouvrirDetailCarte(carte, detailOptions(carte, () => rendreEcranHistorique(section)));
    });
  }
}
