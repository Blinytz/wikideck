// Synchronisation de l'état de jeu avec le Supabase Éclats.
// Le localStorage n'est plus qu'un cache : au démarrage, l'état le plus récent
// (serveur ou appareil) gagne ; ensuite chaque sauvegarde part au serveur,
// regroupée par paquets de quelques secondes.
//
// Migration unique, au premier passage connecté : l'état de l'appareil
// (cartes, paquets, progression) est envoyé au serveur et les Éclats locaux
// sont transférés au registre commun (Centrale).

import { etat, sauvegarderMaintenant, surSauvegarde } from './etat.js';
import { estConnecte, lireEtat, ecrireEtat, crediter, lireQuestions, utilisateur } from './serveur.js';
import { vider } from './portefeuille.js';
import { definirSource } from './questions.js';

const DELAI_ENVOI = 4000;
let minuterie = null;
let envoiEnCours = false;
let synchroEnCours = false;

function remplacerEtat(nouveau) {
  for (const k of Object.keys(etat)) delete etat[k];
  Object.assign(etat, nouveau);
}

async function envoyer() {
  if (synchroEnCours || envoiEnCours || !etat.serveur?.actif || !estConnecte()) return;
  envoiEnCours = true;
  try {
    await ecrireEtat(etat);
    etat.serveur.envoyeLe = Date.now();
  } catch (e) {
    console.warn('État non envoyé :', e.message);
  } finally {
    envoiEnCours = false;
  }
}

// chaque changement, même hors ligne, date l'état de l'appareil : au prochain
// démarrage connecté, l'état le plus récemment modifié gagne
surSauvegarde(() => {
  if (synchroEnCours || !etat.serveur?.actif) return;
  etat.serveur.modifieLe = Date.now();
  clearTimeout(minuterie);
  minuterie = setTimeout(envoyer, DELAI_ENVOI);
});

/* Au démarrage (ou après connexion). Retourne true si l'état a changé. */
export async function demarrerSynchro() {
  if (!estConnecte()) return false;
  etat.serveur ??= {};
  let change = false;
  synchroEnCours = true;
  try {
    const distant = await lireEtat();
    if (!distant) {
      // premier passage : migration de l'appareil vers le serveur
      if (!etat.serveur.migre) {
        const locaux = Math.round(etat.eclats || 0);
        if (locaux > 0) {
          await crediter(locaux, 'Transfert des Éclats locaux de WikiDeck', 'migration',
            `wikideck-migration-${utilisateur()?.id}`);
        }
        etat.serveur.migre = true;
      }
      etat.serveur.actif = true;
      etat.serveur.modifieLe = Date.now();
      await ecrireEtat(etat);
    } else {
      const distantMaj = distant.etat?.serveur?.modifieLe || 0;
      const localMaj = etat.serveur.modifieLe || 0;
      if (distantMaj >= localMaj || !etat.serveur.actif) {
        remplacerEtat(distant.etat);
        change = true;
      }
      etat.serveur ??= {};
      etat.serveur.actif = true;
      etat.serveur.migre = true;
      if (!change) await ecrireEtat(etat);
    }
    synchroEnCours = false;
    sauvegarderMaintenant();
    await vider();   // aligne le compteur d'Éclats sur le registre commun
  } catch (e) {
    console.warn('Synchronisation impossible :', e.message);
  } finally {
    synchroEnCours = false;
  }
  return change;
}

export async function chargerQuestionsServeur() {
  if (!estConnecte()) return definirSource([]);
  try {
    const q = await lireQuestions();
    definirSource(q);
    try { localStorage.setItem('wikideck-questions-cache', JSON.stringify(q)); } catch {}
  } catch (e) {
    // hors ligne : dernière copie reçue
    try { definirSource(JSON.parse(localStorage.getItem('wikideck-questions-cache') || '[]')); } catch { definirSource([]); }
  }
}

export function forcerEnvoi() { clearTimeout(minuterie); return envoyer(); }
