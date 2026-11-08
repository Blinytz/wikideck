// Point d'entrée du jeu v2 : mêmes moteurs que l'ancienne interface (js/*.js),
// nouvelle interface (js/v2/ecrans/*.js). L'ancienne reste servie par ancien.html.

import { etat, sauvegarderMaintenant } from '../etat.js';
import { chargerDonnees, donnees } from '../donnees.js';
import { tickPaquets } from '../ecran-paquets.js';
import { config } from '../config.js';
import { initStation } from '../station.js';
import { initEclats } from '../eclats.js';
import { reconcilierCatalogue } from '../recompenses.js';
import { traiterJours } from '../serie.js';
import { verifierObjectifs } from '../objectifs.js';
import { chargerQuestions } from '../source-questions.js';
import { demarrerSynchro } from '../synchro.js';
import { vider } from '../portefeuille.js';
import { rendreEcranHistorique } from '../ecran-historique.js';
import { rendreEcranSerie } from '../ecran-serie.js';
import { rendreEcranObjectifs } from '../ecran-objectifs.js';
import { rendreEcranEclats, majEclatsUI } from '../ecran-eclats.js';
import { rendreEcranReglages } from '../ecran-reglages.js';
import '../vente.js';
import { son } from './son.js';
import { $, vibrer, fr, transition, toast, compter } from './commun.js';
import { poserHabillages } from './effets.js';
import * as accueil from './ecrans/accueil.js';
import * as questions from './ecrans/questions.js';
import * as collection from './ecrans/collection.js';
import * as boutique from './ecrans/boutique.js';
import * as plus from './ecrans/plus.js';

const PRINCIPAUX = { accueil, questions, collection, boutique, plus };
// écrans secondaires : l'ancienne interface, confinée (css/ancien.css), sous l'onglet Plus
const SECONDAIRES = {
  historique: ['Historique', rendreEcranHistorique], serie: ['Série', rendreEcranSerie], objectifs: ['Objectifs', rendreEcranObjectifs],
  eclats: ['Éclats', rendreEcranEclats], reglages: ['Réglages', rendreEcranReglages],
};

let ecran = 'accueil';
export const ecranActif = () => ecran;

function rendre(nom = ecran, options = {}) {
  if (PRINCIPAUX[nom]) return PRINCIPAUX[nom].rendre($(`#${nom}`), options);
  const [titre, fn] = SECONDAIRES[nom];
  const z = $('#secondaire');
  z.innerHTML = `<div class="grand-titre sec-titre"><button class="retour" id="sec-retour" aria-label="Retour"><i class="ph-bold ph-caret-left"></i></button><h1>${titre}</h1></div><div class="ancien sec-corps" id="ecran-${nom}"></div>`;
  $('#sec-retour', z).addEventListener('click', () => aller('plus'));
  fn($(`#ecran-${nom}`, z), options);
}

export function aller(nom, options = {}) {
  if (!PRINCIPAUX[nom] && !SECONDAIRES[nom]) return;
  if (nom === ecran && nom !== 'collection' && !SECONDAIRES[nom]) return;
  vibrer(); son('onglet');
  const onglet = SECONDAIRES[nom] ? 'plus' : nom;
  transition(() => {
    ecran = nom; document.body.dataset.ecran = onglet;
    const sec = SECONDAIRES[nom] ? 'secondaire' : nom;
    document.querySelectorAll('.page > .ecran').forEach((e) => e.classList.toggle('actif', e.id === sec));
    document.querySelectorAll('#onglets button').forEach((b) => {
      const a = b.dataset.aller === onglet, i = b.querySelector('i');
      b.classList.toggle('actif', a);
      i.className = `${a ? 'ph-fill' : 'ph'} ${i.className.split(' ').find((x) => x.startsWith('ph-') && x !== 'ph-fill')}`;
    });
    rendre(nom, options);
    scrollTo(0, 0);
  });
}

function majSolde() {
  document.querySelectorAll('.solde-v').forEach((s) => compter(s, 'solde', Math.round(etat.eclats || 0), 700));
}

async function demarrer() {
  const debut = performance.now();
  try {
    await chargerDonnees();
  } catch (err) {
    $('#attente .nom').textContent = `Données indisponibles (${err.message})`;
    return;
  }
  // la v2 affiche « numéro / total » sur chaque carte
  // et les images en adresse absolue : une url() relative portée par une variable CSS
  // se résout depuis la feuille de style (css/), pas depuis la page
  const abs = (u) => (u ? new URL(u, location.href).href : u);
  for (const col of donnees.collections) for (const c of col.cartes) { c.total = col.nbCartes; c.imageUrl = abs(c.imageUrl); c.thumbUrl = abs(c.thumbUrl); }

  poserHabillages();
  await demarrerSynchro();
  initEclats();
  if (config.get('stationActive')) initStation();
  const changements = reconcilierCatalogue();
  traiterJours();
  await chargerQuestions();
  verifierObjectifs();

  document.addEventListener('click', (e) => { const b = e.target.closest('[data-aller]'); if (b) aller(b.dataset.aller, b.dataset.aller === 'collection' ? { racine: true } : {}); });
  document.addEventListener('v2:aller', (e) => aller(e.detail.nom, e.detail.options));
  document.addEventListener('wikideck:aller', (e) => aller(e.detail));
  document.addEventListener('v2:rafraichir', () => rendre());
  document.addEventListener('wikideck:notif', (e) => toast('ph-bell', e.detail));
  document.addEventListener('gacha:eclats-changes', majSolde);

  rendre('accueil');
  const ancre = location.hash.slice(1);
  if (ancre) aller(ancre);
  window.addEventListener('hashchange', () => aller(location.hash.slice(1)));
  if (changements?.length) toast('ph-arrows-clockwise', `${changements.length} rareté${changements.length > 1 ? 's' : ''} modifiée${changements.length > 1 ? 's' : ''}`);

  setInterval(() => {
    tickPaquets();
    PRINCIPAUX[ecran]?.tic?.($(`#${ecran}`));
    if (ecran === 'eclats') majEclatsUI($('#ecran-eclats'));
  }, 1000);

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState !== 'visible') return;
    demarrerSynchro().finally(() => { tickPaquets(); traiterJours(); vider(); majSolde(); rendre(); });
  });

  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' }).catch((e) => console.warn('Service worker non enregistré :', e));
  surveillerVersion();
  window.gachaDebug = { etat, donnees, sauvegarderMaintenant, aller };
  sauvegarderMaintenant();

  setTimeout(() => { $('#attente').classList.add('parti'); setTimeout(() => $('#attente')?.remove(), 500); }, Math.max(0, 700 - (performance.now() - debut)));
}

/* Une appli installée garde le code de son premier lancement : on relit l'estampille
   de publication (version.json, écrite par le workflow) au retour au premier plan,
   et on recharge si elle a changé, sauf pendant une ouverture, un ticket ou une saisie. */
let versionChargee = null;
async function lireVersion() {
  try { return (await (await fetch('version.json', { cache: 'no-store' })).json()).version; } catch { return null; }
}
function occupe() {
  return document.querySelector('.ov2, .fiche') || ['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName);
}
async function surveillerVersion() {
  versionChargee = await lireVersion();
  const verifier = async () => {
    if (document.visibilityState !== 'visible' || !versionChargee) return;
    const v = await lireVersion();
    if (v && v !== versionChargee && !occupe()) { sauvegarderMaintenant(); location.reload(); }
  };
  document.addEventListener('visibilitychange', verifier);
  window.addEventListener('focus', verifier);
  setInterval(verifier, 10 * 60e3);
}

demarrer();
