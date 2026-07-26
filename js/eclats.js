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

import { etat, sauvegarder } from './etat.js';

/* Valeur d'un doublon, en Éclats, selon la rareté de la carte. */
export const BAREME_VENTE = {
  commune: 100,
  rare: 500,
  epique: 1500,
  mythique: 2500,
  legendaire: 5000,
};

/* Montant crédité par la vente d'un doublon de cette carte. */
export function valeurVente(carte) {
  return BAREME_VENTE[carte?.rarete] ?? BAREME_VENTE.commune;
}

// Vend UN doublon : jamais le dernier exemplaire. Retourne le montant ou null.
export function vendreDoublon(carte) {
  const qte = etat.cartes[carte.id] || 0;
  if (qte < 2) return null;
  const montant = valeurVente(carte);
  etat.cartes[carte.id] = qte - 1;
  etat.eclats += montant;
  sauvegarder();
  return montant;
}

// Retire des Éclats du compteur (simple décompte, aucune action automatisée).
export function consommerEclats(montant) {
  montant = Math.floor(montant);
  if (!Number.isFinite(montant) || montant <= 0 || montant > etat.eclats) return false;
  etat.eclats -= montant;
  sauvegarder();
  return true;
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
