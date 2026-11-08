// Écran Collection (v2) : tuiles des collections (couverture, progression),
// recherche parmi les cartes possédées, filtre par thème ; une collection ouverte
// montre sa progression, sa Résonance et sa grille (absentes en creux).
// Porté de l'essai validé (essais/design.html), sur les données réelles.

import { etat } from '../../etat.js';
import { donnees } from '../../donnees.js';
import { etatResonance, estComplete, estLue } from '../../acquisition.js';
import { htmlCarte, iconeRarete, RARETES, esc } from '../carte.js';
import { son } from '../son.js';
import { $, vibrer, fr, transition, RANG, teinte } from '../commun.js';
import { fiche } from '../fiche.js';

// état de la vue, conservé entre deux rendus (fermeture d'une fiche, retour au premier plan)
let vueCol = null, theme = 'Tous', requete = '', filtre = 'toutes';

// un nouvel appui sur l'onglet (ou tout lien vers la Collection) ramène à la liste.
// Ces écouteurs passent avant ceux de jeu.js : ce module est évalué avant son démarrage.
document.addEventListener('click', (e) => { if (e.target.closest?.('[data-aller="collection"]')) vueCol = null; }, true);
document.addEventListener('v2:aller', (e) => { if (e.detail?.nom === 'collection' && e.detail.options?.collection === undefined) vueCol = null; });

const qte = (id) => etat.cartes[id] || 0;
const actives = (col) => col.cartes.filter((c) => !c.archivee);
const nbAvoir = (cartes) => cartes.reduce((n, c) => n + (qte(c.id) > 0), 0);

const ARTICLES = /^(le|la|les|l|un|une|des|du|de|d|au|aux|the|a|an)\s+/;
const norm = (s) => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’'`]/g, ' ').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim().replace(ARTICLES, '').replace(ARTICLES, '');

// image d'une tuile : le recadrage au format carte s'il existe, sinon l'illustration pleine
const imageDe = (c) => (c.imgC ? c.imageUrl.replace('/full/', '/cartes/') + `?v=${c.imgC}` : c.imageUrl + (c.imgV ? `?v=${c.imgV}` : ''));
// couverture : la plus belle carte possédée, à défaut la plus belle de la collection
const couverture = (cartes) => { const p = cartes.filter((c) => qte(c.id) > 0); return [...(p.length ? p : cartes)].sort((a, b) => RANG(b.rarete) - RANG(a.rarete) || b.pv - a.pv)[0]; };
// les cartes 3D d'une grille chargent leur image à l'approche
const carteGrille = (c) => htmlCarte(c).replace('<img src=', '<img loading="lazy" src=');
// apparition en cascade, sans faire attendre les dernières tuiles d'une longue liste
const cascade = (el) => { if (el) [...el.children].forEach((x, i) => { x.classList.add('entre'); x.style.setProperty('--i', Math.min(i, 12)); }); };

export function rendre(z, options = {}) {
  if (options.racine) vueCol = null;
  if (options.collection !== undefined) { vueCol = options.collection; filtre = 'toutes'; }
  const col = vueCol && donnees.collections.find((c) => c.slug === vueCol);
  if (col) return rendreUneCollection(z, col);
  vueCol = null;
  rendreListe(z);
}

function rendreListe(z) {
  const cols = donnees.collections.filter((c) => actives(c).length);
  const n = donnees.pool.reduce((s, id) => s + (qte(id) > 0), 0);
  const themes = ['Tous', ...[...new Set(cols.map((c) => c.theme).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'fr'))];
  if (!themes.includes(theme)) theme = 'Tous';
  z.innerHTML = `<div class="grand-titre"><div><h1>Collection</h1><div class="sous">${fr(n)} / ${fr(donnees.pool.length)}</div></div></div>
    <div class="recherche"><i class="ph ph-magnifying-glass"></i><input id="rq" type="search" placeholder="Rechercher" value="${esc(requete)}" autocomplete="off"></div>
    <div class="puces">${themes.map((t) => { const x = teinte(t); return `<button class="puce${t === theme ? ' actif' : ''}" data-t="${esc(t)}" style="--t:${t === 'Tous' ? '#f3f1ec' : x.c}">${t === 'Tous' ? '' : `<i class="ph-fill ${x.ic}"></i>`}${esc(t)}</button>`; }).join('')}</div>
    <div id="res"></div>`;

  const remplir = () => {
    const q = norm(requete), res = $('#res', z);
    if (q.length >= 2) {
      const cartes = [];
      for (const c of cols) for (const x of actives(c)) if (qte(x.id) > 0 && norm(x.nom).includes(q)) cartes.push(x);
      const vues = cartes.slice(0, 60);
      res.innerHTML = vues.length
        ? `<div class="grille">${vues.map((c) => `<div class="cellule">${carteGrille(c)}${qte(c.id) > 1 ? `<span class="quantite">×${qte(c.id)}</span>` : ''}${estLue(c.id) ? '' : '<span class="non-lue"></span>'}</div>`).join('')}</div>`
        : '<div class="vide-etat"><i class="ph ph-cards"></i>Aucune carte</div>';
      res.querySelectorAll('.k').forEach((el, i) => { el.classList.add('pressable'); el.addEventListener('click', () => fiche(vues, i, el)); });
      return;
    }
    const visibles = cols.filter((c) => theme === 'Tous' || c.theme === theme);
    res.innerHTML = `<div class="tuiles-col">${visibles.map((c) => {
      const t = teinte(c.theme), liste = actives(c), k = nbAvoir(liste), p = k / liste.length, cv = couverture(liste);
      return `<button class="tc pressable${p === 1 ? ' complete' : ''}${k ? '' : ' vide'}" data-slug="${esc(c.slug)}" style="--t:${t.c}">
        <img src="${esc(imageDe(cv))}" alt="" loading="lazy" decoding="async"><span class="theme-ic"><i class="ph-fill ${t.ic}"></i></span>${p === 1 ? '<span class="sceau"><i class="ph-fill ph-seal-check"></i></span>' : ''}
        <div class="bas"><div class="nom">${esc(c.nom)}</div><div class="meta"><div class="barre2"><i style="width:${p * 100}%"></i></div><span>${k}/${liste.length}</span></div></div></button>`;
    }).join('')}</div>`;
    cascade($('.tuiles-col', res));
    res.querySelectorAll('.tc[data-slug]').forEach((b) => b.addEventListener('click', () => {
      vibrer(); son('tap');
      b.style.viewTransitionName = 'couv';
      transition(() => { b.style.viewTransitionName = ''; vueCol = b.dataset.slug; filtre = 'toutes'; rendre(z); scrollTo(0, 0); });
    }));
  };
  remplir();
  $('#rq', z).addEventListener('input', (e) => { requete = e.target.value; remplir(); });
  z.querySelectorAll('.puce').forEach((b) => b.addEventListener('click', () => { theme = b.dataset.t; vibrer(); son('tap'); rendreListe(z); }));
}

function htmlResonance(col) {
  const r = etatResonance(col.slug);
  const offertes = r.n ? `<span class="offertes"><i class="ph-fill ph-gift"></i>${r.n}</span>` : '';
  if (estComplete(col)) return `<div class="resonance pause"><i class="ph-fill ph-pause-circle"></i><span class="lib">Résonance</span><span class="etat">En pause</span>${offertes}</div>`;
  return `<div class="resonance"><i class="ph-fill ph-waveform"></i><span class="lib">Résonance</span><div class="barre2"><i style="width:${Math.min(100, 100 * r.jauge / r.seuil)}%"></i></div><span class="chiffre">${r.jauge}/${r.seuil}</span>${offertes}</div>`;
}

function rendreUneCollection(z, col) {
  const t = teinte(col.theme);
  const cartes = actives(col).sort((a, b) => (a.numero ?? 0) - (b.numero ?? 0));
  const k = nbAvoir(cartes), p = k / cartes.length, cv = couverture(cartes);
  const parR = RARETES.map((r) => [r, cartes.filter((c) => c.rarete === r)]).filter(([, l]) => l.length);
  const aDoublons = cartes.some((c) => qte(c.id) > 1);
  const aNonLues = cartes.some((c) => qte(c.id) > 0 && !estLue(c.id));
  if ((filtre === 'doublons' && !aDoublons) || (filtre === 'nonlues' && !aNonLues)) filtre = 'toutes';
  const garde = (c) => {
    const q = qte(c.id);
    if (filtre === 'doublons') return q > 1;
    if (filtre === 'nonlues') return q > 0 && !estLue(c.id);
    if (filtre === 'possedees') return q > 0;
    if (filtre === 'manquantes') return !q;
    return true;
  };
  const liste = cartes.filter(garde);
  const segments = [['toutes', 'Toutes'], ['possedees', 'Possédées'], ['manquantes', 'Manquantes'], ...(aDoublons ? [['doublons', 'Doublons']] : []), ...(aNonLues ? [['nonlues', 'Non lues']] : [])];

  z.innerHTML = `<div class="col-hero" style="--img:url('${esc(imageDe(cv))}');--t:${t.c};view-transition-name:couv"><div class="flou"></div>
      <div class="haut-hero"><button class="retour" id="ret" aria-label="Retour"><i class="ph-bold ph-caret-left"></i></button><span class="tag teinte"><i class="ph-fill ${t.ic}"></i>${esc(col.theme || '')}</span></div>
      <h1>${esc(col.nom)}</h1>
      <span class="chiffre">${k} / ${cartes.length}</span>
      <div class="jalons"><div class="barre2"><i style="width:${p * 100}%"></i></div>
        <div class="jalon${p >= 1 ? ' atteint' : ''}" style="left:100%"><b><i class="ph-fill ph-seal-check"></i></b><span>Complète</span></div></div>
      <div class="jalons-pied"></div>
      ${htmlResonance(col)}
      <div class="rar-detail">${parR.map(([r, l]) => `<span style="color:var(--r-${r})">${iconeRarete(r)}${nbAvoir(l)}/${l.length}</span>`).join('')}</div>
    </div>
    <div class="segment n${segments.length}">${segments.map(([v, l]) => `<button data-f="${v}" class="${v === filtre ? 'actif' : ''}">${l}</button>`).join('')}</div>
    ${liste.length ? `<div class="grille">${liste.map((c) => (qte(c.id) > 0
      ? `<div class="cellule">${carteGrille(c)}${qte(c.id) > 1 ? `<span class="quantite">×${qte(c.id)}</span>` : ''}${estLue(c.id) ? '' : '<span class="non-lue"></span>'}</div>`
      : `<div class="absente"><b>${String(c.numero ?? '').padStart(3, '0')}</b>${iconeRarete(c.rarete)}</div>`)).join('')}</div>`
      : filtre === 'manquantes' ? '<div class="vide-etat"><i class="ph-fill ph-seal-check" style="color:var(--or)"></i>Complète</div>' : '<div class="vide-etat"><i class="ph ph-cards"></i>Aucune carte</div>'}`;

  const slug = col.slug;
  $('#ret', z).addEventListener('click', () => {
    vibrer(); son('tap');
    const tuile = () => z.querySelector(`.tc[data-slug="${CSS.escape(slug)}"]`);
    transition(() => { vueCol = null; rendre(z); scrollTo(0, 0); const b = tuile(); if (b) b.style.viewTransitionName = 'couv'; })
      .finished.then(() => { const b = tuile(); if (b) b.style.viewTransitionName = ''; });
  });
  z.querySelectorAll('.segment button').forEach((b) => b.addEventListener('click', () => {
    filtre = b.dataset.f; vibrer(); son('tap');
    const y = scrollY; rendreUneCollection(z, col);
    scrollTo(0, Math.min(y, $('.segment', z).offsetTop - 8));
  }));
  const possedees = liste.filter((c) => qte(c.id) > 0);
  z.querySelectorAll('.grille .k').forEach((el) => {
    el.classList.add('pressable');
    el.addEventListener('click', () => fiche(possedees, possedees.findIndex((c) => c.id === el.dataset.id), el));
  });
}
