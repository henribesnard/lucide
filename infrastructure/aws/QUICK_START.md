# Démarrage Rapide - Déploiement AWS

Guide de déploiement en 5 minutes pour Lucide sur AWS avec **t3a.small**.

---

## 📋 Prérequis

- Compte AWS configuré
- AWS CLI installé et configuré
- Git Bash ou WSL sur Windows
- Budget: $38 = ~2 mois de test complet

---

## 🚀 Déploiement en 3 Étapes

### Étape 1: Créer l'Instance EC2 (5 minutes)

```bash
# Depuis votre PC Windows
cd C:\Users\henri\Projets\lucide\infrastructure\aws

# Lancer le déploiement
bash deploy-lucide-minimal.sh
```

**Résultat attendu:**
```
✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS
Instance ID: i-0abc123...
IP Publique: 54.123.45.67
Connexion SSH:
  ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@54.123.45.67
```

**Notez l'IP publique** - vous en aurez besoin !

---

### Étape 2: Configurer Lucide sur l'Instance (3 minutes)

```bash
# Se connecter à l'instance
ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@<VOTRE_IP_PUBLIQUE>

# Attendre 2-3 minutes si première connexion
# Vérifier que l'initialisation est terminée:
cat /var/log/user-data.log

# Télécharger et exécuter le script de setup
curl -o setup.sh https://raw.githubusercontent.com/VOTRE_USERNAME/lucide/main/infrastructure/aws/setup-lucide-on-ec2.sh
chmod +x setup.sh
./setup.sh
```

Le script va:
1. ✅ Vérifier Docker
2. ✅ Cloner le repo Lucide
3. ✅ Créer le fichier `.env` (vous pourrez l'éditer)
4. ✅ Lancer tous les services Docker
5. ✅ Afficher l'état des services

**Lors de l'exécution**, le script vous demandera:
- L'URL de votre repository Git
- Si vous voulez éditer le `.env` (recommandé: répondre `Y`)
- Si vous voulez configurer le webhook Telegram

---

### Étape 3: Tester le Bot (1 minute)

```bash
# Sur l'instance EC2, vérifier que tout tourne:
docker-compose -f /opt/lucide/lucide/infrastructure/aws/docker-compose.aws-minimal.yml ps

# Tester l'API
curl http://localhost/health

# Voir les logs en temps réel
docker-compose -f /opt/lucide/lucide/infrastructure/aws/docker-compose.aws-minimal.yml logs -f telegram_bot
```

**Sur Telegram:**
1. Cherchez `@lucidebot`
2. Cliquez sur "Start" ou envoyez `/start`
3. Le bot devrait répondre avec le menu principal

---

## 🔧 Configuration Minimale du .env

Quand le script vous propose d'éditer le `.env`, modifiez **AU MINIMUM**:

```bash
# Sécurité (OBLIGATOIRE en production)
DB_PASSWORD=VotreMotDePasseSecurise123!
SECRET_KEY=cle_secrete_aleatoire_minimum_32_caracteres
JWT_SECRET=jwt_secret_aleatoire_minimum_32_caracteres

# Telegram (déjà configuré)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_WEBHOOK_URL=  # Laissez vide pour mode polling
```

**Générer des clés sécurisées:**
```bash
# Sur l'instance EC2
openssl rand -hex 32  # Pour SECRET_KEY
openssl rand -hex 32  # Pour JWT_SECRET
```

---

## ✅ Checklist de Vérification

- [ ] Instance EC2 créée et accessible
- [ ] Services Docker en cours d'exécution (`docker-compose ps`)
- [ ] API répond: `curl http://<IP>/health` retourne "healthy"
- [ ] Bot Telegram répond à `/start`
- [ ] Logs sans erreurs: `docker-compose logs`

---

## 📊 Monitoring Rapide

```bash
# Usage mémoire
free -h

# Usage par conteneur
docker stats

# Logs temps réel
docker-compose -f /opt/lucide/lucide/infrastructure/aws/docker-compose.aws-minimal.yml logs -f

# Redémarrer un service
docker-compose -f /opt/lucide/lucide/infrastructure/aws/docker-compose.aws-minimal.yml restart telegram_bot
```

---

## 🆘 Dépannage Express

### Le bot ne répond pas

```bash
# Vérifier les logs du bot
docker-compose logs telegram_bot

# Vérifier que le bot tourne
docker-compose ps

# Redémarrer le bot
docker-compose restart telegram_bot
```

### Manque de mémoire

```bash
# Vérifier la RAM
free -h

# Activer 1 GB de swap
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### L'IP a changé après redémarrage

```bash
# Récupérer la nouvelle IP
aws ec2 describe-instances \
  --instance-ids <VOTRE_INSTANCE_ID> \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text \
  --region eu-west-1
```

---

## 💰 Coût Estimé

```
Instance t3a.small:    $13.50/mois
EBS 30 GB gp3:         $2.40/mois
Bande passante:        $0-2/mois
───────────────────────────────
TOTAL:                 ~$16-18/mois

Votre budget $38 = ~2 mois de test complet
```

---

## 🎯 Prochaines Étapes

Une fois que tout fonctionne:

1. **Elastic IP** (optionnel): IP fixe pour $3.60/mois
2. **Webhook Telegram**: Meilleure performance que polling
3. **Monitoring**: CloudWatch pour suivre les métriques
4. **Backups**: Snapshots EBS automatiques
5. **Domaine**: Si besoin (Namecheap ~$10/an)

---

**Besoin d'aide ?**
- Documentation complète: `DEPLOYMENT_GUIDE.md`
- Tests locaux: `backend/telegram/LOCAL_TESTING.md`
