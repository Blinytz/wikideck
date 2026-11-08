// Fiche d'une carte (v2) : carte manipulable en 3D, navigation dans une liste,
// épingle de vitrine, lecture Wikipédia, doublons à vendre ou fragmenter.

import { etat, sauvegarder } from '../etat.js';
import { donnees } from '../donnees.js';
import { marquerLue } from '../acquisition.js';
import { valeurVente } from '../eclats.js';
import { htmlCarte, brancherManipulation, iconeRarete, NOMS, esc } from './carte.js';
import { son } from './son.js';
import { $, vibrer, fr, toast, teinte, transition } from './commun.js';
import { quantite, vendre, fragmenter } from './mecaniques.js';

export const vitrine = () => ((etat.prefs ??= {}).vitrine ??= []);

export function fiche(liste, i = 0, source, { surFermeture } = {}) {
  vibrer(); son('tap');
  const f = document.createElement('div');
  f.className = 'fiche';
  const remplir = (sens) => {
    const c = liste[i], q = quantite(c.id), epinglee = vitrine().includes(c.id);
    const t = teinte(donnees.colDe.get(c.id)?.theme);
    if (q) marquerLue(c.id);
    f.style.setProperty('--img', `url('${c.thumbUrl}')`);
    f.innerHTML = `<div class="flou"></div>
      <div class="barre-f"><button class="retour" id="ff" aria-label="Fermer"><i class="ph-bold ph-x"></i></button><span class="pos">${liste.length > 1 ? `${i + 1} / ${liste.length}` : ''}</span>
        ${q ? `<button class="retour epingle${epinglee ? ' on' : ''}" id="fe" aria-label="Vitrine"><i class="ph${epinglee ? '-fill' : ''} ph-push-pin"></i></button>` : '<span style="width:40px"></span>'}</div>
      <div class="scene">${i > 0 ? '<button class="nav-f g" aria-label="Précédente"><i class="ph-bold ph-caret-left"></i></button>' : ''}${htmlCarte(c, { image: 'full' })}${i < liste.length - 1 ? '<button class="nav-f d" aria-label="Suivante"><i class="ph-bold ph-caret-right"></i></button>' : ''}</div>
      <div class="feuille" style="--rar:var(--r-${c.rarete})">
        <div class="poignee"></div>
        <span class="rar">${iconeRarete(c.rarete)}${NOMS[c.rarete]}</span>
        <h2>${esc(c.nom)}</h2>
        <span class="tag teinte" style="--t:${t.c}"><i class="ph-fill ${t.ic}"></i>${esc(c.collection)}</span>
        <div class="stats"><div><b>${c.pv}</b><span>PV</span></div><div><b>×${q}</b><span>Possédée</span></div><div><b>${fr(valeurVente(c))}</b><span>Revente</span></div></div>
        <p>${esc((c.description || '').split('\n')[0])}</p>
        ${q > 1 ? `<div class="echange">
          <div class="ech-tete"><span class="surtitre">Doublons</span><b>×${q - 1}</b></div>
          <div class="ech-choix">
            <button class="ech pressable" id="fv"><i class="ph-fill ph-diamond"></i><b>+${fr(valeurVente(c) * (q - 1))}</b><span>Vendre</span></button>
            <button class="ech pressable" id="fx2" style="--rar:var(--r-${c.rarete})">${iconeRarete(c.rarete)}<b>+${q - 1}</b><span>Fragmenter</span></button>
          </div></div>` : ''}
        <div class="actions">
          ${c.lienWikipedia ? `<a class="btn2 seul" href="${esc(c.lienWikipedia)}" target="_blank" rel="noopener"><i class="ph-bold ph-book-open-text"></i>Lire</a>` : ''}
        </div>
      </div>`;
    const k = $('.scene .k', f);
    if (sens) k.classList.add(sens > 0 ? 'entre-g' : 'entre-d');
    brancherManipulation(k);
    $('#ff', f).addEventListener('click', fermer);
    $('#fv', f)?.addEventListener('click', () => { const v = vendre([c]); if (v) { son('pieces'); vibrer(15); toast('ph-diamond', `+${fr(v)}`); } remplir(); });
    $('#fx2', f)?.addEventListener('click', () => { const n = fragmenter([c]); if (n) { son('palier'); vibrer([15, 30, 15]); toast('ph-diamonds-four', `+${n} fragment${n > 1 ? 's' : ''}`); } remplir(); });
    $('#fe', f)?.addEventListener('click', () => {
      son('epingle'); vibrer(10);
      const v = vitrine();
      if (v.includes(c.id)) etat.prefs.vitrine = v.filter((x) => x !== c.id);
      else { etat.prefs.vitrine = [...v, c.id].slice(-3); toast('ph-push-pin', 'Vitrine'); }
      sauvegarder(); remplir();
    });
    const allerA = (pas) => {
      const j = i + pas; if (j < 0 || j >= liste.length) return;
      vibrer(); son('envoie'); k.classList.add(pas > 0 ? 'sort-g' : 'sort-d');
      setTimeout(() => { i = j; remplir(pas); }, 200);
    };
    f.querySelector('.nav-f.g')?.addEventListener('click', () => allerA(-1));
    f.querySelector('.nav-f.d')?.addEventListener('click', () => allerA(1));
    const sc = $('.scene', f); let x0 = null;
    sc.addEventListener('pointerdown', (e) => { x0 = e.target.closest('.k, .nav-f') ? null : e.clientX; });
    sc.addEventListener('pointerup', (e) => { if (x0 == null) return; const dx = e.clientX - x0; x0 = null; if (Math.abs(dx) > 50) allerA(dx < 0 ? 1 : -1); });
  };
  const ouvrirF = () => { if (source) source.style.viewTransitionName = ''; remplir(); document.body.append(f); document.documentElement.style.overflow = 'hidden'; };
  if (source && document.startViewTransition) { source.style.viewTransitionName = 'carte'; document.startViewTransition(ouvrirF); } else ouvrirF();
  function fermer() {
    vibrer(); son('tap');
    transition(() => {
      f.remove(); if (!document.querySelector('.fiche')) document.documentElement.style.overflow = '';
      surFermeture?.();
      document.dispatchEvent(new CustomEvent('v2:rafraichir'));
    });
  }
}
