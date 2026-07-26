// Vente de doublons depuis le détail d'une carte (branchement du hook de
// l'écran Collection). Module séparé pour éviter tout cycle d'imports.

import { etat } from './etat.js';
import { valeurVente, vendreDoublon } from './eclats.js';
import { definirDetailOptions } from './ecran-collection.js';
import { formaterNombre, confirmer, NOMS_RARETE } from './ui.js';

definirDetailOptions((carte, surMaj) => {
  const qte = etat.cartes[carte.id] || 0;
  if (qte < 2) return {};
  return {
    actions: `
      <div class="panneau-vente">
        <button class="btn btn-vendre">◆ Vendre un doublon —
          ${formaterNombre(valeurVente(carte))} Éclats
          <small>(valeur fixe d'une ${NOMS_RARETE[carte.rarete].toLowerCase()})</small></button>
        <p class="note-vente">Le dernier exemplaire n'est jamais vendable.</p>
      </div>`,
    brancherActions(overlay, fermer) {
      overlay.querySelector('.btn-vendre').addEventListener('click', () => {
        const montant = valeurVente(carte);
        if (!confirmer(`Vendre un doublon de « ${carte.nom} » pour ${formaterNombre(montant)} Éclats ?`)) return;
        if (vendreDoublon(carte) === null) return;
        document.dispatchEvent(new CustomEvent('gacha:eclats-changes'));
        fermer();
        surMaj?.();
      });
    },
  };
});
