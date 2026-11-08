// Écran Questions (v2) : porté de l'essai de design (essais/design.html, rendreQuestions)
// sur le vrai moteur js/questions.js. Le moteur crédite lui-même le temps gagné.

import { etat } from '../../etat.js';
import { config } from '../../config.js';
import { donnees } from '../../donnees.js';
import {
  NIVEAUX, propositions, choisir, questionEnCours, questionDuJour, commencerQuestionDuJour,
  repondre, corriger, suite, multiplicateur, gainMinutes, nbQuestions, normaliser,
} from '../../questions.js';
import { htmlCarte, esc } from '../carte.js';
import { fiche } from '../fiche.js';
import { son } from '../son.js';
import { quantite } from '../mecaniques.js';
import { $, vibrer, transition, teinte, cascade, fmtMin } from '../commun.js';

// mêmes paliers que multiplicateur() du moteur ; couleur et halo de la flamme par palier
const PALIERS = [[3, 1.5], [5, 2], [10, 3], [20, 4]];
const FLAMMES = { 1: ['#6b6873', 0], 1.5: ['#ff9f5a', 6], 2: ['#ff7a3d', 10], 3: ['#f2c66d', 14], 4: ['#9fd8ff', 20] };
const fmtX = (x) => '×' + String(x).replace('.', ',');
const fmtGain = (m) => fmtMin(Math.round(m));
const niveau = (d) => NIVEAUX[d] || '';

// dernier verdict affiché (survit à un re-rendu tant qu'on n'a pas fait « Suivante »)
let verdict = null;

/* ---------- carte liée : la réponse est peut-être une carte du catalogue ---------- */
let indexNoms = null, tailleIndex = -1;
function carteLiee(reponse) {
  if (!indexNoms || tailleIndex !== donnees.parId.size) {
    indexNoms = new Map(); tailleIndex = donnees.parId.size;
    for (const col of donnees.collections) for (const c of col.cartes) {
      if (c.archivee && !quantite(c.id)) continue;
      for (const n of [c.nom, c.titrePage, (c.titrePage || '').replace(/\s*\([^)]*\)/g, '')]) {
        const k = n && normaliser(n);
        if (k && !indexNoms.has(k)) indexNoms.set(k, c);
      }
    }
  }
  for (const r of [reponse, String(reponse || '').replace(/\s*\([^)]*\)/g, '')]) {
    const c = indexNoms.get(normaliser(r)); if (c) return c;
  }
  return null;
}

/* ---------- en-tête : multiplicateur et suite ---------- */
const htmlMulti = (classe = '') => { const m = multiplicateur(suite()); return `<span class="multi${m > 1 ? ' chaud' : ''}${classe}"><i class="ph-fill ph-lightning"></i>${fmtX(m)}</span>`; };
function htmlSuite() {
  const s = suite(), m = multiplicateur(s), [fc, glow] = FLAMMES[m] || FLAMMES[1];
  const base = [...PALIERS].reverse().find(([n]) => s >= n)?.[0] ?? 0, pp = PALIERS.find(([n]) => n > s);
  return `<div class="suite" style="--fc:${fc};--glow:${glow}px">
    <div class="flamme${s ? '' : ' eteinte'}"><i class="ph-fill ph-fire" style="--h:${Math.min(40, 22 + s * 1.2)}px"></i></div>
    <div class="suite-l"><b>${s}</b></div>
    <div class="suite-barre">${pp ? `<div class="barre2"><i style="width:${(s - base) / (pp[0] - base) * 100}%"></i></div><span>${fmtX(pp[1])} à ${pp[0]}</span>` : '<span>Maximum</span>'}</div></div>`;
}
const enteteQuestions = () => `<div class="grand-titre"><div><h1>Questions</h1></div>${htmlMulti()}</div>${htmlSuite()}`;
function majEntete(z, monte) {
  const mu = $('.multi', z), su = $('.suite', z);
  if (mu) mu.outerHTML = htmlMulti(monte ? ' monte' : '');
  if (su) su.outerHTML = htmlSuite();
}

function majPastille() {
  const qdj = questionDuJour();
  if (!qdj?.question || qdj.faite) $('#onglets [data-aller="questions"] .pastille')?.remove();
}

function gagnerMinutes(m) {
  const g = document.createElement('div'); g.className = 'gain'; g.innerHTML = `<i class="ph-bold ph-timer"></i>−${fmtGain(m)}`;
  document.body.append(g); setTimeout(() => g.remove(), 1200);
}

/* ---------- rendu ---------- */
export function rendre(z) {
  z.style.removeProperty('--t');
  if (!nbQuestions()) {
    z.innerHTML = `<div class="grand-titre"><div><h1>Questions</h1></div></div>
      <div class="vide-etat"><i class="ph ph-lightbulb"></i>Aucune question</div>`;
    return;
  }
  majPastille();
  if (verdict) return rendreQuestion(z, verdict, true);

  let q = questionEnCours();
  if (q && !q.question) { etat.quiz.enCours = null; q = null; } // question retirée de la banque
  if (!q) {
    const qdj = questionDuJour();
    if (qdj?.question && !qdj.faite) q = commencerQuestionDuJour();
  }
  if (q?.question) return rendreQuestion(z, q, false);

  let props = propositions();
  if (!props.length && etat.quiz?.propositions?.length) { etat.quiz.propositions = null; props = propositions(); }
  const s1 = suite() + 1;
  z.innerHTML = `${enteteQuestions()}
    <div class="props">${props.map((p) => { const t = teinte(p.theme); return `<button class="bloc prop pressable" data-id="${esc(p.id)}" style="--t:${t.c}">
      <div class="meta"><span class="tag teinte"><i class="ph-fill ${t.ic}"></i>${esc(p.theme || 'Culture générale')}</span><span class="diff">${[1, 2, 3, 4, 5].map((d) => `<i class="${d <= p.difficulte ? 'on' : ''}"></i>`).join('')}</span></div>
      <div class="niv">${niveau(p.difficulte)}</div>
      <div class="gain-prop"><i class="ph-bold ph-timer"></i>−${fmtGain(gainMinutes(p, s1))}</div></button>`; }).join('')}</div>`;
  cascade($('.props', z));
  z.querySelectorAll('.prop').forEach((b) => b.addEventListener('click', () => {
    vibrer(); son('tap');
    transition(() => { choisir(b.dataset.id); rendre(z); });
  }));
}

// q : question en cours, ou entrée du moteur si `repondue` (verdict déjà rendu)
function rendreQuestion(z, q, repondue) {
  const t = teinte(q.theme);
  const gain = repondue ? null : (q.qdj ? config.get('gainQuestionDuJour') : gainMinutes(q, suite() + 1));
  z.style.setProperty('--t', t.c);
  z.innerHTML = `${enteteQuestions()}
    <div class="bloc q-carte${q.qdj ? ' qdj-c' : ''}" id="qc">
      <div class="meta"><span class="tag${q.qdj ? ' or' : ' teinte'}">${q.qdj ? '<i class="ph-fill ph-star"></i>Question du jour' : `<i class="ph-fill ${t.ic}"></i>${esc(q.theme || 'Culture générale')}`}</span><span class="tag" id="qg"><i class="ph-bold ph-timer"></i>−${fmtGain(repondue ? (q.correct ? q.gain : 0) : gain)}</span></div>
      <p class="q-texte">${esc(q.question)}</p>
    </div>
    <form class="q-form" id="qf"><input id="qr" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="send" placeholder="Réponse"><button disabled><i class="ph-bold ph-arrow-up"></i></button></form>
    <div class="verdict" id="qv"></div><div id="liee"></div>`;
  const inp = $('#qr', z), bt = $('#qf button', z);
  inp.addEventListener('input', () => (bt.disabled = !inp.value.trim()));
  if (repondue) {
    inp.value = q.saisie || ''; inp.disabled = true;
    $('#qc', z).classList.add(q.correct ? 'juste' : 'faux');
    poserVerdict(z, q);
    return;
  }
  $('#qf', z).addEventListener('submit', (e) => {
    e.preventDefault();
    if (!inp.value.trim() || inp.disabled) return;
    inp.disabled = true; bt.disabled = true; inp.blur();
    const v = repondre(inp.value);
    if (!v) { rendre(z); return; }
    verdict = v;
    if (v.qdj) majPastille();
    const debloque = multiplicateur(v.suiteApres) > multiplicateur(v.suiteAvant);
    $('#qc', z).classList.add(v.correct ? 'juste' : 'faux');
    vibrer(v.correct ? 20 : [30, 40, 30]);
    son(!v.correct ? 'faux' : debloque ? 'palier' : 'juste');
    if (v.correct) gagnerMinutes(v.gain);
    majEntete(z, debloque);
    poserVerdict(z, v);
  });
}

function detailVerdict(v) {
  const avant = multiplicateur(v.suiteAvant), apres = multiplicateur(v.suiteApres);
  if (v.correct) return !v.qdj && apres > avant ? `${fmtX(apres)} débloqué` : `−${fmtGain(v.gain)}`;
  if (!v.qdj && avant > 1) return `Suite perdue · ${fmtX(1)}`;
  const j = config.get('delaiRatee');
  return `Revient dans ${j} jour${j > 1 ? 's' : ''}`;
}

function poserVerdict(z, v) {
  const el = $('#qv', z);
  el.className = `verdict vu ${v.correct ? 'ok' : 'ko'}`;
  el.innerHTML = `<div class="ico"><i class="ph-bold ${v.correct ? 'ph-check' : 'ph-x'}"></i></div>
    <div class="txt"><b>${esc(v.reponse)}</b><span>${detailVerdict(v)}</span></div>
    <div class="q-actions"><button class="btn2 fantome petit q-corr" id="qx">${v.correct ? 'J’avais faux' : 'J’avais bon'}</button><button class="btn2 petit" id="suiv">Suivante</button></div>`;
  const qg = $('#qg', z);
  if (qg) qg.innerHTML = `<i class="ph-bold ph-timer"></i>−${fmtGain(v.correct ? v.gain : 0)}`;
  if (!$('#liee', z).childElementCount) lier(z, v.reponse);
  $('#suiv', z).addEventListener('click', () => { verdict = null; son('tap'); transition(() => rendre(z)); });
  $('#suiv', z).focus({ preventScroll: true });
  $('#qx', z).addEventListener('click', () => {
    // la correction ne vaut que pour la dernière réponse enregistrée par le moteur
    if (etat.quiz?.derniere?.t !== v.t || etat.quiz.derniere.id !== v.id) { verdict = null; rendre(z); return; }
    const avant = multiplicateur(suite());
    const n = corriger();
    if (!n) return;
    verdict = n;
    const qc = $('#qc', z);
    qc.classList.remove('juste', 'faux'); void qc.offsetWidth;
    qc.classList.add(n.correct ? 'juste' : 'faux');
    vibrer(n.correct ? 20 : [30, 40, 30]);
    son(n.correct ? 'juste' : 'faux');
    if (n.correct) gagnerMinutes(n.gain);
    majEntete(z, multiplicateur(suite()) > avant);
    poserVerdict(z, n);
  });
}

function lier(z, reponse) {
  const c = carteLiee(reponse), zl = $('#liee', z);
  if (!c || !zl) return;
  const a = quantite(c.id) > 0;
  const col = donnees.colDe.get(c.id);
  zl.innerHTML = `<div class="liee">${a ? htmlCarte(c) : `<div class="silhouette"><img src="${esc(c.thumbUrl)}" alt=""></div>`}
    <div class="txt"><span class="tag ${a ? 'teinte' : ''}" style="--t:${teinte(col?.theme).c}"><i class="ph-fill ${a ? 'ph-cards' : 'ph-magnifying-glass'}"></i>${a ? 'Dans ta collection' : 'À trouver'}</span><b>${esc(c.nom)}</b><span>${esc(c.collection || col?.nom || '')}</span></div></div>`;
  const k = $('.k', zl);
  if (a && k) k.addEventListener('click', () => fiche([c], 0, k));
}
