"""Collections de culture generale du 30/09/2026 (geographie, lettres, sciences,
religions, economie et techniques), validees d'avance par l'utilisateur.

Chaque entree : slug -> (nom, titres de pages Wikipedia francaises). Les cartes
deja presentes ailleurs y sont deplacees (transferts calcules a part).
"""

LOT_SUITE = {
    'deserts': ('Déserts', [
        "Sahara", "Désert de Gobi", "Désert d'Atacama", "Désert du Kalahari", "Namib", "Rub al-Khali", "Désert de Syrie",
        "Néguev", "Désert du Thar", "Taklamakan", "Désert des Mojaves", "Vallée de la Mort",
        "Désert de Sonora", "Désert de Chihuahua", "Grand désert de Victoria", "Désert de Simpson", "Désert du Karakoum",
        "Kyzylkoum", "Dasht-e Lut", "Dasht-e Kavir", "Désert libyque", "Ténéré", "Dépression de l'Afar", "Wadi Rum",
        "Désert de Tabernas", "Bardenas Reales", "Désert de Patagonie", "Désert blanc", "Grand Erg oriental"]),
    'lacs': ('Lacs', [
        "Mer Caspienne", "Lac Supérieur", "Lac Victoria", "Lac Huron", "Lac Michigan", "Lac Tanganyika", "Lac Baïkal",
        "Grand lac de l'Ours", "Lac Malawi", "Lac Érié", "Lac Ontario", "Lac Ladoga", "Lac Balkhach", "Lac Titicaca",
        "Lac Tchad", "Mer d'Aral", "Lac Léman", "Lac du Bourget", "Lac d'Annecy", "Lac de Côme", "Lac de Garde",
        "Lac Majeur", "Loch Ness", "Lac de Constance", "Lac Tana", "Lac Turkana", "Lac Kivu", "Grand Lac Salé",
        "Lac Tahoe", "Lac Louise (Alberta)", "Lac Inle", "Lac Toba", "Lac de Bled", "Lacs de Plitvice", "Mer Morte", "Lac Rose",
        "Lac Natron", "Lac de Tibériade"]),
    'regions-francaises': ('Régions françaises', [
        "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne (région administrative)", "Centre-Val de Loire",
        "Collectivité de Corse", "Grand Est", "Hauts-de-France", "Île-de-France", "Normandie (région administrative)",
        "Nouvelle-Aquitaine", "Occitanie (région administrative)", "Pays de la Loire", "Provence-Alpes-Côte d'Azur",
        "Guyane"]),
    'mouvements-litteraires': ('Mouvements littéraires', [
        "Humanisme", "Pléiade (XVIe siècle)", "Littérature baroque", "Préciosité", "Classicisme", "Lumières (philosophie)",
        "Romantisme", "Réalisme (littérature)", "Naturalisme (littérature)", "Parnasse (poésie)", "Symbolisme (art)",
        "Décadentisme", "Surréalisme", "Dada", "Existentialisme", "Théâtre de l'absurde", "Nouveau roman",
        "Oulipo", "Négritude", "Beat Generation", "Génération perdue", "Réalisme magique", "Futurisme",
        "Sturm und Drang", "Préromantisme", "Les Hussards (mouvement littéraire)"]),
    'genres-litteraires': ('Genres littéraires', [
        "Roman (littérature)", "Nouvelle (littérature)", "Conte", "Fable", "Poésie", "Sonnet", "Haïku", "Ballade",
        "Épopée", "Tragédie", "Comédie", "Drame romantique", "Vaudeville", "Farce (théâtre)", "Essai", "Autobiographie",
        "Roman épistolaire", "Roman policier", "Science-fiction", "Fantasy",
        "Roman d'aventures", "Roman historique", "Utopie", "Dystopie", "Pamphlet", "Chanson de geste",
        "Roman de chevalerie"]),
    'prix-goncourt': ('Prix Goncourt', [
        "À l'ombre des jeunes filles en fleurs", "Le Feu (Barbusse)", "La Condition humaine", "Les Mandarins",
        "Les Racines du ciel", "La Vie devant soi", "L'Amant (roman)", "Le Roi des Aulnes (roman)", "Rue des boutiques obscures",
        "Le Rivage des Syrtes", "Les Bienveillantes", "La Carte et le Territoire", "Au revoir là-haut", "Chanson douce",
        "L'Ordre du jour (récit)", "L'Anomalie", "La Plus Secrète Mémoire des hommes", "Veiller sur elle", "Houris (roman)",
        "Trois femmes puissantes", "Le Sermon sur la chute de Rome", "Pas pleurer", "Leurs enfants après eux",
        "Les Grandes Familles", "Batouala", "Le Soleil des Scorta", "Le Rocher de Tanios", "Les Champs d'honneur",
        "La Bataille (roman de Rambaud)"]),
    'corps-humain': ('Corps humain', [
        "Cœur", "Encéphale humain", "Poumon", "Foie", "Rein", "Estomac", "Intestin grêle", "Côlon", "Pancréas",
        "Rate", "Vésicule biliaire", "Peau", "Œil humain", "Oreille", "Langue (anatomie humaine)", "Nez", "Thyroïde",
        "Squelette humain", "Muscle", "Sang", "Moelle osseuse", "Système nerveux", "Système immunitaire",
        "Système endocrinien", "Appareil digestif", "Appareil circulatoire", "Appareil respiratoire",
        "Système lymphatique", "Neurone", "Érythrocyte", "Leucocyte", "Acide désoxyribonucléique", "Hypophyse",
        "Moelle spinale", "Cervelet", "Hippocampe (cerveau)", "Diaphragme (organe)", "Cornée", "Rétine", "Tympan humain"]),
    'maladies-et-epidemies': ('Maladies et épidémies', [
        "Peste noire", "Grippe espagnole", "Maladie à coronavirus 2019", "Syndrome d'immunodéficience acquise",
        "Variole", "Peste", "Choléra", "Tuberculose", "Paludisme", "Lèpre", "Rage (maladie)", "Poliomyélite",
        "Rougeole", "Fièvre jaune", "Maladie à virus Ebola", "Typhus", "Syphilis", "Diphtérie", "Tétanos",
        "Grippe", "Scorbut", "Dengue", "Diabète sucré", "Cancer", "Maladie d'Alzheimer", "Maladie de Parkinson",
        "Accident vasculaire cérébral", "Infarctus du myocarde", "Épilepsie", "Hémophilie", "Mucoviscidose",
        "Sclérose en plaques", "Asthme", "Peste de Justinien", "Variole du singe", "Maladie à virus Zika"]),
    'theoremes-et-lois': ('Théorèmes et lois célèbres', [
        "Théorème de Pythagore", "Théorème de Thalès", "Poussée d'Archimède", "Lois du mouvement de Newton",
        "Loi universelle de la gravitation", "Lois de Kepler", "Relativité restreinte", "Relativité générale",
        "E=mc2", "Principe d'incertitude", "Loi d'Ohm", "Équations de Maxwell", "Conservation de l'énergie",
        "Premier principe de la thermodynamique", "Deuxième principe de la thermodynamique", "Loi de Boyle-Mariotte",
        "Loi d'Avogadro", "Loi de Coulomb (électrostatique)", "Loi de conservation de la masse", "Loi de Hooke",
        "Principe de Pascal", "Effet Doppler", "Lois de Snell-Descartes", "Dernier théorème de Fermat",
        "Théorèmes d'incomplétude de Gödel", "Suite de Fibonacci", "Nombre d'or", "Pi", "Théorème des quatre couleurs",
        "Conjecture de Poincaré", "Loi de Moore", "Sélection naturelle", "Lois de Mendel", "Big Bang",
        "Tectonique des plaques", "Effet photoélectrique"]),
    'religions-du-monde': ('Religions du monde', [
        "Christianisme", "Islam", "Hindouisme", "Bouddhisme", "Judaïsme", "Sikhisme", "Taoïsme", "Confucianisme",
        "Shinto", "Jaïnisme", "Zoroastrisme", "Bahaïsme", "Catholicisme", "Protestantisme", "Christianisme orthodoxe",
        "Sunnisme", "Chiisme", "Theravāda", "Mahāyāna", "Bouddhisme tibétain", "Zen", "Anglicanisme", "Vaudou",
        "Candomblé", "Rastafarisme", "Mormonisme", "Témoins de Jéhovah", "Manichéisme (religion)",
        "Religion de l'Égypte antique", "Religion grecque antique"]),
    'textes-sacres': ('Textes sacrés', [
        "Bible", "Ancien Testament", "Nouveau Testament", "Torah", "Talmud", "Coran", "Hadith", "Veda", "Rig-Veda",
        "Upanishad", "Bhagavad-Gita", "Tipitaka", "Sūtra du Lotus", 
        "Entretiens de Confucius", "Avesta", "Guru Granth Sahib", "Livre de Mormon", "Livre des morts des Anciens Égyptiens",
        "Popol Vuh", "Évangile", "Apocalypse", "Genèse", "Psaumes", "Kojiki", "Sefer HaZohar", "Bardo Thödol",
        "Manuscrits de la mer Morte"]),
    'fetes-religieuses': ('Fêtes religieuses', [
        "Noël", "Pâques", "Pentecôte", "Ascension (fête)", "Toussaint", "Épiphanie", "Carême", "Mardi gras",
        "Assomption de Marie", "Chandeleur", "Dimanche des Rameaux", "Ramadan", "Aïd el-Fitr", "Aïd el-Kebir", "Mawlid",
        "Achoura", "Pessa'h", "Yom Kippour", "Roch Hachana", "Hanoucca", "Pourim", "Souccot", "Divali", "Holi",
        "Vesak", "Nouvel An chinois", "Obon", "Vaisakhi", "Navaratri", "Kumbh Mela", "Norouz", "Jour des morts (Mexique)"]),
    'crises-economiques': ('Crises économiques', [
        "Tulipomanie", "Grande Dépression", "Krach de 1929", "Premier choc pétrolier", "Deuxième choc pétrolier",
        "Krach d'octobre 1987", "Crise économique asiatique", "Bulle Internet", "Crise des subprimes",
        "Crise financière mondiale de 2007-2008", "Crise de la dette dans la zone euro", "Crise de la dette publique grecque",
        "Hyperinflation de la république de Weimar", "Système de Law", "Krach de 1720", "Panique du 18 septembre 1873",
        "Panique de 1907", "Crise économique argentine", "Crise bancaire et financière de l'automne 2008", "Crise économique liée à la pandémie de Covid-19",
        "Hyperinflation au Zimbabwe", ]),
    'entreprises-emblematiques': ('Entreprises emblématiques', [
        "Apple", "Microsoft", "Google", "Amazon (entreprise)", "Meta Platforms", "Tesla (automobile)",
        "Nvidia", "IBM", "Samsung Electronics", "Sony", "Toyota", "Volkswagen (entreprise)", "Ford", "The Coca-Cola Company",
        "McDonald's", "Nike (entreprise)", "LVMH", "Chanel", "Hermès International", "L'Oréal",
        "TotalEnergies", "Airbus (entreprise)", "Boeing", "Renault", "Michelin", "Danone", "Nestlé", "IKEA",
        "The Walt Disney Company", "Netflix", "OpenAI", "Compagnie anglaise des Indes orientales", "Standard Oil",
        "Nokia", "Lego", "Ferrari (entreprise)", "Alibaba Group", "Saudi Aramco"]),
}
