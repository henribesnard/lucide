# Dépannage Bot Telegram - Conflit d'Instance

## ⚠️ Problème Actuel

Le bot affiche l'erreur : `Conflict: terminated by other getUpdates request; make sure that only one bot instance is running`

Cela signifie qu'**une autre instance du bot tourne quelque part** (probablement sur votre PC local).

---

## ✅ Solution en 3 Étapes

### Étape 1 : Arrêter les Instances Locales (Windows)

**Option A - PowerShell (Recommandé):**
```powershell
# Afficher tous les processus Python
Get-Process python

# Arrêter tous les processus Python
Get-Process python | Stop-Process -Force
```

**Option B - Gestionnaire des Tâches:**
1. Ouvrez le Gestionnaire des tâches (Ctrl+Shift+Esc)
2. Onglet "Détails"
3. Cherchez tous les processus `python.exe`
4. Clic droit → Fin de tâche

### Étape 2 : Vérifier qu'aucune instance ne tourne

```powershell
Get-Process python
# Devrait retourner : "Get-Process : Cannot find a process with the name python"
```

### Étape 3 : Tester le Bot sur AWS

Exécutez le script de test :

```bash
cd C:\Users\henri\Projets\lucide\infrastructure\aws
bash test-bot-telegram.sh
```

OU manuellement :

```bash
# Se connecter à l'instance
ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@52.16.82.16

# Redémarrer le bot
cd /opt/lucide/lucide/infrastructure/aws
docker-compose -f docker-compose.aws-minimal.yml restart telegram_bot

# Attendre 5 secondes
sleep 5

# Vérifier les logs
docker logs lucide_telegram_bot --tail 20
```

**Logs attendus (succès):**
```
✅ Application started
✅ Bot commands menu set successfully
✅ Scheduler started
❌ AUCUNE erreur "Conflict"
```

---

## 🧪 Tester le Bot

Une fois le conflit résolu :

1. **Ouvrez Telegram** sur votre téléphone ou PC
2. **Cherchez** `@lucidebot`
3. **Cliquez sur Start** ou envoyez `/start`
4. Le bot devrait répondre avec le menu principal

---

## 🔍 Vérifications Supplémentaires

### Vérifier le statut du bot sur AWS

```bash
ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@52.16.82.16

# État des conteneurs
docker-compose -f /opt/lucide/lucide/infrastructure/aws/docker-compose.aws-minimal.yml ps

# Logs en temps réel
docker logs lucide_telegram_bot -f
```

### Vérifier le webhook Telegram

```bash
curl -s "https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/getWebhookInfo" | jq .
```

**Doit retourner:**
```json
{
  "ok": true,
  "result": {
    "url": "",  // Vide = mode polling OK
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## 💡 Pourquoi ce Problème ?

Telegram ne permet qu'**une seule connexion** par bot à la fois :
- Soit par **polling** (getUpdates)
- Soit par **webhook** (URL HTTPS)

Si plusieurs instances font du polling simultanément, elles entrent en conflit.

---

## 🎯 Solutions à Long Terme

### Option 1 : Mode Polling (Actuel)
✅ Simple
✅ Pas besoin de HTTPS
❌ Une seule instance possible
❌ Moins performant

**Recommandé pour:** Tests, développement

### Option 2 : Mode Webhook (Production)
✅ Performant
✅ Pas de limite d'instance
❌ Nécessite HTTPS
❌ Configuration plus complexe

**Nécessite:**
- Certificat SSL/HTTPS
- Domaine ou service tunnel (ngrok, localtunnel)

**Configuration avec SSL:**
```bash
# Installer Certbot
sudo yum install -y certbot

# Obtenir un certificat (nécessite un domaine)
sudo certbot certonly --standalone -d votredomaine.com

# Configurer Nginx avec HTTPS
# Puis configurer le webhook
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://votredomaine.com/telegram/webhook"
```

---

## 📞 Besoin d'Aide ?

Si le problème persiste :

1. Vérifiez que **AUCUN** terminal n'est ouvert avec le bot
2. Redémarrez votre PC (pour être sûr)
3. Vérifiez les logs AWS : `docker logs lucide_telegram_bot -f`

---

## ✅ Checklist

- [ ] Arrêté tous les processus Python locaux
- [ ] Vérifié avec `Get-Process python` (aucun résultat)
- [ ] Redémarré le bot sur AWS
- [ ] Vérifié les logs (pas de "Conflict")
- [ ] Testé sur Telegram avec `/start`
- [ ] Le bot répond correctement

---

**Une fois résolu, le bot sera pleinement opérationnel !** 🎉
