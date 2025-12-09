# Améliorations Lucide - Système de Contexte Dynamique

## Vue d'ensemble

Ce document détaille les améliorations majeures du système Lucide pour introduire un **système de contexte dynamique** qui adapte les appels API en fonction du statut du match et de l'intention de l'utilisateur.

---

## 1. Types de Contexte

### 1.1 Contexte Match

Un match peut avoir trois statuts temporels :

#### **Match du jour - EN COURS** (`LIVE`)
- **Statuts API-Football** : `1H`, `HT`, `2H`, `ET`, `BT`, `P`, `SUSP`, `INT`, `LIVE`
- **Endpoints disponibles** :
  - `fixtures/{id}` - Informations temps réel (score, temps de jeu)
  - `fixtures/statistics` - Statistiques du match en cours
  - `fixtures/events` - Événements (buts, cartons, remplacements)
  - `fixtures/lineups` - Compositions d'équipes
  - `players/fixtures` - Statistiques joueurs en temps réel

#### **Match du jour - TERMINÉ** (`FINISHED`)
- **Statuts API-Football** : `FT`, `AET`, `PEN`, `AWD`, `WO`
- **Endpoints disponibles** :
  - `fixtures/{id}` - Résultat final
  - `fixtures/statistics` - Statistiques complètes du match
  - `fixtures/events` - Tous les événements du match
  - `fixtures/lineups` - Compositions utilisées
  - `players/fixtures` - Statistiques joueurs finales

#### **Match À VENIR** (`UPCOMING`)
- **Statuts API-Football** : `TBD`, `NS`, `CANC`, `PST`, `ABD`
- **Endpoints par type d'analyse** :

**Analyse globale (prédiction)** :
  - `predictions` - Analyse complète avec pronostic

**Analyses spécifiques (max 2-3 endpoints)** :
  - Forme des équipes : `fixtures?team={id}&last=5` + `standings`
  - Confrontations : `fixtures/headtohead` + `fixtures?team={id}&last=3`
  - Statistiques : `teams/statistics` + `standings`
  - Blessures : `injuries?team={id}` + `fixtures?team={id}&last=3`
  - Compositions probables : `fixtures/lineups` (matchs précédents) + `injuries`

### 1.2 Contexte Ligue

Une ligue peut avoir trois états temporels :

#### **Ligue PASSÉE**
- **Exemple** : Ligue 1 2023-2024 (saison terminée)
- **Endpoints disponibles** :
  - `standings?league={id}&season={year}` - Classement final
  - `fixtures?league={id}&season={year}` - Tous les matchs de la saison
  - `teams/statistics?league={id}&season={year}` - Stats par équipe
  - `players/topscorers?league={id}&season={year}` - Meilleurs buteurs
  - `players/topassists?league={id}&season={year}` - Meilleurs passeurs

#### **Ligue EN COURS**
- **Exemple** : Ligue 1 2024-2025 (saison en cours)
- **Endpoints disponibles** :
  - `standings?league={id}&season={year}` - Classement actuel
  - `fixtures?league={id}&season={year}&next={n}` - Prochains matchs
  - `fixtures?league={id}&season={year}&last={n}` - Derniers matchs
  - `teams/statistics?league={id}&season={year}` - Stats actuelles
  - `players/topscorers?league={id}&season={year}` - Classement buteurs
  - `players/topassists?league={id}&season={year}` - Classement passeurs

#### **Ligue À VENIR**
- **Exemple** : Ligue 1 2025-2026 (pas encore commencée)
- **Endpoints disponibles** :
  - `fixtures?league={id}&season={year}` - Calendrier (si disponible)
  - `teams?league={id}&season={year}` - Équipes participantes

---

## 2. Classification des Intentions Utilisateur

### 2.1 Intentions pour Match EN COURS

| Intention | Description | Endpoints requis |
|-----------|-------------|------------------|
| `score_live` | Connaître le score actuel | `fixtures/{id}` |
| `stats_live` | Statistiques en temps réel | `fixtures/{id}` + `fixtures/statistics` |
| `events_live` | Événements du match | `fixtures/{id}` + `fixtures/events` |
| `players_live` | Performance des joueurs | `fixtures/{id}` + `players/fixtures` |
| `lineups_live` | Compositions et changements | `fixtures/lineups` |

### 2.2 Intentions pour Match TERMINÉ

| Intention | Description | Endpoints requis |
|-----------|-------------|------------------|
| `result_final` | Résultat final | `fixtures/{id}` |
| `stats_final` | Statistiques complètes | `fixtures/statistics` |
| `events_summary` | Résumé des événements | `fixtures/events` |
| `players_performance` | Performance des joueurs | `players/fixtures` |
| `match_analysis` | Analyse complète | `fixtures/{id}` + `fixtures/statistics` + `fixtures/events` |

### 2.3 Intentions pour Match À VENIR

| Intention | Description | Endpoints requis (max 3) |
|-----------|-------------|--------------------------|
| `prediction_global` | Pronostic complet | `predictions` |
| `form_analysis` | Analyse de forme | `fixtures?team={id}&last=5` + `standings` |
| `h2h_analysis` | Confrontations directes | `fixtures/headtohead` + `fixtures?team={id}&last=3` |
| `stats_comparison` | Comparaison statistique | `teams/statistics` + `standings` |
| `injuries_impact` | Impact des blessures | `injuries?team={id}` + `fixtures?team={id}&last=3` |
| `probable_lineups` | Compositions probables | `fixtures/lineups` (historique) + `injuries` |

### 2.4 Intentions pour Ligue

| Intention | Description | Endpoints requis |
|-----------|-------------|------------------|
| `standings` | Classement | `standings` |
| `top_scorers` | Meilleurs buteurs | `players/topscorers` |
| `top_assists` | Meilleurs passeurs | `players/topassists` |
| `team_stats` | Stats d'une équipe | `teams/statistics` |
| `next_fixtures` | Prochains matchs | `fixtures?league={id}&next={n}` |
| `results` | Derniers résultats | `fixtures?league={id}&last={n}` |

---

## 3. Système de Contexte Enrichi (Context Augmentation)

### 3.1 Principe

Chaque match/ligue a un **contexte global** qui s'enrichit avec les questions des utilisateurs :

1. **Première question** sur un match → Contexte initial créé avec données API
2. **Questions suivantes** (même match, autres utilisateurs) → Contexte enrichi avec nouvelles données
3. **Limite de contexte** → Quand le contexte global atteint sa limite, on garde les informations les plus pertinentes

### 3.2 Structure du Contexte

```json
{
  "context_id": "match_12345_2025-12-08",
  "context_type": "match",
  "status": "live",
  "entity": {
    "fixture_id": 12345,
    "home_team": "France",
    "away_team": "England",
    "date": "2025-12-08T20:00:00Z"
  },
  "data_collected": {
    "fixtures": { /* données fixture */ },
    "statistics": { /* données stats */ },
    "events": [ /* événements */ ],
    "lineups": { /* compositions */ }
  },
  "user_questions": [
    {
      "user_id": "user_1",
      "question": "Quel est le score ?",
      "timestamp": "2025-12-08T20:15:00Z",
      "intent": "score_live",
      "endpoints_called": ["fixtures/12345"]
    },
    {
      "user_id": "user_2",
      "question": "Qui a marqué ?",
      "timestamp": "2025-12-08T20:20:00Z",
      "intent": "events_live",
      "endpoints_called": ["fixtures/events"]
    }
  ],
  "context_size": 4520,
  "max_context_size": 10000,
  "created_at": "2025-12-08T20:15:00Z",
  "updated_at": "2025-12-08T20:20:00Z"
}
```

### 3.3 Stratégie de Stockage

- **Redis** : Contexte en cours (TTL = durée du match + 2h)
- **PostgreSQL** : Contexte archivé pour analyse et apprentissage

---

## 4. Architecture Backend

### 4.1 Nouveau module `backend/context/`

```
backend/context/
├── __init__.py
├── context_manager.py      # Gestion du contexte global
├── context_types.py         # Définitions des types de contexte
├── status_classifier.py     # Classification du statut (live/finished/upcoming)
├── intent_classifier.py     # Classification de l'intention utilisateur
└── endpoint_selector.py     # Sélection des endpoints selon statut + intention
```

### 4.2 Modifications des agents

#### `backend/agents/tool_agent.py`

**Avant** :
```python
# Appelle tous les endpoints disponibles
```

**Après** :
```python
# 1. Classifier le statut du match/ligue
status = status_classifier.classify(fixture_data)

# 2. Classifier l'intention utilisateur
intent = intent_classifier.classify(user_question, status)

# 3. Sélectionner les endpoints nécessaires
endpoints = endpoint_selector.select(status, intent)

# 4. Vérifier le contexte existant
context = context_manager.get_or_create(context_id)

# 5. Appeler uniquement les endpoints manquants
for endpoint in endpoints:
    if not context.has_data(endpoint):
        data = await api_call(endpoint)
        context.add_data(endpoint, data)

# 6. Sauvegarder le contexte enrichi
context_manager.save(context)
```

#### `backend/agents/pipeline.py`

**Ajout** : Récupération du contexte avant l'analyse

```python
# Récupérer le contexte enrichi
context = await context_manager.get_context(context_id)

# Passer le contexte complet à l'analysis_agent
analysis = await analysis_agent.analyze(
    user_question=question,
    context_data=context.data_collected,
    previous_questions=context.user_questions[-5:]  # 5 dernières questions
)
```

---

## 5. Frontend - Affichage du Contexte

### 5.1 Composant `ContextHeader.tsx`

Affiche le contexte en haut de la conversation :

```tsx
<div className="context-header">
  {/* Match context */}
  {contextType === 'match' && (
    <div className="flex items-center gap-3 p-4 bg-teal-50 border-b">
      <div className="flex items-center gap-2">
        <img src={homeTeamLogo} className="w-8 h-8" />
        <span className="font-semibold">{homeTeamName}</span>
      </div>

      {status === 'live' && (
        <div className="px-3 py-1 bg-red-500 text-white rounded-full text-sm animate-pulse">
          EN DIRECT
        </div>
      )}

      <div className="text-2xl font-bold">{score}</div>

      <div className="flex items-center gap-2">
        <span className="font-semibold">{awayTeamName}</span>
        <img src={awayTeamLogo} className="w-8 h-8" />
      </div>

      <div className="ml-auto text-sm text-gray-600">
        {status === 'live' ? `${elapsed}'` : formatDate(date)}
      </div>
    </div>
  )}

  {/* League context */}
  {contextType === 'league' && (
    <div className="flex items-center gap-3 p-4 bg-teal-50 border-b">
      <img src={leagueLogo} className="w-10 h-10" />
      <div>
        <div className="font-semibold">{leagueName}</div>
        <div className="text-sm text-gray-600">Saison {season}</div>
      </div>
    </div>
  )}
</div>
```

### 5.2 Modifications `ChatBubble.tsx`

```typescript
// Ajouter un état pour le contexte
const [context, setContext] = useState<Context | null>(null);

// Récupérer le contexte lors de la sélection d'un match
const handleMatchSelect = async (match: Match) => {
  setSelectedMatch(match);

  // Récupérer ou créer le contexte
  const ctx = await fetch(`${API_URL}/api/context/match/${match.fixture.id}`);
  setContext(await ctx.json());
};

// Afficher le ContextHeader
return (
  <div className="chat-container">
    {context && <ContextHeader context={context} />}
    {/* ... reste du chat */}
  </div>
);
```

---

## 6. Nouveaux Endpoints API

### 6.1 Gestion du Contexte

```python
@app.get("/api/context/match/{fixture_id}")
async def get_match_context(fixture_id: int):
    """Récupère ou crée le contexte d'un match."""
    return await context_manager.get_or_create_match_context(fixture_id)

@app.get("/api/context/league/{league_id}")
async def get_league_context(league_id: int, season: int):
    """Récupère ou crée le contexte d'une ligue."""
    return await context_manager.get_or_create_league_context(league_id, season)

@app.post("/api/context/{context_id}/enrich")
async def enrich_context(context_id: str, question: str, intent: str, data: dict):
    """Enrichit le contexte avec une nouvelle question et ses données."""
    return await context_manager.enrich_context(context_id, question, intent, data)
```

---

## 7. Plan d'Implémentation

### Phase 1 : Classification et Sélection (Priorité HAUTE)
- [ ] Créer `backend/context/status_classifier.py`
- [ ] Créer `backend/context/intent_classifier.py`
- [ ] Créer `backend/context/endpoint_selector.py`
- [ ] Mapper les statuts API-Football (FT, LIVE, NS, etc.)
- [ ] Définir les règles de sélection d'endpoints par (statut × intention)

### Phase 2 : Gestion du Contexte (Priorité HAUTE)
- [ ] Créer `backend/context/context_manager.py`
- [ ] Créer `backend/context/context_types.py`
- [ ] Implémenter le stockage Redis pour contextes actifs
- [ ] Implémenter la persistance PostgreSQL pour l'archivage
- [ ] Ajouter les endpoints API `/api/context/*`

### Phase 3 : Intégration Agents (Priorité HAUTE)
- [ ] Modifier `tool_agent.py` pour utiliser le système de contexte
- [ ] Modifier `pipeline.py` pour enrichir le contexte
- [ ] Modifier `analysis_agent.py` pour utiliser le contexte enrichi
- [ ] Ajouter logging pour tracer les décisions de sélection d'endpoints

### Phase 4 : Frontend (Priorité MOYENNE)
- [ ] Créer `frontend/src/components/ContextHeader.tsx`
- [ ] Modifier `ChatBubble.tsx` pour afficher le contexte
- [ ] Ajouter des styles pour différencier les statuts (live/finished/upcoming)
- [ ] Implémenter le rafraîchissement auto pour les matchs en direct

### Phase 5 : Tests et Optimisation (Priorité MOYENNE)
- [ ] Tests unitaires pour les classifiers
- [ ] Tests d'intégration pour le flux complet
- [ ] Vérifier les performances avec Redis
- [ ] Optimiser la taille du contexte (compression si nécessaire)

---

## 8. Exemples de Scénarios

### Scénario 1 : Match EN COURS

**Utilisateur 1** (20h15) : "Quel est le score de France - Angleterre ?"
- **Statut** : LIVE (1H, 30')
- **Intention** : `score_live`
- **Endpoints** : `fixtures/12345`
- **Contexte créé** : score, temps de jeu, compositions
- **Réponse** : "France mène 1-0 contre l'Angleterre à la 30ème minute de jeu."

**Utilisateur 2** (20h25) : "Qui a marqué pour la France ?"
- **Statut** : LIVE (1H, 40')
- **Intention** : `events_live`
- **Endpoints** : `fixtures/events` (déjà en contexte : `fixtures/12345`)
- **Contexte enrichi** : + événements (but de Mbappé 25')
- **Réponse** : "Kylian Mbappé a marqué pour la France à la 25ème minute."

**Utilisateur 3** (20h30) : "Combien de tirs cadrés pour chaque équipe ?"
- **Statut** : LIVE (HT)
- **Intention** : `stats_live`
- **Endpoints** : `fixtures/statistics` (déjà en contexte : `fixtures/12345`, `fixtures/events`)
- **Contexte enrichi** : + statistiques complètes
- **Réponse** : "À la mi-temps : France 4 tirs cadrés, Angleterre 2 tirs cadrés."

### Scénario 2 : Match À VENIR

**Utilisateur** : "Analyse le match PSG - Real Madrid de demain"
- **Statut** : UPCOMING (NS)
- **Intention** : `prediction_global`
- **Endpoints** : `predictions` uniquement
- **Réponse** : Analyse complète basée sur l'endpoint predictions

**Utilisateur** : "Quelle est la forme du PSG ?"
- **Statut** : UPCOMING (NS)
- **Intention** : `form_analysis`
- **Endpoints** : `fixtures?team=85&last=5` + `standings`
- **Contexte enrichi** : + forme des équipes + classement
- **Réponse** : "Le PSG est sur une série de 4 victoires consécutives..."

### Scénario 3 : Contexte Ligue

**Utilisateur** : "Classement de la Ligue 1"
- **Type** : LEAGUE (en cours)
- **Intention** : `standings`
- **Endpoints** : `standings?league=61&season=2025`
- **Réponse** : Tableau du classement

**Utilisateur** : "Qui est le meilleur buteur ?"
- **Type** : LEAGUE (en cours)
- **Intention** : `top_scorers`
- **Endpoints** : `players/topscorers?league=61&season=2025`
- **Contexte enrichi** : + meilleurs buteurs
- **Réponse** : "Kylian Mbappé est le meilleur buteur avec 15 buts."

---

## 9. Bénéfices Attendus

### Performance
- **Réduction de 60-80% des appels API** pour les matchs à venir
- **Temps de réponse divisé par 2-3** grâce au contexte partagé
- **Coût API réduit** (moins d'appels inutiles)

### Expérience Utilisateur
- **Réponses plus rapides** (contexte déjà chargé)
- **Contexte visible** en haut de conversation
- **Informations en temps réel** pour les matchs en direct
- **Analyses ciblées** selon l'intention réelle

### Qualité des Réponses
- **Contexte enrichi** avec questions précédentes
- **Données pertinentes** (pas de surcharge d'infos)
- **Cohérence** entre utilisateurs sur le même match

---

## 10. Métriques de Succès

- **Taux de cache hit** : > 70% (contexte réutilisé)
- **Nombre moyen d'endpoints par question** : < 2 pour matchs à venir
- **Temps de réponse** : < 2s pour questions avec contexte
- **Satisfaction utilisateur** : Mesurée via feedback
