// Paquets spéciaux (spec §7) et inventaire. Un paquet spécial gagné ou acheté
// rejoint l'inventaire et s'ouvre quand on veut ; un « paquet » de récompense
// sans précision est un paquet standard, ajouté aux paquets prêts.

import { crediterEclats } from './portefeuille.js';
import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';
import { donnees } from './donnees.js';
import { acquerir } from './acquisition.js';
import { valeurReference } from './eclats.js';

export const TYPES = {
  collection: 'Collection', theme: 'Thème', duo: 'Duo', grand: 'Grand paquet',
  initiale: 'Initiale', mystere: 'Mystère', plancher: 'Plancher', inedit: 'Inédit', sommet: 'Sommet',
};
const HAUTS = ['mythique', 'legendaire', 'pantheon'];
const pioche = a => a[Math.floor(Math.random() * a.length)];

function pool() { return donnees.pool; }
function poolCol(slug) {
  return donnees.collections.find(c => c.slug === slug)?.cartes.filter(c => !c.archivee).map(c => c.id) || [];
}
function poolTheme(theme) {
  return donnees.collections.filter(c => c.theme === theme).flatMap(c => poolCol(c.slug));
}
function poolInitiale(l) {
  return pool().filter(id => initialeDe(donnees.parId.get(id).nom) === l);
}
function poolRaretes(raretes) {
  return pool().filter(id => raretes.includes(donnees.parId.get(id).rarete));
}
export function initialeDe(nom) {
  const c = [...nom.normalize('NFD').replace(/[̀-ͯ]/g, '')].find(x => /[a-z]/i.test(x));
  return (c || '?').toUpperCase();
}
export function initialesEligibles() {
  const n = {};
  for (const id of pool()) { const l = initialeDe(donnees.parId.get(id).nom); n[l] = (n[l] || 0) + 1; }
  return Object.keys(n).filter(l => n[l] >= config.get('initialeMinCartes')).sort();
}
export function themes() {
  return [...new Set(donnees.collections.map(c => c.theme).filter(Boolean))];
}
const tirer = (p, n) => Array.from({ length: n }, () => pioche(p));

/* Paramètres d'un paquet spécial tiré au hasard (le joueur ne choisit jamais). */
export function parametresAleatoires(type) {
  switch (type) {
    case 'collection': return { slug: pioche(donnees.collections).slug };
    case 'theme': return { theme: pioche(themes()) };
    case 'duo': {
      const a = pioche(donnees.collections);
      let b = pioche(donnees.collections);
      while (b === a) b = pioche(donnees.collections);
      return { slugs: [a.slug, b.slug] };
    }
    case 'initiale': return { lettre: pioche(initialesEligibles()) };
    default: return {};
  }
}

export function libelle({ type, params = {} }) {
  const nomCol = s => donnees.collections.find(c => c.slug === s)?.nom || s;
  switch (type) {
    case 'collection': return `Collection : ${nomCol(params.slug)}`;
    case 'theme': return `Thème : ${params.theme}`;
    case 'duo': return `Duo : ${nomCol(params.slugs[0])} et ${nomCol(params.slugs[1])}`;
    case 'initiale': return `Initiale : ${params.lettre}`;
    default: return TYPES[type] || 'Paquet';
  }
}

/* Tire le contenu d'un paquet spécial. Retourne {ids, eclats, revele}. */
export function contenu({ type, params = {} }) {
  const n = config.get('tailleDuPaquet');
  switch (type) {
    case 'collection': return { ids: tirer(poolCol(params.slug), n) };
    case 'theme': return { ids: tirer(poolTheme(params.theme), n) };
    case 'duo': return { ids: Array.from({ length: n }, () => pioche(poolCol(pioche(params.slugs)))) };
    case 'grand': return { ids: tirer(pool(), config.get('tailleGrandPaquet')) };
    case 'initiale': return { ids: tirer(poolInitiale(params.lettre), n) };
    case 'plancher': return { ids: [...tirer(pool(), n - 1), pioche(poolRaretes(HAUTS))] };
    case 'sommet': return { ids: tirer(poolRaretes(['legendaire', 'pantheon']), n) };
    case 'inedit': {
      const k = config.get('tailleInedit');
      const manquantes = pool().filter(id => !(etat.cartes[id] > 0));
      if (!manquantes.length) return { ids: tirer(pool(), k), eclats: valeurReference('legendaire') };
      const ids = [];
      const reste = [...manquantes];
      while (ids.length < k && reste.length) ids.push(reste.splice(Math.floor(Math.random() * reste.length), 1)[0]);
      return { ids: [...ids, ...tirer(pool(), k - ids.length)] };
    }
    case 'mystere': {
      const types = Object.keys(TYPES).filter(t => t !== 'mystere' && t !== 'sommet');
      const t = pioche(types);
      const p = { type: t, params: parametresAleatoires(t) };
      return { ...contenu(p), revele: p };
    }
  }
  return { ids: tirer(pool(), n) };
}

/* ---------- inventaire ---------- */
function inv() { return (etat.inventaire ??= []); }
export function inventaire() { return inv(); }

export function ajouterSpecial(type, params = parametresAleatoires(type), source = 'recompense') {
  inv().push({ uid: `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`, type, params, source, t: Date.now() });
  sauvegarder();
}

export function ajouterStandard(n = 1) {
  etat.paquets.prets += n;
  sauvegarder();
}

/* Ouvre un paquet de l'inventaire ; retourne le résultat d'acquisition. */
export function ouvrirSpecial(uid) {
  const i = inv().findIndex(p => p.uid === uid);
  if (i < 0) return null;
  const p = inv().splice(i, 1)[0];
  const c = contenu(p);
  const reel = c.revele || p;
  const r = acquerir(c.ids, { source: p.source, type: reel.type });
  if (c.eclats) { crediterEclats(c.eclats, 'Paquet Inédit : collection déjà complète', 'recompense'); r.eclats = c.eclats; }
  r.titre = libelle(reel);
  r.mystere = !!c.revele;
  etat.paquets.ouverts += 1;
  sauvegarder();
  return r;
}
