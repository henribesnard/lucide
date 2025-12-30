# Guide de Déploiement AWS Minimal - Lucide

Déploiement ultra-économique de Lucide sur AWS avec le Free Tier.

---

## 💰 Estimation des Coûts

### Option 1 : Free Tier (GRATUIT - 12 premiers mois)

```
EC2 t2.micro:              $0/mois  (750h/mois Free Tier)
EBS 30 GB:                 $0/mois  (30 GB Free Tier)
Bande passante:            $0/mois  (< 1 GB/mois)
IP publique:               $0/mois  (tant que l'instance tourne)
────────────────────────────────────────────────────
TOTAL:                     $0/mois ✅

Votre budget $38 = ILLIMITÉ (dans la limite Free Tier)
```

### Option 2 : Post Free Tier ou t3a.small

```
EC2 t2.micro (post FT):    $8.47/mois
  OU
EC2 t3a.small:            $13.50/mois  (RECOMMANDÉ - 2 GB RAM)
EBS 30 GB:                $2.40/mois
Elastic IP (optionnel):   $3.60/mois
Bande passante:           $0-5/mois
────────────────────────────────────────────────────
TOTAL:                    $11-25/mois

Avec votre budget $38:
  - t2.micro: 3-4 mois
  - t3a.small: 1.5-2 mois
```

---

## 🚀 Déploiement Rapide (10 minutes)

### Prérequis

```powershell
# Installer AWS CLI (si pas déjà fait)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Configurer AWS CLI
aws configure
# AWS Access Key ID: [Votre clé]
# AWS Secret Access Key: [Votre secret]
# Default region: eu-west-1
# Default output format: json

# Tester la connexion
aws sts get-caller-identity
```

### Étape 1 : Déployer l'Instance EC2

```bash
# Depuis le dossier du projet
cd infrastructure/aws

# Rendre le script exécutable (Git Bash / WSL)
chmod +x deploy-lucide-minimal.sh

# Lancer le déploiement
./deploy-lucide-minimal.sh

# OU sur PowerShell
bash deploy-lucide-minimal.sh
```

**Résultat attendu :**
```
✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS
Instance ID: i-0abc123def456...
Security Group: sg-0xyz789...
IP Publique: 54.123.45.67

Connexion SSH:
  ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@54.123.45.67
```

### Étape 2 : Se Connecter à l'Instance

```bash
# Via SSH
ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@<IP_PUBLIQUE>

# Vérifier que Docker est installé
docker --version
docker-compose --version

# Vérifier les logs d'initialisation
cat /var/log/user-data.log
```

### Étape 3 : Déployer Lucide

```bash
# Sur l'instance EC2 (après SSH)

# 1. Cloner le repo
cd /opt/lucide
git clone https://github.com/VOTRE_USERNAME/lucide.git
cd lucide/infrastructure/aws

# 2. Créer le fichier .env
nano .env
```

**Contenu du .env :**

```bash
# Base de données
DB_PASSWORD=votre_mot_de_passe_securise_123

# APIs
DEEPSEEK_API_KEY=your_deepseek_api_key_here
FOOTBALL_API_KEY=your_football_api_key_here

# Sécurité
SECRET_KEY=votre_secret_key_unique_aleatoire
JWT_SECRET=votre_jwt_secret_unique_aleatoire

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Webhook (utiliser l'IP publique)
# TELEGRAM_WEBHOOK_URL=http://54.123.45.67/telegram/webhook
# OU laisser vide pour mode polling (recommandé pour test)
TELEGRAM_WEBHOOK_URL=

# Logs
LOG_LEVEL=INFO
```

**Sauvegarder** : `Ctrl+O`, `Enter`, `Ctrl+X`

```bash
# 3. Lancer tous les services
docker-compose -f docker-compose.aws-minimal.yml up -d

# 4. Vérifier que tout tourne
docker-compose -f docker-compose.aws-minimal.yml ps

# 5. Vérifier les logs
docker-compose -f docker-compose.aws-minimal.yml logs -f

# 6. Initialiser la base de données
docker-compose exec backend python -c "
from backend.db.database import Base, engine
Base.metadata.create_all(bind=engine)
print('Database initialized!')
"
```

### Étape 4 : Tester

```bash
# Test 1 : Health check
curl http://localhost/health

# Test 2 : API backend
curl http://localhost/api/health

# Test 3 : Depuis votre PC
curl http://<IP_PUBLIQUE>/health

# Test 4 : Telegram Bot
# Sur Telegram, cherchez votre bot et envoyez /start
```

---

## 📊 Monitoring & Gestion

### Vérifier l'Usage Mémoire

```bash
# Sur l'instance EC2
free -h

# Voir l'usage par conteneur
docker stats

# Si mémoire insuffisante, augmenter le swap
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Logs

```bash
# Logs temps réel
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f backend
docker-compose logs -f telegram_bot

# Logs système
tail -f /var/log/user-data.log
```

### Redémarrer les Services

```bash
# Redémarrer tout
docker-compose restart

# Redémarrer un service
docker-compose restart backend
docker-compose restart telegram_bot

# Arrêter tout
docker-compose down

# Redémarrer avec rebuild
docker-compose up -d --build
```

---

## 🔧 Optimisations pour t2.micro (1 GB RAM)

### 1. Activer le Swap

```bash
# Créer 1 GB de swap
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Rendre permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Vérifier
free -h
```

### 2. Limiter les Workers

Dans `backend/main.py` :

```python
# Utiliser 1 seul worker pour économiser la RAM
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Au lieu de 4
        log_level="info"
    )
```

### 3. Désactiver Services Non Essentiels

Si la RAM est trop juste, commentez nginx dans `docker-compose.yml` :

```yaml
# nginx:
#   image: nginx:alpine
#   ...
```

Et exposez directement le backend sur le port 80 :

```yaml
backend:
  ports:
    - "80:8000"  # Au lieu de 8000:8000
```

---

## 🌐 Configurer le Webhook Telegram (Optionnel)

### Sans Nom de Domaine (Utiliser IP)

```bash
# 1. Récupérer votre IP publique
IP=$(curl -s ifconfig.me)
echo "Votre IP: $IP"

# 2. Configurer le webhook
curl "https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/setWebhook?url=http://$IP/telegram/webhook"

# 3. Vérifier
curl "https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

⚠️ **Attention** : L'IP publique change si vous arrêtez/redémarrez l'instance !

### Solution : Utiliser Elastic IP (Recommandé)

```bash
# Allouer une Elastic IP
aws ec2 allocate-address --domain vpc --region eu-west-1

# Récupérer l'Allocation ID et l'associer à votre instance
ALLOCATION_ID=eipalloc-xxxxx
INSTANCE_ID=i-xxxxx

aws ec2 associate-address \
  --instance-id $INSTANCE_ID \
  --allocation-id $ALLOCATION_ID \
  --region eu-west-1
```

**Coût** : $3.60/mois (IP fixe, ne change plus)

---

## 💡 Conseils pour Économiser

### 1. Arrêter l'Instance Quand Non Utilisée

```bash
# Arrêter (ne paie plus le compute, mais paie le stockage)
aws ec2 stop-instances --instance-ids i-xxxxx --region eu-west-1

# Redémarrer
aws ec2 start-instances --instance-ids i-xxxxx --region eu-west-1
```

### 2. Surveiller les Coûts

```bash
# Via CLI
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-02-01 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --region us-east-1

# Ou via Console
# https://console.aws.amazon.com/billing/home
```

### 3. Configurer Budget Alert

```bash
# Créer une alerte à $20
aws budgets create-budget \
  --account-id 204093577928 \
  --budget '{
    "BudgetName": "lucide-monthly-budget",
    "BudgetLimit": {
      "Amount": "20",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'
```

---

## 📋 Checklist de Déploiement

- [ ] AWS CLI configuré
- [ ] Script `deploy-lucide-minimal.sh` exécuté
- [ ] Instance EC2 créée et accessible en SSH
- [ ] Docker et Docker Compose installés
- [ ] Repo Lucide cloné dans `/opt/lucide`
- [ ] Fichier `.env` créé avec tous les secrets
- [ ] Services Docker lancés (`docker-compose up -d`)
- [ ] Base de données initialisée
- [ ] API accessible sur `http://<IP>/api/health`
- [ ] Bot Telegram répond à `/start`
- [ ] Logs vérifiés (pas d'erreurs)
- [ ] Monitoring configuré
- [ ] Budget alert AWS activé

---

## 🆘 Dépannage

### Problème : Instance manque de RAM

**Solution** : Activer le swap (voir section Optimisations)

### Problème : Docker ne démarre pas

```bash
# Vérifier le service
sudo systemctl status docker

# Redémarrer Docker
sudo systemctl restart docker

# Vérifier les logs
sudo journalctl -u docker -f
```

### Problème : Conteneurs crashent

```bash
# Voir les logs
docker-compose logs

# Voir les ressources
docker stats

# Redémarrer avec rebuild
docker-compose down
docker-compose up -d --build
```

### Problème : IP publique a changé

```bash
# Récupérer la nouvelle IP
aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text \
  --region eu-west-1

# OU utiliser Elastic IP (recommandé)
```

---

## 🎯 Prochaines Étapes

Une fois que tout fonctionne :

1. **Sauvegardes** : Configurer des snapshots automatiques
2. **Monitoring** : Installer CloudWatch agent
3. **Sécurité** : Restreindre les Security Groups
4. **Domaine** : Acheter un domaine si besoin (Namecheap ~$10/an)
5. **SSL** : Installer Let's Encrypt (gratuit)
6. **Scaling** : Passer à t3a.small si besoin de plus de RAM

---

**Coût total estimé avec votre budget $38** :

- **Free Tier (12 mois)** : GRATUIT → Budget pour autres services
- **t3a.small** : ~2 mois de test complet
- **t2.micro (post FT)** : ~3-4 mois

**Recommandation** : Commencez avec le Free Tier t2.micro, puis upgradez vers t3a.small quand vous avez des utilisateurs réels.
