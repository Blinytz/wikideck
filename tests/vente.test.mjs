// Vente de doublons : barème fixe par rareté, jamais le dernier exemplaire.
// Lancement : node --test
import test from 'node:test';
import assert from 'node:assert/strict';

// `etat.js` s'appuie sur le navigateur (localStorage, window) : on le simule
// avant d'importer les modules, pour tester le moteur hors navigateur.
globalThis.localStorage = {
  _m: new Map(),
  getItem(k) { return this._m.has(k) ? this._m.get(k) : null; },
  setItem(k, v) { this._m.set(k, String(v)); },
  removeItem(k) { this._m.delete(k); },
};
globalThis.window = { addEventListener() {} };
globalThis.document = { addEventListener() {}, visibilityState: 'visible' };

const { BAREME_VENTE, valeurVente, vendreDoublon } = await import('../js/eclats.js');
const { etat } = await import('../js/etat.js');

test('le barème suit la rareté, de la commune à la légendaire', () => {
  assert.equal(BAREME_VENTE.commune, 100);
  assert.equal(BAREME_VENTE.rare, 500);
  assert.equal(BAREME_VENTE.epique, 1500);
  assert.equal(BAREME_VENTE.mythique, 2500);
  assert.equal(BAREME_VENTE.legendaire, 5000);
  // Strictement croissant : une carte plus rare vaut toujours plus.
  const ordre = ['commune', 'rare', 'epique', 'mythique', 'legendaire']
    .map((r) => BAREME_VENTE[r]);
  assert.deepEqual(ordre, [...ordre].sort((a, b) => a - b));
  assert.equal(new Set(ordre).size, ordre.length);
});

test('la valeur ne dépend plus des PV ni d’un taux', () => {
  assert.equal(valeurVente({ rarete: 'epique', pv: 20 }), 1500);
  assert.equal(valeurVente({ rarete: 'epique', pv: 340 }), 1500);
});

test('une rareté inconnue retombe sur la valeur commune', () => {
  assert.equal(valeurVente({ rarete: 'inexistante' }), 100);
  assert.equal(valeurVente({}), 100);
  assert.equal(valeurVente(null), 100);
});

test('vendre un doublon crédite le barème et retire un exemplaire', () => {
  etat.cartes = { c1: 3 };
  etat.eclats = 0;
  const montant = vendreDoublon({ id: 'c1', rarete: 'legendaire' });
  assert.equal(montant, 5000);
  assert.equal(etat.cartes.c1, 2);
  assert.equal(etat.eclats, 5000);
});

test('le dernier exemplaire n’est jamais vendable', () => {
  etat.cartes = { c1: 1 };
  etat.eclats = 0;
  assert.equal(vendreDoublon({ id: 'c1', rarete: 'commune' }), null);
  assert.equal(etat.cartes.c1, 1, 'la carte reste dans la collection');
  assert.equal(etat.eclats, 0, 'aucun Éclat crédité');

  etat.cartes = {};
  assert.equal(vendreDoublon({ id: 'absente', rarete: 'rare' }), null);
});
