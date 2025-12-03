# API-Football – Cas d’usage par endpoint

Guidage exhaustif des requêtes possibles (sans modèles de réponse), dérivé des fichiers `api-football-doc/`. Toutes les requêtes utilisent la clé `x-apisports-key`.

## Référentiels
- `GET /countries` : lister tous les pays ou filtrer par `name`, `code`, `search`.
- `GET /leagues` : rechercher une ligue/coupe par `id`, `name`, `country`, `code`, `team`, `season`, `type`, `current=true|false`, `search`, `last`.
- `GET /leagues/seasons` : lister toutes les saisons connues.
- `GET /timezone` : lister les timezones supportées.

## Ligues & saisons
- `GET /leagues?id=<league_id>&season=<year>` : récupérer une ligue et ses couvertures pour une saison.
- `GET /leagues?name=<name>|country=<name>|code=<ISO>|type=<league|cup>|current=true|last=<n>` : explorations et filtres divers.
- `GET /leagues?team=<team_id>` : ligues dans lesquelles une équipe a joué.

## Équipes
- `GET /teams?id=<team_id>` : info équipe + stade.
- `GET /teams?name=<name>` ou `search=<query>` : recherche textuelle.
- `GET /teams?league=<league_id>&season=<year>` : équipes d’une ligue/saison.
- `GET /teams?country=<name>|code=<ISO>|venue=<venue_id>` : filtres pays/code/stade.
- `GET /teams/countries` : pays disposant d’équipes.
- `GET /teams/seasons?team=<team_id>` : saisons jouées par une équipe.

## Stades
- `GET /venues?id=<venue_id>|name=<name>|city=<city>|country=<country>|search=<query>` : informations stade.

## Classements
- `GET /standings?league=<league_id>&season=<year>` : classement complet.
- `GET /standings?team=<team_id>&season=<year>` : classement centré équipe.

## Fixtures (calendrier/générique)
- `GET /fixtures?id=<fixture_id>` ou `ids=...` : match précis.
- `GET /fixtures?date=YYYY-MM-DD` : matchs d’une date.
- `GET /fixtures?league=<league_id>&season=<year>` : calendrier d’une compétition.
- `GET /fixtures?team=<team_id>&season=<year>` : calendrier d’une équipe (avec `from`, `to`, `round`, `status`, `timezone`).
- `GET /fixtures?live=all` ou `live=<league_ids>` : matchs en direct.
- `GET /fixtures?next=<n>` / `last=<n>` : prochains/derniers matchs globaux.
- Combinaisons : `from/to`, `venue=<id>`, `status=<code>`, `round=<label>`, `timezone=<tz>`.

## Fixtures – tours/journées
- `GET /fixtures/rounds?league=<league_id>&season=<year>` : toutes les journées.
- Paramètres : `dates=true` pour inclure les dates, `current=true` pour la journée courante.

## Head-to-head
- `GET /fixtures/headtohead?h2h=<team1>-<team2>` : historique entre deux équipes.
- Filtres : `status`, `date` ou `from/to`, `league`, `season`, `next`, `last`, `timezone`.

## Détails de match
- `GET /fixtures/events?fixture=<id>` : chronologie; filtres `team`, `player`, `type`.
- `GET /fixtures/lineups?fixture=<id>` : compositions; filtres `team`, `player`, `type`.
- `GET /fixtures/statistics?fixture=<id>` : stats d’équipe; filtres `team`, `type`, `half=true`.
- `GET /fixtures/players?fixture=<id>` : stats joueurs; filtre `team`.

## Joueurs – référentiels et stats
- `GET /players?search=<name>` : recherche joueur (option `team`, `league`, `season`, `id`).
- `GET /players?team=<team_id>&season=<year>` : joueurs + stats d’une équipe.
- `GET /players?league=<league_id>&season=<year>` : joueurs + stats d’une ligue (pagination via `page`).
- `GET /players?id=<player_id>&season=<year>` : stats d’un joueur pour une saison.
- `GET /players/seasons` ou `players/seasons?player=<id>` : saisons disponibles (globales ou pour un joueur).
- `GET /players/squads?team=<id>` : effectif d’une équipe.
- `GET /players/squads?player=<id>` : équipes d’un joueur.
- `GET /players/profiles?player=<id>` ou `search=<query>` : fiche bio.
- `GET /players/teams?player=<id>` : parcours d’équipes pour un joueur.

## Tops joueurs
- `GET /players/topscorers?league=<id>&season=<year>` : meilleurs buteurs.
- `GET /players/topassists?league=<id>&season=<year>` : meilleurs passeurs.
- `GET /players/topyellowcards?league=<id>&season=<year>` : tops cartons jaunes.
- `GET /players/topredcards?league=<id>&season=<year>` : tops cartons rouges.

## Statuts de match
- Tableau des statuts courts/longs/type/description (fichier `match_status.txt`) à utiliser pour comprendre/filtrer `status`.

## Blessures / indisponibilités
- `GET /injuries?league=<id>&season=<year>` : blessures par ligue/saison.
- Filtres: `fixture`, `team`, `player`, `date`, `timezone` (combinables).
- `GET /sidelined?player=<id>` ou `?players=<ids>` : historiques d’absences joueur.
- `GET /sidelined?coach=<id>` ou `?coachs=<ids>` : historiques d’absences coach.

## Pronostics & cotes
- `GET /predictions?fixture=<id>` : prédiction d’issue pour un match.
- `GET /odds?fixture=<id>` : cotes pré-match d’un match précis.
- `GET /odds?date=YYYY-MM-DD&league=<id>&season=<year>` : cotes pré-match par date/ligue.
- Référentiels : `GET /odds/bookmakers`, `/odds/bets`, `/odds/mapping`, `GET /odds/live`.

## Transferts
- `GET /transfers?player=<id>` : historique transferts joueur.
- `GET /transfers?team=<id>` : transferts liés à une équipe.

## Palmarès
- `GET /trophies?player=<id>` ou `?players=<ids>` : trophées d’un joueur.
- `GET /trophies?coach=<id>` ou `?coachs=<ids>` : trophées d’un coach.

## Coachs
- `GET /coachs?id=<id>` : fiche coach.
- `GET /coachs?team=<team_id>` : coach d’une équipe.
- `GET /coachs?search=<name>` : recherche coach.

## Divers utilitaires
- `GET /status` : statut API / quota compte.
