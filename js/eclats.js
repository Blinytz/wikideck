// Éclats de WikiDeck : compteur local et vente de doublons à un **barème fixe**.
//
// Décision du 26/07/2026 : le taux de change fluctuant (modèle à régimes, courbe,
// rattrapage hors-ligne) est supprimé. Une carte vaut un montant fixe selon sa
// rareté — c'est lisible d'un coup d'œil, et il n'y a plus de « bon moment »
// à guetter pour vendre.
//
// La conversion des Éclats en euros n'a plus lieu ici : elle se fait dans
// Cagnottes, qui gère une Bourse et un taux (voir `apps/cagnottes`).
//
// Ces Éclats restent **locaux à WikiDeck** : l'application n'est pas encore
// raccordée au registre commun de l'écosystème.

import { crediterEclats, debiterEclats } from './portefeuille.js';
import { etat, sauvegarder } from './etat.js';
import { config } from './config.js';

const CLES_VALEUR = {
  commune: 'valeurCommune', rare: 'valeurRare', epique: 'valeurEpique',
  mythique: 'valeurMythique', legendaire: 'valeurLegendaire', pantheon: 'valeurPantheon',
};

/* Valeur de référence d'une carte selon sa rareté actuelle. */
export function valeurReference(rarete) {
  return config.get(CLES_VALEUR[rarete] ?? 'valeurCommune');
}

/* Montant crédité par la revente d'un doublon (30 % de la valeur de référence). */
export function valeurVente(carte) {
  return Math.round(valeurReference(carte?.rarete) * config.get('tauxRevente'));
}

/* Tous les doublons vendables, filtrés par rareté : [{carte, n}] et total. */
export function doublonsVendables(raretes, cartesParId) {
  const lots = [];
  let total = 0;
  for (const [id, q] of Object.entries(etat.cartes)) {
    if (q < 2) continue;
    const carte = cartesParId.get(id);
    if (!carte || !raretes.includes(carte.rarete)) continue;
    lots.push({ carte, n: q - 1 });
    total += (q - 1) * valeurVente(carte);
  }
  return { lots, total };
}

/* Vend tous ces doublons, en gardant toujours un exemplaire. */
export function vendreDoublons(lots) {
  let total = 0;
  for (const { carte, n } of lots) {
    const q = etat.cartes[carte.id] || 0;
    const k = Math.min(n, q - 1);
    if (k <= 0) continue;
    etat.cartes[carte.id] = q - k;
    total += k * valeurVente(carte);
  }
  sauvegarder();
  if (total) crediterEclats(total, 'Revente groupée de doublons', 'revente');
  return total;
}

// Vend UN doublon : jamais le dernier exemplaire. Retourne le montant ou null.
export function vendreDoublon(carte) {
  const qte = etat.cartes[carte.id] || 0;
  if (qte < 2) return null;
  const montant = valeurVente(carte);
  etat.cartes[carte.id] = qte - 1;
  sauvegarder();
  crediterEclats(montant, `Revente d'un doublon : ${carte.nom}`, 'revente');
  return montant;
}

// Retire des Éclats du compteur (simple décompte, aucune action automatisée).
export function consommerEclats(montant) {
  montant = Math.floor(montant);
  if (!Number.isFinite(montant) || montant <= 0) return false;
  return debiterEclats(montant, 'Dépense WikiDeck', 'achat');
}

/*
 * Nettoyage unique de l'ancien moteur de taux : l'état conservait un historique
 * de plusieurs milliers de points, désormais inutile.
 */
export function initEclats() {
  if (etat.tauxEclats) {
    delete etat.tauxEclats;
    sauvegarder();
  }
}
