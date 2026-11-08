// Plus v2 : accès aux écrans secondaires (ancienne interface confinée), aux fragments,
// au ticket, au son, et à l'ancienne interface complète.

import { etat } from '../../etat.js';
import { s as serie } from '../../serie.js';
import { estConnecte } from '../../serveur.js';
import { sonActif, activerSon, son } from '../son.js';
import { $, vibrer, fr, cascade } from '../commun.js';
import { ticket, A_GRATTER, nbDoublons } from '../mecaniques.js';
import { ouvrirFragments } from '../fragments.js';

export function rendre(z) {
  const r = (ic, lib, val = '', coul = 'var(--texte-2)', attrs = '') => `<button class="rangee pressable" ${attrs}><span class="ic" style="color:${coul}"><i class="ph-fill ${ic}"></i></span><span class="lib">${lib}</span>${val}</button>`;
  const chevron = (v = '') => `<span class="val">${v}</span><i class="ph ph-caret-right"></i>`;
  const se = serie(), tk = ticket();
  z.innerHTML = `<div class="grand-titre"><div><h1>Plus</h1></div></div>
    <div class="bloc groupe">
      ${r('ph-fire', 'Série', chevron(`${se.longueur} j`), '#ff9f5a', 'data-aller="serie"')}
      ${r('ph-target', 'Objectifs', chevron(), 'var(--vert)', 'data-aller="objectifs"')}
      ${r('ph-clock-counter-clockwise', 'Historique', chevron(), 'var(--texte-2)', 'data-aller="historique"')}
    </div>
    <div class="bloc groupe">
      ${r('ph-diamonds-four', 'Fragments', chevron(nbDoublons() ? `${fr(nbDoublons())} doublons` : ''), '#b79cff', 'id="r-frag"')}
      ${r('ph-ticket', 'Ticket du jour', chevron(`${Math.min(tk.grattees.length, A_GRATTER)}/${A_GRATTER}`), 'var(--or)', 'data-aller="accueil"')}
      ${r('ph-diamond', 'Éclats', chevron(fr(etat.eclats || 0)), 'var(--or)', 'data-aller="eclats"')}
    </div>
    <div class="bloc groupe">
      ${r('ph-speaker-high', 'Sons', `<span class="interrupteur${sonActif() ? ' on' : ''}"></span>`, '#6ea8ff', 'id="r-son"')}
      ${r('ph-user-circle', 'Compte et réglages', chevron(estConnecte() ? 'connecté' : 'hors ligne'), 'var(--texte-2)', 'data-aller="reglages"')}
      ${r('ph-clock-clockwise', 'Ancienne interface', chevron(), 'var(--texte-3)', 'id="r-ancien"')}
    </div>`;
  cascade(z);
  $('#r-frag', z).addEventListener('click', ouvrirFragments);
  $('#r-son', z).addEventListener('click', () => { activerSon(!sonActif()); $('#r-son .interrupteur', z).classList.toggle('on', sonActif()); son('epingle'); vibrer(); });
  $('#r-ancien', z).addEventListener('click', () => { location.href = 'ancien.html'; });
}
