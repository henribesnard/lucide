# Plan de complétion backend Lucide (API-Football)

Ce plan synthétise les tâches à réaliser pour couvrir l’intégralité des use cases et garantir la robustesse du backend. Les docs produit/tech (Spécification produit Lucide, Guide technique API-Football) ne sont pas présents dans le repo ; la liste ci-dessous s’appuie sur `INTENTS.md`, `API_FOOTBALL_USE_CASES.md`, `API_FOOTBALL_RESPONSES.md` et le code actuel.

## 1) Couverture fonctionnelle / Tools
- Vérifier que chaque intent du catalogue est mappé à un tool : tops cartons, référentiels (countries/leagues/timezones), fixtures avancés (from/to/round/live/next/last), détails de match (events/lineups/statistics/players), profils/teams/squads, coachs, venues, transfers, trophies, sidelined, odds/predictions.
- Ajouter les outils manquants si des use cases du produit ne sont pas couverts (ex : odds live, bookmakers/bets/mapping, statut API).
- Compléter les summarizers pour normaliser les champs clés (id, noms, date, status, scores, pourcentages, etc.) et limiter la taille des réponses.

## 2) Routage des intentions
- Mettre à jour le prompt d’intent pour inclure l’ensemble des nouvelles intentions et entités attendues (référentiels, calendriers avancés, détails de match, tops cartons, indisponibilités).
- Définir les règles de désambiguïsation (ligue floue -> mapping, équipe/joueur -> search_*).
- Documenter les valeurs par défaut (saison en cours, date = aujourd’hui, statut accepté via `match_status.txt`, timezone).
- Ajouter des tests d’intent parsing (JSON strict) sur des scénarios réels.

## 3) Logique ToolAgent
- Prioriser l’utilisation de `fixtures_search` pour les calendriers avancés, et chaîner les détails de match (events/lineups/stats/players) quand l’intention le requiert.
- Gérer les filtres optionnels (from/to, round, status, timezone) et la récupération des prochaines/dernières rencontres avant d’appeler predictions/odds.
- Prévoir un fallback quand l’API renvoie zéro résultat (note factuelle + guidance utilisateur).

## 4) API client / Paramètres
- Vérifier tous les paramètres exposés par API-Football (codes pays, type=league/cup, current, search, last, bookmaker/bet ids, pagination joueurs).
- Gérer la pagination des endpoints joueurs (25 résultats/page) et propager les tokens `paging` dans les réponses tools si nécessaire.
- Normaliser les statuts de match via `match_status.txt` (short/long/type) pour filtrage et affichage.

## 5) Sécurité / Résilience
- Centraliser la gestion d’erreurs API (codes HTTP, erreurs API-Football, timeouts) avec messages clairs vers l’assistant.
- Ajouter un rate-limit basique (sleep/backoff ou compteur) pour éviter le dépassement de quota.
- Valider les inputs utilisateur (dates, entiers, status autorisés) avant appel API.

## 6) Observabilité
- [x] Journaliser les appels tools (nom, args filtrés, durée, statut).
- Ajouter des métriques simples (compteur d’appels par endpoint, erreurs, temps de réponse) si une stack de monitoring est prévue.

## 7) Performance / Coût
- Réduire la taille des payloads renvoyés à l’LLM (summaries, tronquer listes longues, limiter bookmakers/bets).
- [x] Mettre en cache les référentiels peu volatils (countries, leagues current, timezones, match_status) en mémoire ou via un TTL (caches ajoutés pour timezones, saisons, countries, team_countries).

## 8) Qualité / Tests
- Tests unitaires : client API (construction params), summarizers, mapping ligue, parsers de statuts.
- Tests d’intégration simulés : scénarios complets (calendrier date + ligue, analyse_rencontre -> predictions+odds+head_to_head, stats_joueur avec saison, tops cartons).
- Contrôler la validité JSON des sorties agents (intent, analysis, answer) avec cas d’erreur.

## 9) Configuration / Secrets
- Valider la lecture de la clé API via `.env` et désactiver tout log contenant la clé.
- Offrir une configuration pour la saison courante par défaut (variable d’environnement ou calcul automatique via `/leagues?current=true`).

## 10) Documentation & UX
- Documenter pour chaque intent : entités requises/optionnelles, tool(s) invoqués, valeurs par défaut, messages de fallback (données manquantes, saison indisponible, quota atteint).
- Ajouter un tableau de correspondance ligues {nom -> id} maintenable (cache ou fichier).
- Fournir un guide rapide pour les statuts (NS/FT/LIVE...) issu de `match_status.txt`.

## 11) Pipeline et réponses
- S’assurer que l’agent analyste/answer filtre bien sur les données disponibles sans inventer, et rappelle les limites (pronostics non garantis).
- Prévoir la gestion des “gaps” (entités manquantes) pour relancer une question de clarification si besoin.

## 12) Livraison
- Vérifier que `backend/agents/pipeline.py` orchestre toutes les intentions (routing complet vers ToolAgent).
- [x] Mettre à jour le README avec la liste des tools, des intentions supportées et les prérequis (Python, clé API) + lancement Docker (`docker compose up --build`).
- Ajouter docker-compose et vérifier le démarrage du conteneur avec le fichier `.env` fourni.
