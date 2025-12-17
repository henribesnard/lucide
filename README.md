# LUCIDE - Assistant Intelligent d'Analyse Football

Assistant IA conversationnel pour l'analyse football propulsé par DeepSeek et API-Football.

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [API Endpoints](#api-endpoints)
- [Système d'agents autonomes](#système-dagents-autonomes)
- [Sécurité](#sécurité)
- [Tests](#tests)
- [Développement](#développement)

---

## Vue d'ensemble

LUCIDE est un assistant conversationnel intelligent spécialisé dans l'analyse football. Il utilise :
- **DeepSeek** ou **OpenAI** pour le traitement du langage naturel et la génération de réponses
- **API-Football** pour accéder aux données en temps réel (matchs, statistiques, classements)
- **Agents autonomes** pour orchestrer automatiquement les requêtes API nécessaires

### Fonctionnalités principales

- Chat conversationnel avec compréhension contextuelle
- Classification automatique des intentions utilisateur
- Orchestration intelligente d'appels API multiples
- Système de contexte dynamique (match, ligue)
- Authentification JWT avec gestion d'utilisateurs
- Cache intelligent Redis pour optimiser les performances
- Protection contre les surcharges avec circuit breakers
- Support multi-langues (FR/EN)

---

## Architecture

### Architecture globale

```
┌─────────────────┐
│   Frontend      │
│   (Next.js)     │
└────────┬────────┘
         │ HTTP/REST
         ↓
┌─────────────────────────────────────────────┐
│           LUCIDE Backend (FastAPI)          │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  API Layer                           │  │
│  │  - Auth (JWT)                        │  │
│  │  - Chat endpoint                     │  │
│  │  - Conversations                     │  │
│  │  - Context management                │  │
│  └──────────┬───────────────────────────┘  │
│             ↓                               │
│  ┌──────────────────────────────────────┐  │
│  │  Agent System (Autonomous Pipeline)  │  │
│  │  - Question Validator                │  │
│  │  - Endpoint Planner                  │  │
│  │  - API Orchestrator                  │  │
│  └──────────┬───────────────────────────┘  │
│             ↓                               │
│  ┌──────────────────────────────────────┐  │
│  │  LLM Layer                           │  │
│  │  - DeepSeek / OpenAI                 │  │
│  │  - Function calling                  │  │
│  │  - Intent classification             │  │
│  └──────────────────────────────────────┘  │
│                                             │
└────┬────────────────────────────────┬──────┘
     │                                │
     ↓                                ↓
┌─────────────┐              ┌─────────────────┐
│  PostgreSQL │              │  API-Football   │
│  - Users    │              │  - Fixtures     │
│  - Convos   │              │  - Standings    │
│  - Messages │              │  - Statistics   │
└─────────────┘              └─────────────────┘
     ↑
     │
┌─────────────┐
│   Redis     │
│  - Cache    │
│  - Contexts │
│  - Locks    │
└─────────────┘
```

### Pipeline de traitement d'une question

```
User Question
     │
     ↓
┌────────────────────┐
│ Question Validator │ ← Vérifie si question complète
│ - Extract entities │   (équipes, dates, ligues...)
│ - Classify intent  │   Si manque info → demande clarification
│ - Check complete   │
└────────┬───────────┘
         │ Entities + Intent
         ↓
┌────────────────────┐
│ Endpoint Planner   │ ← Décide quels endpoints API appeler
│ - Map to endpoints │   et dans quel ordre
│ - Optimize calls   │
│ - Build exec plan  │
└────────┬───────────┘
         │ Execution Plan
         ↓
┌────────────────────┐
│ API Orchestrator   │ ← Exécute le plan
│ - Parallel calls   │   - Appels parallèles
│ - Cache lookups    │   - Cache Redis
│ - Circuit breaker  │   - Protection surcharge
│ - Retry logic      │   - Retry automatique
└────────┬───────────┘
         │ Raw Data
         ↓
┌────────────────────┐
│ LLM Analysis       │ ← Génère réponse en langage naturel
│ - Analyze data     │
│ - Generate answer  │
│ - Format response  │
└────────┬───────────┘
         │
         ↓
    User Response
```

---

## Stack technique

### Backend

| Composant | Technologie | Version | Usage |
|-----------|-------------|---------|-------|
| **Framework** | FastAPI | 0.109.0 | API REST moderne et performant |
| **Runtime** | Python | 3.10+ | Langage principal |
| **Server** | Uvicorn | 0.27.0 | Serveur ASGI haute performance |
| **Database** | PostgreSQL | 14+ | Base de données relationnelle |
| **ORM** | SQLAlchemy | 2.0.25 | Mapping objet-relationnel |
| **Cache** | Redis | 7+ | Cache distribué et gestion contexte |
| **Auth** | JWT | - | Authentification stateless |
| **LLM** | DeepSeek/OpenAI | - | Génération texte et function calling |
| **External API** | API-Football | v3 | Données football temps réel |

### Librairies principales

```
fastapi==0.109.0           # Framework web
uvicorn[standard]==0.27.0  # Serveur ASGI
pydantic==2.6.0            # Validation données
sqlalchemy==2.0.25         # ORM
redis==5.0.1               # Client Redis
openai==1.12.0             # Client LLM
httpx==0.26.0              # HTTP client async
structlog==24.1.0          # Logging structuré
```

---

## Installation

### Prérequis

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optionnel)

### Installation locale

1. **Cloner le repository**

```bash
git clone <repository-url>
cd lucide
```

2. **Créer environnement virtuel**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Installer dépendances**

```bash
pip install -r requirements.txt
```

4. **Configuration base de données**

```bash
# Créer base de données PostgreSQL
createdb lucide

# Exécuter migrations
alembic upgrade head
```

5. **Lancer Redis**

```bash
# Via Docker
docker run -d -p 6379:6379 redis:7-alpine

# Ou installer localement
redis-server
```

### Installation Docker

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f backend
```

---

## Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine :

```env
# LLM Configuration
LLM_PROVIDER=deepseek              # ou "openai"
DEEPSEEK_API_KEY=sk-xxx            # Clé API DeepSeek
DEEPSEEK_MODEL=deepseek-chat       # Modèle DeepSeek
OPENAI_API_KEY=sk-xxx              # Clé API OpenAI (optionnel)
OPENAI_MODEL=gpt-4o-mini           # Modèle OpenAI (optionnel)

# API-Football
FOOTBALL_API_KEY=your_api_key      # Clé API-Football (requis)
FOOTBALL_API_BASE_URL=https://v3.football.api-sports.io

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/lucide

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here    # Pour JWT (générer aléatoirement)
ALGORITHM=HS256

# App
DEBUG=False
LOG_LEVEL=INFO
FRONTEND_URL=http://localhost:3000
```

### Générer SECRET_KEY

```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## Utilisation

### Démarrer le serveur

```bash
# Mode développement (avec reload)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001

# Mode production
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### API Documentation

Une fois le serveur lancé :
- **Swagger UI** : http://localhost:8001/docs
- **ReDoc** : http://localhost:8001/redoc

### Exemples d'utilisation

#### 1. Créer un compte

```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### 2. Se connecter

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password"
  }'

# Retourne:
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": { ... }
}
```

#### 3. Envoyer un message au chat

```bash
TOKEN="eyJhbGci..."

curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "Quel est le classement de la Ligue 1 ?"
  }'

# Retourne:
{
  "response": "Voici le classement actuel de la Ligue 1...",
  "session_id": "user_123",
  "intent": "standings",
  "entities": {
    "leagues": ["Ligue 1"]
  },
  "tools": ["get_standings"]
}
```

---

## Structure du projet

```
lucide/
├── backend/
│   ├── agents/                    # Système d'agents autonomes
│   │   ├── autonomous_pipeline.py # Pipeline principal
│   │   ├── question_validator.py  # Validation questions
│   │   ├── endpoint_planner.py    # Planification endpoints
│   │   ├── api_orchestrator.py    # Orchestration appels API
│   │   ├── context_types.py       # Types pour contexte structuré
│   │   ├── competition_classification.py  # Classification compétitions
│   │   └── zone_resolver.py       # Résolution zones géographiques
│   │
│   ├── api/
│   │   └── football_api.py        # Client API-Football
│   │
│   ├── auth/                      # Authentification & autorisation
│   │   ├── router.py              # Endpoints auth
│   │   ├── dependencies.py        # Dépendances (get_current_user)
│   │   ├── security.py            # Hashing, JWT
│   │   └── email_service.py       # Envoi emails
│   │
│   ├── conversations/             # Gestion conversations
│   │   ├── router.py              # CRUD conversations
│   │   └── schemas.py             # Modèles Pydantic
│   │
│   ├── context/                   # Système de contexte dynamique
│   │   ├── context_manager.py     # Gestionnaire contextes
│   │   ├── intent_classifier.py   # Classification intentions
│   │   ├── context_types.py       # Types de contexte
│   │   └── circuit_breaker.py     # Circuit breakers
│   │
│   ├── db/                        # Base de données
│   │   ├── database.py            # Session DB
│   │   ├── models.py              # Modèles SQLAlchemy
│   │   └── migrations/            # Alembic migrations
│   │
│   ├── llm/                       # Couche LLM
│   │   ├── llm_client.py          # Client unifié DeepSeek/OpenAI
│   │   └── tools.py               # Définition tools pour function calling
│   │
│   ├── knowledge/                 # Base de connaissance
│   │   └── endpoint_knowledge_base.py  # Connaissance endpoints API-Football
│   │
│   ├── cache/                     # Système de cache
│   │   └── intelligent_cache.py   # Cache intelligent avec TTL adaptatif
│   │
│   ├── monitoring/                # Monitoring & métriques
│   │   └── autonomous_agents_metrics.py
│   │
│   ├── config.py                  # Configuration app
│   └── main.py                    # Point d'entrée FastAPI
│
├── tests/                         # Tests
│   ├── test_autonomous_pipeline_context.py
│   └── test_security_endpoints.py
│
├── docker-compose.yml             # Config Docker
├── requirements.txt               # Dépendances Python
├── alembic.ini                    # Config migrations
└── README.md                      # Ce fichier
```

---

## API Endpoints

### Authentification (`/auth`)

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/auth/register` | POST | Non | Créer un compte |
| `/auth/login` | POST | Non | Se connecter (retourne JWT) |
| `/auth/verify-email` | POST | Non | Vérifier email avec token |

### Chat (`/chat`)

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/chat` | POST | Oui | Envoyer un message au chat |
| `/session/{id}` | DELETE | Oui | Supprimer une session (owner only) |

### Conversations (`/conversations`)

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/conversations` | GET | Oui | Lister toutes les conversations |
| `/conversations` | POST | Oui | Créer une conversation |
| `/conversations/{id}` | GET | Oui | Récupérer une conversation |
| `/conversations/{id}` | PATCH | Oui | Modifier une conversation |
| `/conversations/{id}` | DELETE | Oui | Supprimer une conversation (soft delete) |

### Données (`/api`)

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/api/countries` | GET | Oui | Liste des pays disponibles |
| `/api/leagues` | GET | Oui | Liste des ligues (filtrable par pays) |
| `/api/fixtures` | GET | Oui | Matchs (filtrable par ligue/date) |

### Contexte (`/api/context`)

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/api/context/match/{fixture_id}` | GET | Oui | Contexte d'un match spécifique |
| `/api/context/league/{league_id}` | GET | Oui | Contexte d'une ligue |
| `/api/contexts` | GET | Oui | Liste des contextes actifs |
| `/api/context/stats` | GET | Admin | Statistiques du système de contexte |

### Monitoring (`/api`)

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/api/health` | GET | Non | Health check système |
| `/api/circuit-breakers` | GET | Admin | État des circuit breakers |
| `/api/circuit-breakers/reset` | POST | Admin | Reset circuit breakers |
| `/api/locks` | GET | Admin | Liste des locks distribués |
| `/api/locks/{resource}` | GET | Admin | Info sur un lock spécifique |
| `/api/locks/{resource}` | DELETE | Admin | Forcer libération d'un lock |

---

## Système d'agents autonomes

### Vue d'ensemble

Le système d'agents autonomes permet de traiter automatiquement les questions utilisateur sans intervention manuelle. Il se compose de 3 agents principaux qui travaillent en pipeline.

### Architecture des agents

```
┌─────────────────────┐
│ QuestionValidator   │
│                     │
│ Rôle:               │
│ - Extraire entités  │
│ - Classer type Q    │
│ - Vérifier complét. │
│                     │
│ Input: Question     │
│ Output: Entities +  │
│         Intent +    │
│         Missing[]   │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│ EndpointPlanner     │
│                     │
│ Rôle:               │
│ - Mapper intent →   │
│   endpoints         │
│ - Optimiser ordre   │
│ - Parallélisation   │
│                     │
│ Input: Intent +     │
│        Entities     │
│ Output: Plan        │
│         d'exécution │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│ APIOrchestrator     │
│                     │
│ Rôle:               │
│ - Exécuter plan     │
│ - Cache Redis       │
│ - Circuit breaker   │
│ - Retry logic       │
│                     │
│ Input: Plan         │
│ Output: Data        │
└─────────────────────┘
```

### 1. QuestionValidator

**Responsabilité** : Analyser et valider la question utilisateur

**Fonctionnalités** :
- Extraction d'entités (équipes, joueurs, dates, ligues)
- Classification du type de question (classement, stats, H2H, etc.)
- Détection de langue (FR/EN)
- Vérification de complétude
- Génération de questions de clarification si nécessaire

**Exemple** :
```python
# Question: "Quel est le classement ?"
# → Missing: leagues
# → Clarification: "Quelle ligue ou compétition vous intéresse ?"

# Question: "Quel est le classement de la Ligue 1 ?"
# → Complete: True
# → Entities: {"leagues": ["Ligue 1"]}
# → QuestionType: STANDINGS
```

### 2. EndpointPlanner

**Responsabilité** : Planifier les appels API nécessaires

**Fonctionnalités** :
- Mapping intent → endpoints API-Football
- Résolution des dépendances entre endpoints
- Optimisation de l'ordre d'exécution
- Détection des opportunités de parallélisation

**Exemple** :
```python
# Intent: TEAM_COMPARISON
# Entities: {"teams": ["PSG", "OM"]}
#
# Plan généré:
# 1. get_teams (parallel)
#    - search "PSG"
#    - search "OM"
# 2. get_team_statistics (parallel)
#    - team_id=PSG_id, league=61, season=2024
#    - team_id=OM_id, league=61, season=2024
```

### 3. APIOrchestrator

**Responsabilité** : Exécuter le plan avec résilience

**Fonctionnalités** :
- Exécution parallèle des appels indépendants
- Cache Redis intelligent (TTL adaptatif)
- Circuit breaker (protection surcharge)
- Retry automatique avec backoff exponentiel
- Métriques détaillées

**Cache TTL par endpoint** :
```python
CACHE_TTL = {
    "fixtures_live": 30,          # 30 secondes (live)
    "fixtures_upcoming": 3600,    # 1 heure
    "fixtures_finished": 86400,   # 24 heures
    "standings": 3600,            # 1 heure
    "team_statistics": 7200,      # 2 heures
}
```

### Système de contexte structuré

Le système supporte un contexte hiérarchique pour éviter les clarifications :

```python
# Niveau 1: Zone (pays ou région)
context = StructuredContext(
    zone=Zone(name="France", code="FR")
)

# Niveau 2: Zone + Ligue
context = StructuredContext(
    zone=Zone(name="France", code="FR"),
    league="Ligue 1",
    league_id=61
)

# Niveau 3: Zone + Ligue + Match
context = StructuredContext(
    zone=Zone(name="France", code="FR"),
    league="Ligue 1",
    fixture="PSG vs OM",
    fixture_id=12345
)
```

**Règle** : Le contexte a **priorité** sur les entités extraites de la question.

---

## Sécurité

### Authentification JWT

Tous les endpoints sensibles nécessitent un token JWT valide :

```python
# Dépendances FastAPI
from backend.auth.dependencies import (
    get_current_user,        # User authentifié
    get_current_admin_user   # User admin/superuser
)

# Utilisation
@app.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    # Seulement les users authentifiés peuvent accéder
    ...
```

### Niveaux de protection

| Niveau | Dépendance | Description |
|--------|------------|-------------|
| **Public** | Aucune | Health checks, auth endpoints |
| **User** | `get_current_user` | Utilisateurs authentifiés |
| **Admin** | `get_current_admin_user` | Superusers seulement |

### Isolation des données

- Chaque utilisateur a sa propre session de chat (`user_{user_id}`)
- Les conversations sont isolées par `user_id`
- Ownership check avant suppression de ressources

### Rate limiting (TODO)

```python
# Futur: Rate limiting par user
@limiter.limit("30/minute")
@app.post("/chat")
async def chat(...):
    ...
```

### Quotas par tier (TODO)

```python
# Futur: Quotas selon subscription
SubscriptionTier.FREE:  50 messages/jour
SubscriptionTier.BASIC: 500 messages/jour
SubscriptionTier.PRO:   Illimité
```

---

## Tests

### Exécuter les tests

```bash
# Tous les tests
pytest

# Tests spécifiques
pytest tests/test_autonomous_pipeline_context.py
pytest tests/test_security_endpoints.py

# Avec coverage
pytest --cov=backend --cov-report=html
```

### Tests de sécurité

Vérifier que les endpoints sont protégés :

```bash
# Le serveur doit être lancé
python test_security_endpoints.py

# Résultat attendu: 100% pass rate
```

### Tests du contexte structuré

```bash
python test_autonomous_pipeline_context.py

# Vérifie:
# - Question vague sans contexte → demande clarification
# - Question vague avec contexte → succès
# - Contexte override question → contexte a priorité
```

---

## Développement

### Workflow de développement

1. **Créer une branche**
```bash
git checkout -b feature/my-feature
```

2. **Faire les modifications**
```python
# Code...
```

3. **Lancer les tests**
```bash
pytest
```

4. **Commit & push**
```bash
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
```

5. **Créer Pull Request**

### Conventions de code

- **Format** : Black (line length 100)
- **Imports** : isort
- **Type hints** : mypy
- **Docstrings** : Google style

```python
def my_function(param: str) -> dict:
    """
    Short description.

    Args:
        param: Description

    Returns:
        Description

    Examples:
        >>> my_function("test")
        {"result": "test"}
    """
    return {"result": param}
```

### Migrations base de données

```bash
# Créer migration
alembic revision --autogenerate -m "Add new column"

# Appliquer migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Debugging

Activer debug mode :

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

Logs structurés disponibles via structlog :

```python
logger.info(
    "pipeline_execution",
    user_id=user.user_id,
    question=question,
    duration_ms=123
)
```

---

## Monitoring

### Health checks

```bash
# Basic health
curl http://localhost:8001/health

# Detailed health avec circuit breakers
curl http://localhost:8001/api/health
```

### Métriques disponibles

- **Cache hit rate** : Taux de succès du cache Redis
- **Circuit breakers** : État des protections
- **API calls** : Nombre d'appels API-Football
- **Response times** : Temps de réponse par endpoint

### Logs

Les logs sont au format JSON structuré pour faciliter l'analyse :

```json
{
  "event": "pipeline_execution_complete",
  "user_id": "123",
  "question": "Classement Ligue 1",
  "duration_ms": 1234,
  "cache_hit_rate": 0.75,
  "api_calls": 2,
  "timestamp": "2025-12-17T10:30:00Z"
}
```

---

## License

Propriétaire - Tous droits réservés

---

## Support

Pour toute question ou problème :
- Créer une issue sur GitHub
- Contact : [email]

---

**Version** : 2.0.0
**Dernière mise à jour** : 2025-12-17
