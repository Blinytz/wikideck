// Service worker : hors-ligne complet.
// Stratégie : network-first avec repli cache pour tout GET même-origine.
// Tout ce qui est servi (shell, data/*.json, images) est mis en cache au vol,
// donc l'app reste 100% fonctionnelle hors-ligne après la première visite.

const CACHE = 'wikideck-v12-refonte';

// coquille de la v2 (index.html) et de l'ancienne interface (ancien.html)
const COQUILLE = [
  './', './index.html', './ancien.html', './manifest.json',
  './css/design.css', './css/ouverture2.css', './css/ecrans2.css', './css/effets.css', './css/ancien.css',
  './css/ecran-questions.css', './css/ecran-collection.css', './css/ecran-boutique.css', './css/jeu2.css',
  './css/app.css', './css/ouverture.css', './css/jeu.css',
  './js/v2/jeu.js', './js/v2/commun.js', './js/v2/carte.js', './js/v2/ouverture.js', './js/v2/particules.js', './js/v2/son.js',
  './js/v2/effets.js', './js/v2/fiche.js', './js/v2/fragments.js', './js/v2/mecaniques.js',
  './js/v2/ecrans/accueil.js', './js/v2/ecrans/questions.js', './js/v2/ecrans/collection.js', './js/v2/ecrans/boutique.js', './js/v2/ecrans/plus.js',
  './js/app.js', './js/etat.js', './js/config.js', './js/donnees.js',
  './js/ui.js', './js/eclats.js', './js/carte.js', './js/paquets.js',
  './js/vente.js', './js/station.js', './js/station-m1.js',
  './js/station-m2.js', './js/station-m3.js', './js/ecran-paquets.js',
  './js/ecran-collection.js', './js/ecran-station.js', './js/ecran-eclats.js',
  './js/ecran-reglages.js', './js/acquisition.js', './js/ouverture.js',
  './js/ecran-historique.js', './js/speciaux.js', './js/recompenses.js', './js/jour.js',
  './js/questions.js', './js/serie.js', './js/objectifs.js', './js/boutique.js', './js/source-questions.js',
  './js/ecran-accueil.js', './js/ecran-questions.js', './js/ecran-boutique.js', './js/ecran-serie.js',
  './js/ecran-objectifs.js', './js/ecran-plus.js', './js/serveur.js', './js/synchro.js',
  './js/portefeuille.js', './js/notifications.js',
  './data/collections.json',
  './icons/icon-192.png', './icons/icon-512.png',
];

// Pages sert tout en max-age=600 : addAll remplirait le cache neuf de copies
// périmées. Chaque fichier est donc relu au réseau (cache: 'reload').
self.addEventListener('install', (ev) => {
  ev.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await Promise.all(COQUILLE.map(async (f) => {
      try { const r = await fetch(new Request(f, { cache: 'reload' })); if (r.ok) await c.put(f, r); } catch {}
    }));
    await self.skipWaiting();
  })());
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
      // une requête de navigation ne se clone pas avec un autre mode de cache : on la reconstruit depuis l'URL
      const rep = image ? await fetch(req) : await fetch(new Request(req.url, { cache: 'no-cache', credentials: 'same-origin' }));
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

// Notifications push envoyées par la fonction serveur (spec §9).
self.addEventListener('push', (ev) => {
  let d = {};
  try { d = ev.data ? ev.data.json() : {}; } catch { d = { titre: 'WikiDeck', texte: ev.data?.text() }; }
  ev.waitUntil(self.registration.showNotification(d.titre || 'WikiDeck', {
    body: d.texte || '', tag: d.tag || 'wikideck', icon: './icons/icon-192.png', badge: './icons/icon-192.png',
    data: { url: d.url || './' },
  }));
});

self.addEventListener('notificationclick', (ev) => {
  ev.notification.close();
  const cible = new URL(ev.notification.data?.url || './', self.registration.scope).href;
  ev.waitUntil((async () => {
    const fenetres = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    const ouverte = fenetres.find(f => f.url.startsWith(self.registration.scope));
    if (ouverte) { await ouverte.focus(); return ouverte.navigate ? ouverte.navigate(cible) : null; }
    return self.clients.openWindow(cible);
  })());
});
