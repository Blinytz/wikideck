-- Déclenchement des notifications WikiDeck toutes les 5 minutes.
-- Prérequis : extensions pg_cron et pg_net (Database > Extensions), fonction
-- wikideck-push déployée, secret CRON_SECRET posé sur la fonction.
-- Remplacer __CRON_SECRET__ par la même valeur que le secret de la fonction
-- (une copie remplie est fournie hors dépôt).

create extension if not exists pg_cron;
create extension if not exists pg_net;

select cron.unschedule('wikideck-push') where exists (select 1 from cron.job where jobname = 'wikideck-push');
select cron.schedule('wikideck-push', '*/5 * * * *', $$
  select net.http_post(
    url := 'https://psutbulpezfdftmaqkoo.supabase.co/functions/v1/wikideck-push',
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-cron-secret', '__CRON_SECRET__'),
    body := '{}'::jsonb
  );
$$);
