// Portefeuille d'Éclats : point de passage unique de tout crédit et débit.
// Hors connexion, le compteur local suffit. Connecté, chaque mouvement part au
// registre commun (Centrale) avec une clé d'idempotence ; s'il ne passe pas
// (réseau), il attend dans une file et repart au prochain essai.

import { etat, sauvegarder } from './etat.js';
import { estConnecte, crediter as crediterServeur, debiter as debiterServeur, solde, uuid } from './serveur.js';

function file() { return (etat.eclatsAttente ??= []); }
const modeServeur = () => !!etat.serveur?.actif && estConnecte();
const signaler = () => document.dispatchEvent(new CustomEvent('gacha:eclats-changes'));

export function crediterEclats(montant, motif, type = 'recompense') {
  montant = Math.round(montant);
  if (!(montant > 0)) return;
  etat.eclats += montant;
  if (modeServeur()) file().push({ sens: 1, montant, motif, type, cle: uuid() });
  sauvegarder(); signaler();
  vider();
}

/* Débit plafonné au solde ; retourne false si le solde ne suffit pas. */
export function debiterEclats(montant, motif, type = 'achat') {
  montant = Math.round(montant);
  if (!(montant > 0) || etat.eclats < montant) return false;
  etat.eclats -= montant;
  if (modeServeur()) file().push({ sens: -1, montant, motif, type, cle: uuid() });
  sauvegarder(); signaler();
  vider();
  return true;
}

let enCours = false;
/* Envoie la file au registre, puis aligne le compteur sur le solde commun. */
export async function vider() {
  if (enCours || !modeServeur()) return;
  enCours = true;
  try {
    while (file().length) {
      const op = file()[0];
      try {
        if (op.sens > 0) await crediterServeur(op.montant, op.motif, op.type, op.cle);
        else await debiterServeur(op.montant, op.motif, op.type, op.cle);
      } catch (e) {
        if (!e.status || e.status >= 500 || e.status === 401) break;   // réseau ou session : on réessaiera
        console.warn('Mouvement refusé par le registre :', op, e.message);   // refus métier : abandonné
      }
      file().shift();
      sauvegarder();
    }
    if (!file().length) {
      etat.eclats = await solde();
      sauvegarder(); signaler();
    }
  } catch (e) {
    console.warn('Registre injoignable :', e.message);
  } finally {
    enCours = false;
  }
}
