// Boutique (spec §8) : 3 emplacements, offres pondérées au contenu précis,
// achat unique, remises, offres flash, baisse avec le temps.

import { debiterEclats } from './portefeuille.js';
import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';
import { donnees } from './donnees.js';
import { valeurReference } from './eclats.js';
import { parametresAleatoires, libelle, initialeDe, ajouterSpecial } from './speciaux.js';

const H = 3600e3;
const TYPES = [
  ['collection', 20, [24, 48]], ['theme', 20, [24, 48]], ['duo', 20, [24, 48]],
  ['grand', 10, [24, 24]], ['initiale', 8, [24, 24]], ['mystere', 8, [24, 24]],
  ['plancher', 4, [12, 12]], ['inedit', 2, [12, 12]], ['sommet', 0.5, [6, 6]],
];
const entre = (a, b) => a + Math.random() * (b - a);

/* ---------- prix : valeur moyenne du contenu possible ---------- */
function moyenne(ids) {
  if (!ids.length) return 0;
  return ids.reduce((a, id) => a + valeurReference(donnees.parId.get(id).rarete), 0) / ids.length;
}
function idsCol(slug) { return donnees.collections.find(c => c.slug === slug)?.cartes.filter(c => !c.archivee).map(c => c.id) || []; }
function idsRar(r) { return donnees.pool.filter(id => r.includes(donnees.parId.get(id).rarete)); }

export function prixBase({ type, params = {} }) {
  const n = config.get('tailleDuPaquet');
  let v;
  switch (type) {
    case 'collection': v = n * moyenne(idsCol(params.slug)); break;
    case 'theme': v = n * moyenne(donnees.collections.filter(c => c.theme === params.theme).flatMap(c => idsCol(c.slug))); break;
    case 'duo': v = n * (moyenne(idsCol(params.slugs[0])) + moyenne(idsCol(params.slugs[1]))) / 2; break;
    case 'grand': v = config.get('tailleGrandPaquet') * moyenne(donnees.pool); break;
    case 'initiale': v = n * moyenne(donnees.pool.filter(id => initialeDe(donnees.parId.get(id).nom) === params.lettre)); break;
    case 'plancher': v = (n - 1) * moyenne(donnees.pool) + moyenne(idsRar(['mythique', 'legendaire', 'pantheon'])); break;
    case 'inedit': v = config.get('tailleInedit') * moyenne(donnees.pool) * config.get('multiplicateurInedit'); break;
    case 'sommet': v = n * moyenne(idsRar(['legendaire', 'pantheon'])); break;
    case 'mystere': {
      // prix moyen des types possibles (hors Sommet) ; les types paramétrés
      // comptent à la valeur moyenne du pool
      const types = TYPES.map(t => t[0]).filter(t => t !== 'mystere' && t !== 'sommet');
      return Math.round(types.reduce((a, t) => a + prixType(t), 0) / types.length / 100) * 100;
    }
    default: v = n * moyenne(donnees.pool);
  }
  return Math.round(v / 100) * 100;
}
function prixType(t) {
  if (['collection', 'theme', 'duo', 'initiale'].includes(t)) return config.get('tailleDuPaquet') * moyenne(donnees.pool);
  return prixBase({ type: t, params: {} });
}

/* ---------- offres ---------- */
function b() {
  const e = (etat.boutique ??= { emplacements: [] });
  const n = config.get('emplacementsBoutique');
  while (e.emplacements.length < n) e.emplacements.push({ offre: null, prochaine: 0 });
  return e;
}

function tirerType() {
  const tot = TYPES.reduce((a, t) => a + t[1], 0);
  let r = Math.random() * tot;
  for (const t of TYPES) { r -= t[1]; if (r <= 0) return t; }
  return TYPES[0];
}

function nouvelleOffre(t0) {
  const [type, , [dmin, dmax]] = tirerType();
  const params = type === 'mystere' ? {} : parametresAleatoires(type);
  const base = prixBase({ type, params });
  const offre = { uid: `${t0.toString(36)}${Math.random().toString(36).slice(2, 6)}`, type, params, base, debut: t0, remise: 0, flash: false, baisse: false };
  let duree = entre(dmin, dmax) * H;
  const r = Math.random();
  if (r < config.get('probaFlash')) {
    offre.flash = true; offre.remise = Math.round(entre(40, 50)); duree = entre(2, 6) * H;
  } else {
    if (Math.random() < config.get('probaRemise')) offre.remise = Math.round(entre(10, 30));
    if (Math.random() < config.get('probaBaisse')) offre.baisse = true;
  }
  offre.fin = t0 + duree;
  return offre;
}

/* Remise effective à l'instant t (la baisse progressive s'ajoute à la remise de départ). */
export function remiseEffective(o, t = Date.now()) {
  let r = o.remise;
  if (o.baisse) {
    if (o.fin - t <= 6 * H) r += 25;
    else if (t >= (o.debut + o.fin) / 2) r += 10;
  }
  return Math.min(r, 90);
}
export function prix(o, t = Date.now()) {
  return Math.round(o.base * (1 - remiseEffective(o, t) / 100) / 100) * 100;
}

/* Met la boutique à jour : expirations et remplissage des emplacements vides. */
export function majBoutique(t = Date.now()) {
  const e = b();
  for (const em of e.emplacements) {
    if (em.offre && em.offre.fin <= t) { em.offre = null; em.prochaine = t + entre(config.get('remplissageMinH'), config.get('remplissageMaxH')) * H; }
    if (!em.offre && em.prochaine <= t) { em.offre = nouvelleOffre(Math.max(t, em.prochaine)); }
  }
  sauvegarder();
  return e.emplacements;
}

export function libelleOffre(o) {
  return o.type === 'mystere' ? 'Mystère' : libelle(o);
}

/* Achat unique : débit, puis le paquet rejoint l'inventaire. */
export function acheter(uid) {
  const e = b();
  const em = e.emplacements.find(x => x.offre?.uid === uid);
  if (!em) return { ok: false, raison: 'offre disparue' };
  const p = prix(em.offre);
  if (!debiterEclats(p, `Boutique : ${libelleOffre(em.offre)}`, 'boutique')) return { ok: false, raison: 'solde insuffisant' };
  ajouterSpecial(em.offre.type, em.offre.type === 'mystere' ? {} : em.offre.params, 'boutique');
  em.offre = null;
  em.prochaine = Date.now() + entre(config.get('remplissageMinH'), config.get('remplissageMaxH')) * H;
  sauvegarder();
  document.dispatchEvent(new CustomEvent('gacha:eclats-changes'));
  return { ok: true, prix: p };
}
