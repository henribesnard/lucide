# Guide d'Utilisation - Algorithme d'Analyse de Matchs

## Vue d'Ensemble

L'algorithme d'analyse de matchs détecte automatiquement des **insights cachés** (hidden assets) à partir des données historiques des équipes. Il utilise des analyses statistiques avancées (pandas/scipy/numpy) pour identifier des patterns significatifs dans les performances, les événements, les compositions et les confrontations directes.

### Capacités de l'Algorithme

- **39 types de patterns détectés** (premier but décisif, domination H2H, faiblesses de phase, impact joueurs, etc.)
- **Analyse multi-sources** : événements de match, statistiques, compositions, H2H
- **Statistiques de compétition** : analyse spécifique à la compétition en cours (ex: CAN, Ligue des Champions)
- **Insights pondérés** : confiance haute/moyenne, importance calculée
- **Résumé en français** : rapport markdown complet généré automatiquement

---

## Endpoints Disponibles

### 1. `/match-analysis/analyze/extended` ⭐ **RECOMMANDÉ**

**Analyse complète avec algorithme étendu** (toutes compétitions)

#### URL
```
POST http://localhost:8001/match-analysis/analyze/extended
```

#### Paramètres

**Body (JSON)** - Requis:
```json
{
  "league": "Africa Cup of Nations",
  "league_type": "cup",
  "team_a": "Algeria",
  "team_b": "Burkina Faso"
}
```

**Query Parameters** - Optionnels:
- `num_last_matches` (int, défaut: 30) : Nombre de derniers matchs à analyser par équipe

#### Champs du Body

| Champ | Type | Requis | Description | Exemple |
|-------|------|--------|-------------|---------|
| `league` | string | ✅ | Nom ou ID de la ligue | `"Africa Cup of Nations"` ou `"6"` |
| `league_type` | string | ✅ | Type de compétition | `"cup"` ou `"league"` |
| `team_a` | string | ✅ | Nom ou ID de l'équipe A | `"Morocco"` ou `"31"` |
| `team_b` | string | ✅ | Nom ou ID de l'équipe B | `"Mali"` ou `"29"` |
| `season` | int | ❌ | Saison à analyser | `2025` (défaut: saison courante) |
| `round` | string | ❌ | Round du match | `"Group Stage - 2"` |
| `stadium` | string | ❌ | Nom du stade | `"Stade Prince Moulay Hassan"` |
| `referee` | string | ❌ | Nom de l'arbitre | `"John Doe"` |
| `coach_team_a` | string | ❌ | Coach équipe A | `"Djamel Belmadi"` |
| `coach_team_b` | string | ❌ | Coach équipe B | `"Hubert Velud"` |

#### Réponse

**Status**: `200 OK`

**Format**:
```json
{
  "success": true,
  "analysis_type": "extended",
  "match": {
    "league": "Africa Cup of Nations",
    "league_id": 6,
    "season": 2025,
    "team_a": "Algeria",
    "team_a_id": 1538,
    "team_b": "Burkina Faso",
    "team_b_id": 1546
  },
  "statistics": {
    "team_a": {
      "total_matches": 30,
      "wins": 19,
      "win_rate": 63.3,
      "goals_per_match": 2.17,
      "goals_against_per_match": 0.63,
      "clean_sheet_rate": 50.0,
      "competition_specific": {
        "total_matches": 27,
        "wins": 12,
        "win_rate": 44.4,
        "goals_per_match": 1.52,
        "goals_against_per_match": 0.96,
        "clean_sheet_rate": 37.0
      }
    },
    "team_b": {
      "total_matches": 29,
      "wins": 15,
      "win_rate": 51.7,
      "goals_per_match": 1.76,
      "goals_against_per_match": 1.10,
      "clean_sheet_rate": 27.6,
      "competition_specific": {
        "total_matches": 27,
        "wins": 10,
        "win_rate": 37.0,
        "goals_per_match": 1.22,
        "goals_against_per_match": 1.11,
        "clean_sheet_rate": 37.0
      }
    },
    "h2h": {
      "total_matches": 3,
      "team_a_wins": 0,
      "draws": 3,
      "team_a_losses": 0
    },
    "h2h_league": {
      "total_matches": 1,
      "team_a_wins": 0,
      "draws": 1,
      "team_a_losses": 0
    }
  },
  "insights": {
    "total": 5,
    "items": [
      {
        "type": "events",
        "team": "team_b",
        "text": "Burkina Faso gagne 100% quand marque en premier (12/12). Demarrage crucial.",
        "confidence": "high",
        "category": "first_goal",
        "metric_value": 1.0
      },
      {
        "type": "events",
        "team": "team_a",
        "text": "Algeria gagne 80% quand marque en premier (12/15). Demarrage crucial.",
        "confidence": "high",
        "category": "first_goal",
        "metric_value": 0.8
      }
    ],
    "breakdown": {
      "by_type": {
        "events": 4,
        "statistical": 1
      },
      "by_confidence": {
        "high": 2,
        "medium": 3
      },
      "by_category": {
        "first_goal": 2,
        "comeback": 1,
        "defense": 1,
        "discipline": 1
      },
      "by_team": {
        "team_a": 3,
        "team_b": 1,
        "both": 1
      }
    }
  },
  "metadata": {
    "total_api_calls": 165,
    "processing_time_seconds": 23.51,
    "matches_analyzed": {
      "team_a": 30,
      "team_b": 30,
      "h2h": 3
    },
    "data_coverage": {
      "events": 116,
      "stats": 116,
      "lineups": 116
    },
    "timestamp": "2025-12-28T08:37:18.029208"
  },
  "summary": "# Analyse Match : Algeria vs Burkina Faso\n## Africa Cup of Nations 2025\n\n### 📊 Statistiques Globales\n..."
}
```

#### Champs de la Réponse

**`statistics.team_a` / `statistics.team_b`**:
- `total_matches`: Nombre de matchs analysés (toutes compétitions)
- `wins`: Nombre de victoires
- `win_rate`: Taux de victoire (%)
- `goals_per_match`: Moyenne de buts marqués par match
- `goals_against_per_match`: Moyenne de buts encaissés par match
- `clean_sheet_rate`: Pourcentage de matchs sans but encaissé (%)
- `competition_specific`: Mêmes stats mais uniquement pour la compétition en cours (ex: CAN)

**`statistics.h2h`**:
- `total_matches`: Nombre de confrontations directes (toutes compétitions)
- `team_a_wins`: Victoires de l'équipe A
- `draws`: Matchs nuls
- `team_a_losses`: Défaites de l'équipe A (= victoires de l'équipe B)

**`statistics.h2h_league`**:
- Même structure que `h2h` mais uniquement pour la compétition en cours

**`insights.items[]`**:
- `type`: Type d'analyse (`events`, `statistical`, `h2h`, `player_impact`, `phase_performance`)
- `team`: Équipe concernée (`team_a`, `team_b`, ou `both`)
- `text`: Description textuelle de l'insight en français
- `confidence`: Niveau de confiance (`high`, `medium`, `low`)
- `category`: Catégorie de l'insight (`first_goal`, `h2h_dominance`, `comeback`, `defense`, `key_player`, etc.)
- `metric_value`: Valeur métrique (0.0 à 1.0+) pour pondération

**`summary`**:
- Résumé complet en markdown (format français)
- Inclut : statistiques, H2H, insights clés, tendances, conclusion
- Prêt à être affiché ou sauvegardé en fichier `.md`

---

### 2. `/match-analysis/analyze`

**Analyse standard** (multi-saisons, algorithme classique)

#### URL
```
POST http://localhost:8001/match-analysis/analyze
```

#### Paramètres

**Body (JSON)** - Même structure que `/analyze/extended`

**Différences**:
- Analyse sur plusieurs saisons (défaut: 3 saisons)
- Algorithme classique (patterns basiques)
- Moins d'insights détectés
- Pas de stats de compétition spécifiques
- Réponse format `MatchAnalysisResult` (structure différente)

#### Utilisation
```bash
curl -X POST http://localhost:8001/match-analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "league": "Premier League",
    "league_type": "league",
    "team_a": "Manchester City",
    "team_b": "Arsenal",
    "num_seasons_history": 3
  }'
```

---

### 3. `/match-analysis/analyze/quick`

**Analyse rapide** (1 saison uniquement)

#### URL
```
POST http://localhost:8001/match-analysis/analyze/quick
```

#### Paramètres

**Body (JSON)** - Même structure que `/analyze`

**Différences**:
- Analyse sur 1 saison uniquement (plus rapide)
- Moins d'appels API (~50% de réduction)
- Historique limité
- Convient pour les tests ou analyses rapides

---

## Exemples d'Utilisation

### Exemple 1: Analyse CAN (Python)

```python
import requests

API_URL = "http://localhost:8001/match-analysis/analyze/extended"

payload = {
    "league": "Africa Cup of Nations",
    "league_type": "cup",
    "team_a": "Ivory Coast",
    "team_b": "Cameroon",
}

response = requests.post(
    API_URL,
    json=payload,
    params={"num_last_matches": 30},
    timeout=120
)

if response.status_code == 200:
    result = response.json()

    # Statistiques
    stats_a = result["statistics"]["team_a"]
    print(f"Ivory Coast: {stats_a['win_rate']}% victoires ({stats_a['total_matches']} matchs)")

    # Insights
    insights = result["insights"]["items"]
    print(f"\n{len(insights)} insights détectés:")
    for insight in insights[:5]:  # Top 5
        print(f"- [{insight['confidence'].upper()}] {insight['text']}")

    # Sauvegarder le résumé
    with open("analyse_ivory_cameroon.md", "w", encoding="utf-8") as f:
        f.write(result["summary"])

    print("\nRésumé sauvegardé: analyse_ivory_cameroon.md")
else:
    print(f"Erreur: {response.status_code}")
```

### Exemple 2: Analyse Ligue des Champions (cURL)

```bash
curl -X POST "http://localhost:8001/match-analysis/analyze/extended?num_last_matches=30" \
  -H "Content-Type: application/json" \
  -d '{
    "league": "UEFA Champions League",
    "league_type": "cup",
    "team_a": "Real Madrid",
    "team_b": "Manchester City",
    "season": 2024
  }' | jq '.insights.items[] | select(.confidence == "high")'
```

### Exemple 3: Analyse avec Contexte Complet (Python)

```python
import requests
from datetime import datetime

API_URL = "http://localhost:8001/match-analysis/analyze/extended"

# Match complet avec tous les paramètres
payload = {
    "league": "Africa Cup of Nations",
    "league_type": "cup",
    "team_a": "Algeria",
    "team_b": "Burkina Faso",
    "season": 2025,
    "round": "Group Stage - 2",
    "stadium": "Stade Prince Moulay Hassan",
    "coach_team_a": "Djamel Belmadi",
    "coach_team_b": "Hubert Velud"
}

response = requests.post(
    API_URL,
    json=payload,
    params={"num_last_matches": 30},
    timeout=120
)

if response.status_code == 200:
    result = response.json()

    # H2H
    h2h = result["statistics"]["h2h"]
    h2h_league = result["statistics"]["h2h_league"]

    print(f"H2H Global: {h2h['team_a_wins']}V - {h2h['draws']}N - {h2h['team_a_losses']}D")
    print(f"H2H CAN: {h2h_league['team_a_wins']}V - {h2h_league['draws']}N - {h2h_league['team_a_losses']}D")

    # Breakdown
    breakdown = result["insights"]["breakdown"]
    print(f"\nInsights par catégorie:")
    for category, count in breakdown["by_category"].items():
        print(f"  {category}: {count}")

    # Metadata
    metadata = result["metadata"]
    print(f"\nPerformance:")
    print(f"  Appels API: {metadata['total_api_calls']}")
    print(f"  Temps: {metadata['processing_time_seconds']}s")
    print(f"  Couverture: {metadata['data_coverage']['events']} matchs avec données complètes")
```

### Exemple 4: Batch Analysis (Multiple Matches)

```python
import requests
import time

API_URL = "http://localhost:8001/match-analysis/analyze/extended"

matches = [
    {"team_a": "Gabon", "team_b": "Mozambique"},
    {"team_a": "Equatorial Guinea", "team_b": "Sudan"},
    {"team_a": "Algeria", "team_b": "Burkina Faso"},
    {"team_a": "Ivory Coast", "team_b": "Cameroon"}
]

for i, match in enumerate(matches, 1):
    print(f"[{i}/{len(matches)}] Analyse {match['team_a']} vs {match['team_b']}...")

    payload = {
        "league": "Africa Cup of Nations",
        "league_type": "cup",
        **match
    }

    response = requests.post(
        API_URL,
        json=payload,
        params={"num_last_matches": 30},
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()

        # Sauvegarder
        filename = f"can_analysis_{match['team_a']}_vs_{match['team_b']}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result["summary"])

        print(f"  ✓ Sauvegardé: {filename}")
        print(f"  Insights: {result['insights']['total']}")
        print(f"  Temps: {result['metadata']['processing_time_seconds']}s")
    else:
        print(f"  ✗ Erreur: {response.status_code}")

    # Pause entre requêtes (rate limiting)
    if i < len(matches):
        time.sleep(2)
```

---

## Bonnes Pratiques

### 1. Choix du Nombre de Matchs

- **30 matchs** (défaut) : Équilibre optimal entre données historiques et pertinence récente
- **15-20 matchs** : Pour les équipes avec peu d'historique ou analyses très récentes
- **40-50 matchs** : Pour les grandes équipes avec beaucoup d'historique (augmente le temps de traitement)

### 2. Gestion du Rate Limiting

L'API Football a une limite de **300 requêtes par minute**. Chaque analyse consomme environ **120-170 appels API**.

**Recommandations**:
- Espacer les analyses de **2-3 secondes** minimum
- Traiter les erreurs 429 (Too Many Requests) avec un retry après 60s
- Pour des analyses en masse, prévoir des pauses périodiques

```python
import time
from requests.exceptions import HTTPError

def analyze_with_retry(payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                wait_time = 60 * (attempt + 1)
                print(f"Rate limit atteint, attente {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries atteints")
```

### 3. Gestion des Erreurs

**Codes HTTP**:
- `200` : Succès
- `400` : Paramètres invalides (vérifier le payload)
- `404` : Ligue ou équipe non trouvée (vérifier les noms)
- `500` : Erreur serveur (API Football down, rate limit, etc.)

**Validation avant envoi**:
```python
def validate_payload(payload):
    required = ["league", "league_type", "team_a", "team_b"]
    missing = [f for f in required if f not in payload]

    if missing:
        raise ValueError(f"Champs manquants: {', '.join(missing)}")

    if payload["league_type"] not in ["cup", "league"]:
        raise ValueError("league_type doit être 'cup' ou 'league'")

    return True
```

### 4. Optimisation des Performances

**Cache**:
- Les résultats sont mis en cache par Redis (si activé)
- Même requête dans les 15 minutes : réponse instantanée
- Désactiver le cache pour forcer une nouvelle analyse : ajouter `?force_refresh=true`

**Timeout**:
- Timeout recommandé : **120 secondes** (2 minutes)
- Analyses complexes peuvent prendre 15-30s

### 5. Interprétation des Insights

**Niveaux de Confiance**:
- `high` : Pattern très significatif (>85% confiance), échantillon >= 10 matchs
- `medium` : Pattern significatif (>70% confiance), échantillon >= 6 matchs
- `low` : Pattern indicatif (>60% confiance), échantillon >= 3 matchs

**Catégories d'Insights**:
- `first_goal` : Impact du premier but (ex: "gagne 90% quand marque en premier")
- `h2h_dominance` : Domination historique en H2H
- `comeback` : Capacité à renverser des matchs
- `defense` : Solidité défensive (clean sheets)
- `key_player` : Impact d'un joueur clé (+/- 20 points de win rate)
- `discipline` : Impact des cartons précoces
- `phase_dominance` / `phase_weakness` : Performance dans certaines phases de compétition
- `competition_regular_time` : Performance en temps réglementaire vs prolongations

**Utilisation**:
```python
# Filtrer les insights haute confiance
high_conf = [i for i in insights if i["confidence"] == "high"]

# Regrouper par équipe
team_a_insights = [i for i in insights if i["team"] == "team_a"]
team_b_insights = [i for i in insights if i["team"] == "team_b"]

# Top insights (déjà triés par importance)
top_5 = insights[:5]
```

### 6. Format du Résumé Markdown

Le champ `summary` contient un rapport complet en français :

**Structure**:
1. **Header** : Titre, compétition, saison
2. **Statistiques Globales** : Stats des 2 équipes (toutes compétitions)
3. **Statistiques dans [Compétition]** : Stats spécifiques à la compétition (ex: CAN)
4. **Historique H2H** : H2H global + H2H dans la compétition
5. **Insights Clés** : Insights haute confiance, puis moyenne confiance
6. **Tendances et Patterns** : Breakdown des insights par catégorie et type
7. **Analyse Technique** : Métadonnées (API calls, temps, couverture)
8. **Conclusion** : Synthèse automatique

**Sauvegarde**:
```python
# Sauvegarder le résumé
summary = result["summary"]
filename = f"analyse_{team_a}_vs_{team_b}.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(summary)

print(f"Résumé sauvegardé: {filename}")
```

---

## Endpoints Utilitaires

### Health Check
```bash
GET http://localhost:8001/match-analysis/health
```

**Réponse**:
```json
{
  "status": "healthy",
  "service": "match-analysis",
  "version": "1.0.0"
}
```

### Service Stats
```bash
GET http://localhost:8001/match-analysis/stats
```

**Réponse**:
```json
{
  "total_api_calls": 1247,
  "service_name": "MatchAnalysisService",
  "version": "1.0.0"
}
```

---

## Troubleshooting

### Erreur: "API Error: rateLimit"
**Cause**: Limite de 300 req/min dépassée
**Solution**: Attendre 60 secondes avant de réessayer

### Erreur: "League not found"
**Cause**: Nom de ligue incorrect
**Solution**: Utiliser le nom exact ou l'ID (ex: "6" pour CAN)

### Erreur: "Team not found"
**Cause**: Nom d'équipe incorrect
**Solution**: Vérifier l'orthographe exacte (ex: "Ivory Coast" pas "Cote d'Ivoire")

### Timeout après 120s
**Cause**: Analyse très longue (beaucoup de données)
**Solution**: Réduire `num_last_matches` ou augmenter le timeout

### Aucun insight détecté
**Cause**: Pas assez de données historiques
**Solution**: Normal pour de nouvelles équipes ou compétitions

---

## Changelog de l'Algorithme

### Version 1.2 (2025-12-28)
- ✅ **Fix H2H Dominance**: Ne génère plus "domination" quand tous les matchs sont nuls
- ✅ **Fix Phase Insights**: Exclut les phases spécifiques de groupe (group_match_1/2/3) pour éviter insights non pertinents
- ✅ Stats de compétition corrigées (toutes saisons historiques, pas seulement 1)

### Version 1.1
- Ajout H2H dans la compétition (`h2h_league`)
- Format H2H amélioré: "XV - YN - ZD"
- Stats de compétition spécifiques (`competition_specific`)

### Version 1.0
- Algorithme de base avec 39 patterns
- Analyse étendue avec événements, stats, lineups
- Résumé markdown automatique

---

## Support

Pour toute question ou problème:
- **Issues GitHub**: https://github.com/henribesnard/lucide/issues
- **Documentation API**: http://localhost:8001/docs (Swagger UI)
