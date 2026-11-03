// Point d'entrée : chargement des données, navigation, boucle d'horloge.

import { etat, sauvegarderMaintenant } from './etat.js';
import { chargerDonnees, donnees } from './donnees.js';
import { formaterNombre, esc, NOMS_RARETE } from './ui.js';
import { tickPaquets } from './ecran-paquets.js';
import { rendreEcranAccueil } from './ecran-accueil.js';
import { rendreEcranCollection } from './ecran-collection.js';
import { rendreEcranStation, majStationUI } from './ecran-station.js';
import { initStation } from './station.js';
import { rendreEcranReglages } from './ecran-reglages.js';
import { rendreEcranHistorique } from './ecran-historique.js';
import { rendreEcranQuestions } from './ecran-questions.js';
import { rendreEcranBoutique } from './ecran-boutique.js';
import { rendreEcranSerie } from './ecran-serie.js';
import { rendreEcranObjectifs } from './ecran-objectifs.js';
import { rendreEcranPlus } from './ecran-plus.js';
import { config } from './config.js';
import { rendreEcranEclats, majEclatsUI } from './ecran-eclats.js';
import { initEclats } from './eclats.js';
import { reconcilierCatalogue } from './recompenses.js';
import { traiterJours } from './serie.js';
import { verifierObjectifs } from './objectifs.js';
import { chargerQuestions } from './source-questions.js';
import './vente.js';   // branche la vente de doublons sur le détail de carte

const ecrans = {
  accueil: rendreEcranAccueil,
  questions: rendreEcranQuestions,
  collection: rendreEcranCollection,
  boutique: rendreEcranBoutique,
  plus: rendreEcranPlus,
  historique: rendreEcranHistorique,
  serie: rendreEcranSerie,
  objectifs: rendreEcranObjectifs,
  station: rendreEcranStation,
  eclats: rendreEcranEclats,
  reglages: rendreEcranReglages,
};
// écrans du menu « Plus » : l'onglet Plus reste allumé
const SOUS_PLUS = ['historique', 'serie', 'objectifs', 'eclats', 'reglages', 'station'];

export let ecranActif = 'accueil';

export function afficherEcran(nom, options = {}) {
  ecranActif = nom;
  const onglet = SOUS_PLUS.includes(nom) ? 'plus' : nom;
  for (const btn of document.querySelectorAll('#navbar button')) {
    btn.classList.toggle('actif', btn.dataset.ecran === onglet);
  }
  for (const sec of document.querySelectorAll('.ecran')) {
    sec.classList.toggle('visible', sec.id === `ecran-${nom}`);
  }
  ecrans[nom](document.getElementById(`ecran-${nom}`), options);
}

export function rafraichirEntete() {
  document.getElementById('eclats-total').textContent = formaterNombre(etat.eclats);
}

function toast(texte) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = texte;
  document.getElementById('overlays').append(el);
  setTimeout(() => el.classList.add('sort'), 4200);
  setTimeout(() => el.remove(), 4800);
}

function recapRaretes(changements) {
  if (!changements.length) return;
  const o = document.createElement('div');
  o.className = 'overlay-carte';
  o.innerHTML = `<div class="fond-overlay"></div><div class="contenu-overlay carte-panneau recap-raretes">
    <h2>Raretés modifiées</h2>
    ${changements.map(c => `<div class="ligne-inventaire"><span>${esc(c.carte.nom)}</span>
      <span class="texte-doux">${NOMS_RARETE[c.avant]} → <b>${NOMS_RARETE[c.carte.rarete]}</b></span></div>`).join('')}
    <button class="btn btn-primaire">OK</button></div>`;
  document.getElementById('overlays').append(o);
  o.querySelector('.btn').addEventListener('click', () => o.remove());
}

async function demarrer() {
  try {
    await chargerDonnees();
  } catch (err) {
    document.getElementById('chargement').textContent =
      `Impossible de charger les données de cartes (${err.message}). ` +
      'Vérifie ta connexion pour le premier lancement.';
    return;
  }
  document.getElementById('chargement').remove();

  initEclats();          // purge de l'ancien état de taux, s'il subsiste
  if (config.get('stationActive')) initStation();   // Station désactivée par défaut (code conservé)
  const changements = reconcilierCatalogue();
  traiterJours();
  await chargerQuestions();
  verifierObjectifs();

  for (const btn of document.querySelectorAll('#navbar button')) {
    btn.addEventListener('click', () => afficherEcran(btn.dataset.ecran));
  }
  document.getElementById('chip-eclats').addEventListener('click',
    () => afficherEcran('eclats'));
  document.addEventListener('wikideck:aller', e => afficherEcran(e.detail));
  document.addEventListener('wikideck:notif', e => toast(e.detail));

  afficherEcran('accueil');
  rafraichirEntete();
  recapRaretes(changements);

  // Horloge : 1 tick/s pour l'UI et les moteurs (chacun gère sa propre cadence).
  setInterval(() => {
    tickPaquets();
    if (ecranActif === 'accueil') rendreEcranAccueil(document.getElementById('ecran-accueil'), { tick: true });
    if (ecranActif === 'boutique') rendreEcranBoutique(document.getElementById('ecran-boutique'), { tick: true });
    if (ecranActif === 'eclats') majEclatsUI(document.getElementById('ecran-eclats'));
    if (ecranActif === 'station') majStationUI(document.getElementById('ecran-station'));
    rafraichirEntete();
  }, 1000);

  document.addEventListener('gacha:eclats-changes', rafraichirEntete);

  // Retour au premier plan : rattrapage immédiat (paquets, jours de série).
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      tickPaquets(); traiterJours(); rafraichirEntete();
      afficherEcran(ecranActif);
    }
  });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(err =>
      console.warn('Service worker non enregistré :', err));
  }

  // Accès console pour le débogage (projet perso) — pas utilisé par l'app.
  window.gachaDebug = { etat, donnees, sauvegarderMaintenant, afficherEcran };
  sauvegarderMaintenant();
}

demarrer();
