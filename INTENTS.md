# Intents & Tools (Lucide Backend)

Ce document résume les intentions actuellement gérées par le backend et les entités attendues, ainsi que les tools (function calling) qui doivent être déclenchés. Il sert de référence produit/technique pour étendre le routage.

## Principes généraux
- Modèle : `deepseek-chat` avec `response_format: {"type": "json_object"}` pour l’extraction d’intentions/entités.
- Tools disponibles : `search_team`, `search_player`, `fixtures_by_date`, `team_next_fixtures`, `live_fixtures`, `standings`, `team_statistics`, `head_to_head`, `top_scorers`, `top_assists`, `injuries`, `predictions`, `odds_by_date`, `odds_by_fixture`.
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

## Notes de mise en œuvre
- Désambiguïsation d’équipe/joueur : toujours passer par `search_team`/`search_player` avant d’appeler un tool nécessitant un ID.
- Plans gratuits : certaines saisons ou endpoints peuvent être limités ; prévoir des messages clairs quand les données ne sont pas disponibles.
- JSON strict : l’agent d’intention doit toujours renvoyer un JSON valide (`intent`, `needs_data`, `entities`, `confidence`, `reasoning`), même en fallback.
