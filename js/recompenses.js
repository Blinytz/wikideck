// Récompenses : paquets standard, paquets spéciaux, Éclats, Panthéon garantie.
// Fins de collection (spec §5.5, §5.6) : branchées sur chaque acquisition.

import { crediterEclats } from './portefeuille.js';
import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';
import { donnees } from './donnees.js';
import { definirSurAcquisition, estComplete, acquerir, nbPossedees } from './acquisition.js';
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
      crediterEclats(valeurReference('pantheon'), `${motif} : Panthéon déjà toutes possédées`, 'recompense');
      dons.push(`${valeurReference('pantheon').toLocaleString('fr-FR')} Éclats`);
    }
  }
  if (r.eclats) { crediterEclats(r.eclats, motif, 'recompense'); dons.push(`${r.eclats.toLocaleString('fr-FR')} Éclats`); }
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

/* ---------- jalons de collection : 25, 50 et 75 % (100 % = fin de collection) ---------- */
const PALIERS_COLLECTION = [25, 50, 75];
function jalons() { return (etat.jalons ??= {}); }   // slug -> paliers déjà récompensés
function pourcent(col) { return col.cartes.length ? nbPossedees(col) / col.cartes.length * 100 : 0; }
function recompenseJalon(p, col) {
  if (p === 25) return { paquets: config.get('jalon25Paquets') };
  if (p === 50) return { speciaux: Array.from({ length: config.get('jalon50Collection') }, () => ({ type: 'collection', params: { slug: col.slug } })) };
  return { eclats: config.get('jalon75Eclats') };
}
function verifierJalons(slugs) {
  for (const slug of slugs) {
    const col = donnees.collections.find(c => c.slug === slug);
    if (!col) continue;
    const faits = jalons()[slug] ??= [];
    const pct = pourcent(col);
    for (const p of PALIERS_COLLECTION) {
      if (pct < p || faits.includes(p)) continue;
      faits.push(p);
      donner(recompenseJalon(p, col), `${col.nom} : ${p} %`);
    }
  }
}

definirSurAcquisition(resultat => {
  const slugs = (resultat.progres || []).map(p => p.slug);
  verifierJalons(slugs);
  verifierFins(slugs);
});

/*
 * Catalogue évolutif (§5.6), à chaque chargement des données :
 * - collection terminée qui reçoit de nouvelles cartes : repasse ouverte ;
 * - cartes possédées dont la rareté a changé : mémorisées pour la fiche
 *   (« anciennement X ») et pour un récapitulatif unique.
 * Retourne la liste des changements de rareté à présenter.
 */
export function reconcilierCatalogue() {
  // Arrivée des jalons : les paliers déjà franchis sont notés sans être donnés,
  // seuls les suivants rapportent (pas de pluie de récompenses rétroactives).
  if (!etat.jalonsInities) {
    for (const col of donnees.collections) {
      const pct = pourcent(col);
      jalons()[col.slug] = PALIERS_COLLECTION.filter(p => pct >= p);
    }
    etat.jalonsInities = true;
  }
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
