# Intents & Tools (Lucide Backend)

Ce document résume les intentions actuellement gérées par le backend et les entités attendues, ainsi que les tools (function calling) qui doivent être déclenchés. Il sert de référence produit/technique pour étendre le routage.

## Principes généraux
- Modèle : `deepseek-chat` avec `response_format: {"type": "json_object"}` pour l’extraction d’intentions/entités.
- Tools disponibles : `search_team`, `search_player`, `fixtures_by_date`, `team_next_fixtures`, `live_fixtures`, `standings`, `team_statistics`, `head_to_head`, `top_scorers`, `top_assists`, `injuries`, `predictions`, `odds_by_date`, `odds_by_fixture`.
- Tools a ajouter (doc API-Football) : referentiels (countries, leagues, leagues/seasons, timezone, teams/countries), recherche/filtre fixtures generique, detail fixture (events/lineups/statistics/players), info equipe/saisons/effectif, profils et stats joueur avancees, tops cartons, sidelined, transferts, trophees, coachs, venues.
- Mapping ligues : Ligue 1=61, Premier League=39, La Liga=140, Bundesliga=78, Serie A=135, Ligue des Champions=2, Europa League=3 (compléter selon besoin).
- Séquence standard : détection intent/entités → tool(s) appropriés → analyse → réponse finale (rappel : ne jamais garantir un résultat de match).

## Intentions prioritaires (Doc développeur v1)
Ces règles s’appliquent en priorité pour les quatre premières intentions.

- `calendrier_matchs`
  - Entités : `date` (défaut = aujourd’hui), `league`/`league_id` (mapping {pays + division} pour les ligues floues), `season` (défaut saison en cours), `status` (NS/FT/LIVE).
  - Flow : si ligue ambiguë → demander clarification ; sinon appeler `fixtures_by_date` avec date + league_id + season (+ status si fourni).

- `analyse_rencontre`
  - Entités : deux `teams` (résolues via `search_team`), `fixture_id` si connu, `league`/`date`/`season` optionnels.
  - Flow : identifier la prochaine fixture à venir (via `fixtures_by_date` ou `team_next_fixtures`) puis chaîner `predictions`, `head_to_head`, `odds_by_fixture`.

- `stats_equipe_saison`
  - Entités : `team` → `team_id` (via `search_team`), `league`/`league_id` optionnel, `season` (défaut saison en cours), `depth` non exploité pour l’instant.
  - Flow : appeler `team_statistics` avec `team_id`, `league_id`, `season`.

- `stats_joueur`
  - Entités : `player` → `player_id` (via `search_player`), `team` en cas d’ambiguïté, `season` (défaut saison active), `depth` non exploité.
  - Flow : `search_player` suffit pour récupérer les statistiques globales.

## Intentions et tools attendus

### 1) `calendrier_matchs`
- **Entités attendues** : `date` (YYYY-MM-DD), `league_id` ou `league` (nom à mapper), `season`, `status` (NS/FT/LIVE), éventuellement `team` si demande ciblée.
- **Tools** : `fixtures_by_date` (date + league_id/season), ou `team_next_fixtures` si la requête vise le calendrier futur d’une équipe.

### 2) `live_scores`
- **Entités attendues** : aucune obligatoire ; optionnel `league` ou `team` pour filtrer.
- **Tools** : `live_fixtures`.

### 3) `prochain_match_equipe`
- **Entités attendues** : `teams` (nom(s) à résoudre), `count` (par défaut 1).
- **Tools** : `search_team` → `team_next_fixtures` (avec l’ID résolu et count).

### 4) `analyse_rencontre`
- **Entités attendues** : `fixture_id` si connu ; sinon `teams` (2 équipes), `league`, `season`, éventuellement `date`.
- **Tools** : typiquement enchaînement `head_to_head`, `predictions`, `odds_by_fixture`, et selon besoin `fixtures_by_date` ou `team_next_fixtures` pour identifier le match.

### 5) `head_to_head`
- **Entités attendues** : `team1_id`, `team2_id` ou `teams` (noms à résoudre), `last` (nb de matchs).
- **Tools** : `head_to_head`.

### 6) `classement_ligue`
- **Entités attendues** : `league` ou `league_id`, `season`.
- **Tools** : `standings`.

### 7) `stats_equipe_saison`
- **Entités attendues** : `team_id` ou `team` (nom), `league_id` ou `league`, `season`.
- **Tools** : `team_statistics`.

### 8) `stats_joueur`
- **Entités attendues** : `player` (nom), `season` (optionnel), `team` (optionnel pour désambiguer).
- **Tools** : `search_player` (débute la chaîne) ; possibilité d’étendre plus tard avec des stats de match (non implémenté pour l’instant).

### 9) `top_performers`
- **Entités attendues** : `league` ou `league_id`, `season`, et le type (buteurs ou passes). Si non précisé, default buteurs.
- **Tools** : `top_scorers` ou `top_assists` selon la demande.

### 10) `blessures`
- **Entités attendues** : `team` ou `team_id`, `league`/`league_id`, `season` (optionnels).
- **Tools** : `injuries`.

### 11) `predictions`
- **Entités attendues** : `fixture_id` (ou `teams` + contexte pour identifier le match).
- **Tools** : `predictions`.

### 12) `cotes`
- **Entités attendues** : soit `date` + `league_id`/`league`, soit `fixture_id`.
- **Tools** : `odds_by_date` ou `odds_by_fixture`.

### 13) `info_generale`
- **Entités attendues** : aucune obligatoire.
- **Tools** : aucun (réponse discursive sans données).

## Intentions supplementaires (API-Football) a outiller
- `referentiel_pays` : entites `name|code|search`; tool cible `countries`.
- `referentiel_ligues` / `info_ligue` : entites `id|name|country|code|type|season|current|team|search|last`; tool `leagues`.
- `saisons_disponibles` : pas d'entite; tool `leagues/seasons`.
- `timezones_disponibles` : pas d'entite; tool `timezone`.
- `statuts_match` : pas de tool (repondre depuis tableau doc `match_status.txt`).
- `calendrier_ligue_saison` : entites `league|league_id`, `season`, `from/to`, `round`, `status`, `timezone`; tool `fixtures?league&season`.
- `calendrier_equipe` : entites `team`, `season`, `from/to`, `status`, `timezone`; tool `fixtures?team` ou extension `team_next_fixtures`.
- `matchs_live_filtre` : entites optionnelles `league(s)` ou `team`; tool `fixtures?live` (etendre `live_fixtures` pour filtrer).
- `prochains_ou_derniers_matchs` : entites `count`, filtres `league|team|status`; tool `fixtures?next|last`.
- `detail_fixture` : entite `fixture_id`; tool `fixtures?id`.
- `chronologie_match` : entites `fixture_id`, filtres `team|player|type`; tool `fixtures/events`.
- `compositions_match` : entites `fixture_id`, filtres `team|player|type`; tool `fixtures/lineups`.
- `stats_equipes_match` : entites `fixture_id`, `team`, `half`; tool `fixtures/statistics`.
- `stats_joueurs_match` : entites `fixture_id`, `team`; tool `fixtures/players`.
- `journees_competition` : entites `league`, `season`, `dates`; tool `fixtures/rounds`.
- `head_to_head_avance` : entites `team1`, `team2`, `league|season`, `date` ou `from/to`, `status`, `next|last`, `timezone`; tool `fixtures/headtohead` (etendre).
- `info_equipe` : entites `team_id` ou `name`, `league|season`, `country|code|venue`, `search`; tool `teams`.
- `saisons_equipe` : entite `team_id`; tool `teams/seasons`.
- `effectif_equipe` / `equipes_dun_joueur` : entites `team` ou `player`; tool `players/squads`.
- `profil_joueur` : entites `player_id` ou `search`; tool `players/profiles`.
- `stats_joueur_saison_detail` : entites `player_id` ou `search`, `season`, option `team|league`; tool `players`.
- `saisons_joueur` : entite `player_id`; tool `players/seasons`.
- `parcours_equipes_joueur` : entite `player_id`; tool `players/teams`.
- `top_cartons_jaunes` : entites `league|league_id`, `season`; tool `players/topyellowcards`.
- `top_cartons_rouges` : entites `league|league_id`, `season`; tool `players/topredcards`.
- `blessures_precises` : entites `fixture|league|season|team|player|date`; tool `injuries` (etendre args fixture/player/date).
- `indisponibilites_historiques` : entites `player(s)` ou `coach(s)`; tool `sidelined`.
- `transferts` : entites `player` ou `team`; tool `transfers`.
- `palmares` : entites `player` ou `coach`; tool `trophies`.
- `coach_info` : entites `coach_id`, `team`, `search`; tool `coachs`.
- `stade_info` : entites `venue_id`, `name`, `city`, `country`, `search`; tool `venues`.

## Notes de mise en œuvre
- Désambiguïsation d’équipe/joueur : toujours passer par `search_team`/`search_player` avant d’appeler un tool nécessitant un ID.
- Plans gratuits : certaines saisons ou endpoints peuvent être limités ; prévoir des messages clairs quand les données ne sont pas disponibles.
- JSON strict : l’agent d’intention doit toujours renvoyer un JSON valide (`intent`, `needs_data`, `entities`, `confidence`, `reasoning`), même en fallback.
