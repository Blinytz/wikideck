# Activer le serveur de WikiDeck

Les clés VAPID et le secret du cron sont dans `.secrets/vapid.json` (hors dépôt, sur ce PC).

1. **Supabase Éclats > SQL Editor** : exécuter `sql/01_wikideck.sql`.
2. **GitHub, Blinytz/wikideck > Settings > Secrets and variables > Actions** :
   - `ECLATS_SERVICE_KEY` : clé secrète (service_role) du projet Éclats ;
   - `QUINYTZ_SUPABASE_URL` et `QUINYTZ_SERVICE_KEY` : URL et clé secrète du projet Quinytz.
   Puis lancer à la main (Actions > Run workflow) « Catalogue vers Supabase Éclats » et « Copie des questions Quinytz ».
3. **Supabase Éclats > Edge Functions** : créer `wikideck-push` avec le code de
   `supabase/functions/wikideck-push/index.ts`, vérification JWT désactivée, et les secrets
   `VAPID_PUBLIC`, `VAPID_PRIVATE`, `VAPID_SUBJECT`, `CRON_SECRET` (valeurs de `.secrets/vapid.json` :
   publicKey, privateKey, subject, cronSecret).
4. **SQL Editor** : exécuter `.secrets/02_cron_rempli.sql` (pg_cron et pg_net).
5. **WikiDeck > Plus > Réglages** : se connecter au compte Éclats (la migration se fait seule :
   cartes, paquets et progression envoyés, Éclats locaux transférés à la Centrale), puis
   activer les notifications.
