# Guide de Test Local - Bot Telegram Lucide

## 🎯 Vue d'Ensemble

Telegram **n'a pas de sandbox officiel**, mais offre plusieurs méthodes pour tester localement sans affecter les utilisateurs en production.

---

## 🤖 Méthode 1 : Bot de Test Dédié (Recommandé)

### Créer un Bot de Test

1. **Ouvrir Telegram** et chercher `@BotFather`
2. **Créer un nouveau bot** :
   ```
   /newbot
   ```
3. **Nommer le bot** :
   - Nom : `Lucide Test Bot`
   - Username : `lucide_test_bot` (doit finir par "bot")

4. **Récupérer le token** :
   ```
   Use this token to access the HTTP API:
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### Configuration

```bash
# 1. Copier le fichier d'exemple
cd backend/telegram
copy .env.example .env  # Windows
# ou
cp .env.example .env    # Linux/Mac

# 2. Éditer .env
notepad .env  # Windows
# ou
nano .env     # Linux/Mac
```

**Contenu minimal de `.env`** :

```bash
# Bot de test
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_USERNAME=lucide_test_bot

# Base de données (locale)
DATABASE_URL=postgresql://postgres:password@localhost:5432/lucide_test

# Pas de webhook en dev
TELEGRAM_WEBHOOK_URL=

# Optionnel : Redis local
REDIS_URL=redis://localhost:6379
```

### Lancer le Bot

**Windows** :
```bash
# Mode polling (développement)
test_local.bat polling

# Tests automatisés
test_local.bat tests
```

**Linux/Mac** :
```bash
# Rendre le script exécutable
chmod +x test_local.sh

# Mode polling
./test_local.sh polling

# Tests automatisés
./test_local.sh tests
```

**Manuellement** :
```bash
python -m backend.telegram.run_bot
```

### Tester dans Telegram

1. Ouvrir Telegram
2. Chercher votre bot : `@lucide_test_bot`
3. Cliquer sur "Start" ou envoyer `/start`
4. Tester toutes les commandes :
   - `/help` - Voir l'aide
   - `/new` - Nouvelle conversation
   - `/context` - Choisir contexte
   - Envoyer un message texte

---

## 🌐 Méthode 2 : Webhook avec Tunnel (Production Simulée)

Pour tester les webhooks comme en production, utilisez un tunnel HTTPS.

### Avec ngrok

```bash
# 1. Installer ngrok
# https://ngrok.com/download

# 2. Lancer ngrok
ngrok http 8443

# Vous obtenez une URL comme: https://abc123.ngrok.io

# 3. Mettre à jour .env
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok.io
TELEGRAM_WEBHOOK_PATH=/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=mon_secret_unique_abc123

# 4. Lancer le bot
python -m backend.telegram.run_bot --webhook
```

### Avec localtunnel

```bash
# 1. Installer localtunnel
npm install -g localtunnel

# 2. Créer le tunnel
lt --port 8443 --subdomain lucide-test

# URL: https://lucide-test.loca.lt

# 3. Mettre à jour .env
TELEGRAM_WEBHOOK_URL=https://lucide-test.loca.lt

# 4. Lancer le bot
python -m backend.telegram.run_bot --webhook
```

### Avec Cloudflare Tunnel (Gratuit, Stable)

```bash
# 1. Installer cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

# 2. Lancer le tunnel
cloudflared tunnel --url http://localhost:8443

# 3. Utiliser l'URL fournie dans .env
```

---

## 🧪 Méthode 3 : Tests Automatisés (Sans Bot Réel)

La suite de tests complète permet de valider le code sans bot Telegram actif.

### Tests Complets

```bash
cd backend/telegram

# Tous les tests avec couverture
DATABASE_URL="sqlite:///:memory:" pytest --cov=. --cov-report=html

# Ouvrir le rapport
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html  # Linux
```

### Tests Spécifiques

```bash
# Tests unitaires uniquement
DATABASE_URL="sqlite:///:memory:" pytest tests/unit/ -v

# Tests d'intégration uniquement
DATABASE_URL="sqlite:///:memory:" pytest tests/integration/ -v

# Un fichier spécifique
DATABASE_URL="sqlite:///:memory:" pytest tests/unit/test_user_service.py -v

# Une fonction spécifique
DATABASE_URL="sqlite:///:memory:" pytest tests/unit/test_user_service.py::TestUserService::test_get_or_create_user_creates_new_user -v
```

### Tests en Continu (Watch Mode)

```bash
# Installer pytest-watch
pip install pytest-watch

# Lancer en mode watch
DATABASE_URL="sqlite:///:memory:" ptw -- -v
```

---

## 🔍 Débogage et Logs

### Niveau de Logs

```bash
# Dans .env
LOG_LEVEL=DEBUG

# Ou en ligne de commande
LOG_LEVEL=DEBUG python -m backend.telegram.run_bot
```

### Logs Structurés

```python
# Les logs apparaissent dans le terminal
2025-12-29 14:30:15 - backend.telegram.bot - INFO - Bot initialized
2025-12-29 14:30:16 - backend.telegram.handlers.command_handlers - INFO - User 123456 started bot
2025-12-29 14:30:20 - backend.telegram.handlers.message_handlers - INFO - Processing message from user 123456
```

### Debugger avec pdb

```python
# Ajouter dans le code
import pdb; pdb.set_trace()

# Ou avec breakpoint() (Python 3.7+)
breakpoint()
```

---

## 📊 Comparaison des Méthodes

| Méthode | Avantages | Inconvénients | Usage |
|---------|-----------|---------------|-------|
| **Bot de Test + Polling** | ✅ Simple<br>✅ Pas de config réseau<br>✅ Instantané | ⚠️ Pas de webhooks | Développement quotidien |
| **Tunnel + Webhook** | ✅ Simule production<br>✅ Teste webhooks | ⚠️ Configuration réseau<br>⚠️ Plus lent | Tests pré-production |
| **Tests Automatisés** | ✅ Rapide<br>✅ Reproductible<br>✅ CI/CD | ⚠️ Pas de vraie interaction | Validation continue |

---

## 🚀 Workflow Recommandé

### 1. Développement Local (Quotidien)

```bash
# Lancer le bot en polling
test_local.bat polling

# Tester manuellement dans Telegram
# - Envoyer des messages
# - Tester les commandes
# - Vérifier les réponses
```

### 2. Validation (Avant Commit)

```bash
# Lancer les tests
test_local.bat tests

# Vérifier la couverture > 70%
# Corriger les tests échoués
```

### 3. Tests Pré-Production (Avant Deploy)

```bash
# Lancer avec webhook via tunnel
ngrok http 8443

# Mettre à jour .env avec URL ngrok
test_local.bat webhook

# Tester les scénarios critiques
```

### 4. Production

```bash
# Webhook réel sur serveur
# Variables d'environnement configurées
# Monitoring actif
```

---

## 🔧 Dépannage

### "Token invalide"

```bash
# Vérifier le token dans .env
echo $TELEGRAM_BOT_TOKEN

# Recréer le token avec @BotFather
/revoke
/newbot
```

### "Base de données introuvable"

```bash
# Vérifier PostgreSQL est actif
pg_isready

# Créer la base de données
createdb lucide_test

# Ou utiliser SQLite pour les tests
DATABASE_URL="sqlite:///test.db" python -m backend.telegram.run_bot
```

### "Module non trouvé"

```bash
# Installer les dépendances
pip install -r requirements.txt
pip install -r backend/telegram/requirements.txt

# Vérifier le PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/lucide"
```

### "Webhook déjà configuré"

```bash
# Supprimer le webhook existant
# Via @BotFather
/mybots -> Sélectionner bot -> Bot Settings -> Delete Webhook

# Ou via API
curl https://api.telegram.org/bot<TOKEN>/deleteWebhook
```

---

## 📝 Checklist de Test

Avant de déployer en production :

- [ ] Bot répond à `/start`
- [ ] Création d'utilisateur fonctionne
- [ ] Messages texte sont traités
- [ ] Commandes fonctionnent (`/help`, `/new`, etc.)
- [ ] Rate limiting actif
- [ ] Gestion d'erreurs correcte
- [ ] Logs structurés visibles
- [ ] Tests automatisés passent (> 70% couverture)
- [ ] Pas de secrets dans le code
- [ ] Base de données connectée
- [ ] Redis connecté (si utilisé)

---

## 🎓 Ressources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [BotFather Commands](https://core.telegram.org/bots#6-botfather)
- [Webhook Guide](https://core.telegram.org/bots/webhooks)
- [ngrok Documentation](https://ngrok.com/docs)

---

**Prêt à tester ! 🚀**

Pour commencer immédiatement :
```bash
# Windows
test_local.bat polling

# Linux/Mac
./test_local.sh polling
```
