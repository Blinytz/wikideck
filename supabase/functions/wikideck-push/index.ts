// Fonction serveur des notifications WikiDeck (spec §9).
// Appelée toutes les 5 minutes par pg_cron. Lit chaque abonnement et l'état
// de jeu de son propriétaire, décide quoi envoyer, n'envoie jamais deux fois
// la même chose (table wikideck_push_envoyees).
//
// Secrets de la fonction : VAPID_PUBLIC, VAPID_PRIVATE, VAPID_SUBJECT, CRON_SECRET.
// SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont fournis par la plateforme.
// Déploiement : supabase functions deploy wikideck-push --no-verify-jwt

import webpush from 'npm:web-push@3.6.7';
import { createClient } from 'npm:@supabase/supabase-js@2';

const H = 3600e3;
const SITE = 'https://blinytz.github.io/wikideck/';

function paris(t: number) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('fr-CA', {
    timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date(t)).map(x => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, heure: Number(p.hour) };
}
const jourDeJeu = (t: number, debut = 4) => paris(t - debut * H).date;

type Notif = { cle: string; type: string; titre: string; texte: string; url?: string };

// deno-lint-ignore no-explicit-any
function aEnvoyer(etat: any, t: number): Notif[] {
  const out: Notif[] = [];
  const cfg = etat.configUtilisateur || {};
  // paquet prêt
  const p = etat.paquets;
  if (p) {
    const duree = cfg.dureeBaseSecondes ?? 43200;
    const prog = (p.progression || 0) + Math.max(0, (t - (p.lastTs || t)) / 1000 / duree);
    const prets = (p.prets || 0) + Math.floor(prog);
    if (prets > 0) out.push({ cle: `paquet:${p.lastTs}:${prets}`, type: 'paquet', titre: 'Paquet prêt', texte: prets > 1 ? `${prets} paquets à ouvrir` : 'Un paquet t’attend', url: SITE });
  }
  // boutique
  for (const em of etat.boutique?.emplacements || []) {
    const o = em.offre;
    if (o && o.fin > t) {
      if (o.flash) out.push({ cle: `flash:${o.uid}`, type: 'flash', titre: 'Offre flash', texte: `-${o.remise} % pendant quelques heures`, url: `${SITE}#boutique` });
      else out.push({ cle: `offre:${o.uid}`, type: 'offre', titre: 'Nouvelle offre', texte: 'La boutique a une nouvelle offre', url: `${SITE}#boutique` });
      if (o.fin - t <= 2 * H) out.push({ cle: `expire:${o.uid}`, type: 'expire', titre: 'Offre bientôt expirée', texte: 'Une offre de la boutique expire dans moins de 2 h', url: `${SITE}#boutique` });
    } else if (!o && em.prochaine && em.prochaine <= t) {
      out.push({ cle: `offre-vide:${em.prochaine}`, type: 'offre', titre: 'Nouvelle offre', texte: 'La boutique a une nouvelle offre', url: `${SITE}#boutique` });
    }
  }
  const debut = cfg.heureDebutJour ?? 4;
  const jour = jourDeJeu(t, debut);
  const heure = paris(t).heure;
  // série en danger, à 21 h
  const objectif = cfg.bonnesParJour ?? 10;
  const bonnes = etat.serie?.jours?.[jour] || 0;
  if (heure >= 21 && bonnes < objectif) {
    const gels = etat.serie?.gels || 0;
    out.push({ cle: `serie:${jour}`, type: 'serie', titre: 'Série en danger',
      texte: `${bonnes} / ${objectif} bonnes réponses aujourd’hui · ${gels} Gel${gels > 1 ? 's' : ''}`, url: `${SITE}#questions` });
  }
  // question du jour, à 9 h
  const qdj = etat.quiz?.qdj;
  if (heure >= 9 && heure < 21 && !(qdj?.jour === jour && qdj?.faite)) {
    out.push({ cle: `qdj:${jour}`, type: 'qdj', titre: 'Question du jour', texte: 'Une question Omniscient t’attend', url: `${SITE}#questions` });
  }
  return out;
}

Deno.serve(async (req) => {
  if (req.headers.get('x-cron-secret') !== Deno.env.get('CRON_SECRET')) return new Response('interdit', { status: 403 });
  webpush.setVapidDetails(Deno.env.get('VAPID_SUBJECT')!, Deno.env.get('VAPID_PUBLIC')!, Deno.env.get('VAPID_PRIVATE')!);
  const db = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);
  const t = Date.now();
  const { data: abos } = await db.from('wikideck_push').select('endpoint,user_id,abonnement,prefs');
  let envoyees = 0;
  for (const ab of abos || []) {
    const { data: e } = await db.from('wikideck_etat').select('etat').eq('user_id', ab.user_id).maybeSingle();
    if (!e) continue;
    for (const n of aEnvoyer(e.etat, t)) {
      if (ab.prefs?.[n.type] === false) continue;
      const { error } = await db.from('wikideck_push_envoyees').insert({ user_id: ab.user_id, cle: n.cle });
      if (error) continue;   // déjà envoyée
      try {
        await webpush.sendNotification(ab.abonnement, JSON.stringify({ titre: n.titre, texte: n.texte, tag: n.type, url: n.url }));
        envoyees++;
      } catch (err) {
        // deno-lint-ignore no-explicit-any
        const code = (err as any)?.statusCode;
        if (code === 404 || code === 410) { await db.from('wikideck_push').delete().eq('endpoint', ab.endpoint); break; }
      }
    }
  }
  await db.rpc('wikideck_purger_push');
  return Response.json({ abonnements: abos?.length || 0, envoyees });
});
