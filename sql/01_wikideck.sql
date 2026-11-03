-- WikiDeck dans le Supabase Éclats (projet psutbulpezfdftmaqkoo).
-- Additif et idempotent : se rejoue sans casse. Ne touche à aucune table
-- existante ; les Éclats passent par le registre commun (eclats_reward,
-- eclats_spend, eclats_balance), déjà en place.
--
-- À exécuter dans l'éditeur SQL du projet. Poids attendu : quelques Mo
-- (catalogue ~8 800 lignes, questions ~11 000 lignes, un état de jeu par joueur).

-- 1. État de jeu : un document par joueur (cartes, paquets, historique,
--    lectures, Résonance, questions, série, objectifs, boutique).
create table if not exists wikideck_etat (
  user_id    uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  etat       jsonb not null,
  version    integer not null default 1,
  updated_at timestamptz not null default now()
);
alter table wikideck_etat enable row level security;
drop policy if exists wikideck_etat_proprio on wikideck_etat;
create policy wikideck_etat_proprio on wikideck_etat
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
grant select, insert, update on wikideck_etat to authenticated;

-- 2. Catalogue des cartes, synchronisé par GitHub Action à chaque push de data/.
--    Une carte retirée n'est jamais supprimée : elle passe archivee = true.
create table if not exists wikideck_cartes (
  id          text primary key,
  nom         text not null,
  collection  text not null,
  rarete      text not null,
  archivee    boolean not null default false,
  maj         timestamptz not null default now()
);
alter table wikideck_cartes enable row level security;
drop policy if exists wikideck_cartes_lecture on wikideck_cartes;
create policy wikideck_cartes_lecture on wikideck_cartes for select to authenticated using (true);
grant select on wikideck_cartes to authenticated;

-- 3. Copie des questions Quinytz (GitHub Action hebdomadaire). Lisibles par
--    un utilisateur connecté seulement : les réponses ne sortent jamais en public.
create table if not exists wikideck_questions (
  id          text primary key,
  question    text not null,
  reponse     text not null,
  variantes   text[] not null default '{}',
  theme       text,
  difficulte  smallint not null check (difficulte between 1 and 5),
  actif       boolean not null default true,
  maj         timestamptz not null default now()
);
alter table wikideck_questions enable row level security;
drop policy if exists wikideck_questions_lecture on wikideck_questions;
create policy wikideck_questions_lecture on wikideck_questions for select to authenticated using (true);
grant select on wikideck_questions to authenticated;

-- 4. Notifications push : abonnements du navigateur et préférences.
create table if not exists wikideck_push (
  endpoint    text primary key,
  user_id     uuid not null default auth.uid() references auth.users (id) on delete cascade,
  abonnement  jsonb not null,
  prefs       jsonb not null default '{}'::jsonb,
  maj         timestamptz not null default now()
);
alter table wikideck_push enable row level security;
drop policy if exists wikideck_push_proprio on wikideck_push;
create policy wikideck_push_proprio on wikideck_push
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
grant select, insert, update, delete on wikideck_push to authenticated;

-- Journal des notifications déjà envoyées (anti-doublon), lu par la fonction
-- serveur seulement (clé secrète) : aucun accès client.
create table if not exists wikideck_push_envoyees (
  user_id  uuid not null,
  cle      text not null,
  envoyee  timestamptz not null default now(),
  primary key (user_id, cle)
);
alter table wikideck_push_envoyees enable row level security;

-- Purge : on ne garde que 30 jours d'anti-doublon.
create or replace function wikideck_purger_push() returns void
language sql security definer set search_path = public as $$
  delete from wikideck_push_envoyees where envoyee < now() - interval '30 days';
$$;
revoke all on function wikideck_purger_push() from public, anon, authenticated;
