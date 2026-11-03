// Notifications push (spec §9) : abonnement du navigateur via le service
// worker, préférences une par une. L'envoi est fait par une fonction du
// Supabase Éclats, déclenchée par pg_cron.

import { etat, sauvegarder } from './etat.js';
import { enregistrerAbonnement, supprimerAbonnement, estConnecte } from './serveur.js';

// Clé publique VAPID (la clé privée vit dans les secrets de la fonction serveur).
export const VAPID_PUBLIQUE = 'BDP0es16rH6pFdoCwUi3Qmy4n3EMWGSeFci5mMinNSipPNZuKeRR--vLf4D9PTrkdesZZ8bzGxui5-nYCRIiTIc';

export const TYPES_NOTIF = {
  paquet: 'Paquet prêt',
  offre: 'Nouvelle offre',
  flash: 'Offre flash',
  expire: 'Offre qui expire dans 2 h',
  serie: 'Série en danger (21 h)',
  qdj: 'Question du jour (9 h)',
};

export function prefs() {
  etat.prefs ??= {};
  return (etat.prefs.notifs ??= Object.fromEntries(Object.keys(TYPES_NOTIF).map(k => [k, true])));
}

export function disponible() {
  return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
}

function cleVersOctets(b64) {
  const s = atob(b64.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((b64.length + 3) % 4));
  return Uint8Array.from(s, c => c.charCodeAt(0));
}

async function abonnement(creer) {
  const reg = await navigator.serviceWorker.ready;
  let ab = await reg.pushManager.getSubscription();
  if (!ab && creer) {
    ab = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: cleVersOctets(VAPID_PUBLIQUE) });
  }
  return ab;
}

export async function estAbonne() {
  if (!disponible()) return false;
  return !!(await abonnement(false));
}

/* Active les notifications : permission, abonnement, enregistrement au serveur. */
export async function activer() {
  if (!disponible()) throw new Error('Notifications indisponibles sur ce navigateur.');
  if (!estConnecte()) throw new Error('Connecte-toi au compte Éclats d’abord.');
  const perm = await Notification.requestPermission();
  if (perm !== 'granted') throw new Error('Notifications refusées par le navigateur.');
  const ab = await abonnement(true);
  await enregistrerAbonnement(ab.toJSON(), prefs());
}

export async function desactiver() {
  const ab = await abonnement(false);
  if (ab) { await supprimerAbonnement(ab.endpoint).catch(() => {}); await ab.unsubscribe(); }
}

export async function changerPref(cle, valeur) {
  prefs()[cle] = valeur;
  sauvegarder();
  const ab = disponible() ? await abonnement(false) : null;
  if (ab && estConnecte()) await enregistrerAbonnement(ab.toJSON(), prefs());
}
