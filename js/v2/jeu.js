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
import * as serie2 from './ecrans/serie.js';
import * as journal from './ecrans/journal.js';

const PRINCIPAUX = { accueil, questions, collection, boutique, plus };
// écrans secondaires : l'ancienne interface, confinée (css/ancien.css), sous l'onglet Plus
const SECONDAIRES = {
  historique: ['Historique', rendreEcranHistorique], serie: ['Série', serie2.rendre, true], paquets: ['Paquets', journal.rendre, true], objectifs: ['Objectifs', rendreEcranObjectifs],
  eclats: ['Éclats', rendreEcranEclats], reglages: ['Réglages', rendreEcranReglages],
};

let ecran = 'accueil';
export const ecranActif = () => ecran;

function rendre(nom = ecran, options = {}) {
  if (PRINCIPAUX[nom]) return PRINCIPAUX[nom].rendre($(`#${nom}`), options);
  const [titre, fn, v2] = SECONDAIRES[nom];
  const z = $('#secondaire');
  z.innerHTML = `<div class="grand-titre sec-titre"><button class="retour" id="sec-retour" aria-label="Retour"><i class="ph-bold ph-caret-left"></i></button><h1>${titre}</h1></div><div class="${v2 ? '' : 'ancien '}sec-corps" id="ecran-${nom}"></div>`;
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
  // chaque gain dit d'où il vient : récompenses (série, objectifs…) et paquets gagnés par le temps
  document.addEventListener('wikideck:notif', (e) => toast('ph-gift', e.detail, 4500));
  const ORIGINES = { minuteur: 'Minuteur', question: 'Questions', qdj: 'Question du jour', ticket: 'Ticket', temps: 'Temps' };
  document.addEventListener('wikideck:paquet', (e) => {
    const { src, n } = e.detail;
    if (ORIGINES[src]) toast('ph-package', `+${n} paquet${n > 1 ? 's' : ''} · ${ORIGINES[src]}`, 4500);
  });
  await demarrerSynchro();
  // remise à zéro unique de toute la partie (demandée le 08/11/2026), sauf les Éclats :
  // ils appartiennent au registre commun, et leur file d'envoi doit partir intacte
  const correctifs = etat.correctifs || {};
  if (!correctifs.remiseAZero20261108) {
    const maintenant = Date.now();
    correctifs.remiseAZero20261108 = { le: maintenant, prets: etat.paquets?.prets ?? 0, cartes: Object.keys(etat.cartes || {}).length, config: etat.configUtilisateur || {} };
    correctifs.paquets20261108 ??= { le: maintenant };
    const garde = { serveur: etat.serveur, eclats: etat.eclats || 0, eclatsAttente: etat.eclatsAttente || [], correctifs };
    for (const k of Object.keys(etat)) delete etat[k];
    Object.assign(etat, { version: 1, creeLe: maintenant, cartes: {}, paquets: null, station: null, configUtilisateur: {}, prefs: { afficherVides: true } }, garde);
    sauvegarderMaintenant();
  }
  // marques « lue » posées par le simple affichage des fiches (bug corrigé le 11/11/2026) : effacées une fois
  if (!etat.correctifs?.lues20261111) {
    etat.correctifs = { ...(etat.correctifs || {}), lues20261111: { le: Date.now(), effacees: Object.keys(etat.lues || {}).length } };
    etat.lues = {};
    sauvegarderMaintenant();
  }
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
  suivreClavier();
  window.gachaDebug = { etat, donnees, sauvegarderMaintenant, aller };
  sauvegarderMaintenant();

  setTimeout(() => { $('#attente').classList.add('parti'); setTimeout(() => $('#attente')?.remove(), 500); }, Math.max(0, 700 - (performance.now() - debut)));
}

/* Clavier du téléphone : il recouvre le bas de l'écran sans le redimensionner.
   On mesure la place qu'il prend et on remonte la question juste au-dessus du champ. */
function suivreClavier() {
  const vv = window.visualViewport;
  if (!vv) return;
  let attente = null;
  const caler = () => {
    const clavier = Math.max(0, Math.round(innerHeight - vv.height - vv.offsetTop));
    document.documentElement.style.setProperty('--clavier', `${clavier}px`);
    const champ = document.activeElement;
    if (clavier < 80 || champ?.tagName !== 'INPUT') return;
    const carte = champ.closest('.fiche, .ecran')?.querySelector('.q-carte');
    if (carte) { clearTimeout(attente); attente = setTimeout(() => carte.scrollIntoView({ block: 'start', behavior: 'smooth' }), 60); }
  };
  vv.addEventListener('resize', caler);
  document.addEventListener('focusin', (e) => { if (e.target.tagName === 'INPUT') setTimeout(caler, 350); });
  document.addEventListener('focusout', () => setTimeout(caler, 100));
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
