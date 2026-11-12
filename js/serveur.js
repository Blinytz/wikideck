// Raccordement au Supabase Éclats : session commune à l'écosystème, état de
// jeu, registre des Éclats (Centrale), questions Quinytz, notifications push.
//
// Aucune clé secrète : la clé publishable, comme les autres applications.
// La session vit sous `eclats_session`, partagée par toutes les applications
// de blinytz.github.io : se connecter une fois suffit.
// Hors connexion, le jeu tourne sur son cache local ; la synchronisation
// reprend dès que le serveur répond.

export const SERVEUR = {
  url: 'https://psutbulpezfdftmaqkoo.supabase.co',
  anonKey: 'sb_publishable_KTE_3tQq6eGEo4z2f4QrUA_v7F4K4fT',
  appId: 'wikideck',
};
const CLE_SESSION = 'eclats_session';

// La session est partagée : une autre application peut la renouveler à tout moment
// (le jeton de renouvellement d'avant devient alors invalide). On relit donc toujours
// la copie commune plutôt que de garder la sienne en mémoire.
let session = null;
const lireStockee = () => { try { return JSON.parse(localStorage.getItem(CLE_SESSION) || 'null'); } catch { return null; } };
const relire = () => { session = lireStockee(); return session; };
relire();
window.addEventListener?.('storage', (e) => { if (e.key === CLE_SESSION) relire(); });

function sauverSession(s) {
  session = s;
  try { s ? localStorage.setItem(CLE_SESSION, JSON.stringify(s)) : localStorage.removeItem(CLE_SESSION); } catch {}
}
export function estConnecte() { relire(); return !!session?.access_token; }
export function utilisateur() { return session?.user || null; }

export async function connexion(email, motDePasse) {
  const r = await fetch(`${SERVEUR.url}/auth/v1/token?grant_type=password`, {
    method: 'POST',
    headers: { apikey: SERVEUR.anonKey, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: motDePasse }),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.error_description || d.msg || 'Connexion refusée');
  sauverSession(d);
  return d.user;
}
export function deconnexion() { sauverSession(null); }

/* Renouvellement : un seul à la fois ; on ne se déconnecte que si le serveur refuse
   vraiment le jeton ET qu'aucune autre application n'a renouvelé la session entre-temps. */
let renouvellement = null;
function rafraichir(jetonRefuse) {
  return (renouvellement ??= (async () => {
    const s = relire();
    if (!s?.refresh_token) return false;
    if (jetonRefuse && s.access_token !== jetonRefuse) return true;   // déjà renouvelée ailleurs
    let r;
    try {
      r = await fetch(`${SERVEUR.url}/auth/v1/token?grant_type=refresh_token`, {
        method: 'POST',
        headers: { apikey: SERVEUR.anonKey, 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: s.refresh_token }),
      });
    } catch { return false; }   // réseau : on garde la session
    if (r.ok) { sauverSession(await r.json()); return true; }
    const apres = lireStockee();
    if (apres?.refresh_token && apres.refresh_token !== s.refresh_token) { session = apres; return true; }
    if (r.status === 400 || r.status === 401) sauverSession(null);
    return false;
  })().finally(() => { renouvellement = null; }));
}

async function appel(chemin, options = {}, deja = false) {
  relire();
  // jeton expiré (ou presque) : renouvelé avant l'appel plutôt qu'après un refus
  if (session?.expires_at && session.expires_at * 1000 < Date.now() + 30e3) await rafraichir();
  const entetes = { apikey: SERVEUR.anonKey, 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (session?.access_token) entetes.Authorization = `Bearer ${session.access_token}`;
  const r = await fetch(`${SERVEUR.url}${chemin}`, { ...options, headers: entetes });
  if (r.status === 401 && !deja && await rafraichir(entetes.Authorization?.slice(7))) return appel(chemin, options, true);
  const texte = await r.text();
  if (!r.ok) {
    let m = `Erreur ${r.status}`;
    try { m = JSON.parse(texte).message || m; } catch {}
    const e = new Error(m); e.status = r.status; throw e;
  }
  return texte ? JSON.parse(texte) : null;
}
const rpc = (f, args = {}) => appel(`/rest/v1/rpc/${f}`, { method: 'POST', body: JSON.stringify(args) });

/* ---------- registre des Éclats ---------- */
export function uuid() {
  return crypto.randomUUID ? crypto.randomUUID()
    : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16);
    });
}
export async function solde() { return Number(await rpc('eclats_balance')) || 0; }
export function crediter(montant, reason, referenceType, cle = uuid(), metadata = null) {
  return rpc('eclats_reward', {
    p_app_id: SERVEUR.appId, p_amount: montant, p_reason: reason, p_reference_type: referenceType,
    p_idempotency_key: cle, p_reference_id: null, p_metadata: metadata,
  });
}
export function debiter(montant, reason, referenceType, cle = uuid(), metadata = null) {
  return rpc('eclats_spend', {
    p_app_id: SERVEUR.appId, p_amount: montant, p_reason: reason, p_reference_type: referenceType,
    p_reference_id: uuid(), p_idempotency_key: cle, p_metadata: metadata,
  });
}

/* ---------- état de jeu ---------- */
export async function lireEtat() {
  const lignes = await appel('/rest/v1/wikideck_etat?select=etat,updated_at');
  return lignes?.[0] || null;
}
export async function ecrireEtat(etat) {
  return appel('/rest/v1/wikideck_etat?on_conflict=user_id', {
    method: 'POST',
    headers: { Prefer: 'resolution=merge-duplicates,return=minimal' },
    body: JSON.stringify({ etat, version: etat.version || 1, updated_at: new Date().toISOString() }),
  });
}

/* ---------- questions Quinytz ---------- */
export async function lireQuestions() {
  const toutes = [];
  for (let debut = 0; ; debut += 1000) {
    const lot = await appel(`/rest/v1/wikideck_questions?select=id,question,reponse,variantes,theme,difficulte,actif&actif=eq.true&order=id`,
      { headers: { Range: `${debut}-${debut + 999}` } });
    toutes.push(...lot);
    if (lot.length < 1000) break;
  }
  return toutes;
}

/* ---------- notifications push ---------- */
export async function enregistrerAbonnement(abonnement, prefs) {
  return appel('/rest/v1/wikideck_push?on_conflict=endpoint', {
    method: 'POST',
    headers: { Prefer: 'resolution=merge-duplicates,return=minimal' },
    body: JSON.stringify({ endpoint: abonnement.endpoint, abonnement, prefs, maj: new Date().toISOString() }),
  });
}
export async function supprimerAbonnement(endpoint) {
  return appel(`/rest/v1/wikideck_push?endpoint=eq.${encodeURIComponent(endpoint)}`, { method: 'DELETE' });
}
