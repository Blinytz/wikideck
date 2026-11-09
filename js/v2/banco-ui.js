// Banco et Super Banco : bloc de l'accueil et partie en plein écran.

import { banco, superBanco, question, score, repondre, corriger, clore, carnetSuper, rateesVeille, PALIERS, TAILLE } from './banco.js';
import { iconeRarete, NOMS, esc } from './carte.js';
import { son } from './son.js';
import { $, vibrer, teinte, ouvrirFeuille } from './commun.js';

const NOMS_JEU = { banco: 'Banco', superBanco: 'Super Banco' };
const partieDe = (cle) => (cle === 'banco' ? banco() : superBanco());

function etatBloc(cle) {
  const p = partieDe(cle);
  if (p.fini) return { lib: `${score(p)} / ${p.ids.length}`, classe: 'fait', ic: 'ph-check-circle' };
  if (p.ids) return { lib: p.rep.length ? `${p.rep.length} / ${p.ids.length}` : `${p.ids.length} question${p.ids.length > 1 ? 's' : ''}`, classe: 'pret', ic: 'ph-play' };
  if (cle === 'superBanco') return { lib: `${carnetSuper().length} / ${TAILLE}`, classe: 'ferme', ic: 'ph-lock-simple' };
  return { lib: '0', classe: 'ferme', ic: 'ph-moon' };
}

export function htmlBlocBanco() {
  const b = etatBloc('banco'), s = etatBloc('superBanco');
  const tuile = (cle, e, sous, ic) => `<button class="bloc banco-t ${cle} ${e.classe} pressable" data-banco="${cle}">
      <div class="haut"><span class="surtitre">${sous}</span><i class="ph-fill ${ic}"></i></div>
      <div class="bt-nom">${NOMS_JEU[cle]}</div>
      <span class="tag"><i class="ph-fill ${e.ic}"></i>${e.lib}</span></button>`;
  return `<div class="duo banco-duo">${tuile('banco', b, 'Veille', 'ph-arrow-counter-clockwise')}${tuile('superBanco', s, `Carnet · ${carnetSuper().length}`, 'ph-books')}</div>`;
}

export function brancherBanco(z, surFermeture) {
  z.querySelectorAll('[data-banco]').forEach((b) => b.addEventListener('click', () => {
    const cle = b.dataset.banco, p = partieDe(cle);
    if (!p.ids) { vibrer([20, 30, 20]); b.classList.remove('non'); void b.offsetWidth; b.classList.add('non'); return; }
    ouvrirBanco(cle, surFermeture);
  }));
}

const htmlPaliers = (s, gains) => `<div class="bk-paliers">${PALIERS.map(([n, r, k]) => `<div class="bk-pal${s >= n ? ' on' : ''}${gains ? '' : ''}" style="--rar:var(--r-${r})">
    <span class="bk-n">${n}</span>${iconeRarete(r)}<b>×${k}</b></div>`).join('')}</div>`;

const htmlPerles = (p) => `<div class="bk-perles">${p.ids.map((_, i) => {
  const r = p.rep[i];
  return `<i class="${r ? (r.ok ? 'ok' : 'ko') : i === p.rep.length ? 'cour' : ''}"></i>`;
}).join('')}</div>`;

export function ouvrirBanco(cle, surFermeture) {
  vibrer(); son('tap');
  const { f, fermer } = ouvrirFeuille(`defi banco-f ${cle}`, { surFermeture });
  const nom = NOMS_JEU[cle];
  f.innerHTML = `<div class="barre-f"><button class="retour" id="bx" aria-label="Fermer"><i class="ph-bold ph-x"></i></button><span class="surtitre">${nom}</span><span class="record" id="bs"></span></div>
    <div class="bk-tete"><h2>${nom}</h2><div id="bp"></div></div>
    <div class="defi-corps" id="bc"></div>`;
  $('#bx', f).addEventListener('click', () => { son('tap'); fermer(); });

  const entete = () => {
    const p = partieDe(cle);
    $('#bs', f).innerHTML = `<i class="ph-fill ph-check-circle"></i>${score(p)}`;
    $('#bp', f).innerHTML = htmlPerles(p);
  };

  const fin = () => {
    const p = partieDe(cle), gains = clore(cle) || [], s = score(p);
    entete();
    son(gains.length ? 'palier' : 'tap'); vibrer(gains.length ? [20, 40, 60] : 15);
    const titre = s === p.ids.length && s >= TAILLE ? `${nom} !` : `${s} / ${p.ids.length}`;
    $('#bc', f).innerHTML = `<div class="bk-fin${s >= TAILLE ? ' total' : ''}">
        <h3>${titre}</h3>
        ${htmlPaliers(s, gains)}
        ${gains.length ? `<div class="bk-gains">${gains.map((g) => `<span style="--rar:var(--r-${g.r})">${iconeRarete(g.r)}<b>+${g.k}</b>${NOMS[g.r]}</span>`).join('')}</div>` : ''}
        <button class="btn2" id="bf">Fermer</button></div>`;
    $('#bf', f).addEventListener('click', () => { son('tap'); fermer(); });
  };

  const poser = () => {
    const p = partieDe(cle);
    entete();
    if (p.fini) return fin();
    const q = question(p);
    if (!q) return fin();
    const t = teinte(q.theme);
    const dc = $('#bc', f);
    dc.style.setProperty('--t', t.c);
    dc.innerHTML = `<div class="bloc q-carte" id="bq">
        <div class="meta"><span class="tag teinte"><i class="ph-fill ${t.ic}"></i>${esc(q.theme || '')}</span><span class="bk-num">${p.rep.length + 1} / ${p.ids.length}</span></div>
        <p class="q-texte">${esc(q.question)}</p></div>
      <form class="q-form" id="bform"><input id="br" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="send" placeholder="Réponse"><button disabled aria-label="Valider"><i class="ph-bold ph-arrow-up"></i></button></form>
      <div class="verdict" id="bv"></div>
      ${htmlPaliers(score(p))}`;
    const inp = $('#br', f), bt = $('#bform button', f);
    inp.addEventListener('input', () => (bt.disabled = !inp.value.trim()));
    setTimeout(() => inp.focus({ preventScroll: true }), 60);
    $('#bform', f).addEventListener('submit', (e) => {
      e.preventDefault();
      if (!inp.value.trim() || inp.disabled) return;
      inp.disabled = true; bt.disabled = true;
      montrer(repondre(cle, inp.value));
    });
  };

  const montrer = (r) => {
    if (!r) return;
    const bq = $('#bq', f); bq.classList.remove('juste', 'faux'); void bq.offsetWidth;
    bq.classList.add(r.ok ? 'juste' : 'faux');
    vibrer(r.ok ? 20 : [30, 40, 30]); son(r.ok ? 'juste' : 'faux');
    entete();
    $('.bk-paliers', f).outerHTML = htmlPaliers(r.score);
    const v = $('#bv', f); v.className = `verdict vu ${r.ok ? 'ok' : 'ko'}`;
    v.innerHTML = `<div class="ico"><i class="ph-bold ${r.ok ? 'ph-check' : 'ph-x'}"></i></div><div class="txt"><b>${esc(r.q.reponse)}</b></div>
      <div class="q-actions"><button class="btn2 fantome petit q-corr" id="bcorr">${r.ok ? 'J’avais faux' : 'J’avais bon'}</button><button class="btn2 petit" id="bsuiv">${r.reste ? 'Suivante' : 'Résultat'}</button></div>`;
    $('#bsuiv', f).addEventListener('click', () => { son('tap'); poser(); });
    $('#bcorr', f).addEventListener('click', () => montrer(corriger(cle)));
    $('#bsuiv', f).focus({ preventScroll: true });
  };

  poser();
}
