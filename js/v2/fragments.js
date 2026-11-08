// Fragments : bande récapitulative (accueil, boutique) et écran de forge.

import { RARETES, NOMS, iconeRarete } from './carte.js';
import { son } from './son.js';
import { $, vibrer, fr, cascade, ouvrirFeuille, rafraichir } from './commun.js';
import { fragments, manquantes, forgeable, forger, PRIX_FORGE } from './mecaniques.js';
import { ouvrir, tirageDe } from './effets.js';

export function htmlFragBande() {
  const f = fragments(), pret = RARETES.some(forgeable);
  return `<button class="bloc frag-bande pressable${pret ? ' pret' : ''}" data-frag>
    <div class="haut"><span class="surtitre">Fragments</span>${pret ? '<span class="tag or"><i class="ph-fill ph-hammer"></i>Forge</span>' : '<i class="ph-bold ph-arrow-right"></i>'}</div>
    <div class="fb-rangee">${RARETES.map((r) => `<div class="fb${f[r] >= PRIX_FORGE ? ' plein' : ''}" style="--rar:var(--r-${r});--p:${Math.min(1, f[r] / PRIX_FORGE)}">${iconeRarete(r)}<b>${fr(f[r])}</b><i></i></div>`).join('')}</div>
  </button>`;
}

export function ouvrirFragments() {
  vibrer(); son('tap');
  const { f, fermer } = ouvrirFeuille('frags', { surFermeture: rafraichir });
  const rendre = () => {
    const fr_ = fragments();
    f.innerHTML = `<div class="barre-f"><button class="retour" id="fx" aria-label="Fermer"><i class="ph-bold ph-x"></i></button><span class="surtitre">Fragments</span><span style="width:40px"></span></div>
      <div class="fr-grille">${RARETES.map((r) => { const m = manquantes(r).length, n = fr_[r], ok = forgeable(r); return `<div class="bloc fr-tuile${ok ? ' pret' : ''}" style="--rar:var(--r-${r})">
        <div class="fr-gemme">${iconeRarete(r)}</div>
        <div class="fr-nom">${NOMS[r]}</div>
        <div class="fr-compte"><b>${fr(n)}</b><span>/ ${PRIX_FORGE}</span></div>
        <div class="fr-jauge">${Array.from({ length: PRIX_FORGE }, (_, k) => `<i class="${k < n ? 'on' : ''}"></i>`).join('')}</div>
        <button class="btn2 ${ok ? 'or' : 'fantome'} petit" data-forger="${r}" ${ok ? '' : 'disabled'}><i class="ph-fill ph-hammer"></i>Forger</button>
        <span class="fr-manque">${m ? `${fr(m)} à découvrir` : 'Complet'}</span>
      </div>`; }).join('')}</div>`;
    cascade($('.fr-grille', f));
    $('#fx', f).addEventListener('click', () => { son('tap'); fermer(); });
    f.querySelectorAll('[data-forger]').forEach((b) => b.addEventListener('click', async () => {
      const r = forger(b.dataset.forger);
      if (!r) return;
      son('achat'); vibrer([15, 30, 15]);
      await ouvrir(tirageDe(r), { nom: 'Forge' });
      rendre();
    }));
  };
  rendre();
}
document.addEventListener('click', (e) => { if (e.target.closest('[data-frag]')) ouvrirFragments(); });
