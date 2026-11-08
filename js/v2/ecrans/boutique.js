// Écran Boutique (v2) : porté de l'essai validé (essais/design.html, rendreBoutique),
// branché sur la vraie boutique (js/boutique.js) et les vrais paquets (js/speciaux.js).
// Aucune donnée simulée : offres, prix, remises, fins et contenus viennent des moteurs.

import { etat } from '../../etat.js';
import { config } from '../../config.js';
import { donnees } from '../../donnees.js';
import { majBoutique, prix, remiseEffective, acheter } from '../../boutique.js';
import { TYPES, initialeDe, inventaire, ouvrirSpecial } from '../../speciaux.js';
import { RARETES, NOMS, iconeRarete, esc } from '../carte.js';
import { son } from '../son.js';
import { $, vibrer, fr, RANG, teinte, cascade, compter, toast, fmtTemps, ouvrirFeuille } from '../commun.js';
import { lesDoublons, nbDoublons, valeurDoublons, vendre, fragmenter, quantite } from '../mecaniques.js';
import { htmlFragBande } from '../fragments.js';
import { fiche } from '../fiche.js';
import { ouvrir, tirageDe } from '../effets.js';

const HAUTS = ['mythique', 'legendaire', 'pantheon'];
const carteDe = (id) => donnees.parId.get(id);
const possede = (id) => (etat.cartes[id] || 0) > 0;
const nomCol = (s) => donnees.collections.find((c) => c.slug === s)?.nom || s;
const sec = (ms) => Math.max(0, Math.round(ms / 1000));

/* ---------- pools : mêmes règles que contenu() de js/speciaux.js ---------- */
const idsCol = (slug) => donnees.collections.find((c) => c.slug === slug)?.cartes.filter((c) => !c.archivee).map((c) => c.id) || [];
const idsTheme = (t) => donnees.collections.filter((c) => c.theme === t).flatMap((c) => idsCol(c.slug));
const idsInitiale = (l) => donnees.pool.filter((id) => initialeDe(carteDe(id).nom) === l);
const idsRar = (rs) => donnees.pool.filter((id) => rs.includes(carteDe(id).rarete));

// part de chaque rareté dans un pool tiré uniformément
function parts(ids) {
  const n = {}; for (const id of ids) { const r = carteDe(id).rarete; n[r] = (n[r] || 0) + 1; }
  const p = {}; for (const r of RARETES) p[r] = ids.length ? (n[r] || 0) / ids.length : 0;
  return p;
}
const melange = (liste) => { const p = {}; for (const r of RARETES) p[r] = liste.reduce((s, [w, q]) => s + w * q[r], 0); return p; };

const STYLE = {
  grand: { c: '#6ea8ff', ic: 'ph-stack' },
  initiale: { c: '#d8c49a', ic: 'ph-text-aa' },
  mystere: { c: '#a7a4ae', ic: 'ph-question' },
  plancher: { c: '#ff8fd6', ic: 'ph-arrow-line-up' },
  inedit: { c: '#b69cff', ic: 'ph-sparkle' },
  sommet: { c: '#f2c66d', ic: 'ph-crown-simple' },
};

/* Ce que la boutique montre d'une offre : titre, teinte, cartes possibles, chances par carte.
   Les chances sont exactes : contenu() tire uniformément dans ces pools. */
function decrire(o) {
  const n = config.get('tailleDuPaquet'), p = o.params || {};
  const d = { type: o.type, sous: TYPES[o.type] || 'Paquet', titre: TYPES[o.type] || 'Paquet', nb: n, ids: [], chances: null, garantie: null, mystere: false };
  switch (o.type) {
    case 'collection': {
      const col = donnees.collections.find((c) => c.slug === p.slug);
      d.titre = col?.nom || p.slug; d.t = teinte(col?.theme); d.ids = idsCol(p.slug); d.chances = parts(d.ids); break;
    }
    case 'theme': d.titre = p.theme; d.t = teinte(p.theme); d.ids = idsTheme(p.theme); d.chances = parts(d.ids); break;
    case 'duo': {
      const [a, b] = p.slugs || [];
      d.titre = `${nomCol(a)} et ${nomCol(b)}`; d.slugs = [a, b];
      d.t = teinte(donnees.collections.find((c) => c.slug === a)?.theme);
      const ia = idsCol(a), ib = idsCol(b);
      d.ids = [...new Set([...ia, ...ib])]; d.chances = melange([[.5, parts(ia)], [.5, parts(ib)]]); break;
    }
    case 'grand': d.nb = config.get('tailleGrandPaquet'); d.ids = [...donnees.pool]; d.chances = parts(d.ids); break;
    case 'initiale': d.titre = p.lettre; d.ids = idsInitiale(p.lettre); d.chances = parts(d.ids); break;
    case 'plancher': {
      d.ids = [...donnees.pool]; d.garantie = 'mythique';
      d.chances = melange([[(n - 1) / n, parts(donnees.pool)], [1 / n, parts(idsRar(HAUTS))]]); break;
    }
    case 'sommet': d.ids = idsRar(['legendaire', 'pantheon']); d.garantie = 'legendaire'; d.chances = parts(d.ids); break;
    case 'inedit': {
      const k = config.get('tailleInedit'), manq = donnees.pool.filter((id) => !possede(id)), m = Math.min(k, manq.length);
      d.nb = k; d.ids = manq.length ? manq : [...donnees.pool]; d.inedites = m;
      d.chances = manq.length ? melange([[m / k, parts(manq)], [(k - m) / k, parts(donnees.pool)]]) : parts(donnees.pool); break;
    }
    case 'mystere': d.mystere = true; d.nb = null; break;
  }
  d.t ??= STYLE[o.type] || teinte();
  d.cartes = d.ids.map(carteDe).filter(Boolean);
  return d;
}

const vitrines = (d, n = 4) => d.cartes.filter((c) => possede(c.id)).sort((a, b) => RANG(b.rarete) - RANG(a.rarete) || b.pv - a.pv).slice(0, n);

function htmlVisuel(d, grand = false) {
  const src = (c) => esc(grand ? c.imageUrl : c.thumbUrl);
  let fond = '', ic = '';
  if (d.type === 'theme' || d.type === 'duo') {
    const im = d.type === 'duo' ? vitrinesDuo(d) : vitrines(d, 4);
    if (im.length) fond = `<div class="pki-mosaique">${im.map((c) => `<img src="${src(c)}" alt="" loading="lazy">`).join('')}</div>`;
  } else if (d.type === 'collection' || d.type === 'initiale') {
    const im = vitrines(d, 1)[0];
    if (im) fond = `<img class="pki-img" src="${src(im)}" alt="" loading="lazy">`;
  }
  if (!fond) ic = d.type === 'initiale' ? `<span class="pki-ic pki-lettre">${esc(d.titre)}</span>` : `<i class="ph-fill ${d.t.ic} pki-ic"></i>`;
  return `<div class="pki t-${d.type}${grand ? ' grand' : ''}" style="--t:${d.t.c}">${fond}<div class="pki-voile"></div>
    <div class="pki-haut"><span class="k-mono">W</span></div>${ic}
    <div class="pki-nom">${esc(d.titre)}</div></div>`;
}
// duo : la plus belle carte possédée de chaque collection
function vitrinesDuo(d) {
  const out = [];
  for (const slug of d.slugs || []) {
    const c = idsCol(slug).map(carteDe).filter((x) => possede(x.id)).sort((a, b) => RANG(b.rarete) - RANG(a.rarete) || b.pv - a.pv)[0];
    if (c) out.push(c);
  }
  return out;
}

const htmlSolde = () => `<button class="solde pressable" data-aller="boutique"><i class="ph-fill ph-diamond"></i><span class="chiffre solde-v">${fr(etat.eclats || 0)}</span></button>`;

function htmlContenu(d, detail = false) {
  if (d.mystere) return '<div class="ob-contenu"><span><b>?</b> cartes</span></div>';
  const g = d.garantie;
  const garantie = g ? `<span style="color:var(--r-${g})">${iconeRarete(g)}${d.type === 'plancher' ? (detail ? 'dernière : ' : '1 ') : ''}${NOMS[g]}${g === 'pantheon' ? '' : ' ou mieux'}</span>` : '';
  return `<div class="ob-contenu"${detail ? ' style="margin-bottom:18px"' : ''}><span><b>${d.nb}</b> carte${d.nb > 1 ? 's' : ''}</span>${garantie}</div>`;
}

function htmlOffre(o, t) {
  const d = decrire(o), r = remiseEffective(o, t), p = prix(o, t), vedette = o.flash || o.type === 'sommet';
  const nouvelles = d.cartes.filter((c) => !possede(c.id)).length;
  const info = d.mystere ? '' : d.type === 'inedit' ? (d.inedites >= d.nb ? '100 % nouvelles' : `${fr(d.inedites)} nouvelle${d.inedites > 1 ? 's' : ''}`) : `${fr(nouvelles)} à découvrir`;
  return `<article class="bloc ob${vedette ? ' vedette' : ''}${o.flash ? ' flash' : ''}" style="--t:${d.t.c}" data-uid="${esc(o.uid)}">
    ${o.flash ? '<span class="ob-ruban">Flash</span>' : vedette ? '<span class="ob-ruban">À la une</span>' : ''}
    <div class="ob-visuel">${htmlVisuel(d, vedette)}</div>
    <div class="ob-corps">
      <div class="ob-tags"><span class="tag teinte"><i class="ph-fill ${d.t.ic}"></i>${esc(d.sous)}</span>${o.baisse ? '<span class="tag ob-baisse"><i class="ph-bold ph-trend-down"></i>Baisse</span>' : ''}</div>
      <h3>${esc(d.titre)}</h3>
      ${htmlContenu(d)}
      <div class="ob-info">${info ? `<span>${info}</span>` : ''}<span class="ob-fin"><i class="ph-bold ph-timer"></i><span class="chiffre" data-fin="${o.fin}">${fmtTemps(sec(o.fin - t))}</span></span></div>
      ${d.mystere ? '' : `<div class="rar-detail ob-rar">${RARETES.map((rr) => { const l = d.cartes.filter((c) => c.rarete === rr); const m = l.filter((c) => !possede(c.id)).length; return l.length ? `<span style="color:var(--r-${rr})">${iconeRarete(rr)}${fr(m)}</span>` : ''; }).join('')}</div>`}
      <div class="ob-pied">
        <button class="btn2 or pressable" data-acheter data-prix="${p}" ${p <= (etat.eclats || 0) ? '' : 'disabled'}><i class="ph-fill ph-diamond"></i><span class="ob-lib">${fr(p)}</span></button>
        ${r ? `<s>${fr(o.base)}</s><span class="ob-remise">-${r} %</span>` : ''}
        ${d.mystere ? '' : '<button class="retour ob-det" data-detail aria-label="Contenu"><i class="ph-bold ph-info"></i></button>'}
      </div>
    </div></article>`;
}

const fmtPct = (p) => (p < .1 ? '< 0,1' : p < 1 ? p.toFixed(1).replace('.', ',') : String(Math.round(p)));

function detailOffre(o) {
  const d = decrire(o);
  if (d.mystere) return;
  vibrer(); son('tap');
  const { f, fermer } = ouvrirFeuille('');
  const fondImg = vitrines(d, 1)[0];
  if (fondImg) f.style.setProperty('--img', `url('${fondImg.thumbUrl}')`);
  const rs = RARETES.filter((r) => d.chances?.[r] > 0);
  const nouvelles = d.cartes.filter((c) => !possede(c.id)).length;
  f.innerHTML = `<div class="flou"></div>
    <div class="barre-f"><button class="retour" id="ff" aria-label="Fermer"><i class="ph-bold ph-x"></i></button><span></span><span style="width:40px"></span></div>
    <div class="scene">${htmlVisuel(d, true)}</div>
    <div class="feuille" style="--t:${d.t.c}">
      <div class="poignee"></div>
      <span class="tag teinte"><i class="ph-fill ${d.t.ic}"></i>${esc(d.sous)}</span>
      <h2>${esc(d.titre)}</h2>
      <div class="chances">${rs.map((r) => { const p = d.chances[r] * 100; return `<div class="chance"><span style="color:var(--r-${r})">${iconeRarete(r)}${NOMS[r]}</span><div class="barre2"><i style="width:${Math.max(1.5, p)}%;background:var(--r-${r})"></i></div><b>${fmtPct(p)} %</b></div>`; }).join('')}</div>
      ${htmlContenu(d, true)}
      <div class="section-titre"><h2>À découvrir</h2><span class="surtitre">${fr(nouvelles)} / ${fr(d.cartes.length)}</span></div>
      <div class="manques">${RARETES.map((r) => { const l = d.cartes.filter((c) => c.rarete === r); if (!l.length) return ''; const m = l.filter((c) => !possede(c.id)).length; return `<div style="--r:var(--r-${r})">${iconeRarete(r)}<b>${fr(m)}</b><span>${NOMS[r]}</span></div>`; }).join('')}</div>
    </div>`;
  $('#ff', f).addEventListener('click', () => { son('tap'); fermer(); });
}

/* ---------- doublons ---------- */
function htmlDoublons() {
  const d = lesDoublons(), n = nbDoublons(d), v = valeurDoublons(d);
  return `<div class="section-titre"><h2>Doublons</h2>${n ? '<button class="lien" id="db-voir">Voir</button>' : ''}</div>
    <div class="bloc doublons-b">
      <div class="rar-detail">${RARETES.map((r) => { const k = d.filter((c) => c.rarete === r).reduce((s, c) => s + quantite(c.id) - 1, 0); return k ? `<span style="color:var(--r-${r})">${iconeRarete(r)}${fr(k)}</span>` : ''; }).join('') || '<span>0</span>'}</div>
      <div class="ech-choix">
        <button class="ech pressable" id="db-vendre" ${n ? '' : 'disabled'}><i class="ph-fill ph-diamond"></i><b>+${fr(v)}</b><span>Tout vendre</span></button>
        <button class="ech pressable" id="db-frag" ${n ? '' : 'disabled'}><i class="ph-fill ph-diamonds-four"></i><b>+${fr(n)}</b><span>Tout fragmenter</span></button>
      </div>
    </div>`;
}

// action irréversible : un premier appui arme le bouton, le second confirme
function armer(b, action) {
  b.addEventListener('click', () => {
    if (!b.classList.contains('arme')) {
      vibrer(); son('tap');
      b.classList.add('arme');
      clearTimeout(b._arme); b._arme = setTimeout(() => b.classList.remove('arme'), 3000);
      return;
    }
    clearTimeout(b._arme); b.classList.remove('arme');
    action();
  });
}

function brancherDoublons(z) {
  $('#db-voir', z)?.addEventListener('click', () => {
    const d = lesDoublons().sort((a, b) => RANG(b.rarete) - RANG(a.rarete) || b.pv - a.pv);
    if (d.length) fiche(d, 0);
  });
  const v = $('#db-vendre', z), f = $('#db-frag', z);
  if (v && !v.disabled) armer(v, () => { const e = vendre(lesDoublons()); if (e) { son('pieces'); vibrer(15); toast('ph-diamond', `+${fr(e)}`); } rendre(z); });
  if (f && !f.disabled) armer(f, () => { const k = fragmenter(lesDoublons()); if (k) { son('palier'); vibrer([15, 30, 15]); toast('ph-diamonds-four', `+${fr(k)} fragment${k > 1 ? 's' : ''}`); } rendre(z); });
}

/* ---------- écran ---------- */
let enAchat = false;
const signature = (emps, t) => emps.map((e) => (e.offre ? `${e.offre.uid}:${prix(e.offre, t)}` : '')).join('|');
const prochaineArrivee = (emps) => { const v = emps.filter((e) => !e.offre).map((e) => e.prochaine); return v.length ? Math.min(...v) : null; };

export function rendre(z, options = {}) {
  const t = Date.now();
  const emps = majBoutique(t);
  const offres = emps.filter((e) => e.offre).map((e) => e.offre);
  const proch = prochaineArrivee(emps);
  z.dataset.sig = signature(emps, t);
  z.innerHTML = `<div class="grand-titre"><div><h1>Boutique</h1></div>${htmlSolde()}</div>
    ${proch ? `<div class="rotation"><i class="ph-fill ph-arrows-clockwise"></i><span>Prochaine offre dans</span><b class="chiffre" data-fin="${proch}">${fmtTemps(sec(proch - t))}</b></div>` : ''}
    ${offres.length ? `<div class="offres">${offres.map((o) => htmlOffre(o, t)).join('')}</div>` : ''}
    ${htmlDoublons()}
    <div class="section-titre"><h2>Fragments</h2></div>
    ${htmlFragBande()}`;
  if (!options.sansCascade) cascade(z);
  compter($('.solde-v', z), 'solde', Math.round(etat.eclats || 0), 1);
  brancherDoublons(z);

  z.querySelectorAll('.ob').forEach((el) => {
    const o = offres.find((x) => x.uid === el.dataset.uid);
    if (!o) return;
    el.querySelector('[data-detail]')?.addEventListener('click', () => detailOffre(o));
    el.querySelector('.ob-visuel').addEventListener('click', () => detailOffre(o));
    const b = el.querySelector('[data-acheter]');
    armer(b, async () => {
      if (enAchat) return;
      enAchat = true;
      try {
        const res = acheter(o.uid);
        if (!res.ok) { son('faux'); toast('ph-warning', res.raison === 'solde insuffisant' ? 'Solde insuffisant' : 'Offre disparue'); return; }
        son('achat'); vibrer(15);
        const uid = inventaire().at(-1)?.uid;
        const r = uid && ouvrirSpecial(uid);
        if (r) {
          await ouvrir(tirageDe(r), { nom: r.titre });
          if (r.eclats) toast('ph-diamond', `+${fr(r.eclats)}`);
        }
      } finally {
        enAchat = false;
        rendre(z, { sansCascade: true });
      }
    });
  });
}

export function tic(z) {
  if (enAchat || !z.isConnected) return;
  const t = Date.now();
  const e = etat.boutique?.emplacements || [];
  const change = e.length < config.get('emplacementsBoutique')
    || e.some((em) => (em.offre ? em.offre.fin <= t : em.prochaine <= t));
  if (change || signature(e, t) !== z.dataset.sig) {
    const avant = new Set(e.map((em) => em.offre?.uid).filter(Boolean));
    rendre(z, { sansCascade: true });
    const apres = (etat.boutique?.emplacements || []).map((em) => em.offre?.uid).filter(Boolean);
    if (apres.some((u) => !avant.has(u))) { son('tap'); toast('ph-storefront', 'Nouvelle offre'); }
    return;
  }
  for (const el of z.querySelectorAll('[data-fin]')) el.textContent = fmtTemps(sec(Number(el.dataset.fin) - t));
  const solde = etat.eclats || 0;
  for (const b of z.querySelectorAll('[data-acheter]')) b.disabled = Number(b.dataset.prix) > solde;
}
