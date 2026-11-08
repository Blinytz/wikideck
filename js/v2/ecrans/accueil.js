// Accueil v2 : paquet en cours, inventaire, question du jour, carte du jour (défi),
// ticket à gratter, fragments, série, collection, vitrine, dernières cartes.

import { etat } from '../../etat.js';
import { donnees } from '../../donnees.js';
import { config } from '../../config.js';
import { initPaquets, secondesRestantes, ouvrirPaquet } from '../../paquets.js';
import { inventaire, ouvrirSpecial, libelle } from '../../speciaux.js';
import { s as serie, bonnesDuJour, prochainPalier } from '../../serie.js';
import { questionDuJour, estCorrecte } from '../../questions.js';
import { historique } from '../../acquisition.js';
import { htmlCarte, brancherManipulation, iconeRarete, NOMS, RARETES, esc } from '../carte.js';
import { son } from '../son.js';
import { $, vibrer, fr, RANG, fmtTemps, phrase, teinte, cascade, compter, toast, aller, ouvrirFeuille } from '../commun.js';
import { ouvrir, tirageDe } from '../effets.js';
import { fiche, vitrine } from '../fiche.js';
import { htmlFragBande } from '../fragments.js';
import {
  possede, fragments, defi, carteDuJour, questionDefi, repondreDefi, SERIE_DEFI,
  ticket, A_GRATTER, estGros, choisirCase, gratter, encaisserTicket, cartesEnAttente,
} from '../mecaniques.js';

const RAYON = 134, CIRC = 2 * Math.PI * RAYON;
const htmlSolde = () => `<button class="solde pressable" data-aller="eclats"><i class="ph-fill ph-diamond"></i><span class="chiffre solde-v">${fr(etat.eclats || 0)}</span></button>`;
const htmlPerles = (n, k) => `<div class="perles">${Array.from({ length: n }, (_, i) => `<i class="${i < k ? 'on' : ''}"></i>`).join('')}</div>`;
const carte = (id) => donnees.parId.get(id);

/* Les dernières cartes reçues, de la plus récente à la plus ancienne, sans répétition. */
function dernieres(n = 14) {
  const vu = new Set(), out = [];
  const h = historique();
  for (let i = h.length - 1; i >= 0 && out.length < n; i--) {
    for (const x of h[i].cartes) { if (vu.has(x.id)) continue; const c = carte(x.id); if (c) { vu.add(x.id); out.push(c); } if (out.length >= n) break; }
  }
  return out;
}

export function rendre(z) {
  initPaquets();
  const p = etat.paquets;
  const actives = donnees.pool.length, n = donnees.pool.filter(possede).length, pct = n / Math.max(1, actives);
  const der = dernieres();
  const vit = vitrine().map(carte).filter((c) => c && possede(c.id));
  const qdj = questionDuJour(), tq = teinte(qdj?.theme);
  const cdj = carteDuJour(), d = defi(), tc = teinte(donnees.colDe.get(cdj?.id)?.theme);
  const inv = inventaire();
  const se = serie(), bonnes = bonnesDuJour(), objectif = config.get('bonnesParJour');
  const vedette = [...der].sort((a, b) => RANG(b.rarete) - RANG(a.rarete))[0];
  if (vedette) $('#ambiance').style.setProperty('--img', `url('${vedette.imageUrl}')`);

  z.innerHTML = `<div class="barre"><div class="marque">Wiki<em>Deck</em></div>${htmlSolde()}</div>
    <div class="hero" id="hero">
      <div class="orbite">
        <svg viewBox="0 0 280 280"><defs><linearGradient id="degrade-or" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff3c4"/><stop offset="1" stop-color="#e2b35a"/></linearGradient></defs>
          <circle class="fond-anneau" cx="140" cy="140" r="${RAYON}"/><circle class="arc" id="arc" cx="140" cy="140" r="${RAYON}" stroke-dasharray="${CIRC}" stroke-dashoffset="${CIRC}"/><circle class="tete" id="tete-arc" r="4.5" cx="${140 + RAYON}" cy="140"/></svg>
        <div class="paquets${p.prets ? '' : ' aucun'}" id="paquets">
          ${p.prets > 2 ? '<div class="mini-pk derriere2"></div>' : ''}${p.prets > 1 ? '<div class="mini-pk derriere"></div>' : ''}
          <div class="mini-pk devant"><div class="k-mono">W</div></div>
          ${p.prets > 1 ? `<span class="nb-paquets">${p.prets}</span>` : ''}
        </div>
      </div>
      ${p.prets ? '<button class="btn2 or" id="ouvrir"><i class="ph-bold ph-cards"></i>Ouvrir</button>' : ''}
      <div class="prochain"><i class="ph-fill ph-timer"></i><span id="minuteur">${fmtTemps(Math.round(secondesRestantes()))}</span></div>
    </div>
    ${inv.length ? `<div class="section-titre"><h2>Inventaire</h2><span class="surtitre">${inv.length}</span></div>
    <div class="bloc inventaire2">${inv.map((x) => `<button class="inv-ligne pressable" data-uid="${esc(x.uid)}"><span class="inv-pk"><span class="k-mono">W</span></span><span class="inv-nom">${esc(x.type === 'mystere' ? 'Mystère' : libelle(x))}</span><i class="ph-bold ph-arrow-right"></i></button>`).join('')}</div>` : ''}
    ${qdj && !qdj.faite ? `<button class="bloc qdj pressable" data-aller="questions" style="--t:${tq.c}">
      <div class="ligne1"><span class="tag or"><i class="ph-fill ph-star"></i>Question du jour</span><span class="tag"><i class="ph-bold ph-timer"></i>−${Math.round(config.get('gainQuestionDuJour') / 60)} h</span></div>
      <div class="q">${esc(qdj.question)}</div>
      <div class="aller"><span class="tag teinte"><i class="ph-fill ${tq.ic}"></i>${esc(qdj.theme || '')}</span><i class="ph-bold ph-arrow-right"></i></div>
    </button>` : ''}
    ${cdj ? `<button class="bloc carte-jour pressable${d.gagne ? ' gagnee' : ''}" id="cdj" style="--t:${tc.c};--rar:var(--r-${cdj.rarete})">
      <div class="${d.gagne ? '' : 'voile'}" style="--p:${Math.max(.12, d.suite / SERIE_DEFI[cdj.rarete])}">${htmlCarte(cdj)}</div>
      <div class="droite"><span class="surtitre">Carte du jour</span><h3>${esc(cdj.nom)}</h3>
        ${d.gagne ? '<span class="tag gagne"><i class="ph-fill ph-check-circle"></i>Gagnée</span>' : `<span class="tag"><i class="ph-fill ph-fire"></i>Série de ${SERIE_DEFI[cdj.rarete]}</span>${htmlPerles(SERIE_DEFI[cdj.rarete], d.suite)}`}
        <p>${esc(phrase(cdj.description))}</p></div>
    </button>` : ''}
    ${htmlTicketBloc()}
    ${htmlFragBande()}
    <div class="duo">
      <button class="bloc pressable" data-aller="serie">
        <div class="haut"><span class="surtitre">Série</span><i class="ph-fill ph-fire" style="color:#ff9f5a;font-size:20px"></i></div>
        <div class="grand"><span id="v-serie">${se.longueur}</span><small>jour${se.longueur > 1 ? 's' : ''}</small></div>
        <div class="serie-jour"><div class="barre2"><i style="width:${Math.min(100, bonnes / objectif * 100)}%"></i></div><span class="chiffre">${Math.min(bonnes, objectif)}/${objectif}</span></div>
        <span class="chiffre serie-pied">${se.gels ? `<i class="ph-fill ph-snowflake"></i>${se.gels} · ` : ''}palier ${prochainPalier()} j</span>
      </button>
      <button class="bloc pressable" data-aller="collection">
        <div class="haut"><span class="surtitre">Collection</span></div>
        <div style="display:flex;align-items:center;justify-content:space-between">
          <div class="grand"><span id="v-pct">0</span><small>%</small></div>
          <div class="anneau"><svg width="52" height="52"><circle cx="26" cy="26" r="22" fill="none" stroke="#ffffff14" stroke-width="5"/><circle class="v" id="anneau-col" cx="26" cy="26" r="22" fill="none" stroke="#f3f1ec" stroke-width="5" stroke-linecap="round" stroke-dasharray="${2 * Math.PI * 22}" stroke-dashoffset="${2 * Math.PI * 22}"/></svg></div>
        </div>
        <span class="chiffre" style="font-size:12px;color:var(--texte-3)"><span id="v-n">0</span> / ${fr(actives)}</span>
      </button>
    </div>
    <div class="section-titre"><h2>Vitrine</h2><span class="surtitre">${vit.length}/3</span></div>
    <div class="vitrine" id="vitrine">${[0, 1, 2].map((i) => (vit[i] ? htmlCarte(vit[i]) : '<button class="case-vide" data-aller="collection"><i class="ph ph-push-pin"></i></button>')).join('')}</div>
    ${der.length ? `<div class="section-titre"><h2>Dernières cartes</h2><button class="lien" data-aller="historique">Historique</button></div>
    <div class="defile" id="dernieres">${der.map((c) => htmlCarte(c)).join('')}</div>` : ''}`;
  z.dataset.prets = p.prets;
  cascade(z);
  requestAnimationFrame(() => {
    compter($('#v-pct', z), 'pct', Math.round(pct * 100)); compter($('#v-n', z), 'n', n);
    $('#anneau-col', z).style.strokeDashoffset = 2 * Math.PI * 22 * (1 - pct);
  });
  tic(z); majDemain();

  const lancer = async () => {
    const r = ouvrirPaquet(); if (!r) return;
    vibrer(12);
    await ouvrir(tirageDe(r), { nom: 'WikiDeck' });
    rendre(z);
  };
  $('#ouvrir', z)?.addEventListener('click', lancer);
  const pk = $('#paquets', z), orb = $('.orbite', z);
  pk.addEventListener('click', lancer);
  orb.addEventListener('pointermove', (e) => { const r = pk.getBoundingClientRect(); pk.classList.add('tilt'); pk.style.setProperty('--ry', `${((e.clientX - r.left) / r.width - .5) * 26}deg`); pk.style.setProperty('--rx', `${(.5 - (e.clientY - r.top) / r.height) * 26}deg`); });
  orb.addEventListener('pointerleave', () => { pk.classList.remove('tilt'); pk.style.setProperty('--rx', '0deg'); pk.style.setProperty('--ry', '0deg'); });
  z.querySelectorAll('[data-uid]').forEach((b) => b.addEventListener('click', async () => {
    const r = ouvrirSpecial(b.dataset.uid); if (!r) return;
    vibrer(12);
    await ouvrir(tirageDe(r), { nom: r.titre });
    if (r.eclats) toast('ph-diamond', `+${fr(r.eclats)}`);
    rendre(z);
  }));
  const lier = (sel, liste) => z.querySelectorAll(sel).forEach((el) => { el.classList.add('pressable'); el.addEventListener('click', (e) => { e.stopPropagation(); fiche(liste, liste.findIndex((c) => c.id === el.dataset.id), el); }); });
  lier('#dernieres .k', der); lier('#vitrine .k', vit);
  $('#cdj', z)?.addEventListener('click', () => (d.gagne ? fiche([cdj], 0, $('#cdj .k', z)) : ouvrirDefi(cdj, z)));
  $('#ticket', z).addEventListener('click', () => ouvrirTicket(z));
}

export function tic(z) {
  const p = etat.paquets; if (!p) return;
  const m = $('#minuteur', z);
  if (!m) return;
  const prets = p.prets, avant = +(z.dataset.prets ?? prets);
  if (prets !== avant) { if (prets > avant) { son('palier'); toast('ph-cards', 'Nouveau paquet'); } return rendre(z); }
  m.textContent = fmtTemps(Math.round(secondesRestantes()));
  const a = $('#arc', z), t = $('#tete-arc', z), pr = Math.max(0, Math.min(1, p.progression));
  if (a) a.style.strokeDashoffset = CIRC * (1 - pr);
  if (t) { const ang = pr * 2 * Math.PI; t.setAttribute('cx', 140 + RAYON * Math.cos(ang)); t.setAttribute('cy', 140 + RAYON * Math.sin(ang)); }
  majDemain();
}

/* ---------------- carte du jour : le défi ---------------- */
function ouvrirDefi(c, zAccueil) {
  vibrer(); son('tap');
  const N = SERIE_DEFI[c.rarete], d = defi();
  const { f, fermer } = ouvrirFeuille('defi', { surFermeture: () => rendre(zAccueil) });
  f.style.setProperty('--img', `url('${c.thumbUrl}')`);
  f.style.setProperty('--rar', `var(--r-${c.rarete})`);
  f.innerHTML = `<div class="flou"></div>
    <div class="barre-f"><button class="retour" id="dx" aria-label="Fermer"><i class="ph-bold ph-x"></i></button><span class="surtitre">Carte du jour</span><span class="record"><i class="ph-fill ph-trophy"></i>${d.record}</span></div>
    <div class="defi-scene voile" style="--p:${Math.max(.08, d.suite / N)}">${htmlCarte(c, { image: 'full' })}</div>
    <div class="defi-suite"><b id="dn">${d.suite}</b><span>/ ${N}</span>${htmlPerles(N, d.suite)}</div>
    <div class="defi-corps" id="dc"></div>`;
  $('#dx', f).addEventListener('click', () => { son('tap'); fermer(); });
  const majSuite = (ko) => {
    $('.defi-scene', f).style.setProperty('--p', Math.max(.08, defi().suite / N));
    $('#dn', f).textContent = defi().suite;
    $('.defi-suite .perles', f).outerHTML = htmlPerles(N, defi().suite);
    $('.record', f).innerHTML = `<i class="ph-fill ph-trophy"></i>${defi().record}`;
    if (ko) { const sc = $('.defi-scene', f); sc.classList.remove('rechute'); void sc.offsetWidth; sc.classList.add('rechute'); }
  };
  const gagner = async (resultat) => {
    son('palier'); vibrer([20, 40, 60]);
    const sc = $('.defi-scene', f); sc.classList.remove('voile'); sc.classList.add('devoilee');
    brancherManipulation($('.k', sc));
    $('#dc', f).innerHTML = `<div class="defi-fin"><span class="tag gagne"><i class="ph-fill ph-check-circle"></i>Gagnée</span><h2>${esc(c.nom)}</h2>
      <button class="btn2 or" id="dv"><i class="ph-bold ph-cards"></i>Voir la fiche</button></div>`;
    $('#dv', f).addEventListener('click', () => { fermer(); fiche([c], 0); });
  };
  const poser = () => {
    const q = questionDefi(), dc = $('#dc', f);
    if (!q) { dc.innerHTML = '<div class="vide-etat"><i class="ph ph-cloud-slash"></i></div>'; return; }
    const t = teinte(q.theme);
    dc.style.setProperty('--t', t.c);
    dc.innerHTML = `<div class="bloc q-carte" id="dq">
        <div class="meta"><span class="tag teinte"><i class="ph-fill ${t.ic}"></i>${esc(q.theme || '')}</span><span class="diff">${[1, 2, 3, 4, 5].map((k) => `<i class="${k <= q.difficulte ? 'on' : ''}"></i>`).join('')}</span></div>
        <p class="q-texte">${esc(q.question)}</p></div>
      <form class="q-form" id="df"><input id="dr" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="send" placeholder="Réponse"><button disabled aria-label="Valider"><i class="ph-bold ph-arrow-up"></i></button></form>
      <div class="verdict" id="dvd"></div>`;
    const inp = $('#dr', f), bt = $('#df button', f);
    inp.addEventListener('input', () => (bt.disabled = !inp.value.trim()));
    setTimeout(() => inp.focus({ preventScroll: true }), 60);
    $('#df', f).addEventListener('submit', (e) => {
      e.preventDefault();
      if (!inp.value.trim() || inp.disabled) return;
      inp.disabled = true; bt.disabled = true;
      const r = repondreDefi(q, inp.value);
      $('#dq', f).classList.add(r.ok ? 'juste' : 'faux');
      majSuite(!r.ok);
      if (r.resultat) { setTimeout(() => gagner(r.resultat), 500); return; }
      vibrer(r.ok ? 20 : [30, 40, 30]); son(r.ok ? 'juste' : 'faux');
      const v = $('#dvd', f); v.className = `verdict vu ${r.ok ? 'ok' : 'ko'}`;
      v.innerHTML = `<div class="ico"><i class="ph-bold ${r.ok ? 'ph-check' : 'ph-x'}"></i></div><div class="txt"><b>${esc(q.reponse)}</b><span>${r.ok ? `${r.suite} / ${N}` : 'Série perdue'}</span></div><button class="btn2 petit" id="ds">${r.ok ? 'Suivante' : 'Recommencer'}</button>`;
      $('#ds', f).addEventListener('click', () => { son('tap'); poser(); });
      $('#ds', f).focus({ preventScroll: true });
    });
  };
  poser();
}

/* ---------------- ticket à gratter ---------------- */
function htmlLot(l) {
  if (l.t === 'temps') return `<div class="tk-lot l-temps"><i class="ph-fill ph-timer"></i><b>−${l.h} h</b></div>`;
  if (l.t === 'frag') return `<div class="tk-lot l-frag" style="--rar:var(--r-${l.r})">${iconeRarete(l.r)}<b>×${l.n}</b></div>`;
  if (l.t === 'carte') return `<div class="tk-lot l-carte" style="--rar:var(--r-${l.r})"><span class="tk-dos">W</span><b>${NOMS[l.r]}</b></div>`;
  return '<div class="tk-lot l-paquet"><span class="tk-pk">W</span><b>Paquet</b></div>';
}
const miniLot = (l) => (l.t === 'temps' ? '<i class="ph-fill ph-timer" style="color:#9fd8ff"></i>' : l.t === 'frag' ? iconeRarete(l.r) : l.t === 'carte' ? `<i class="ph-fill ph-cards" style="color:var(--r-${l.r})"></i>` : '<i class="ph-fill ph-package" style="color:var(--or)"></i>');
// le ticket se renouvelle avec le jour de jeu (4 h, heure de Paris)
function prochainJour() {
  const h = config.get('heureDebutJour');
  const maintenant = new Date(), paris = new Date(maintenant.toLocaleString('en-US', { timeZone: 'Europe/Paris' }));
  const cible = new Date(paris); cible.setHours(h, 0, 0, 0); if (cible <= paris) cible.setDate(cible.getDate() + 1);
  return maintenant.getTime() + (cible - paris);
}
function majDemain() { const s = fmtTemps(Math.max(0, Math.round((prochainJour() - Date.now()) / 1000))); document.querySelectorAll('.tk-demain-v').forEach((e) => (e.textContent = s)); }
function htmlTicketBloc() {
  const tk = ticket(), n = tk.grattees.length, fait = n >= A_GRATTER;
  return `<button class="bloc ticket-bloc pressable${fait ? ' fait' : ''}" id="ticket">
    <div class="tb-mini">${tk.cases.map((l, i) => (tk.grattees.includes(i) ? `<i class="vu">${miniLot(l)}</i>` : `<i style="--k:${i}"></i>`)).join('')}</div>
    <div class="droite"><span class="surtitre">Ticket du jour</span><h3>${fait ? 'Gratté' : `${A_GRATTER - n} à gratter`}</h3>
      ${fait ? '<span class="tag"><i class="ph-bold ph-clock"></i><span class="tk-demain-v"></span></span>' : htmlPerles(A_GRATTER, n)}</div>
  </button>`;
}
function peindreFeuille(cv) {
  const r = cv.getBoundingClientRect(), dp = Math.min(2, devicePixelRatio || 1);
  cv.width = Math.max(1, Math.round(r.width * dp)); cv.height = Math.max(1, Math.round(r.height * dp));
  const g = cv.getContext('2d', { willReadFrequently: true }), w = cv.width, h = cv.height;
  const lg = g.createLinearGradient(0, 0, w, h);
  [[0, '#fff3c2'], [.32, '#d6a447'], [.52, '#fbe6a6'], [.78, '#b47d28'], [1, '#efcb78']].forEach(([o, c]) => lg.addColorStop(o, c));
  g.fillStyle = lg; g.fillRect(0, 0, w, h);
  for (let k = 0; k < (w * h) / 30; k++) { g.fillStyle = Math.random() < .5 ? '#ffffff26' : '#5a3a081c'; g.fillRect(Math.random() * w, Math.random() * h, dp, dp); }
  g.font = `${Math.round(h * .46)}px 'Instrument Serif', serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillStyle = '#7a4f1260'; g.fillText('W', w / 2, h / 2 + dp * 1.5); g.fillStyle = '#fff8dd70'; g.fillText('W', w / 2, h / 2 - dp);
}
function ouvrirTicket(zAccueil) {
  vibrer(); son('tap');
  const tk = ticket();
  let tictac = null;
  const encaisserSilence = () => { const r = encaisserTicket(); if (r) toast('ph-cards', `+${r.cartes.length} carte${r.cartes.length > 1 ? 's' : ''}`); };
  const { f, fermer } = ouvrirFeuille('ticket', { surFermeture: () => { clearInterval(tictac); encaisserSilence(); rendre(zAccueil); } });
  f.innerHTML = `<div class="barre-f"><button class="retour" id="tx" aria-label="Fermer"><i class="ph-bold ph-x"></i></button><span class="surtitre">Ticket du jour</span><span style="width:40px"></span></div>
    <div class="tk-slots" id="tk-slots"></div>
    <div class="tk-carton"><div class="tk-grille">${tk.cases.map((l, i) => `<div class="tk-case" data-i="${i}" style="${l.r ? `--rar:var(--r-${l.r})` : ''}">${htmlLot(l)}<canvas class="tk-feuille"></canvas></div>`).join('')}</div></div>
    <div class="tk-bas" id="tk-bas"></div>`;
  const caseEl = (i) => f.querySelector(`.tk-case[data-i="${i}"]`);
  const fini = () => tk.grattees.length >= A_GRATTER;
  $('#tx', f).addEventListener('click', () => { son('tap'); fermer(); });
  const majSlots = () => { $('#tk-slots', f).innerHTML = Array.from({ length: A_GRATTER }, (_, k) => { const l = tk.cases[tk.grattees[k]]; return l ? `<div class="tk-slot plein${estGros(l) ? ' gros' : ''}" style="${l.r ? `--rar:var(--r-${l.r})` : ''}">${htmlLot(l)}</div>` : '<div class="tk-slot"></div>'; }).join(''); };
  const majBas = () => {
    const b = $('#tk-bas', f);
    if (!fini()) { b.innerHTML = ''; return; }
    const att = cartesEnAttente();
    b.innerHTML = `${att.length ? '<button class="btn2 or" id="tk-ouvrir"><i class="ph-bold ph-cards"></i>Ouvrir</button>' : ''}<span class="tk-demain"><i class="ph-bold ph-clock"></i><span class="tk-demain-v"></span></span>`;
    majDemain();
    $('#tk-ouvrir', f)?.addEventListener('click', async () => {
      const r = encaisserTicket(); if (!r) return;
      await ouvrir(tirageDe(r), { nom: 'Ticket' });
      majBas();
    });
  };
  const devoilerReste = () => tk.cases.forEach((_, i) => { if (!tk.grattees.includes(i)) setTimeout(() => caseEl(i).classList.add('manque'), 80 * i); });
  const finir = (i) => {
    const l = gratter(i); if (!l) return;
    const el = caseEl(i); el.classList.add('vu'); if (estGros(l)) el.classList.add('jackpot');
    son(estGros(l) ? 'palier' : 'juste'); vibrer(estGros(l) ? [20, 40, 60] : 15);
    if (l.t === 'temps') toast('ph-timer', `−${l.h} h`);
    if (l.t === 'paquet') toast('ph-cards', '+1 paquet');
    majSlots();
    if (fini()) setTimeout(() => { devoilerReste(); majBas(); }, 700);
  };
  const refus = (i) => { const el = caseEl(i); el.classList.remove('non'); void el.offsetWidth; el.classList.add('non'); vibrer([10, 30, 10]); son('faux'); };
  f.querySelectorAll('.tk-case').forEach((el) => {
    const i = +el.dataset.i, cv = el.querySelector('canvas');
    if (tk.grattees.includes(i)) { el.classList.add('vu'); if (estGros(tk.cases[i])) el.classList.add('jackpot'); return; }
    if (fini()) { el.classList.add('manque'); return; }
    const g = cv.getContext('2d', { willReadFrequently: true });
    let bas = false, prec = null, coups = 0;
    const pt = (e) => { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * cv.width / r.width, (e.clientY - r.top) * cv.height / r.height]; };
    const trait = (a, b) => { g.globalCompositeOperation = 'destination-out'; g.lineCap = g.lineJoin = 'round'; g.lineWidth = cv.width * .24; g.beginPath(); g.moveTo(...a); g.lineTo(...b); g.stroke(); };
    const ratio = () => { const dt = g.getImageData(0, 0, cv.width, cv.height).data; let v = 0, n = 0; for (let k = 3; k < dt.length; k += 52) { n++; if (dt[k] < 40) v++; } return v / n; };
    cv.addEventListener('pointerdown', (e) => {
      if (!choisirCase(i)) return refus(i);
      bas = true; try { cv.setPointerCapture(e.pointerId); } catch {} prec = pt(e); trait(prec, [prec[0] + 1, prec[1]]);
    });
    cv.addEventListener('pointermove', (e) => { if (!bas) return; const p = pt(e); trait(prec, p); prec = p; if (++coups % 7 === 0) { vibrer(3); if (ratio() > .5) { bas = false; finir(i); } } });
    const lever = () => { if (bas && ratio() > .5) finir(i); bas = false; };
    cv.addEventListener('pointerup', lever); cv.addEventListener('pointercancel', lever);
  });
  const peindre = () => f.querySelectorAll('.tk-case:not(.vu):not(.manque) canvas').forEach(peindreFeuille);
  requestAnimationFrame(peindre);
  document.fonts?.ready.then(() => f.querySelectorAll('.tk-case:not(.vu):not(.manque) canvas').forEach((cv) => { if (!tk.choisies.includes(+cv.parentElement.dataset.i)) peindreFeuille(cv); }));
  tictac = setInterval(majDemain, 1000);
  majSlots(); majBas();
}
