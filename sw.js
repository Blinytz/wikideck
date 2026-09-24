// Service worker — hors-ligne complet.
// Stratégie : network-first avec repli cache pour tout GET même-origine.
// Tout ce qui est servi (shell, data/*.json, images) est mis en cache au vol,
// donc l'app reste 100% fonctionnelle hors-ligne après la première visite.

const CACHE = 'wikideck-v6-atelier-libre';

const COQUILLE = [
  './', './index.html', './manifest.json', './css/app.css',
  './js/app.js', './js/etat.js', './js/config.js', './js/donnees.js',
  './js/ui.js', './js/eclats.js', './js/carte.js', './js/paquets.js',
  './js/vente.js', './js/station.js', './js/station-m1.js',
  './js/station-m2.js', './js/station-m3.js', './js/ecran-paquets.js',
  './js/ecran-collection.js', './js/ecran-station.js', './js/ecran-eclats.js',
  './js/ecran-reglages.js',
  './data/collections.json',
  './icons/icon-192.png', './icons/icon-512.png',
];

self.addEventListener('install', (ev) => {
  ev.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(COQUILLE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (ev) => {
  ev.waitUntil(
    caches.keys()
      .then(cles => Promise.all(cles.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Réponse de secours : la copie en cache, sinon la réponse reçue telle quelle.
async function repli(req, rep) {
  const enCache = await caches.match(req, { ignoreSearch: true });
  if (enCache) return enCache;
  return rep || caches.match('./index.html');
}

self.addEventListener('fetch', (ev) => {
  const req = ev.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  // L'atelier n'est pas l'app hors-ligne. Le service worker interceptait
  // pourtant ses 5 500 vignettes, en forçant une revalidation HTTP pour
  // chacune : le quota de GitHub Pages s'épuisait (429) et l'atelier ne
  // montrait plus les nouvelles images. On le laisse désormais au navigateur.
  if (url.pathname.includes('atelier')) return;
  ev.respondWith((async () => {
    const client = ev.clientId ? await self.clients.get(ev.clientId) : null;
    if (client && client.url.includes('atelier')) return fetch(req);

    // Les images passent par le cache HTTP normal (pas de revalidation forcée) :
    // une vignette ne change que lorsqu'on la régénère, et Pages la sert avec
    // dix minutes de fraîcheur. Le reste (modules JS, données) est revalidé,
    // pour ne jamais servir un module périmé après une mise à jour.
    const image = url.pathname.includes('/images/');
    try {
      const rep = await fetch(req, image ? {} : { cache: 'no-cache' });
      if (rep.ok) {
        const copie = rep.clone();
        caches.open(CACHE).then(c => c.put(req, copie));
        return rep;
      }
      // 429 « trop de requêtes » ou erreur serveur : la copie en cache vaut
      // mieux qu'une image cassée. Avant, seule une coupure réseau y menait.
      return repli(req, rep);
    } catch {
      return repli(req, null);
    }
  })());
});
