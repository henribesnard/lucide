# Lucide - backend (DeepSeek function calling)

Backend minimal (FastAPI) centre sur le workflow function calling DeepSeek + API-Football. Tout le code est dans `backend/`.

## Installation rapide

```bash
pip install -r requirements.txt
```

## Configuration (.env)

Renseigne les variables suivantes dans `.env` (garde uniquement les valeurs, sans les partager):

```
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=ta_cle
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

FOOTBALL_API_KEY=ta_cle_api_football
FOOTBALL_API_BASE_URL=https://v3.football.api-sports.io

DEBUG=true
LOG_LEVEL=INFO
```

## Lancer l'API

```bash
uvicorn backend.main:app --reload
```

## Lancer via Docker

```bash
# Assure-toi d'avoir un .env avec les clés LLM et API-Football
docker compose up --build
# L'API sera disponible sur http://localhost:5000
```

Endpoints utiles :
- `GET /health` : verifie la configuration LLM
- `POST /chat` : payload `{ "message": "...", "session_id": "optionnel" }`

## Frontend (statique)
- Ouvre `frontend/index.html` dans un navigateur (le frontend cible `http://localhost:5000/chat` par défaut).
- Le frontend est responsive et peut être packagé en webview (Android/iOS). Il maintient la `session_id` en localStorage et affiche l’intention, les tools et les entités renvoyées par l’API.

La reponse du `/chat` expose aussi l'intention detectee, les entites extraites et les tools utilises (pour debug).

## Pipeline agentique

- **IntentAgent** : classe `backend/agents/intent_agent.py`. Extrait intention + entites en JSON strict.
- **ToolAgent** : classe `backend/agents/tool_agent.py`. Utilise la function calling DeepSeek avec les tools definis dans `backend/tools/football.py`.
- **AnalysisAgent** : classe `backend/agents/analysis_agent.py`. Compacte les resultats et produit un resume structure.
- **ResponseAgent** : classe `backend/agents/response_agent.py`. Genere la reponse finale (pas de garantie de resultat de match).
- **LucidePipeline** : orchestration complete dans `backend/agents/pipeline.py`.

Les prompts centraux sont regroupes dans `backend/prompts.py`.

## Tools exposes a l'agent

Outils principaux relies a l'API-Football (voir `backend/tools/football.py`) :
- `search_team`, `search_player`
- `fixtures_by_date`, `team_next_fixtures`, `live_fixtures`
- `standings`, `team_statistics`, `head_to_head`
- `top_scorers`, `top_assists`
- `injuries`
- `predictions`
- `odds_by_date`, `odds_by_fixture`

Chaque tool renvoie des structures compactes pour limiter le contexte envoye au LLM.

## Notes

- Le projet est volontairement epure: cache/mocks/frontends/docs historiques supprimes pour repartir de zero.
- Aucune reponse ne doit promettre un resultat de match; rappeler l'incertitude fait partie du prompt final.
