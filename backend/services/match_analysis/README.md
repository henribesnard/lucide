# Service d'Analyse de Match - Détection d'Assets Cachés

Service indépendant pour analyser un match et détecter des "assets cachés" (patterns rares et différenciants) basé sur l'algorithme décrit dans `documentation/ALGORITHME_ANALYSE_MATCH_API_FOOTBALL.md`.

## Vue d'ensemble

Le service implémente un algorithme en 7 étapes :

1. **Étape 0** : Normaliser les identifiants (league, teams, venue, etc.)
2. **Étape 1** : Définir le périmètre de données (saisons à analyser)
3. **Étape 2** : Collecter les données (fixtures, statistics, H2H)
4. **Étape 3** : Construire les features (équipe, contexte, H2H)
5. **Étape 4** : Générer des patterns candidats
6. **Étape 5-6** : Scorer et sélectionner les assets cachés
7. **Étape 7** : Formater les insights

## Architecture

```
services/match_analysis/
├── __init__.py              # Point d'entrée du module
├── types.py                 # Modèles Pydantic (Input, Output, Features, Patterns)
├── data_collector.py        # Étapes 0-2 (normalisation + collecte)
├── feature_builder.py       # Étape 3 (construction des features)
├── pattern_analyzer.py      # Étapes 4-6 (génération + scoring + filtrage)
├── insight_formatter.py     # Étape 7 (formatage des insights)
├── service.py               # Service orchestrateur principal
├── router.py                # Router FastAPI
└── README.md                # Cette documentation
```

## Utilisation

### Via API REST

#### 1. Analyse complète (3 saisons par défaut)

```bash
POST /match-analysis/analyze
Content-Type: application/json

{
  "league": "Premier League",
  "league_type": "league",
  "round": "Regular Season - 10",
  "stadium": "Old Trafford",
  "referee": "Michael Oliver",
  "team_a": "Manchester United",
  "team_b": "Liverpool",
  "season": 2023,
  "num_seasons_history": 3
}
```

#### 2. Analyse rapide (1 saison uniquement)

```bash
POST /match-analysis/analyze/quick
Content-Type: application/json

{
  "league": "39",
  "league_type": "league",
  "team_a": "33",
  "team_b": "34"
}
```

#### 3. Vérifier le statut du service

```bash
GET /match-analysis/health
```

#### 4. Statistiques du service

```bash
GET /match-analysis/stats
```

### Via Python (utilisation directe)

```python
from backend.api.football_api import FootballAPIClient
from backend.services.match_analysis import MatchAnalysisService, MatchAnalysisInput
from backend.config import settings

# Créer le client API
api_client = FootballAPIClient(
    api_key=settings.FOOTBALL_API_KEY,
    base_url=settings.FOOTBALL_API_BASE_URL,
)

# Créer le service
service = MatchAnalysisService(api_client)

# Préparer l'input
input_data = MatchAnalysisInput(
    league="Premier League",
    league_type="league",
    round="Regular Season - 10",
    team_a="Manchester United",
    team_b="Liverpool",
    season=2023,
    num_seasons_history=3,
)

# Exécuter l'analyse
result = await service.analyze_match(input_data)

# Accéder aux insights
for asset in result.hidden_assets:
    print(f"[{asset.confidence_level}] {asset.insight_text}")
```

## Structure des données

### Input (MatchAnalysisInput)

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `league` | str | Oui | Nom ou ID de la league |
| `league_type` | "league" \| "cup" | Oui | Type de compétition |
| `round` | str | Non | Round (ex: "Group Stage - 2") |
| `stadium` | str | Non | Nom du stade |
| `referee` | str | Non | Nom de l'arbitre |
| `team_a` | str | Oui | Nom ou ID de l'équipe A |
| `team_b` | str | Oui | Nom ou ID de l'équipe B |
| `coach_team_a` | str | Non | Coach de l'équipe A |
| `coach_team_b` | str | Non | Coach de l'équipe B |
| `season` | int | Non | Saison (ex: 2023) |
| `num_seasons_history` | int | Non | Nombre de saisons à analyser (défaut: 3) |

### Output (MatchAnalysisResult)

```python
{
  "input": MatchAnalysisInput,                    # Input original
  "normalized_ids": NormalizedIDs,                # IDs normalisés
  "features": FeatureSet,                         # Features extraites
  "all_patterns": List[Pattern],                  # Tous les patterns générés
  "hidden_assets": List[HiddenAsset],             # Assets cachés sélectionnés
  "analysis_timestamp": datetime,                 # Timestamp de l'analyse
  "total_api_calls": int,                         # Nombre d'appels API
  "processing_time_seconds": float,               # Temps de traitement
  "warnings": List[str]                           # Avertissements
}
```

### HiddenAsset (insight final)

```python
{
  "pattern": Pattern,                             # Pattern détecté
  "insight_text": str,                            # Description textuelle
  "confidence_level": "low" | "medium" | "high",  # Niveau de confiance
  "category": "rare" | "strong" | "differential", # Catégorie
  "metadata": Dict[str, Any]                      # Métadonnées
}
```

## Exemples d'insights générés

```
[high] Manchester United n'a jamais gagné en Group Stage - 2 sur les 5 dernières éditions (0V-2N-3D), alors que son taux de victoire global est 54%.

[high] Liverpool gagne 90% des matchs quand joueurs Salah et Mané sont titulaires (9/10), contre 48% sans ce duo.

[medium] Manchester United en formation 4-3-3 gagne 85% de ses matchs (17/20), contre seulement 40% en 3-5-2 (2/5).

[medium] Liverpool marque 78% de ses buts en 2nde mi-temps cette saison (35/45 buts), contre 22% en 1ère mi-temps.

[high] Manchester United est actuellement sur une série de 5 victoires consécutives, sa meilleure série depuis 3 saisons.
```

## Configuration

Le service utilise les paramètres suivants (configurables dans `service.py`) :

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `min_sample_size` | 6 | Taille minimale d'échantillon pour un pattern |
| `min_delta_baseline` | 20.0 | Écart minimal vs baseline (en pts %) |
| `extreme_threshold` | 95.0 | Seuil pour patterns extrêmes (0% ou 100%) |
| `strong_threshold` | 80.0 | Seuil pour patterns forts (>= 80%) |

## Performance

- **API calls** : ~10-30 appels API-Football par analyse (selon couverture)
- **Temps de traitement** : 5-15 secondes (selon nombre de saisons)
- **Cache Redis** : Activé par défaut pour réduire les appels API

## Limitations actuelles

1. **Formations tactiques** : Calcul approximatif (nécessite données détaillées par match)
2. **Stats arbitre** : Non implémenté (nécessite agrégation globale)
3. **Stats coach** : Non implémenté (nécessite historique complet)
4. **Lineups / joueurs** : Non implémenté (nécessite coverage.lineups=true)
5. **Stats par mi-temps** : Partiellement implémenté (nécessite half=true)

## Évolutions futures

- [ ] Implémenter l'analyse des lineups (synergies joueurs)
- [ ] Ajouter les stats par mi-temps (via half=true)
- [ ] Implémenter l'agrégation des stats arbitres
- [ ] Ajouter l'analyse des transferts et leur impact
- [ ] Intégrer les predictions API comme baseline
- [ ] Ajouter le support des venues (surface, capacité)
- [ ] Implémenter le scoring par récence (pondération temporelle)

## Tests

```bash
# Tester l'endpoint health
curl http://localhost:8001/match-analysis/health

# Tester une analyse rapide
curl -X POST http://localhost:8001/match-analysis/analyze/quick \
  -H "Content-Type: application/json" \
  -d '{
    "league": "39",
    "league_type": "league",
    "team_a": "33",
    "team_b": "34"
  }'
```

## Dépendances

- `FastAPI` : Framework web
- `Pydantic` : Validation des données
- `backend.api.football_api` : Client API-Football
- `backend.config` : Configuration de l'application

## Auteur

Service développé selon l'algorithme documenté dans `documentation/ALGORITHME_ANALYSE_MATCH_API_FOOTBALL.md`.
