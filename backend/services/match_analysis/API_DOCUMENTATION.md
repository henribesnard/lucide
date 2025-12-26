# API Match Analysis - Documentation

## Vue d'ensemble

L'API Match Analysis fournit 3 endpoints pour analyser des matchs de football avec différents niveaux de profondeur.

**Base URL**: `http://localhost:8001/match-analysis`

---

## Endpoints

### 1. Analyse Standard
`POST /match-analysis/analyze`

Analyse complète avec historique multi-saisons (version originale).

**Paramètres**:
```json
{
  "league": "39",           // ID ou nom de la compétition
  "team_a": "Manchester City",  // Équipe A (ID ou nom)
  "team_b": "Arsenal",          // Équipe B (ID ou nom)
  "league_type": "league",      // Type: "league", "cup", etc.
  "num_seasons_history": 3      // Nombre de saisons (optionnel, défaut: 3)
}
```

**Réponse**: Objet `MatchAnalysisResult` (structure complexe)

---

### 2. Analyse Rapide
`POST /match-analysis/analyze/quick`

Version allégée avec 1 saison uniquement (plus rapide).

**Paramètres**: Identiques à l'analyse standard

**Réponse**: Objet `MatchAnalysisResult`

---

### 3. ✨ **Analyse Étendue** (NOUVEAU)
`POST /match-analysis/analyze/extended?num_last_matches=30`

**Analyse complète avec algorithme élargi toutes compétitions.**

#### Caractéristiques

Cette analyse utilise le **nouvel algorithme étendu** avec :

- ✅ **30 derniers matchs par équipe** (toutes compétitions confondues)
- ✅ **Events détaillés** : timeline, buts, cartons, substitutions
- ✅ **Statistiques match par match** : possession, tirs, passes
- ✅ **Lineups complètes** : compositions, remplaçants
- ✅ **Analyses statistiques avancées** : pandas/numpy/scipy
- ✅ **39 types de patterns** : statistiques, événements, joueurs, coaches
- ✅ **Impact joueurs** : présence/absence, synergies
- ✅ **Throttling automatique** : 2s entre batches (évite rate limiting)

#### Paramètres

**Query params**:
- `num_last_matches` (optionnel, défaut: 30) : Nombre de matchs à analyser

**Body**:
```json
{
  "league": "6",           // ID ou nom de la compétition
  "team_a": "Morocco",     // Équipe A (ID ou nom)
  "team_b": "Mali",        // Équipe B (ID ou nom)
  "league_type": "cup"     // Type de compétition
}
```

#### Réponse

**Structure JSON** :

```json
{
  "success": true,
  "analysis_type": "extended",

  "match": {
    "league": "Africa Cup of Nations",
    "league_id": 6,
    "season": 2025,
    "team_a": "Morocco",
    "team_a_id": 31,
    "team_b": "Mali",
    "team_b_id": 1500
  },

  "statistics": {
    "team_a": {
      "total_matches": 29,
      "wins": 26,
      "win_rate": 89.7,
      "goals_per_match": 2.38,
      "goals_against_per_match": 0.52,
      "clean_sheet_rate": 69.0
    },
    "team_b": {
      "total_matches": 30,
      "wins": 15,
      "win_rate": 50.0,
      "goals_per_match": 1.57,
      "goals_against_per_match": 1.13,
      "clean_sheet_rate": 53.3
    },
    "h2h": {
      "total_matches": 3,
      "team_a_wins": 2
    }
  },

  "insights": {
    "total": 6,
    "items": [
      {
        "type": "events",
        "team": "team_a",
        "text": "Morocco gagne 100% quand marque en premier (23/23). Démarrage crucial.",
        "confidence": "high",
        "category": "first_goal",
        "metric_value": 1.0
      },
      {
        "type": "statistical",
        "team": "team_a",
        "text": "Morocco gagne 90% de ses matchs (26/29). Excellente forme.",
        "confidence": "high",
        "category": "form",
        "metric_value": 0.897
      }
      // ... 18 autres insights
    ],
    "breakdown": {
      "by_type": {
        "events": 3,
        "statistical": 3
      },
      "by_confidence": {
        "high": 3,
        "medium": 3
      },
      "by_category": {
        "first_goal": 2,
        "defense": 2,
        "form": 1,
        "comeback": 1
      },
      "by_team": {
        "team_a": 4,
        "team_b": 2
      }
    }
  },

  "metadata": {
    "total_api_calls": 89,
    "processing_time_seconds": 18.43,
    "matches_analyzed": {
      "team_a": 30,
      "team_b": 30,
      "h2h": 3
    },
    "data_coverage": {
      "events": 63,
      "stats": 63,
      "lineups": 63
    },
    "timestamp": "2025-12-26T20:30:00.000000"
  },

  "summary": "# Analyse Match : Morocco vs Mali\n## Africa Cup of Nations 2025\n\n### 📊 Statistiques Globales\n\n**Morocco** (29 matchs analysés)\n- Taux de victoire : **89.7%** (26 victoires)\n...\n\n### ✅ Conclusion\n\nLe **Morocco** part largement favori...\n\n*Analyse générée par le système étendu avec algorithme complet (pandas/scipy/numpy) - 5 insights détectés sur 39 patterns possibles*"
}
```

**Note**: Le champ `summary` contient un résumé complet de l'analyse en format Markdown (français), incluant:
- Statistiques globales des deux équipes
- Historique H2H
- Insights clés classés par confiance
- Tendances et patterns
- Analyse technique
- Conclusion avec détermination du favori

---

## Exemples d'utilisation

### cURL

```bash
curl -X POST "http://localhost:8001/match-analysis/analyze/extended?num_last_matches=30" \
  -H "Content-Type: application/json" \
  -d '{
    "league": "6",
    "team_a": "Morocco",
    "team_b": "Mali",
    "league_type": "cup"
  }'
```

### Python (requests)

```python
import requests

response = requests.post(
    "http://localhost:8001/match-analysis/analyze/extended",
    json={
        "league": "6",
        "team_a": "Morocco",
        "team_b": "Mali",
        "league_type": "cup"
    },
    params={"num_last_matches": 30}
)

data = response.json()

# Afficher les insights
print(f"Total insights: {data['insights']['total']}")
for insight in data['insights']['items']:
    print(f"[{insight['confidence']}] {insight['text']}")

# Afficher le résumé formaté
print("\n" + "="*80)
print(data['summary'])  # Résumé complet en français (Markdown)
```

### JavaScript (fetch)

```javascript
fetch('http://localhost:8001/match-analysis/analyze/extended?num_last_matches=30', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    league: '6',
    team_a: 'Morocco',
    team_b: 'Mali',
    league_type: 'cup'
  })
})
.then(res => res.json())
.then(data => {
  console.log(`Total insights: ${data.insights.total}`);
  data.insights.items.forEach(insight => {
    console.log(`[${insight.confidence}] ${insight.text}`);
  });
});
```

---

## Types d'Insights Détectés

### Statistiques (statistical)
- **Form** : Forme générale (win rate global)
- **Defense** : Clean sheets, solidité défensive
- **Attack** : Efficacité offensive
- **Key Factor** : Corrélations statistiques (possession, tirs, etc.)

### Événements (events)
- **First Goal** : Impact du premier but
- **Comeback** : Capacité de renversement
- **Discipline** : Impact des cartons précoces
- **Timing** : Périodes dangereuses (heatmap des buts)

### Joueurs (player_impact, player_synergy)
- **Key Player** : Impact présence/absence joueur clé
- **Player Negative** : Joueurs pénalisants
- **Synergy** : Synergies duos/trios
- **Availability** : Blessures/suspensions

### H2H (h2h)
- **H2H Dominance** : Domination historique
- **H2H Patterns** : Tendances confrontations directes

---

## Temps d'Exécution

| Périmètre | Appels API | Temps (avec throttling) | Insights |
|-----------|-----------|------------------------|----------|
| 10 matchs | ~70 | ~8-10s | 5-10 |
| 15 matchs | ~100 | ~12-15s | 8-15 |
| 30 matchs | ~191 | ~18-20s | 15-30 |

**Note**: Le throttling automatique (2s entre batches) évite les erreurs de rate limiting mais ralentit l'analyse. Sans throttling, l'analyse prend 3-5s mais génère beaucoup d'erreurs API.

---

## Codes d'Erreur

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Paramètres invalides | Vérifier le format des données |
| 404 | League/Team non trouvée | Vérifier les IDs/noms |
| 500 | Erreur serveur | Consulter les logs backend |
| 503 | Rate limiting API | Attendre 60s ou réduire num_last_matches |

---

## Monitoring

### Endpoint Health
```bash
GET /match-analysis/health
```

**Réponse**:
```json
{
  "status": "healthy",
  "service": "match-analysis",
  "version": "1.0.0"
}
```

### Stats du Service
```bash
GET /match-analysis/stats
```

**Réponse**:
```json
{
  "total_api_calls": 189,
  "service_name": "MatchAnalysisService",
  "version": "1.0.0"
}
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     API ENDPOINT                            │
│              /match-analysis/analyze/extended              │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│              MatchAnalysisService                           │
│              ├─ DataCollector (avec throttling)            │
│              ├─ FeatureBuilderV2                           │
│              └─ PatternGenerator                           │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│                  ANALYSEURS SPÉCIALISÉS                     │
│    ├─ StatisticalAnalyzer (pandas/scipy)                  │
│    ├─ EventsAnalyzer (timeline, patterns)                 │
│    ├─ PlayerAnalyzer (impact, synergies)                  │
│    └─ CoachAnalyzer (confrontations)                      │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│                   API-FOOTBALL v3                           │
│    Endpoints: fixtures, events, statistics, lineups        │
└────────────────────────────────────────────────────────────┘
```

---

## Changelog

### Version 2.0.0 (2025-12-26)
- ✨ Nouveau endpoint `/analyze/extended`
- ✨ Algorithme élargi toutes compétitions
- ✨ 39 types de patterns (vs 6-7 avant)
- ✨ Analyses pandas/numpy/scipy
- ✨ Impact joueurs et synergies
- ✨ Throttling automatique (évite rate limiting)
- ✨ Résolution intelligente équipes (similarité)
- ✨ **Résumé automatique en français** : Champ `summary` en format Markdown avec conclusion
- 🐛 Fix: Gestion matchs sans scores (null)

### Version 1.0.0 (2025-11-23)
- ✅ Endpoints `/analyze` et `/analyze/quick`
- ✅ Analyse multi-saisons
- ✅ Patterns basiques (6-7 types)

---

## Support

Pour toute question ou problème :
- **Issues**: Créer une issue GitHub
- **Logs**: Consulter les logs backend (`backend.log`)
- **Documentation complète**: `backend/services/match_analysis/README.md`
