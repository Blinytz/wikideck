# La Station · conception du gameplay

Document de travail, avant toute ligne de code. Version 2 du 09/10/2026.

## But

Obtenir les paquets de plus en plus vite en progressant, avec des améliorations de plus en plus dures et longues à obtenir, et un vrai avantage à être présent et actif.

Pas de cartes (elles servent au roguelike), pas de bourse.

## La boucle

```
Expéditions ──► minerai de Lumen ──► Raffinerie ──► Lumen pur ──► Presse ──► paquet
     ▲                                   │
     │ vivres                            └──► résidus ──► Recherche (savoir)
Plantations                                                   │
     ▲                                                        ▼
     └─────────────── arbres de recherche ◄───────────────────┘
```

1. **Expéditions** : partir chercher le minerai de Lumen sur une carte en anneaux. Plus loin, c'est plus long, plus dangereux, plus riche.
2. **Raffinerie** : le minerai brut devient du Lumen pur ; plus le minerai vient de loin, plus il est riche et impur, donc exigeant à raffiner.
3. **Presse** : le Lumen pur remplit la jauge du paquet.
4. **Plantations** : produisent les vivres sans lesquels une expédition ne part pas loin, et des cultures spéciales qui servent de boosts.
5. **Recherche** : les résidus du raffinage et les découvertes d'expédition donnent du savoir, qui débloque des nœuds dans trois arbres.

## Ce qui pousse à s'améliorer

- **Les zones proches s'épuisent.** Le rendement d'une zone baisse à chaque expédition et remonte lentement. Pour produire plus, il faut aller plus loin.
- **Aller plus loin exige de meilleures expéditions** : plus d'endurance (vivres), plus de capacité, de quoi survivre aux dangers de la zone.
- **Le minerai lointain exige une meilleure raffinerie** : sans la technologie adaptée, ses impuretés gâchent l'essentiel de sa richesse.
- **La surchauffe de la Presse** : chaque paquet renchérit le suivant, la chaleur retombe en une journée. Améliorer la Presse (refroidissement) relève ce plafond.

## La croissance exponentielle

**Trois arbres de recherche** :
- **Logistique** : vitesse, capacité et endurance des expéditions, nouvelles zones, nombre d'équipes.
- **Industrie** : rendement et vitesse de la raffinerie, traitement des impuretés, automatisations, refroidissement de la Presse.
- **Agronomie** : nouvelles cultures, rendement, cultures-boosts.

**La règle de fond** : chaque amélioration multiplie la production (par exemple ×1,3), mais coûte nettement plus cher que la précédente (par exemple ×2). Chaque palier demande donc environ 1,5 fois plus de temps que le précédent, tout en rendant le jeu plus rapide.

| Moment | Une amélioration toutes les... |
|---|---|
| premier jour | quelques minutes |
| première semaine | heure |
| premier mois | jour |
| ensuite | plusieurs jours, avec de grands objectifs |

Les nœuds profonds débloquent des mécaniques, pas seulement des pourcentages : une deuxième équipe, la fusion automatique, une zone nouvelle, une culture nouvelle.

## Être présent paie

- **Expéditions courtes** : à l'heure passée, une expédition de 15 minutes rapporte bien plus qu'une de 8 heures. Celui qui repasse souvent gagne plus ; celui qui part dormir lance une longue.
- **Raffinage à la main** : la raffinerie automatique est lente ; raffiner soi-même (le plateau de fusion) va beaucoup plus vite.
- **Événements d'expédition** : en route, une équipe rencontre un choix (filon caché, danger, rencontre). Sur place, on choisit ; absent, l'équipe prend l'option prudente.
- **L'élan** : chaque action entretient un multiplicateur qui monte tant qu'on joue et retombe doucement quand on part.

## Les temps visés selon la progression

Chiffres de départ, à régler au simulateur.

| Niveau | Sans y toucher | Passages réguliers | Jeu actif |
|---|---|---|---|
| début | 24 h | 6 h | 15 min |
| après une semaine | 18 h | 2 h | 5 min |
| après un mois | 12 h | 45 min | 2 min |
| après trois mois | 8 h | 20 min | 1 min |

Le temps au repos baisse peu ; le temps actif baisse beaucoup. L'écart entre les deux grandit avec le niveau : plus on progresse, plus la présence rapporte.

## L'équilibrage

Avant tout code de jeu, un simulateur fait jouer quatre profils sur 90 jours :
1. le joueur qui ne touche à rien ;
2. celui qui passe 4 fois par jour ;
3. celui qui passe 10 fois par jour ;
4. celui qui joue activement 30 minutes par jour en plus de ses passages.

On règle les coûts, les multiplicateurs et la surchauffe jusqu'à obtenir les courbes visées, et pour vérifier que chaque profil progresse sans stagner ni exploser.
