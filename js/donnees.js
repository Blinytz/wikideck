// Chargement des données statiques de cartes (data/*.json).
// Les fichiers sont générés par build/ (provisoires en phase B, définitifs à
// l'étape 2) et mis en cache par le service worker pour le hors-ligne.

export const donnees = {
  provisoire: false,
  collections: [],       // [{slug, nom, nbCartes, cartes: [...]}]
  parId: new Map(),      // id -> carte
  pool: [],              // tous les ids (tirage équiprobable global)
};

// GitHub Pages limite les requêtes par IP et par salve. Un `Promise.all` sur
// la liste des collections en tirait autant qu'il y a de collections, d'un
// seul coup : 32 au début du projet, 95 aujourd'hui, et la page reçoit alors
// « Rate limit exceeded » au lieu de ses données. On plafonne donc le nombre
// de requêtes en vol, et on retente celles qui se font refuser.
const LARGEUR = 6;

async function fetchRetente(url, essais = 4) {
  for (let i = 0; ; i++) {
    const r = await fetch(url);
    if (r.ok) return r;
    // 429 « trop de requêtes », 403 que Pages renvoie parfois à la place :
    // les deux se résolvent en patientant, les autres non.
    if ((r.status !== 429 && r.status !== 403) || i >= essais) {
      throw new Error(`${url} : HTTP ${r.status}`);
    }
    await new Promise(t => setTimeout(t, 400 * 2 ** i));
  }
}

async function parLots(liste, travail, largeur = LARGEUR) {
  const sortie = new Array(liste.length);
  let curseur = 0;
  await Promise.all(
    Array.from({ length: Math.min(largeur, liste.length) }, async () => {
      while (curseur < liste.length) {
        const i = curseur++;
        sortie[i] = await travail(liste[i]);
      }
    })
  );
  return sortie;
}

export async function chargerDonnees() {
  const index = await (await fetchRetente('data/collections.json')).json();
  donnees.provisoire = !!index.provisoire;
  const fichiers = await parLots(index.collections,
    c => fetchRetente(c.fichier).then(r => r.json()));
  donnees.collections = fichiers.map(f => ({
    slug: f.slug, nom: f.collection, nbCartes: f.cartes.length, cartes: f.cartes,
  }));
  for (const col of donnees.collections) {
    for (const carte of col.cartes) {
      donnees.parId.set(carte.id, carte);
      donnees.pool.push(carte.id);
    }
  }
}
