// Écran Objectifs : familles, palier suivant, progression, récompense.

import { esc, formaterNombre } from './ui.js';
import { familles, obtenus, seuil, recompenseRang } from './objectifs.js';
import { TYPES } from './speciaux.js';

function texteRecompense(r) {
  const p = [];
  if (r.paquets) p.push(`${r.paquets} paquet${r.paquets > 1 ? 's' : ''}`);
  for (const s of r.speciaux || []) p.push(TYPES[s] || s);
  if (r.eclats) p.push(`${formaterNombre(r.eclats)} ◆`);
  return p.join(' + ');
}

export function rendreEcranObjectifs(section) {
  const lignes = familles().map(f => {
    const n = obtenus(f.cle);
    const v = f.val();
    if (n >= f.paliers.length) {
      return `<div class="carte-panneau objectif fini"><b>${esc(f.nom)}</b><span class="texte-doux">${formaterNombre(v)} · terminé</span></div>`;
    }
    const p = f.paliers[n];
    const cible = seuil(f, p);
    return `<div class="carte-panneau objectif">
      <div class="objectif-tete"><b>${esc(f.nom)}</b><span class="texte-doux">${formaterNombre(v)} / ${formaterNombre(cible)}</span></div>
      <div class="barre-progression"><div style="width:${Math.min(100, Math.round(100 * v / Math.max(1, cible)))}%"></div></div>
      <span class="texte-doux">${n} / ${f.paliers.length} · ${esc(texteRecompense(recompenseRang(n, p === 'toutes')))}</span>
    </div>`;
  }).join('');
  section.innerHTML = `<div class="entete-ecran"><h2>Objectifs</h2></div>${lignes}`;
}
