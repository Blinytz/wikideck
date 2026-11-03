// Récompenses : paquets standard, paquets spéciaux, Éclats, Panthéon garantie.
// Fins de collection (spec §5.5, §5.6) : branchées sur chaque acquisition.

import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';
import { donnees } from './donnees.js';
import { definirSurAcquisition, estComplete, acquerir } from './acquisition.js';
import { ajouterSpecial, ajouterStandard, libelle } from './speciaux.js';
import { valeurReference } from './eclats.js';

const notifs = [];
export function notifier(texte) {
  notifs.push(texte);
  document.dispatchEvent(new CustomEvent('wikideck:notif', { detail: texte }));
}
export function prendreNotifs() { return notifs.splice(0); }

/*
 * Donne une récompense. r : {paquets, speciaux: [type | {type, params}], eclats, pantheon}.
 * Retourne la liste lisible de ce qui a été donné.
 */
export function donner(r, motif) {
  const dons = [];
  if (r.paquets) { ajouterStandard(r.paquets); dons.push(`${r.paquets} paquet${r.paquets > 1 ? 's' : ''}`); }
  for (const s of r.speciaux || []) {
    const sp = typeof s === 'string' ? { type: s } : s;
    if (sp.params) ajouterSpecial(sp.type, sp.params);
    else ajouterSpecial(sp.type);
    dons.push(`paquet ${libelle(etat.inventaire.at(-1))}`);
  }
  if (r.gels) { etat.serie ??= {}; etat.serie.gels = (etat.serie.gels || 0) + r.gels; dons.push(`${r.gels} Gel${r.gels > 1 ? 's' : ''}`); }
  if (r.pantheon) {
    const manquantes = donnees.pool.filter(id => donnees.parId.get(id).rarete === 'pantheon' && !(etat.cartes[id] > 0));
    if (manquantes.length) {
      const id = manquantes[Math.floor(Math.random() * manquantes.length)];
      acquerir([id], { source: 'recompense', type: 'pantheon' });
      dons.push(`la Panthéon ${donnees.parId.get(id).nom}`);
    } else {
      etat.eclats += valeurReference('pantheon');
      dons.push(`${valeurReference('pantheon').toLocaleString('fr-FR')} Éclats`);
    }
  }
  if (r.eclats) { etat.eclats += r.eclats; dons.push(`${r.eclats.toLocaleString('fr-FR')} Éclats`); }
  sauvegarder();
  document.dispatchEvent(new CustomEvent('gacha:eclats-changes'));
  if (dons.length) notifier(`${motif} : ${dons.join(', ')}`);
  return dons;
}

/* ---------- fins de collection ---------- */
function terminees() { return (etat.terminees ??= {}); }   // slug -> {premiere, reouvertures, recompensees, ouverte}

function verifierFins(slugs) {
  for (const slug of slugs) {
    const col = donnees.collections.find(c => c.slug === slug);
    if (!col || !estComplete(col)) continue;
    const t = terminees()[slug] ??= { premiere: false, reouvertures: 0, recompensees: 0, ouverte: false };
    t.ouverte = false;
    if (!t.premiere) {
      t.premiere = true;
      const autres = donnees.collections.filter(c => c.slug !== slug && !estComplete(c));
      const special = autres.length
        ? { type: 'collection', params: { slug: autres[Math.floor(Math.random() * autres.length)].slug } }
        : 'inedit';
      donner({ speciaux: [special], eclats: config.get('eclatsParCarteTerminee') * col.cartes.length },
        `Collection terminée : ${col.nom}`);
      verifierTheme(col.theme);
    } else if (t.reouvertures > t.recompensees) {
      t.recompensees += 1;
      donner({ speciaux: [{ type: 'collection', params: { slug } }] }, `Collection recomplétée : ${col.nom}`);
    }
  }
}

function verifierTheme(theme) {
  if (!theme) return;
  etat.themesTermines ??= {};
  if (etat.themesTermines[theme]) return;
  const cols = donnees.collections.filter(c => c.theme === theme);
  if (cols.length && cols.every(estComplete)) {
    etat.themesTermines[theme] = true;
    donner({ speciaux: ['inedit'] }, `Thème terminé : ${theme}`);
  }
}

definirSurAcquisition(resultat => {
  verifierFins((resultat.progres || []).map(p => p.slug));
});

/*
 * Catalogue évolutif (§5.6), à chaque chargement des données :
 * - collection terminée qui reçoit de nouvelles cartes : repasse ouverte ;
 * - cartes possédées dont la rareté a changé : mémorisées pour la fiche
 *   (« anciennement X ») et pour un récapitulatif unique.
 * Retourne la liste des changements de rareté à présenter.
 */
export function reconcilierCatalogue() {
  for (const [slug, t] of Object.entries(terminees())) {
    const col = donnees.collections.find(c => c.slug === slug);
    if (col && t.premiere && !t.ouverte && !estComplete(col)) { t.ouverte = true; t.reouvertures += 1; }
  }
  etat.raretesConnues ??= {};
  etat.anciennesRaretes ??= {};
  const changements = [];
  for (const [id, q] of Object.entries(etat.cartes)) {
    if (!(q > 0)) continue;
    const carte = donnees.parId.get(id);
    if (!carte) continue;
    const avant = etat.raretesConnues[id];
    if (avant && avant !== carte.rarete) {
      etat.anciennesRaretes[id] = avant;
      changements.push({ carte, avant });
    }
    etat.raretesConnues[id] = carte.rarete;
  }
  sauvegarder();
  return changements;
}
