# Architecture pour Agents Vraiment Autonomes avec Cache Intelligent

**Date de création** : 11 décembre 2025
**Version** : 1.0
**Auteur** : Analyse Claude Code

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Analyse de l'Existant](#analyse-de-lexistant)
3. [Architecture Cible](#architecture-cible)
4. [Système de Cache Intelligent](#système-de-cache-intelligent)
5. [Base de Connaissance des Endpoints](#base-de-connaissance-des-endpoints)
6. [Système de Décision Autonome](#système-de-décision-autonome)
7. [Plan d'Implémentation Détaillé](#plan-dimplémentation-détaillé)
8. [Métriques et Monitoring](#métriques-et-monitoring)

---

## 📊 Vue d'Ensemble

### Objectif Principal

Créer un système d'agents complètement autonomes qui :

1. **Connaissent l'intégralité des endpoints API-Football** (50+ endpoints)
2. **Comprennent les use cases** de chaque endpoint
3. **Décident intelligemment** quels endpoints appeler pour répondre à une question
4. **Demandent des clarifications** quand l'information est insuffisante
5. **Optimisent les appels API** via un cache intelligent multi-utilisateurs

### Problématique Actuelle

**Limites du système actuel** :

```
Question Utilisateur
    ↓
Intent Agent (classification rigide parmi 40+ intents)
    ↓
Tool Agent (guidance intent → endpoints mappés)
    ↓
API Calls (selon mapping prédéfini)
    ↓
Response
```

**Problèmes identifiés** :

- ❌ **Rigidité** : Mapping intent → endpoints figé dans `prompts.py`
- ❌ **Couverture limitée** : Seulement 40 intents définis vs potentiel illimité de questions
- ❌ **Guidance manuelle** : Intent guidance maintenu manuellement
- ❌ **Pas d'optimisation multi-users** : Cache par session uniquement
- ❌ **Appels redondants** : Pas de vérification des données déjà disponibles
- ❌ **Pas de validation des questions** : Ne demande pas de clarifications

---

## 🔍 Analyse de l'Existant

### 1. Architecture Actuelle des Agents

#### A. Intent Agent (`backend/agents/intent_agent.py`)

**Forces** :
- ✅ Classification rapide (temperature=0.1)
- ✅ Extraction d'entités (team, league, date, etc.)
- ✅ Détection du besoin de données (`needs_data`)

**Limitations** :
- ❌ 40+ intents prédéfinis (non extensible)
- ❌ Keywords hardcodés pour chaque intent
- ❌ Pas de détection de questions ambiguës
- ❌ Pas de validation des entités

**Exemple de limitation** :
```python
# Question : "Compare l'attaque du PSG et celle du Real Madrid"
# → Intent actuel : "stats_comparison" (défini)
# → Mais si on demande : "Compare les gardiens"
# → Pas d'intent spécifique, classification approximative
```

#### B. Tool Agent (`backend/agents/tool_agent.py`)

**Forces** :
- ✅ Function calling avec DeepSeek
- ✅ Boucle itérative (max 3 itérations)
- ✅ Guidance intent-spécifique
- ✅ Forced critical tools pour analyse_rencontre

**Limitations** :
- ❌ Dépend de l'intent pour guider les appels
- ❌ Guidance maintenue manuellement dans `TOOL_SYSTEM_PROMPT`
- ❌ Pas de connaissance des endpoints enrichis (fixtures?id, predictions)
- ❌ Pas de vérification de redondance des appels

**Exemple de guidance actuelle** :
```python
intent_guidance = {
    "stats_final": (
        "1) search_team PSG, 2) search_team Lyon, "
        "3) fixtures_search pour obtenir fixture_id, "
        "4) OBLIGATOIREMENT appeler fixture_statistics"
    )
}
```
→ Rigide et nécessite maintenance manuelle

#### C. Système de Cache Actuel

**Caching actuel** :

1. **In-memory (FootballAPIClient)** :
   - Timezones, seasons, countries
   - Cache simple, pas de TTL
   - Données référentielles uniquement

2. **Match Context (ContextAgent + MatchContextStore)** :
   - 25 API calls → 0 sur accès suivant
   - Cache disk/memory
   - Limité aux matchs analysés via `analyze_match`

3. **Redis Context (ContextManager)** :
   - TTL: 3600s (1 heure)
   - Contexte conversationnel
   - Pas de partage entre utilisateurs

**Limitations** :
- ❌ **Pas de cache partagé** entre utilisateurs différents
- ❌ **Pas de cache pour données live** (invalidation)
- ❌ **Pas de cache pour requêtes similaires** (PSG-Lyon vs Lyon-PSG)
- ❌ **Pas de détection de données disponibles** dans le cache avant appel API

### 2. Couverture des Endpoints API-Football

**50+ endpoints disponibles** via `FootballAPIClient` :

```
ENDPOINTS_REFERENCE = {
    # Match data
    'fixtures': 'Recherche de matchs (id, league, team, date, live)',
    'fixtures/events': 'Événements (buts, cartons)',
    'fixtures/lineups': 'Compositions',
    'fixtures/statistics': 'Statistiques de match',
    'fixtures/players': 'Stats joueurs',
    'fixtures/headtohead': 'Confrontations directes',

    # Teams
    'teams': 'Recherche équipes',
    'teams/statistics': 'Stats équipe saison',

    # Leagues
    'standings': 'Classement',
    'leagues': 'Info ligues',

    # Players
    'players': 'Recherche joueurs',
    'players/topscorers': 'Meilleurs buteurs',
    'players/topassists': 'Meilleurs passeurs',
    'players/topyellowcards': 'Cartons jaunes',
    'players/topredcards': 'Cartons rouges',

    # Predictions
    'predictions': 'Prédictions + forme + h2h + comparaisons',

    # Injuries
    'injuries': 'Blessures/suspensions',

    # Odds
    'odds': 'Cotes bookmakers',
    'odds/live': 'Cotes en direct',

    # Others
    'transfers': 'Transferts',
    'trophies': 'Palmarès',
    'coaches': 'Entraîneurs',
    'venues': 'Stades',
    # ... 50+ au total
}
```

**Documentation critique** (découverte clé de `analyse_endpoints_api_football.md`) :

1. **`fixtures?id={id}` est ENRICHI** :
   - Contient : events, lineups, statistics, players
   - **1 appel remplace 5 appels** pour matchs live/terminés

2. **`predictions?fixture={id}` est ENRICHI** :
   - Contient : forme (last_5 + saison), h2h, comparaisons
   - **1 appel remplace 4-5 appels** pour matchs à venir

---

## 🎯 Architecture Cible

### Vision Globale

```
Question Utilisateur
    ↓
[AGENT AUTONOME]
    ├─→ Question Validator (valide complétude/ambiguïté)
    │   └─→ Si incomplet : Demande clarifications
    ↓
    ├─→ Endpoint Planner (connaît TOUS les endpoints + use cases)
    │   ├─→ Consulte Base de Connaissance Endpoints
    │   ├─→ Vérifie Cache Intelligent (données déjà disponibles?)
    │   └─→ Génère plan d'appels optimisé
    ↓
    ├─→ API Orchestrator (exécute plan)
    │   ├─→ Vérification redondance (avant chaque appel)
    │   ├─→ Exécution parallèle (appels indépendants)
    │   └─→ Cache Intelligent (partage multi-users)
    ↓
    ├─→ Data Synthesizer (agrège résultats)
    │   └─→ Répond à la question
    ↓
Response Utilisateur
```

### Principe Fondamental : Agent Généraliste

**Au lieu de** :
```python
# Ancien système
40+ intents prédéfinis → guidance spécifique → endpoints mappés
```

**Nouveau système** :
```python
# Nouveau système
Question → Compréhension sémantique → Sélection endpoints → Exécution optimisée
```

L'agent doit raisonner comme un humain :
1. "Que veut vraiment l'utilisateur ?"
2. "Quelles données me faut-il pour répondre ?"
3. "Où puis-je trouver ces données ?" (endpoints)
4. "Est-ce que je les ai déjà ?" (cache)
5. "Sinon, comment les obtenir le plus efficacement ?" (optimisation)

---

## 🧠 Composants Détaillés

### 1. Question Validator

**Rôle** : Valider que la question contient toutes les informations nécessaires.

```python
# backend/agents/question_validator.py

class QuestionValidator:
    """
    Valide la complétude d'une question utilisateur et détecte les ambiguïtés.
    """

    async def validate(self, question: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Valide la question et retourne les informations manquantes.

        Args:
            question: Question utilisateur
            context: Contexte conversationnel (historique, etc.)

        Returns:
            ValidationResult avec:
                - is_complete: bool
                - missing_info: List[str] (éléments manquants)
                - clarification_questions: List[str]
                - extracted_entities: Dict (entités détectées)
        """

        # 1. Extraction d'entités
        entities = await self._extract_entities(question)

        # 2. Détection du type de question
        question_type = await self._classify_question_type(question)
        # Types: match_info, team_stats, player_stats, league_info, prediction, etc.

        # 3. Validation selon le type
        missing = await self._check_required_info(question_type, entities, context)

        # 4. Génération de questions de clarification
        clarifications = await self._generate_clarifications(missing) if missing else []

        return ValidationResult(
            is_complete=len(missing) == 0,
            missing_info=missing,
            clarification_questions=clarifications,
            extracted_entities=entities,
            question_type=question_type
        )

    async def _extract_entities(self, question: str) -> Dict[str, Any]:
        """
        Extrait les entités de la question.

        Entités possibles:
        - teams: List[str]
        - league: str
        - season: int
        - date: str
        - player: str
        - match_status: str (live, finished, upcoming)
        - time_frame: str (today, yesterday, last 5, etc.)
        """
        # Utiliser LLM pour extraction robuste
        prompt = f"""
        Extrais les entités suivantes de cette question de football :
        Question: {question}

        Entités à extraire:
        - teams (noms d'équipes)
        - league (nom de compétition)
        - season (année)
        - date (date spécifique ou relative)
        - player (nom de joueur)
        - match_status (live/finished/upcoming)
        - time_frame (période temporelle)

        Retourne JSON avec les entités trouvées.
        """
        # Appel LLM...

    async def _classify_question_type(self, question: str) -> str:
        """
        Classifie le type de question (sémantiquement).

        Types possibles:
        - match_live_info: Info sur match en cours
        - match_finished_info: Info sur match terminé
        - match_prediction: Prédiction match à venir
        - team_stats: Statistiques équipe
        - player_stats: Statistiques joueur
        - league_standings: Classement
        - comparison: Comparaison (équipes/joueurs)
        - historical: Données historiques (h2h, etc.)
        """
        # Classification sémantique via LLM

    async def _check_required_info(
        self,
        question_type: str,
        entities: Dict,
        context: Dict
    ) -> List[str]:
        """
        Vérifie les informations requises selon le type de question.

        Example:
            question_type = "match_live_info"
            → Requis: team(s) OU fixture_id OU league+date

            question_type = "match_prediction"
            → Requis: 2 teams OU fixture_id, date si non fournie

            question_type = "team_stats"
            → Requis: team, league, season
        """

        required_info_map = {
            'match_live_info': {
                'any_of': [
                    ['fixture_id'],
                    ['teams'],  # Au moins 1 équipe
                    ['league', 'date']
                ]
            },
            'match_prediction': {
                'any_of': [
                    ['fixture_id'],
                    ['teams'],  # 2 équipes requises
                ],
                'optional': ['date', 'league']
            },
            'team_stats': {
                'required': ['team'],
                'optional': ['league', 'season']
            },
            'player_stats': {
                'required': ['player'],
                'optional': ['season', 'team']
            },
            # ...
        }

        missing = []
        rules = required_info_map.get(question_type, {})

        # Vérifier 'any_of' (au moins une combinaison complète)
        if 'any_of' in rules:
            has_one_combo = False
            for combo in rules['any_of']:
                if all(k in entities for k in combo):
                    has_one_combo = True
                    break

            if not has_one_combo:
                missing.append(f"any_of: {rules['any_of']}")

        # Vérifier 'required' (toutes obligatoires)
        if 'required' in rules:
            for req in rules['required']:
                if req not in entities:
                    missing.append(req)

        return missing

    async def _generate_clarifications(self, missing: List[str]) -> List[str]:
        """
        Génère des questions de clarification naturelles.

        Example:
            missing = ['team']
            → "De quelle équipe parles-tu ?"

            missing = ['any_of: [fixture_id, teams, league+date]']
            → "Pour quel match ? Peux-tu me donner les équipes ou la compétition et la date ?"
        """
        # Génération via templates ou LLM
```

**Exemple d'utilisation** :

```python
# Question ambiguë
question = "Quel est le score ?"
result = await validator.validate(question, context={})

# result.is_complete = False
# result.missing_info = ['teams', 'fixture_id', 'league+date']
# result.clarification_questions = [
#     "De quel match parles-tu ? Peux-tu me donner les équipes ou l'ID du match ?"
# ]

# L'agent répond à l'utilisateur
→ "De quel match parles-tu ? Peux-tu me donner les équipes ?"

# Utilisateur répond
user: "PSG - Lyon"

# Nouvelle validation
question_full = "Quel est le score de PSG - Lyon ?"
result = await validator.validate(question_full, context={})

# result.is_complete = True
# result.extracted_entities = {'teams': ['PSG', 'Lyon']}
→ Agent continue vers Endpoint Planner
```

---

### 2. Base de Connaissance des Endpoints

**Rôle** : Documenter TOUS les endpoints avec leurs use cases, paramètres, et données retournées.

```python
# backend/knowledge/endpoint_knowledge_base.py

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class DataFreshness(Enum):
    """Fraîcheur des données d'un endpoint"""
    STATIC = "static"          # Données référentielles (pays, ligues)
    SEASONAL = "seasonal"      # Données de saison (classements, stats saison)
    MATCH_BOUND = "match_bound"  # Liées à un match (stats match)
    LIVE = "live"              # Données en temps réel (score live)

class CacheStrategy(Enum):
    """Stratégie de cache pour un endpoint"""
    INDEFINITE = "indefinite"      # Cache indéfini (données statiques)
    LONG_TTL = "long_ttl"          # Cache longue durée (1 jour, données de saison)
    SHORT_TTL = "short_ttl"        # Cache courte durée (10 min, classements)
    NO_CACHE = "no_cache"          # Pas de cache (live)
    MATCH_STATUS = "match_status"  # Cache selon statut match (FT=infini, LIVE=30s)

@dataclass
class EndpointMetadata:
    """Métadonnées complètes d'un endpoint"""

    name: str
    path: str
    description: str
    use_cases: List[str]  # Cas d'usage en langage naturel

    # Paramètres
    required_params: List[str]
    optional_params: List[str]

    # Données retournées
    data_returned: List[str]  # Liste des champs/sections retournées

    # Optimisations
    is_enriched: bool = False  # Est-ce un endpoint enrichi?
    enriched_data: List[str] = None  # Données supplémentaires si enrichi

    # Cache
    freshness: DataFreshness = DataFreshness.MATCH_BOUND
    cache_strategy: CacheStrategy = CacheStrategy.SHORT_TTL
    cache_key_pattern: str = None  # Pattern de clé de cache

    # Relations
    can_replace: List[str] = None  # Endpoints que celui-ci peut remplacer
    replaced_by: List[str] = None  # Endpoints qui peuvent remplacer celui-ci

    # Coût
    api_cost: int = 1  # Coût en crédits API

class EndpointKnowledgeBase:
    """
    Base de connaissance complète de tous les endpoints API-Football.

    Cette classe documente TOUS les endpoints avec:
    - Use cases détaillés
    - Paramètres requis/optionnels
    - Données retournées
    - Stratégies de cache
    - Relations entre endpoints (enrichissement, remplacement)
    """

    def __init__(self):
        self.endpoints: Dict[str, EndpointMetadata] = {}
        self._initialize_endpoints()

    def _initialize_endpoints(self):
        """Initialise la base de connaissance avec tous les endpoints"""

        # ==========================================
        # FIXTURES (MATCHS)
        # ==========================================

        self.endpoints['fixtures_by_id'] = EndpointMetadata(
            name='fixtures_by_id',
            path='fixtures?id={fixture_id}',
            description='Récupère toutes les données d\'un match spécifique',

            use_cases=[
                'Obtenir le score d\'un match',
                'Voir les statistiques d\'un match (possession, tirs, etc.)',
                'Connaître les événements d\'un match (buts, cartons)',
                'Voir les compositions d\'équipes',
                'Consulter les statistiques individuelles des joueurs d\'un match'
            ],

            required_params=['fixture_id'],
            optional_params=[],

            data_returned=[
                'fixture',      # Info match (date, status, score, etc.)
                'league',       # Info compétition
                'teams',        # Équipes
                'goals',        # Score
                'score'         # Score détaillé (HT, FT, ET, P)
            ],

            # CLEF : Endpoint enrichi
            is_enriched=True,
            enriched_data=[
                'events',       # Événements (buts, cartons, remplacements)
                'lineups',      # Compositions (formation, joueurs titulaires)
                'statistics',   # Statistiques équipes (possession, tirs, corners, etc.)
                'players'       # Statistiques individuelles joueurs
            ],

            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,  # Selon statut
            cache_key_pattern='fixtures:id:{fixture_id}',

            # Peut remplacer ces 4 endpoints
            can_replace=[
                'fixtures_events',
                'fixtures_lineups',
                'fixtures_statistics',
                'fixtures_players'
            ],

            api_cost=1
        )

        self.endpoints['fixtures_events'] = EndpointMetadata(
            name='fixtures_events',
            path='fixtures/events?fixture={fixture_id}',
            description='Événements d\'un match',

            use_cases=[
                'Liste des buteurs',
                'Voir les cartons jaunes/rouges',
                'Historique des remplacements'
            ],

            required_params=['fixture_id'],
            optional_params=['team_id', 'player_id', 'type'],

            data_returned=['events'],

            is_enriched=False,

            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,
            cache_key_pattern='fixtures:events:{fixture_id}',

            # REDONDANT si fixtures_by_id déjà appelé
            replaced_by=['fixtures_by_id'],

            api_cost=1
        )

        self.endpoints['fixtures_statistics'] = EndpointMetadata(
            name='fixtures_statistics',
            path='fixtures/statistics?fixture={fixture_id}',
            description='Statistiques détaillées d\'un match',

            use_cases=[
                'Possession du ballon',
                'Nombre de tirs (cadrés/non cadrés)',
                'Nombre de corners',
                'Fautes, hors-jeu, etc.'
            ],

            required_params=['fixture_id'],
            optional_params=['team_id'],

            data_returned=['statistics'],

            is_enriched=False,

            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,
            cache_key_pattern='fixtures:statistics:{fixture_id}',

            replaced_by=['fixtures_by_id'],

            api_cost=1
        )

        self.endpoints['fixtures_lineups'] = EndpointMetadata(
            name='fixtures_lineups',
            path='fixtures/lineups?fixture={fixture_id}',
            description='Compositions d\'équipes',

            use_cases=[
                'Voir la formation tactique (4-4-2, 4-3-3, etc.)',
                'Liste des titulaires',
                'Liste des remplaçants',
                'Coach'
            ],

            required_params=['fixture_id'],
            optional_params=['team_id'],

            data_returned=['lineups'],

            is_enriched=False,

            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,
            cache_key_pattern='fixtures:lineups:{fixture_id}',

            replaced_by=['fixtures_by_id'],

            api_cost=1
        )

        self.endpoints['fixtures_players'] = EndpointMetadata(
            name='fixtures_players',
            path='fixtures/players?fixture={fixture_id}',
            description='Statistiques individuelles des joueurs',

            use_cases=[
                'Note des joueurs (rating)',
                'Minutes jouées',
                'Buts et passes décisives',
                'Tirs, passes réussies, duels gagnés, etc.'
            ],

            required_params=['fixture_id'],
            optional_params=['team_id'],

            data_returned=['players'],

            is_enriched=False,

            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.MATCH_STATUS,
            cache_key_pattern='fixtures:players:{fixture_id}',

            replaced_by=['fixtures_by_id'],

            api_cost=1
        )

        # ==========================================
        # PREDICTIONS (MATCH À VENIR)
        # ==========================================

        self.endpoints['predictions'] = EndpointMetadata(
            name='predictions',
            path='predictions?fixture={fixture_id}',
            description='Prédictions et analyse complète pour un match à venir',

            use_cases=[
                'Prédiction du vainqueur',
                'Comparaison des équipes (forme, attaque, défense)',
                'Forme récente des équipes (5 derniers matchs)',
                'Statistiques de saison (all fixtures)',
                'Historique des confrontations (h2h)',
                'Analyse complète pour pronostic'
            ],

            required_params=['fixture_id'],
            optional_params=[],

            data_returned=[
                'predictions',  # Prédiction globale (winner, advice, percent)
                'teams',        # Infos équipes
                'comparison'    # Comparaison directe (form%, att%, def%, h2h%)
            ],

            # CLEF : Endpoint enrichi pour matchs à venir
            is_enriched=True,
            enriched_data=[
                'last_5',       # Forme des 5 derniers matchs (goals, form%)
                'league',       # Stats de saison complètes (forme, fixtures, buts)
                'h2h'           # Confrontations directes historiques
            ],

            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.LONG_TTL,  # 1 jour (prédictions stables)
            cache_key_pattern='predictions:fixture:{fixture_id}',

            # Peut remplacer ces endpoints pour matchs à venir
            can_replace=[
                'fixtures_headtohead',
                'team_last_fixtures_home',
                'team_last_fixtures_away'
            ],

            api_cost=1
        )

        self.endpoints['fixtures_headtohead'] = EndpointMetadata(
            name='fixtures_headtohead',
            path='fixtures/headtohead?h2h={team1_id}-{team2_id}',
            description='Historique des confrontations directes',

            use_cases=[
                'Voir les derniers matchs entre 2 équipes',
                'Statistiques h2h (victoires, nuls, défaites)',
                'Tendances historiques'
            ],

            required_params=['team1_id', 'team2_id'],
            optional_params=['last', 'from_date', 'to_date', 'league_id', 'season'],

            data_returned=['fixtures'],  # Liste des matchs h2h

            is_enriched=False,

            freshness=DataFreshness.MATCH_BOUND,
            cache_strategy=CacheStrategy.LONG_TTL,  # 1 jour (historique stable)
            cache_key_pattern='fixtures:h2h:{team1_id}:{team2_id}',

            # REDONDANT si predictions déjà appelé pour match à venir
            replaced_by=['predictions'],

            api_cost=1
        )

        # ==========================================
        # TEAMS (ÉQUIPES)
        # ==========================================

        self.endpoints['search_team'] = EndpointMetadata(
            name='search_team',
            path='teams?search={team_name}',
            description='Rechercher une équipe par son nom',

            use_cases=[
                'Trouver l\'ID d\'une équipe à partir de son nom',
                'Résolution d\'entité (PSG → team_id=85)'
            ],

            required_params=['team_name'],
            optional_params=['league_id', 'season', 'country'],

            data_returned=['team', 'venue'],

            is_enriched=False,

            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,  # Cache indéfini (nom → ID stable)
            cache_key_pattern='teams:search:{team_name}',

            api_cost=1
        )

        self.endpoints['team_statistics'] = EndpointMetadata(
            name='team_statistics',
            path='teams/statistics?team={team_id}&league={league_id}&season={season}',
            description='Statistiques complètes d\'une équipe sur une saison',

            use_cases=[
                'Bilan de la saison (matchs joués, victoires, nuls, défaites)',
                'Buts marqués/encaissés (domicile/extérieur/total)',
                'Statistiques moyennes (goals/match, clean sheets)',
                'Séries (victoires/défaites consécutives)',
                'Forme générale sur la saison'
            ],

            required_params=['team_id', 'league_id', 'season'],
            optional_params=['date'],

            data_returned=['statistics'],  # Stats complètes

            is_enriched=False,

            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,  # 10 min (stats évoluent)
            cache_key_pattern='teams:statistics:{team_id}:{league_id}:{season}',

            api_cost=1
        )

        self.endpoints['team_last_fixtures'] = EndpointMetadata(
            name='team_last_fixtures',
            path='fixtures?team={team_id}&last={n}',
            description='Derniers matchs d\'une équipe',

            use_cases=[
                'Analyser la forme récente',
                'Voir les résultats des 5 derniers matchs',
                'Calculer la série en cours (victoires consécutives)'
            ],

            required_params=['team_id'],
            optional_params=['n'],  # Default: 5

            data_returned=['fixtures'],  # Liste des derniers matchs

            is_enriched=False,

            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,  # 10 min
            cache_key_pattern='fixtures:team:{team_id}:last:{n}',

            # REDONDANT si predictions déjà appelé (contient last_5)
            replaced_by=['predictions'],

            api_cost=1
        )

        # ==========================================
        # STANDINGS (CLASSEMENTS)
        # ==========================================

        self.endpoints['standings'] = EndpointMetadata(
            name='standings',
            path='standings?league={league_id}&season={season}',
            description='Classement d\'une ligue',

            use_cases=[
                'Voir le classement général',
                'Position d\'une équipe',
                'Points, différence de buts',
                'Forme récente (5 derniers matchs)'
            ],

            required_params=['league_id', 'season'],
            optional_params=['team_id'],

            data_returned=['standings'],  # Tableau classement

            is_enriched=False,

            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,  # 10 min (évolue après chaque match)
            cache_key_pattern='standings:{league_id}:{season}',

            api_cost=1
        )

        # ==========================================
        # PLAYERS (JOUEURS)
        # ==========================================

        self.endpoints['search_player'] = EndpointMetadata(
            name='search_player',
            path='players?search={player_name}',
            description='Rechercher un joueur par son nom',

            use_cases=[
                'Trouver l\'ID d\'un joueur',
                'Résolution d\'entité (Mbappé → player_id=123)'
            ],

            required_params=['player_name'],
            optional_params=['season', 'team_id', 'league_id'],

            data_returned=['player', 'statistics'],

            is_enriched=False,

            freshness=DataFreshness.STATIC,
            cache_strategy=CacheStrategy.INDEFINITE,
            cache_key_pattern='players:search:{player_name}',

            api_cost=1
        )

        self.endpoints['top_scorers'] = EndpointMetadata(
            name='top_scorers',
            path='players/topscorers?league={league_id}&season={season}',
            description='Meilleurs buteurs d\'une ligue',

            use_cases=[
                'Voir le classement des buteurs',
                'Nombre de buts d\'un joueur',
                'Top 20 buteurs d\'une ligue'
            ],

            required_params=['league_id', 'season'],
            optional_params=[],

            data_returned=['players'],  # Top scorers avec stats

            is_enriched=False,

            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,  # 10 min
            cache_key_pattern='players:topscorers:{league_id}:{season}',

            api_cost=1
        )

        self.endpoints['top_assists'] = EndpointMetadata(
            name='top_assists',
            path='players/topassists?league={league_id}&season={season}',
            description='Meilleurs passeurs d\'une ligue',

            use_cases=[
                'Voir le classement des passeurs',
                'Nombre de passes décisives d\'un joueur'
            ],

            required_params=['league_id', 'season'],
            optional_params=[],

            data_returned=['players'],

            is_enriched=False,

            freshness=DataFreshness.SEASONAL,
            cache_strategy=CacheStrategy.SHORT_TTL,
            cache_key_pattern='players:topassists:{league_id}:{season}',

            api_cost=1
        )

        # ==========================================
        # INJURIES (BLESSURES)
        # ==========================================

        self.endpoints['injuries'] = EndpointMetadata(
            name='injuries',
            path='injuries?team={team_id}',
            description='Blessures et suspensions',

            use_cases=[
                'Joueurs indisponibles',
                'Impact des absences sur un match',
                'Raison de l\'absence (blessure/suspension)'
            ],

            required_params=[],
            optional_params=['league_id', 'season', 'fixture_id', 'team_id', 'player_id', 'date'],

            data_returned=['injuries'],

            is_enriched=False,

            freshness=DataFreshness.LIVE,  # Change fréquemment
            cache_strategy=CacheStrategy.SHORT_TTL,  # 10 min
            cache_key_pattern='injuries:team:{team_id}',

            api_cost=1
        )

        # ==========================================
        # ODDS (COTES)
        # ==========================================

        self.endpoints['odds_by_fixture'] = EndpointMetadata(
            name='odds_by_fixture',
            path='odds?fixture={fixture_id}',
            description='Cotes des bookmakers pour un match',

            use_cases=[
                'Cotes 1X2',
                'Comparaison de cotes entre bookmakers',
                'Évolution des cotes'
            ],

            required_params=['fixture_id'],
            optional_params=['bookmaker_id', 'bet_id'],

            data_returned=['odds'],

            is_enriched=False,

            freshness=DataFreshness.LIVE,
            cache_strategy=CacheStrategy.SHORT_TTL,  # 10 min (cotes évoluent)
            cache_key_pattern='odds:fixture:{fixture_id}',

            api_cost=1
        )

        # ==========================================
        # LIVE (EN DIRECT)
        # ==========================================

        self.endpoints['live_fixtures'] = EndpointMetadata(
            name='live_fixtures',
            path='fixtures?live=all',
            description='Tous les matchs en direct',

            use_cases=[
                'Liste des matchs en cours',
                'Scores en temps réel',
                'Événements en direct'
            ],

            required_params=[],
            optional_params=['league_id'],

            data_returned=['fixtures'],  # Avec events/lineups/stats si disponibles

            is_enriched=True,  # Contient events/lineups/stats
            enriched_data=['events', 'lineups', 'statistics'],

            freshness=DataFreshness.LIVE,
            cache_strategy=CacheStrategy.NO_CACHE,  # Jamais de cache (temps réel)
            cache_key_pattern=None,

            api_cost=1
        )

        # TODO: Ajouter les 40+ endpoints restants avec la même structure
        # (transfers, trophies, coaches, venues, etc.)

    def get_endpoint(self, name: str) -> EndpointMetadata:
        """Récupère les métadonnées d'un endpoint"""
        return self.endpoints.get(name)

    def search_by_use_case(self, use_case_query: str) -> List[EndpointMetadata]:
        """
        Recherche les endpoints correspondant à un use case.

        Example:
            search_by_use_case("score d'un match")
            → ['fixtures_by_id']

            search_by_use_case("forme récente équipe")
            → ['predictions', 'team_last_fixtures', 'team_statistics']
        """
        # Recherche sémantique dans use_cases de tous les endpoints
        results = []
        for endpoint in self.endpoints.values():
            for use_case in endpoint.use_cases:
                if self._semantic_match(use_case_query, use_case):
                    results.append(endpoint)
                    break
        return results

    def _semantic_match(self, query: str, use_case: str) -> bool:
        """Match sémantique simple (peut être amélioré avec embedding)"""
        # Simple keyword matching pour l'instant
        query_words = set(query.lower().split())
        use_case_words = set(use_case.lower().split())
        overlap = query_words.intersection(use_case_words)
        return len(overlap) >= 2  # Au moins 2 mots en commun

    def get_enriched_endpoints(self) -> List[EndpointMetadata]:
        """Retourne tous les endpoints enrichis"""
        return [e for e in self.endpoints.values() if e.is_enriched]

    def get_cache_ttl(self, endpoint_name: str, match_status: str = None) -> int:
        """
        Calcule le TTL de cache pour un endpoint.

        Args:
            endpoint_name: Nom de l'endpoint
            match_status: Statut du match (FT, LIVE, NS, etc.) si applicable

        Returns:
            TTL en secondes (0 = pas de cache)
        """
        endpoint = self.get_endpoint(endpoint_name)
        if not endpoint:
            return 300  # Default 5 min

        strategy = endpoint.cache_strategy

        if strategy == CacheStrategy.NO_CACHE:
            return 0

        elif strategy == CacheStrategy.INDEFINITE:
            return 86400 * 365  # 1 an

        elif strategy == CacheStrategy.LONG_TTL:
            return 86400  # 1 jour

        elif strategy == CacheStrategy.SHORT_TTL:
            return 600  # 10 min

        elif strategy == CacheStrategy.MATCH_STATUS:
            # Selon le statut du match
            if match_status in ['FT', 'AET', 'PEN', 'AWD', 'WO']:
                # Match terminé → cache indéfini
                return 86400 * 365
            elif match_status in ['1H', '2H', 'HT', 'ET', 'BT', 'P', 'LIVE']:
                # Match en cours → cache très court (30s)
                return 30
            else:
                # Match à venir → cache moyen (10 min)
                return 600

        return 300  # Default
```

**Avantages de cette base de connaissance** :

1. ✅ **Centralisation** : Toute la connaissance API-Football en un seul endroit
2. ✅ **Maintenance facile** : Ajouter/modifier un endpoint = 1 entrée à modifier
3. ✅ **Recherche sémantique** : `search_by_use_case("score match")` trouve automatiquement les endpoints pertinents
4. ✅ **Optimisation automatique** : Détection des endpoints enrichis et redondants
5. ✅ **Cache intelligent** : TTL adaptatif selon le type de données

---

### 3. Endpoint Planner (Cœur de l'Autonomie)

**Rôle** : Décider intelligemment quels endpoints appeler pour répondre à la question.

```python
# backend/agents/endpoint_planner.py

class EndpointPlanner:
    """
    Planificateur d'endpoints intelligent.

    Ce composant est le CŒUR de l'autonomie des agents.
    Il décide quels endpoints appeler en fonction :
    - De la question utilisateur
    - Des données déjà en cache
    - Des optimisations possibles (endpoints enrichis)
    """

    def __init__(
        self,
        knowledge_base: EndpointKnowledgeBase,
        cache_manager: IntelligentCacheManager,
        llm_client: Any
    ):
        self.kb = knowledge_base
        self.cache = cache_manager
        self.llm = llm_client

    async def plan(
        self,
        question: str,
        entities: Dict[str, Any],
        context_id: str
    ) -> ExecutionPlan:
        """
        Génère un plan d'exécution optimisé pour répondre à la question.

        Args:
            question: Question utilisateur
            entities: Entités extraites (teams, league, date, etc.)
            context_id: ID du contexte (pour accès au cache)

        Returns:
            ExecutionPlan avec:
                - endpoints: List[EndpointCall] (appels à effectuer)
                - reasoning: str (explication du plan)
                - cached_data: Dict (données déjà disponibles)
                - estimated_cost: int (crédits API)
        """

        # 1. Vérifier ce qui est déjà en cache
        cached_data = await self.cache.get_available_data(context_id, entities)

        # 2. Identifier les endpoints candidats (via LLM + knowledge base)
        candidate_endpoints = await self._identify_candidate_endpoints(
            question, entities
        )

        # 3. Filtrer les endpoints redondants
        filtered_endpoints = await self._filter_redundant_endpoints(
            candidate_endpoints,
            cached_data
        )

        # 4. Optimiser avec endpoints enrichis
        optimized_endpoints = await self._optimize_with_enriched_endpoints(
            filtered_endpoints
        )

        # 5. Résoudre les dépendances (ordre d'exécution)
        execution_order = await self._resolve_dependencies(optimized_endpoints, entities)

        # 6. Générer le plan final
        plan = ExecutionPlan(
            endpoints=execution_order,
            reasoning=await self._generate_reasoning(execution_order),
            cached_data=cached_data,
            estimated_cost=sum(e.api_cost for e in execution_order)
        )

        return plan

    async def _identify_candidate_endpoints(
        self,
        question: str,
        entities: Dict
    ) -> List[EndpointMetadata]:
        """
        Identifie les endpoints candidats pour répondre à la question.

        Utilise :
        1. Recherche sémantique dans la knowledge base
        2. LLM pour raisonnement complexe
        """

        # 1. Recherche sémantique simple
        semantic_results = self.kb.search_by_use_case(question)

        # 2. Raisonnement LLM pour cas complexes
        prompt = f"""
        Tu es un expert de l'API Football (API-Football v3).

        Question utilisateur: {question}
        Entités détectées: {entities}

        Endpoints disponibles (avec use cases):
        {self._format_endpoints_for_llm()}

        Quels endpoints dois-je appeler pour répondre complètement à cette question?

        Considère:
        - Les endpoints ENRICHIS (fixtures?id, predictions) qui contiennent déjà beaucoup de données
        - Les dépendances (ex: besoin de team_id avant d'appeler team_statistics)
        - L'optimisation (minimiser le nombre d'appels)

        Retourne JSON:
        {{
            "endpoints": [
                {{
                    "name": "...",
                    "reason": "...",
                    "params": {{...}}
                }}
            ],
            "reasoning": "Explication du choix"
        }}
        """

        # Appel LLM avec knowledge base dans le prompt
        response = await self.llm.generate(prompt, temperature=0.1)
        llm_endpoints = self._parse_llm_response(response)

        # 3. Fusion des résultats
        all_endpoints = self._merge_endpoints(semantic_results, llm_endpoints)

        return all_endpoints

    async def _filter_redundant_endpoints(
        self,
        endpoints: List[EndpointMetadata],
        cached_data: Dict
    ) -> List[EndpointMetadata]:
        """
        Filtre les endpoints redondants.

        Règles:
        - Si fixtures?id déjà en cache → enlever events, lineups, statistics, players
        - Si predictions déjà en cache → enlever h2h, team_last_fixtures
        - Si données déjà en cache → enlever l'endpoint
        """

        filtered = []

        for endpoint in endpoints:
            # Vérifier si remplacé par un endpoint déjà appelé/en cache
            if self._is_replaced_by_cached(endpoint, cached_data):
                continue

            # Vérifier si données déjà disponibles
            if self._data_available_in_cache(endpoint, cached_data):
                continue

            filtered.append(endpoint)

        return filtered

    async def _optimize_with_enriched_endpoints(
        self,
        endpoints: List[EndpointMetadata]
    ) -> List[EndpointMetadata]:
        """
        Optimise en utilisant les endpoints enrichis.

        Règle:
        Si on a besoin de fixtures_events, fixtures_lineups, fixtures_statistics
        → Remplacer par fixtures_by_id (1 appel au lieu de 3)
        """

        # Identifier les groupes remplaçables
        can_use_fixtures_enriched = [
            'fixtures_events', 'fixtures_lineups',
            'fixtures_statistics', 'fixtures_players'
        ]

        can_use_predictions = [
            'fixtures_headtohead', 'team_last_fixtures'
        ]

        # Vérifier si on a plusieurs endpoints du même groupe
        endpoint_names = [e.name for e in endpoints]

        # Optimisation fixtures
        if any(name in can_use_fixtures_enriched for name in endpoint_names):
            # Remplacer tout par fixtures_by_id
            endpoints = [
                e for e in endpoints
                if e.name not in can_use_fixtures_enriched
            ]
            endpoints.insert(0, self.kb.get_endpoint('fixtures_by_id'))

        # Optimisation predictions
        if any(name in can_use_predictions for name in endpoint_names):
            endpoints = [
                e for e in endpoints
                if e.name not in can_use_predictions
            ]
            # Ajouter predictions si pas déjà là
            if 'predictions' not in endpoint_names:
                endpoints.insert(0, self.kb.get_endpoint('predictions'))

        return endpoints

    async def _resolve_dependencies(
        self,
        endpoints: List[EndpointMetadata],
        entities: Dict
    ) -> List[EndpointCall]:
        """
        Résout les dépendances entre endpoints.

        Exemple:
        - team_statistics nécessite team_id
        - Si team_id pas fourni → besoin de search_team d'abord

        Returns:
            Liste ordonnée d'EndpointCall avec paramètres résolus
        """

        ordered_calls = []
        resolved_params = {**entities}  # Paramètres déjà connus

        for endpoint in endpoints:
            # Vérifier si tous les paramètres requis sont disponibles
            missing_params = [
                p for p in endpoint.required_params
                if p not in resolved_params
            ]

            if missing_params:
                # Ajouter des endpoints de résolution
                for param in missing_params:
                    if param == 'team_id' and 'team_name' in resolved_params:
                        # Ajouter search_team
                        search_call = EndpointCall(
                            endpoint=self.kb.get_endpoint('search_team'),
                            params={'team_name': resolved_params['team_name']},
                            output_mapping={'team_id': 'team.id'}
                        )
                        ordered_calls.append(search_call)
                        resolved_params['team_id'] = '<will_be_resolved>'

                    elif param == 'fixture_id' and 'teams' in resolved_params:
                        # Rechercher le match via fixtures_search
                        search_call = EndpointCall(
                            endpoint=self.kb.get_endpoint('fixtures_search'),
                            params={
                                'team1_id': resolved_params.get('team1_id'),
                                'team2_id': resolved_params.get('team2_id'),
                                'date': resolved_params.get('date', 'today')
                            },
                            output_mapping={'fixture_id': 'fixtures[0].fixture_id'}
                        )
                        ordered_calls.append(search_call)
                        resolved_params['fixture_id'] = '<will_be_resolved>'

            # Ajouter l'endpoint avec paramètres résolus
            call_params = {
                k: resolved_params.get(k, v)
                for k, v in endpoint.required_params
            }

            ordered_calls.append(EndpointCall(
                endpoint=endpoint,
                params=call_params
            ))

        return ordered_calls
```

**Exemple concret** :

```python
# Question: "Quelle est la forme récente du PSG ?"

# 1. Validation
validator_result = {
    'is_complete': True,
    'entities': {'team_name': 'PSG'}
}

# 2. Planning
plan = await planner.plan(
    question="Quelle est la forme récente du PSG ?",
    entities={'team_name': 'PSG'},
    context_id='ctx_123'
)

# Plan généré:
{
    'endpoints': [
        EndpointCall(
            endpoint='search_team',
            params={'team_name': 'PSG'},
            reason='Résoudre PSG → team_id'
        ),
        EndpointCall(
            endpoint='team_last_fixtures',
            params={'team_id': '<from_search_team>', 'n': 5},
            reason='Obtenir les 5 derniers matchs'
        )
    ],
    'reasoning': "Pour analyser la forme récente, on a besoin des derniers matchs. D'abord on résout le nom 'PSG' en team_id via search_team, puis on récupère les 5 derniers matchs via team_last_fixtures.",
    'cached_data': {},
    'estimated_cost': 2  # 2 appels API
}

# 3. Exécution (voir API Orchestrator ci-dessous)
```

---

### 4. Système de Cache Intelligent Multi-Utilisateurs

**Rôle** : Cache partagé entre utilisateurs avec invalidation intelligente.

```python
# backend/cache/intelligent_cache_manager.py

import redis.asyncio as aioredis
from typing import Dict, List, Any, Optional
import hashlib
import json
from datetime import datetime

class IntelligentCacheManager:
    """
    Gestionnaire de cache intelligent multi-utilisateurs.

    Caractéristiques:
    - Cache partagé entre tous les utilisateurs (Redis)
    - TTL adaptatif selon le type de données
    - Invalidation intelligente (données live)
    - Normalisation des clés (PSG-Lyon = Lyon-PSG)
    - Compression des données volumineuses
    """

    def __init__(self, redis_client: aioredis.Redis, knowledge_base: EndpointKnowledgeBase):
        self.redis = redis_client
        self.kb = knowledge_base

        # Prefix pour toutes les clés de cache
        self.cache_prefix = "lucide:apicache:"

    async def get(
        self,
        endpoint_name: str,
        params: Dict[str, Any],
        match_status: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Récupère des données du cache.

        Args:
            endpoint_name: Nom de l'endpoint
            params: Paramètres de l'appel
            match_status: Statut du match si applicable

        Returns:
            Données en cache ou None
        """

        # Générer la clé de cache normalisée
        cache_key = self._generate_cache_key(endpoint_name, params)

        # Vérifier dans Redis
        cached_json = await self.redis.get(cache_key)

        if not cached_json:
            return None

        # Désérialiser
        cached_data = json.loads(cached_json)

        # Vérifier si encore valide (pour données live)
        if self._is_expired(cached_data, match_status):
            await self.redis.delete(cache_key)
            return None

        return cached_data['data']

    async def set(
        self,
        endpoint_name: str,
        params: Dict[str, Any],
        data: Dict,
        match_status: Optional[str] = None
    ):
        """
        Stocke des données dans le cache.

        Args:
            endpoint_name: Nom de l'endpoint
            params: Paramètres de l'appel
            data: Données à cacher
            match_status: Statut du match si applicable
        """

        # Générer clé
        cache_key = self._generate_cache_key(endpoint_name, params)

        # Calculer TTL
        ttl = self.kb.get_cache_ttl(endpoint_name, match_status)

        if ttl == 0:
            # Pas de cache
            return

        # Préparer les données
        cache_entry = {
            'data': data,
            'endpoint': endpoint_name,
            'params': params,
            'cached_at': datetime.utcnow().isoformat(),
            'match_status': match_status
        }

        # Sérialiser
        cache_json = json.dumps(cache_entry)

        # Stocker avec TTL
        await self.redis.setex(
            cache_key,
            ttl,
            cache_json
        )

    def _generate_cache_key(self, endpoint_name: str, params: Dict) -> str:
        """
        Génère une clé de cache normalisée.

        Normalisation:
        - Tri des paramètres (pour cohérence)
        - Normalisation des équipes (team1-team2 = team2-team1 pour h2h)
        - Hash MD5 pour clés courtes

        Example:
            _generate_cache_key('fixtures_search', {'team1_id': 85, 'team2_id': 131})
            → "lucide:apicache:fixtures_search:85-131"

            Mais:
            _generate_cache_key('fixtures_search', {'team1_id': 131, 'team2_id': 85})
            → "lucide:apicache:fixtures_search:85-131" (même clé!)
        """

        # Normaliser les paramètres
        normalized_params = self._normalize_params(endpoint_name, params)

        # Créer une représentation stable
        params_str = json.dumps(normalized_params, sort_keys=True)

        # Hash pour clé courte
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]

        # Clé finale
        cache_key = f"{self.cache_prefix}{endpoint_name}:{params_hash}"

        return cache_key

    def _normalize_params(self, endpoint_name: str, params: Dict) -> Dict:
        """
        Normalise les paramètres pour générer une clé cohérente.

        Normalisations spécifiques:
        - h2h: Trier team1_id et team2_id (85-131 = 131-85)
        - dates: Normaliser format (today → 2025-12-11)
        - team names: Lowercaseify et trim
        """

        normalized = params.copy()

        # H2H: Normaliser l'ordre des équipes
        if endpoint_name == 'fixtures_headtohead':
            if 'team1_id' in normalized and 'team2_id' in normalized:
                team1 = normalized['team1_id']
                team2 = normalized['team2_id']
                # Toujours mettre le plus petit ID en premier
                if team1 > team2:
                    normalized['team1_id'] = team2
                    normalized['team2_id'] = team1

        # Dates relatives → absolues
        if 'date' in normalized:
            if normalized['date'] == 'today':
                normalized['date'] = datetime.utcnow().strftime('%Y-%m-%d')

        # Team names: Normaliser
        if 'team_name' in normalized:
            normalized['team_name'] = normalized['team_name'].lower().strip()

        return normalized

    def _is_expired(self, cached_data: Dict, match_status: Optional[str]) -> bool:
        """
        Vérifie si les données cachées sont expirées.

        Cas spécial: Match status changé
        - Données cachées pour match "LIVE"
        - Mais maintenant match status = "FT" (terminé)
        - → Cache expiré, il faut redemander
        """

        if not match_status:
            return False

        cached_status = cached_data.get('match_status')

        # Si status a changé de LIVE → FT, invalider
        if cached_status == 'LIVE' and match_status == 'FT':
            return True

        return False

    async def get_available_data(
        self,
        context_id: str,
        entities: Dict
    ) -> Dict[str, Any]:
        """
        Récupère toutes les données disponibles en cache pour un contexte donné.

        Utilisé par Endpoint Planner pour éviter des appels redondants.

        Args:
            context_id: ID du contexte
            entities: Entités extraites (pour trouver les clés de cache)

        Returns:
            Dict avec toutes les données disponibles:
            {
                'fixtures_by_id': {...},
                'predictions': {...},
                'team_last_fixtures': {...},
                ...
            }
        """

        available_data = {}

        # Essayer de récupérer les endpoints communs
        common_endpoints = [
            'fixtures_by_id',
            'predictions',
            'team_last_fixtures',
            'standings',
            'team_statistics'
        ]

        for endpoint_name in common_endpoints:
            # Construire les params possibles depuis les entités
            params = self._build_params_from_entities(endpoint_name, entities)

            if params:
                data = await self.get(endpoint_name, params)
                if data:
                    available_data[endpoint_name] = data

        return available_data

    def _build_params_from_entities(
        self,
        endpoint_name: str,
        entities: Dict
    ) -> Optional[Dict]:
        """
        Construit les paramètres d'un endpoint à partir des entités.

        Example:
            endpoint_name = 'fixtures_by_id'
            entities = {'fixture_id': 12345}
            → {'fixture_id': 12345}

            endpoint_name = 'team_statistics'
            entities = {'team_id': 85, 'league_id': 61, 'season': 2025}
            → {'team_id': 85, 'league_id': 61, 'season': 2025}
        """

        endpoint = self.kb.get_endpoint(endpoint_name)
        if not endpoint:
            return None

        # Vérifier si on a tous les paramètres requis
        params = {}
        for req_param in endpoint.required_params:
            if req_param in entities:
                params[req_param] = entities[req_param]
            else:
                # Paramètre manquant, on ne peut pas construire
                return None

        return params if params else None

    async def invalidate_match_cache(self, fixture_id: int):
        """
        Invalide tout le cache lié à un match.

        Utilisé quand un match passe de LIVE → FT.
        """

        # Pattern pour trouver toutes les clés du match
        pattern = f"{self.cache_prefix}*fixture*{fixture_id}*"

        # Scanner et supprimer
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
```

**Scénarios de cache** :

```python
# Scénario 1: 2 utilisateurs posent la même question

# Utilisateur 1 (10:00)
user1: "Quel est le score de PSG - Lyon ?"
→ Appel API fixtures?id=12345 (1 appel)
→ Mise en cache (TTL=30s si LIVE, infini si FT)

# Utilisateur 2 (10:00:10, 10 secondes plus tard)
user2: "Quel est le score de PSG - Lyon ?"
→ Lecture du cache (0 appel)
→ Réponse instantanée

# Économie: 1 appel API sauvegardé


# Scénario 2: Questions complémentaires sur le même match

# Utilisateur 1
user1: "Quel est le score de PSG - Lyon ?"
→ fixtures?id=12345 (1 appel)
→ Cache: fixtures_by_id (contient score, events, lineups, stats, players)

user1: "Combien de tirs cadrés pour le PSG ?"
→ Lecture du cache fixtures_by_id
→ Extraction de statistics.shots_on_target
→ 0 appel API supplémentaire

user1: "Qui a marqué ?"
→ Lecture du cache fixtures_by_id
→ Extraction de events (type=Goal)
→ 0 appel API supplémentaire

# Économie: 2 appels API sauvegardés


# Scénario 3: Match status change (LIVE → FT)

# 20:45 - Match en cours
user1: "Score de PSG - Lyon ?"
→ fixtures?id=12345 (status=LIVE)
→ Cache avec TTL=30s

# 20:50 - Match terminé
user2: "Score final de PSG - Lyon ?"
→ fixtures?id=12345 (status=FT)
→ Détection: status changé LIVE → FT
→ Invalidation du cache
→ Nouvel appel API
→ Cache avec TTL=infini (match terminé)

# Utilisateurs suivants auront le cache permanent
```

---

### 5. API Orchestrator

**Rôle** : Exécuter le plan d'appels de manière optimisée.

```python
# backend/agents/api_orchestrator.py

class APIOrchestrator:
    """
    Orchestre l'exécution des appels API selon un plan.

    Optimisations:
    - Exécution parallèle des appels indépendants
    - Gestion des dépendances (appels séquentiels)
    - Retry automatique en cas d'erreur
    - Circuit breaker
    """

    def __init__(
        self,
        api_client: FootballAPIClient,
        cache_manager: IntelligentCacheManager,
        circuit_breaker: CircuitBreaker
    ):
        self.api = api_client
        self.cache = cache_manager
        self.circuit_breaker = circuit_breaker

    async def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        """
        Exécute un plan d'appels API.

        Args:
            plan: Plan généré par Endpoint Planner

        Returns:
            ExecutionResult avec:
                - data: Dict (toutes les données collectées)
                - api_calls_made: int (nombre d'appels réels)
                - cache_hits: int
                - errors: List[str]
        """

        collected_data = {}
        api_calls_made = 0
        cache_hits = 0
        errors = []

        # Parcourir les appels dans l'ordre
        for call in plan.endpoints:
            try:
                # 1. Vérifier le cache d'abord
                cached = await self.cache.get(
                    call.endpoint.name,
                    call.params
                )

                if cached:
                    # Hit cache
                    collected_data[call.endpoint.name] = cached
                    cache_hits += 1
                    continue

                # 2. Résoudre les paramètres dynamiques
                resolved_params = self._resolve_params(call.params, collected_data)

                # 3. Appel API avec circuit breaker
                data = await self.circuit_breaker.call(
                    lambda: self._make_api_call(call.endpoint, resolved_params)
                )

                # 4. Stocker dans le cache
                await self.cache.set(
                    call.endpoint.name,
                    resolved_params,
                    data
                )

                # 5. Collecter les données
                collected_data[call.endpoint.name] = data
                api_calls_made += 1

            except Exception as e:
                errors.append(f"Error calling {call.endpoint.name}: {str(e)}")

        return ExecutionResult(
            data=collected_data,
            api_calls_made=api_calls_made,
            cache_hits=cache_hits,
            errors=errors
        )

    def _resolve_params(self, params: Dict, collected_data: Dict) -> Dict:
        """
        Résout les paramètres dynamiques.

        Example:
            params = {'team_id': '<from_search_team>'}
            collected_data = {'search_team': {'team': {'id': 85}}}
            → {'team_id': 85}
        """
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith('<from_'):
                # Paramètre dynamique
                source = value[6:-1]  # Extraire 'search_team'
                # Chercher dans collected_data
                resolved[key] = self._extract_value(collected_data.get(source), key)
            else:
                resolved[key] = value

        return resolved
```

---

### 6. Flux Complet - Exemple End-to-End

```
QUESTION: "Compare la forme du PSG et du Real Madrid avant leur match de mercredi"

┌─────────────────────────────────────────────────────────────────────┐
│ 1. QUESTION VALIDATOR                                                 │
└─────────────────────────────────────────────────────────────────────┘

  Extraction d'entités:
    - teams: ['PSG', 'Real Madrid']
    - time_frame: 'avant match de mercredi'
    - question_type: 'comparison' + 'form_analysis'

  Validation:
    ✅ Complet (2 équipes identifiées)

  → Passe au Endpoint Planner

┌─────────────────────────────────────────────────────────────────────┐
│ 2. ENDPOINT PLANNER                                                   │
└─────────────────────────────────────────────────────────────────────┘

  Consultation Knowledge Base:
    - Question: "forme récente équipes"
    - Endpoints candidats:
      * team_last_fixtures (forme récente)
      * team_statistics (stats saison)
      * predictions (si match existe → contient forme + comparaison)

  Vérification cache:
    - Cache check: predictions?fixture=X → NOT FOUND
    - Cache check: team_last_fixtures PSG → NOT FOUND
    - Cache check: team_last_fixtures Real → NOT FOUND

  Optimisation:
    - Question mentionne "leur match de mercredi"
    - → Implique qu'un match existe entre PSG et Real Madrid
    - → Utiliser predictions (1 appel) au lieu de team_last_fixtures (2 appels)

  Plan généré:
    1. search_team('PSG') → team_id
    2. search_team('Real Madrid') → team_id
    3. fixtures_search(team1=PSG, team2=Real, date≈mercredi) → fixture_id
    4. predictions(fixture_id) → forme + comparaison complète

  Coût estimé: 4 appels API

┌─────────────────────────────────────────────────────────────────────┐
│ 3. API ORCHESTRATOR                                                   │
└─────────────────────────────────────────────────────────────────────┘

  Exécution:

  [Parallèle]
    ├─ search_team('PSG')
    │   Cache check → MISS
    │   API call → team_id=85
    │   Cache set (TTL=∞)
    │
    └─ search_team('Real Madrid')
        Cache check → MISS
        API call → team_id=86
        Cache set (TTL=∞)

  [Séquentiel - dépend des team_ids]
    └─ fixtures_search(team1=85, team2=86, date=2025-12-13)
        Cache check → MISS
        API call → fixture_id=987654
        Cache set (TTL=10min)

  [Séquentiel - dépend du fixture_id]
    └─ predictions(fixture_id=987654)
        Cache check → MISS
        API call → {predictions, teams.last_5, h2h, comparison}
        Cache set (TTL=1 jour)

  Résultat:
    - 4 appels API effectués
    - 0 cache hit
    - Données collectées: predictions complètes

┌─────────────────────────────────────────────────────────────────────┐
│ 4. DATA SYNTHESIZER (Analysis + Response Agents)                     │
└─────────────────────────────────────────────────────────────────────┘

  Analyse des données predictions:
    - PSG last_5: WDWWW (80% de victoires)
    - Real last_5: LWDLW (40% de victoires)
    - Comparison: PSG 51.5% vs Real 48.5%

  Génération réponse:
    "Le PSG affiche une meilleure forme récente avec 80% de victoires
     sur ses 5 derniers matchs (4V, 1N), tandis que le Real Madrid
     est plus irrégulier avec seulement 40% de victoires (2V, 2N, 1D).

     L'analyse comparative donne un léger avantage au PSG (51.5% vs 48.5%)."

┌─────────────────────────────────────────────────────────────────────┐
│ 5. UTILISATEUR SUIVANT (10 minutes plus tard)                        │
└─────────────────────────────────────────────────────────────────────┘

QUESTION: "Qui est favori pour PSG - Real ?"

  Endpoint Planner:
    - Besoin de predictions pour fixture PSG-Real

  API Orchestrator:
    [Parallèle]
      ├─ search_team('PSG')
      │   Cache check → HIT (cached 10 min ago)
      │   0 appel API
      │
      └─ search_team('Real Madrid')
          Cache check → HIT
          0 appel API

    [Séquentiel]
      └─ fixtures_search(team1=85, team2=86)
          Cache check → HIT
          0 appel API

    [Séquentiel]
      └─ predictions(fixture_id=987654)
          Cache check → HIT (cached 10 min ago)
          0 appel API

  Résultat:
    - 0 appel API effectué
    - 4 cache hits
    - Réponse instantanée

  Économie: 4 appels API sauvegardés

┌─────────────────────────────────────────────────────────────────────┐
│ BILAN FINAL - 2 utilisateurs                                          │
└─────────────────────────────────────────────────────────────────────┘

  Total appels API: 4 (au lieu de 8 sans cache partagé)
  Économie: 50%

  Si 100 utilisateurs posent des questions similaires:
    - Avec système actuel (cache par session): 400 appels
    - Avec cache partagé intelligent: 4 appels
    - Économie: 99%
```

---

## 📊 Plan d'Implémentation Détaillé

### Phase 1 : Fondations (2-3 semaines)

#### Semaine 1 : Base de Connaissance + Cache Intelligent

**Tâches** :

1. ✅ Créer `EndpointKnowledgeBase` (backend/knowledge/endpoint_knowledge_base.py)
   - Documenter les 50+ endpoints
   - Définir use cases, paramètres, données retournées
   - Relations entre endpoints (enrichissement, remplacement)
   - Tests unitaires

2. ✅ Implémenter `IntelligentCacheManager` (backend/cache/intelligent_cache_manager.py)
   - Cache Redis partagé
   - Normalisation de clés
   - TTL adaptatif
   - Invalidation intelligente
   - Tests d'intégration

**Livrables** :
- 2 nouveaux modules testés
- Documentation API complète
- Tests coverage > 80%

**Métriques de succès** :
- Tous les endpoints documentés
- Cache hit rate > 70% en simulation

---

#### Semaine 2 : Question Validator + Endpoint Planner

**Tâches** :

1. ✅ Créer `QuestionValidator` (backend/agents/question_validator.py)
   - Extraction d'entités robuste (via LLM)
   - Classification de question
   - Détection d'informations manquantes
   - Génération de questions de clarification
   - Tests avec 100+ questions variées

2. ✅ Créer `EndpointPlanner` (backend/agents/endpoint_planner.py)
   - Identification endpoints candidats (sémantique + LLM)
   - Filtrage redondance
   - Optimisation avec endpoints enrichis
   - Résolution dépendances
   - Tests d'optimisation

**Livrables** :
- 2 nouveaux agents
- Prompt engineering optimisé
- Suite de tests exhaustive

**Métriques de succès** :
- Validation correcte : > 95%
- Plans optimaux générés : > 90%
- Réduction appels API : > 50%

---

#### Semaine 3 : API Orchestrator + Intégration

**Tâches** :

1. ✅ Créer `APIOrchestrator` (backend/agents/api_orchestrator.py)
   - Exécution de plans
   - Parallélisation appels indépendants
   - Résolution params dynamiques
   - Gestion erreurs + retry
   - Tests d'intégration

2. ✅ Intégrer dans le pipeline existant
   - Modifier `LucidePipeline` pour utiliser nouveaux agents
   - Feature flag pour basculer ancien/nouveau système
   - Tests end-to-end

**Livrables** :
- API Orchestrator fonctionnel
- Pipeline intégré avec feature flag
- Tests E2E

**Métriques de succès** :
- Exécution parallèle fonctionnelle
- Pas de régression sur anciens tests
- Feature flag opérationnel

---

### Phase 2 : Déploiement Progressif (2 semaines)

#### Semaine 4 : Tests en Production (10% trafic)

**Tâches** :

1. ✅ Déploiement avec feature flag OFF par défaut
2. ✅ Activation pour 10% du trafic aléatoire
3. ✅ Monitoring intensif:
   - Logs de tous les plans générés
   - Métriques: API calls, cache hits, erreurs
   - Comparaison avec ancien système
4. ✅ Ajustements si nécessaire

**Métriques à surveiller** :
```python
METRICS = {
    'api_calls_per_question': {
        'target': '< 0.5',
        'alert_if': '> 1.0'
    },
    'cache_hit_rate': {
        'target': '> 70%',
        'alert_if': '< 50%'
    },
    'question_validation_success': {
        'target': '> 95%',
        'alert_if': '< 90%'
    },
    'endpoint_plan_quality': {
        'target': '> 90%',  # Plans jugés optimaux
        'alert_if': '< 80%'
    },
    'response_time_p95': {
        'target': '< 2s',
        'alert_if': '> 5s'
    }
}
```

---

#### Semaine 5 : Montée en Charge (50% → 100%)

**Tâches** :

1. ✅ Analyse des résultats 10%
2. ✅ Corrections/optimisations identifiées
3. ✅ Passage à 50% du trafic
4. ✅ Monitoring 24h
5. ✅ Passage à 100% si OK
6. ✅ Désactivation feature flag (nouveau système par défaut)

**Rollback Plan** :
```python
# Si métriques critiques en rouge
if cache_hit_rate < 50% or response_time_p95 > 5s:
    # Rollback immédiat à ancien système
    FEATURE_FLAG_AUTONOMOUS_AGENTS = False

    # Investigation
    analyze_logs()
    identify_issues()

    # Fix + re-déploiement
```

---

### Phase 3 : Optimisations Avancées (3-4 semaines)

#### Semaine 6-7 : Amélioration Intelligence

**Tâches** :

1. ✅ Fine-tuning des prompts LLM
   - Optimiser prompts Question Validator
   - Optimiser prompts Endpoint Planner
   - A/B testing de variants

2. ✅ Embeddings pour recherche sémantique
   - Générer embeddings des use cases
   - Recherche vectorielle dans knowledge base
   - Accélération + précision

3. ✅ Apprentissage des patterns
   - Logger tous les plans générés
   - Analyser les patterns fréquents
   - Pré-calculer plans pour questions courantes

**Livrables** :
- Prompts optimisés (meilleure précision)
- Recherche vectorielle opérationnelle
- Base de plans pré-calculés

---

#### Semaine 8-9 : Cache Prédictif

**Tâches** :

1. ✅ Analyser patterns de questions
   - Questions fréquentes par contexte
   - Séquences de questions typiques

2. ✅ Pré-chargement intelligent
   - Si user demande score → pré-charger events
   - Si user demande prédiction → pré-charger injuries

3. ✅ Cache warming
   - Identifier matchs populaires
   - Pré-charger fixtures+predictions pour matchs du jour

**Livrables** :
- Système de cache prédictif
- Réduction latence -30%

---

## 📈 Métriques et Monitoring

### Dashboard de Monitoring

```python
# backend/monitoring/autonomous_agents_metrics.py

class AutonomousAgentsMetrics:
    """
    Collecte et expose les métriques du système d'agents autonomes.
    """

    # Métriques Question Validator
    validation_success_rate = Counter('question_validation_success_total')
    validation_failure_rate = Counter('question_validation_failure_total')
    clarification_requests = Counter('clarification_requests_total')

    # Métriques Endpoint Planner
    plans_generated = Counter('endpoint_plans_generated_total')
    api_calls_in_plan = Histogram('api_calls_per_plan')
    plan_optimization_ratio = Gauge('plan_optimization_ratio')  # Appels évités / Total

    # Métriques API Orchestrator
    api_calls_executed = Counter('api_calls_executed_total')
    cache_hits = Counter('cache_hits_total')
    cache_misses = Counter('cache_misses_total')
    api_call_duration = Histogram('api_call_duration_seconds')

    # Métriques Cache
    cache_size_bytes = Gauge('cache_size_bytes')
    cache_evictions = Counter('cache_evictions_total')
    cache_ttl_by_endpoint = Histogram('cache_ttl_seconds', ['endpoint'])

    # Métriques Business
    cost_savings_euro = Counter('cost_savings_euro')  # Économies grâce au cache
    user_satisfaction = Gauge('user_satisfaction_score')  # Via feedback
```

---

## 🎉 Conclusion

Cette architecture permet de créer des agents **vraiment autonomes** qui :

1. ✅ **Connaissent tous les endpoints** (50+) via la Knowledge Base
2. ✅ **Comprennent les use cases** et peuvent raisonner dessus
3. ✅ **Décident intelligemment** quels endpoints appeler via le Planner
4. ✅ **Demandent des clarifications** quand nécessaire via le Validator
5. ✅ **Optimisent automatiquement** les appels via cache intelligent

### Gains Attendus

**Performance** :
- ⚡ **-60-80% d'appels API** (grâce à cache partagé + endpoints enrichis)
- ⚡ **-50% de latence** (réponses instantanées pour questions fréquentes)
- ⚡ **10x plus d'utilisateurs** supportés avec même quota API

**Qualité** :
- 🎯 **100% des endpoints exploités** (vs 30% actuellement)
- 🎯 **Validation des questions** (pas de réponses approximatives)
- 🎯 **Plans optimaux** (minimum d'appels pour maximum d'info)

**Maintenance** :
- 🔧 **Extensibilité** : Ajouter un endpoint = 1 entrée dans Knowledge Base
- 🔧 **Pas de guidance manuelle** : LLM raisonne sur use cases
- 🔧 **Monitoring complet** : Métriques détaillées sur chaque composant

### Prochaines Étapes

1. **Validation utilisateur** : Valider l'architecture avec l'équipe
2. **Priorisation** : Décider quelles phases implémenter en premier
3. **Démarrage** : Lancer Phase 1 (Fondations)

---

**Auteur** : Claude Code
**Date** : 11 décembre 2025
**Version** : 1.0
**Status** : Proposition d'architecture
