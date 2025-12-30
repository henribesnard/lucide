# Guide Développeur - Bot Telegram Lucide

**Dernière mise à jour**: 2025-12-30
**Auteur**: Henri Besnard
**Instance AWS**: i-01b89758e2a71f232 (lucide-bot)
**IP Fixe**: 52.16.82.16

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Infrastructure AWS](#infrastructure-aws)
3. [Gestion du Bot](#gestion-du-bot)
4. [Architecture du Code](#architecture-du-code)
5. [Fonctionnalités Attendues](#fonctionnalités-attendues)
6. [Limitations Telegram](#limitations-telegram)
7. [Développement Local](#développement-local)
8. [Déploiement](#déploiement)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Vue d'ensemble

Le bot Telegram Lucide permet aux utilisateurs d'obtenir des analyses de matchs de football via Telegram. Il utilise:
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Bot Framework**: python-telegram-bot v20.7
- **Cache**: Redis
- **Déploiement**: Docker Compose sur AWS EC2

**Token du bot**: `YOUR_TELEGRAM_BOT_TOKEN`
**Nom du bot**: `@Besnard_lucide_test_bot`

---

## ☁️ Infrastructure AWS

### Instance EC2

- **ID**: i-01b89758e2a71f232
- **Nom**: lucide-bot
- **Type**: t3.small (2 vCPU, 2 GB RAM)
- **Région**: eu-west-1 (Irlande)
- **AMI**: Amazon Linux 2023
- **Stockage**: 30 GB gp3 SSD
- **IP Élastique**: 52.16.82.16 (eipalloc-066664f42e98600d0)

### Security Group

- **ID**: sg-0be48bf8b433e72e8
- **Nom**: lucide-bot-sg
- **Ports ouverts**:
  - 22 (SSH)
  - 80 (HTTP)
  - 443 (HTTPS)
  - 8000 (Backend API - dev uniquement)

### Connexion SSH

```bash
# Clé SSH
~/.ssh/lucide-key-2025.pem

# Se connecter
ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@52.16.82.16

# Vérifier l'état de l'instance
aws ec2 describe-instances --instance-ids i-01b89758e2a71f232 --region eu-west-1
```

### Services Docker

Tous les services tournent via Docker Compose:

```bash
cd /opt/lucide/lucide/infrastructure/aws

# Fichier de configuration
docker-compose.aws-minimal.yml
```

**Services déployés**:
1. **postgres** (lucide_postgres) - Port 5432
2. **redis** (lucide_redis) - Port 6379
3. **backend** (lucide_backend) - Port 8000
4. **telegram_bot** (lucide_telegram_bot)
5. **nginx** (lucide_nginx) - Ports 80, 443

**Limites mémoire** (optimisé pour 2 GB RAM):
- PostgreSQL: 512 MB (shared_buffers: 256MB, work_mem: 8MB)
- Redis: 128 MB (maxmemory: 64MB)
- Backend: 384 MB
- Telegram Bot: 256 MB
- Nginx: 64 MB

---

## 🤖 Gestion du Bot

### Démarrer le Bot

```bash
# Se connecter à l'instance
ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@52.16.82.16

# Démarrer tous les services
cd /opt/lucide/lucide/infrastructure/aws
docker-compose -f docker-compose.aws-minimal.yml up -d

# Démarrer uniquement le bot
docker-compose -f docker-compose.aws-minimal.yml up -d telegram_bot
```

### Arrêter le Bot

```bash
# Arrêter le bot uniquement
docker-compose -f docker-compose.aws-minimal.yml stop telegram_bot

# Arrêter tous les services
docker-compose -f docker-compose.aws-minimal.yml down

# Arrêter et supprimer les volumes (⚠️ DANGER: perte de données)
docker-compose -f docker-compose.aws-minimal.yml down -v
```

### Redémarrer le Bot

```bash
# Redémarrage rapide
docker-compose -f docker-compose.aws-minimal.yml restart telegram_bot

# Reconstruire l'image et redémarrer (après modification du code)
cd /opt/lucide/lucide
docker build -t aws-telegram_bot:latest -f backend/telegram/Dockerfile .
cd infrastructure/aws
docker-compose -f docker-compose.aws-minimal.yml up -d telegram_bot
```

### Consulter les Logs

```bash
# Logs en temps réel
docker logs lucide_telegram_bot -f

# Dernières 50 lignes
docker logs lucide_telegram_bot --tail 50

# Logs avec horodatage
docker logs lucide_telegram_bot -f --timestamps

# Chercher des erreurs
docker logs lucide_telegram_bot 2>&1 | grep -i error
```

### Vérifier l'État des Services

```bash
# État de tous les conteneurs
docker-compose -f docker-compose.aws-minimal.yml ps

# Statistiques d'utilisation (CPU, mémoire)
docker stats

# Vérifier la connexion Telegram
curl -s "https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/getMe" | jq .

# Vérifier le webhook (doit être vide en mode polling)
curl -s "https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/getWebhookInfo" | jq .
```

### Accéder à la Base de Données

```bash
# Via Docker
docker exec -it lucide_postgres psql -U lucide_user -d lucide

# Lister les tables
\dt

# Voir la structure d'une table
\d users

# Exécuter une requête
SELECT user_id, telegram_id, telegram_username, created_at FROM users;

# Quitter
\q
```

### Accéder à Redis

```bash
# Via Docker
docker exec -it lucide_redis redis-cli

# Lister toutes les clés
KEYS *

# Voir une valeur
GET <key>

# Voir toutes les clés match_*
KEYS match_*

# Quitter
exit
```

---

## 📁 Architecture du Code

### Structure des Fichiers

```
backend/telegram/
├── __init__.py
├── bot.py                    # Application principale du bot
├── run_bot.py               # Point d'entrée (lance le bot)
├── config.py                # Configuration (tokens, DB, etc.)
├── handlers/
│   ├── __init__.py
│   ├── command_handlers.py  # Handlers pour /start, /help, /context, etc.
│   ├── callback_handlers.py # Handlers pour les boutons inline
│   └── message_handlers.py  # Handlers pour les messages texte
├── keyboards/
│   ├── __init__.py
│   ├── context_keyboards.py # Claviers pour sélection de contexte
│   ├── main_keyboards.py    # Menu principal
│   └── settings_keyboards.py# Paramètres utilisateur
├── services/
│   ├── __init__.py
│   ├── user_service.py      # Gestion des utilisateurs
│   ├── conversation_service.py # Gestion des conversations
│   └── football_service.py  # API Football (à implémenter)
└── middleware/
    ├── __init__.py
    └── error_handler.py     # Gestion centralisée des erreurs
```

### Handlers Principaux

#### command_handlers.py

Gère toutes les commandes `/`:

- `/start` → `start_command()` - Accueil et création de compte
- `/help` → `help_command()` - Affiche l'aide
- `/context` → `context_command()` - Menu de sélection de contexte
- `/language` → `language_command()` - Changement de langue
- `/subscription` → `subscription_command()` - Infos abonnement
- `/new` → `new_conversation_command()` - Nouvelle conversation
- `/history` → `history_command()` - Historique des conversations

**Important**: Toutes ces fonctions détectent si elles sont appelées depuis:
- Une commande normale (`update.message`)
- Un callback query depuis un bouton (`update.callback_query`)

```python
# Pattern utilisé partout
if update.callback_query:
    await update.callback_query.edit_message_text(text, ...)
else:
    await update.message.reply_text(text, ...)
```

#### callback_handlers.py

Gère les clics sur les boutons inline:

- `ctx_*` → Sélection de contexte (league, match, team, player)
- `lang_*` → Changement de langue (fr, en)
- `conv_*` → Actions sur les conversations
- `sub_*` → Actions d'abonnement
- `cmd_*` → Raccourcis vers les commandes

#### context_keyboards.py

**Fonction principale**: `get_main_context_menu(current_context)`

**Logique de contexte conditionnelle**:
1. **Par défaut** (pas de contexte): Seulement "🏆 Select League"
2. **Avec League**: "⚽ Select Match" + "👥 Select Team"
3. **Avec League + Match**: "👥 Select Team" + "🎯 Select Player"
4. **Avec League + Team**: "🎯 Select Player"
5. **Avec League + Match + Player**: Seulement "❌ Clear Context"

Le contexte est stocké dans `context.user_data["context"]`:
```python
{
    "league": {"id": 61, "name": "Ligue 1", "country": "France"},
    "match": {"id": 12345, "home": "PSG", "away": "OM"},
    "team": {"id": 85, "name": "Paris Saint Germain"},
    "player": {"id": 276, "name": "Kylian Mbappé"}
}
```

---

## ✅ Fonctionnalités Attendues

### 1. Sélection de Contexte (En Cours)

**État actuel**:
- ✅ Menu de contexte conditionnel implémenté
- ✅ Logique de filtrage des options selon le contexte
- ❌ **Sélection des leagues non implémentée**
- ❌ **Sélection des matchs non implémentée**
- ❌ **Sélection des équipes non implémentée**
- ❌ **Sélection des joueurs non implémentée**

**Ce qui doit être fait**:

#### A. Implémenter la sélection de League

Quand l'utilisateur clique sur "🏆 Select League":

1. **Afficher les leagues populaires** (pagination):
   ```
   🏆 Select a League

   Page 1/3:
   🇫🇷 Ligue 1 (France)
   🇬🇧 Premier League (England)
   🇪🇸 La Liga (Spain)
   🇮🇹 Serie A (Italy)
   🇩🇪 Bundesliga (Germany)

   ⬅️ Prev | Next ➡️
   🔍 Search | ❌ Cancel
   ```

2. **Bouton "Search"** → Demander à l'utilisateur de taper le nom:
   ```
   🔍 Search League

   Type the name of the league you want to search for:
   Example: "Premier", "Ligue 1", "Champions"

   ❌ Cancel
   ```

3. **Après saisie** → Chercher via API Football et afficher résultats:
   ```
   🔍 Results for "Premier"

   🇬🇧 Premier League (England)
   🇷🇺 Russian Premier League
   🇪🇬 Egyptian Premier League

   ⬅️ Back to popular
   ```

4. **Après sélection** → Enregistrer dans le contexte et afficher confirmation:
   ```
   ✅ Context Updated

   🏆 League: Premier League 🇬🇧

   What's next?
   ⚽ Select Match
   👥 Select Team
   ❌ Clear Context
   ```

#### B. Implémenter la sélection de Match

Quand l'utilisateur clique sur "⚽ Select Match" (après avoir choisi une league):

1. **Afficher les matchs à venir** de la league choisie:
   ```
   ⚽ Upcoming Matches - Premier League

   Today:
   🏴󠁧󠁢󠁥󠁮󠁧󠁿 Man City vs Arsenal 🏴󠁧󠁢󠁥󠁮󠁧󠁿 (20:00)
   🏴󠁧󠁢󠁥󠁮󠁧󠁿 Liverpool vs Chelsea 🏴󠁧󠁢󠁥󠁮󠁧󠁿 (17:30)

   Tomorrow:
   🏴󠁧󠁢󠁥󠁮󠁧󠁿 Tottenham vs Newcastle 🏴󠁧󠁢󠁥󠁮󠁧󠁿 (15:00)

   ⬅️ Prev | Next ➡️
   🔍 Search | ❌ Back
   ```

2. **Après sélection** → Enregistrer et proposer Team/Player

#### C. Implémenter la sélection de Team

**Cas 1**: Après League seule → Toutes les équipes de la league
**Cas 2**: Après League + Match → Seulement les 2 équipes du match

#### D. Implémenter la sélection de Player

**Cas 1**: Après League + Match → Joueurs des 2 équipes
**Cas 2**: Après League + Team → Joueurs de l'équipe
**Cas 3**: Après League + Match + Team → Joueurs de l'équipe

### 2. Gestion des Conversations

**État actuel**:
- ✅ Création de conversation à chaque /start
- ✅ Stockage des messages en base
- ❌ **Génération de titre intelligent non implémentée**
- ❌ **Historique des conversations non implémenté**

**Ce qui doit être fait**:
- Implémenter `/history` pour afficher la liste des conversations
- Permettre de reprendre une conversation
- Générer un titre basé sur le premier message (via DeepSeek API)

### 3. Analyse de Match

**État actuel**:
- ❌ **Complètement non implémenté**

**Ce qui doit être fait**:
- Détecter les questions sur les matchs dans `message_handlers.py`
- Récupérer les analyses depuis le cache PostgreSQL (table `match_analyses`)
- Utiliser l'API Football si pas en cache
- Formater la réponse avec les prédictions
- Envoyer la réponse à l'utilisateur

### 4. Abonnements et Limites

**État actuel**:
- ✅ Structure de la base de données (subscription_tier, subscription_status)
- ❌ **Vérification des limites non implémentée**
- ❌ **Compteur de messages non implémenté**

**Ce qui doit être fait**:
- Middleware pour vérifier le nombre de messages par jour
- Bloquer si limite atteinte (FREE: 50/jour)
- Afficher message de mise à niveau

---

## 🚧 Limitations Telegram

### Pas de Dropdown Natif

**Telegram ne supporte PAS**:
- ❌ Dropdown/Select HTML-like
- ❌ Auto-complétion de formulaire
- ❌ Champs de recherche avec suggestions en temps réel

**Telegram supporte**:
- ✅ **InlineKeyboardButton** - Boutons sous un message (max ~100 boutons)
- ✅ **ReplyKeyboardMarkup** - Clavier personnalisé (remplace le clavier standard)
- ✅ **ForceReply** - Force l'utilisateur à répondre au message
- ✅ **InlineQuery** - Recherche via `@bot query` (mode inline)

### Solutions pour les Listes Longues

#### Option 1: Pagination avec InlineKeyboardButton (Recommandé)

```python
def get_league_selector_page(leagues: list, page: int = 0, page_size: int = 5):
    """Afficher 5 leagues par page avec boutons Next/Prev."""
    start = page * page_size
    end = start + page_size
    page_leagues = leagues[start:end]

    keyboard = []

    # Leagues de la page actuelle
    for league in page_leagues:
        keyboard.append([
            InlineKeyboardButton(
                f"{league['flag']} {league['name']}",
                callback_data=f"league_{league['id']}"
            )
        ])

    # Navigation
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"leagues_page_{page-1}")
        )
    if end < len(leagues):
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"leagues_page_{page+1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Bouton Search
    keyboard.append([
        InlineKeyboardButton("🔍 Search by Name", callback_data="league_search")
    ])

    return keyboard
```

**Avantages**:
- Simple à implémenter
- Pas besoin d'état complexe
- Fonctionne bien pour 10-50 items

**Inconvénients**:
- Fastidieux pour 100+ items
- Beaucoup de clics

#### Option 2: Recherche Textuelle

```python
async def league_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Demander à l'utilisateur de taper le nom."""
    await update.callback_query.edit_message_text(
        "🔍 **Search League**\n\n"
        "Type the name of the league:\n"
        "Example: `Premier`, `Ligue 1`, `Champions`\n\n"
        "Send your search query now.",
        parse_mode="Markdown"
    )

    # Définir l'état pour attendre la saisie
    context.user_data["awaiting_input"] = "league_search"

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Traiter le texte saisi par l'utilisateur."""
    if context.user_data.get("awaiting_input") == "league_search":
        query = update.message.text

        # Chercher les leagues via API
        results = await football_api.search_leagues(query)

        # Afficher les résultats
        keyboard = []
        for league in results[:10]:  # Max 10 résultats
            keyboard.append([
                InlineKeyboardButton(
                    f"{league['flag']} {league['name']}",
                    callback_data=f"league_{league['id']}"
                )
            ])

        await update.message.reply_text(
            f"🔍 Results for '{query}':",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Réinitialiser l'état
        context.user_data["awaiting_input"] = None
```

**Avantages**:
- Rapide pour trouver un item spécifique
- Pas de limite de taille de liste
- Expérience utilisateur naturelle

**Inconvénients**:
- Nécessite gestion d'état
- L'utilisateur doit savoir ce qu'il cherche

#### Option 3: Inline Query (Mode Avancé)

```python
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    L'utilisateur tape: @bot premier league
    Le bot affiche des suggestions
    """
    query = update.inline_query.query

    if not query:
        return

    # Chercher les leagues
    results = await football_api.search_leagues(query)

    # Créer les résultats inline
    inline_results = []
    for league in results[:50]:
        inline_results.append(
            InlineQueryResultArticle(
                id=str(league['id']),
                title=f"{league['flag']} {league['name']}",
                input_message_content=InputTextMessageContent(
                    f"Selected: {league['name']}"
                ),
                description=f"{league['country']}"
            )
        )

    await update.inline_query.answer(inline_results)
```

**Avantages**:
- Expérience ultra-rapide
- Suggestions en temps réel
- Pas de pagination

**Inconvénients**:
- Plus complexe à implémenter
- Moins intuitif pour les utilisateurs novices

### ⭐ Recommandation

**Utiliser une combinaison**:

1. **Leagues populaires** → Boutons directs (5-10 leagues)
2. **Bouton "More Leagues"** → Pagination (afficher par région/pays)
3. **Bouton "Search"** → Recherche textuelle
4. **Optionnel**: Mode inline pour utilisateurs avancés

---

## 💻 Développement Local

### Prérequis

```bash
# Python 3.10+
python --version

# PostgreSQL
psql --version

# Redis
redis-cli --version
```

### Installation

```bash
# Cloner le repo
git clone <repo_url>
cd lucide

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
pip install python-telegram-bot[all]==20.7

# Configurer les variables d'environnement
cp backend/telegram/.env.example backend/telegram/.env
# Éditer .env avec vos valeurs
```

### Configuration Locale

**backend/telegram/.env**:
```bash
# Base de données
DATABASE_URL=postgresql://lucide_user:password@localhost:5432/lucide

# Redis
REDIS_URL=redis://localhost:6379

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_WEBHOOK_URL=  # Vide = mode polling

# API Keys
DEEPSEEK_API_KEY=your_deepseek_api_key_here
FOOTBALL_API_KEY=your_football_api_key_here

# Secrets
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production

# Logs
LOG_LEVEL=DEBUG
```

### Lancer le Bot Localement

```bash
# ⚠️ IMPORTANT: Arrêter le bot sur AWS d'abord !
# Telegram n'autorise qu'une seule connexion par bot

# Méthode 1: Directement
cd backend/telegram
python run_bot.py

# Méthode 2: Via module
python -m backend.telegram.run_bot
```

### Tests

```bash
# Lancer les tests
pytest backend/telegram/tests/

# Avec couverture
pytest --cov=backend/telegram backend/telegram/tests/

# Test spécifique
pytest backend/telegram/tests/test_handlers.py::test_start_command
```

---

## 🚀 Déploiement

### Déployer des Modifications

```bash
# 1. Modifier le code localement
# 2. Tester localement
# 3. Copier les fichiers sur AWS

# Copier un fichier spécifique
scp -i ~/.ssh/lucide-key-2025.pem \
    backend/telegram/handlers/command_handlers.py \
    ec2-user@52.16.82.16:/opt/lucide/lucide/backend/telegram/handlers/

# Copier plusieurs fichiers
scp -i ~/.ssh/lucide-key-2025.pem -r \
    backend/telegram/keyboards/ \
    ec2-user@52.16.82.16:/opt/lucide/lucide/backend/telegram/

# 4. Se connecter et reconstruire
ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@52.16.82.16

cd /opt/lucide/lucide
docker build -t aws-telegram_bot:latest -f backend/telegram/Dockerfile .

cd infrastructure/aws
docker-compose -f docker-compose.aws-minimal.yml up -d telegram_bot

# 5. Vérifier les logs
docker logs lucide_telegram_bot -f
```

### Déploiement via Git (Recommandé)

```bash
# Sur votre machine locale
git add .
git commit -m "feat: implement league selector"
git push origin main

# Sur AWS
ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@52.16.82.16

cd /opt/lucide/lucide
git pull origin main

# Reconstruire et redémarrer
docker build -t aws-telegram_bot:latest -f backend/telegram/Dockerfile .
cd infrastructure/aws
docker-compose -f docker-compose.aws-minimal.yml up -d telegram_bot
```

---

## 🔧 Troubleshooting

### Le bot ne répond pas

```bash
# Vérifier que le conteneur tourne
docker ps | grep telegram

# Vérifier les logs
docker logs lucide_telegram_bot --tail 50

# Redémarrer le bot
docker-compose -f docker-compose.aws-minimal.yml restart telegram_bot
```

### Erreur "Conflict: terminated by other getUpdates"

**Cause**: Une autre instance du bot tourne (probablement en local)

**Solution**:
```bash
# Sur Windows (PowerShell)
Get-Process python | Stop-Process -Force

# Sur Linux/Mac
pkill -f "python.*telegram"

# Sur AWS, redémarrer le bot
docker-compose -f docker-compose.aws-minimal.yml restart telegram_bot
```

### Erreur de base de données

```bash
# Vérifier que PostgreSQL tourne
docker ps | grep postgres

# Se connecter à la base
docker exec -it lucide_postgres psql -U lucide_user -d lucide

# Vérifier les migrations
SELECT * FROM users LIMIT 5;

# Recréer la base (⚠️ DANGER: perte de données)
docker-compose -f docker-compose.aws-minimal.yml down -v
docker-compose -f docker-compose.aws-minimal.yml up -d
```

### Erreur de mémoire

```bash
# Vérifier l'utilisation mémoire
docker stats

# Si un service utilise trop de mémoire, le redémarrer
docker-compose -f docker-compose.aws-minimal.yml restart <service>

# Augmenter les limites dans docker-compose.aws-minimal.yml
# Puis redéployer
```

### Le bot est lent

```bash
# Vérifier les ressources système
htop

# Vérifier les logs du backend
docker logs lucide_backend --tail 100

# Vérifier Redis
docker exec -it lucide_redis redis-cli
> INFO memory
> KEYS *
```

---

## 📞 Support

**Développeur principal**: Henri Besnard
**Email**: henri@lucide.ai (exemple)
**Documentation supplémentaire**:
- `TROUBLESHOOTING_BOT.md` - Dépannage des erreurs courantes
- `DEPLOYMENT_GUIDE.md` - Guide de déploiement complet
- `README.md` - Vue d'ensemble de l'infrastructure

---

## 📝 Checklist pour Reprendre le Développement

- [ ] Lire ce document en entier
- [ ] Se connecter à l'instance AWS pour vérifier que tout fonctionne
- [ ] Tester le bot sur Telegram (`/start`)
- [ ] Consulter les logs pour voir les erreurs actuelles
- [ ] Configurer l'environnement de développement local
- [ ] Lire le code dans `backend/telegram/handlers/`
- [ ] Comprendre la logique de contexte dans `context_keyboards.py`
- [ ] Implémenter la sélection de league (voir section "Fonctionnalités Attendues")
- [ ] Tester localement (arrêter le bot AWS d'abord !)
- [ ] Déployer sur AWS
- [ ] Tester en production

---

**Bonne chance !** 🚀
