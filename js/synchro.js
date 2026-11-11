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
// un geste du joueur pendant la lecture du serveur (retour au premier plan) : la copie
// distante, lue avant ce geste, ne doit pas l'écraser (ticket gratté deux fois, 11/11/2026)
let modifPendant = false;

// Empreinte de ce que le joueur a fait, sans ce qui bouge tout seul (horloge du minuteur,
// solde relu dans le registre commun, données de synchro) : seule une vraie action date la partie.
const VOLATILS = new Set(['serveur', 'eclats', 'eclatsAttente', 'lastTs', 'progression', 'lastTick']);
function empreinte() {
  const s = JSON.stringify(etat, (k, v) => (VOLATILS.has(k) ? undefined : v));
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return `${s.length}:${h >>> 0}`;
}
let derniere = empreinte();

let fusionne = false;   // la copie du serveur a été complétée par des gains de cet appareil
function remplacerEtat(nouveau) {
  fusionne = false;
  // Filet : ce que cet appareil a gagné ne disparaît pas avec la copie du serveur
  // (même partie seulement : après une remise à zéro, rien n'est repris).
  const local = { creeLe: etat.creeLe, cartes: { ...(etat.cartes || {}) }, defi: etat.defi, lues: { ...(etat.lues || {}) } };
  for (const k of Object.keys(etat)) delete etat[k];
  Object.assign(etat, nouveau);
  if (local.creeLe && local.creeLe === etat.creeLe) {
    etat.cartes ??= {};
    for (const [id, q] of Object.entries(local.cartes)) if (q > 0 && !(etat.cartes[id] > 0)) { etat.cartes[id] = q; fusionne = true; }
    const nLues = Object.keys(etat.lues || {}).length;
    etat.lues = { ...local.lues, ...(etat.lues || {}) };
    if (Object.keys(etat.lues).length !== nLues) fusionne = true;
    if (local.defi?.gagne && local.defi.jour === etat.defi?.jour && !etat.defi.gagne) { etat.defi = local.defi; fusionne = true; }
  }
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
  if (!etat.serveur?.actif) return;
  const e = empreinte();
  if (e === derniere) return;   // rien de joué depuis le dernier enregistrement
  if (synchroEnCours) { modifPendant = true; return; }
  derniere = e;
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
  modifPendant = false;
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
      if ((distantMaj >= localMaj && !modifPendant) || !etat.serveur.actif) {
        remplacerEtat(distant.etat);
        change = true;
      }
      etat.serveur ??= {};
      etat.serveur.actif = true;
      etat.serveur.migre = true;
      if (!change) await ecrireEtat(etat);
    }
    synchroEnCours = false;
    // la partie qu'on garde (serveur, ou appareil + actions faites pendant la lecture) devient la référence ;
    // si l'appareil a gagné quelque chose que le serveur n'avait pas, la fusion est renvoyée
    derniere = change && fusionne ? null : empreinte();
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
