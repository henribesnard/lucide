# Infrastructure AWS - Lucide

Configuration complète pour déployer Lucide sur AWS avec une instance **t3a.small** (2 vCPU, 2 GB RAM).

---

## 📁 Fichiers Disponibles

### Scripts de Déploiement

| Fichier | Description | Usage |
|---------|-------------|-------|
| `deploy-lucide-minimal.sh` | Script principal de déploiement AWS | Crée l'instance EC2 automatiquement |
| `setup-lucide-on-ec2.sh` | Script de configuration post-déploiement | À exécuter SUR l'instance EC2 après SSH |
| `generate-secrets.sh` | Génère des clés sécurisées aléatoires | Génère DB_PASSWORD, SECRET_KEY, JWT_SECRET |

### Configuration Docker

| Fichier | Description |
|---------|-------------|
| `docker-compose.aws-minimal.yml` | Configuration Docker Compose pour production |
| `nginx.conf` | Configuration du reverse proxy Nginx |
| `init-db.sql` | Script d'initialisation PostgreSQL |

### Configuration Environnement

| Fichier | Description |
|---------|-------------|
| `.env.example` | Template de configuration environnement | À copier en `.env` et personnaliser |

### Documentation

| Fichier | Description |
|---------|-------------|
| `QUICK_START.md` | **COMMENCEZ ICI** - Guide de démarrage rapide (5 min) |
| `DEPLOYMENT_GUIDE.md` | Guide complet de déploiement et troubleshooting |
| `README.md` | Ce fichier - Vue d'ensemble |

---

## 🚀 Démarrage Rapide

**1. Depuis votre PC Windows:**

```bash
cd C:\Users\henri\Projets\lucide\infrastructure\aws
bash deploy-lucide-minimal.sh
```

**2. Se connecter à l'instance:**

```bash
ssh -i ~/.ssh/lucide-key-2025.pem ec2-user@<IP_PUBLIQUE>
```

**3. Configurer Lucide sur l'instance:**

```bash
curl -o setup.sh https://raw.githubusercontent.com/VOTRE_USERNAME/lucide/main/infrastructure/aws/setup-lucide-on-ec2.sh
chmod +x setup.sh
./setup.sh
```

📖 **Guide détaillé:** Consultez `QUICK_START.md`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Instance EC2 t3a.small          │
│          (2 vCPU, 2 GB RAM)             │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Nginx (Port 80)                 │ │
│  │   - Reverse Proxy                 │ │
│  │   - Health checks                 │ │
│  └────────┬──────────────────────────┘ │
│           │                             │
│  ┌────────▼──────────────────────────┐ │
│  │   Backend FastAPI (Port 8000)    │ │
│  │   - API REST                      │ │
│  │   - LLM DeepSeek                  │ │
│  │   - Football API                  │ │
│  └────────┬──────────────────────────┘ │
│           │                             │
│  ┌────────▼──────────────────────────┐ │
│  │   Telegram Bot                    │ │
│  │   - Webhook / Polling             │ │
│  │   - Handlers                      │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   PostgreSQL (Port 5432)          │ │
│  │   - Base de données principale    │ │
│  │   - 512 MB RAM                    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Redis (Port 6379)               │ │
│  │   - Cache analyses                │ │
│  │   - 64 MB RAM                     │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 💰 Coût Estimé

### Configuration t3a.small

```
Instance t3a.small:     $13.50/mois
EBS 30 GB gp3:          $2.40/mois
Bande passante:         $0-2/mois
Elastic IP (optionnel): $3.60/mois
────────────────────────────────────
TOTAL (sans EIP):       ~$16-18/mois
TOTAL (avec EIP):       ~$20-22/mois

Budget disponible: $38
Durée estimée: ~2 mois de test complet
```

---

## 🔧 Limites Mémoire par Service

Configuration optimisée pour **2 GB RAM totale** :

| Service | Limite | Réservation | % RAM |
|---------|--------|-------------|-------|
| PostgreSQL | 512 MB | 256 MB | 25% |
| Backend | 384 MB | 256 MB | 19% |
| Telegram Bot | 256 MB | 128 MB | 13% |
| Redis | 128 MB | 64 MB | 6% |
| Nginx | 64 MB | 32 MB | 3% |
| **TOTAL** | **1344 MB** | **736 MB** | **67%** |
| Système | - | ~660 MB | 33% |

---

## 📊 Monitoring

### Vérifier l'état des services

```bash
# Sur l'instance EC2
docker-compose -f /opt/lucide/lucide/infrastructure/aws/docker-compose.aws-minimal.yml ps

# Usage mémoire
free -h
docker stats

# Logs
docker-compose -f /opt/lucide/lucide/infrastructure/aws/docker-compose.aws-minimal.yml logs -f
```

### Health Checks

```bash
# Nginx
curl http://localhost/health

# Backend API
curl http://localhost/api/health

# Depuis l'extérieur
curl http://<IP_PUBLIQUE>/health
```

---

## 🔐 Sécurité

### Générer des secrets sécurisés

```bash
# Sur l'instance EC2
bash /opt/lucide/lucide/infrastructure/aws/generate-secrets.sh
```

### Secrets à configurer dans `.env`

```bash
DB_PASSWORD=<généré_par_script>
SECRET_KEY=<généré_par_script>
JWT_SECRET=<généré_par_script>
```

### Security Group

Le script de déploiement configure automatiquement:
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS)
- Port 8000 (API Backend)

---

## 🛠️ Commandes Utiles

### Gestion des services

```bash
# Redémarrer tous les services
docker-compose restart

# Redémarrer un service spécifique
docker-compose restart telegram_bot
docker-compose restart backend

# Arrêter tous les services
docker-compose down

# Démarrer avec rebuild
docker-compose up -d --build

# Voir les logs
docker-compose logs -f telegram_bot
```

### Gestion de l'instance

```bash
# Arrêter l'instance (économise le compute)
aws ec2 stop-instances --instance-ids <INSTANCE_ID> --region eu-west-1

# Démarrer l'instance
aws ec2 start-instances --instance-ids <INSTANCE_ID> --region eu-west-1

# Récupérer l'IP publique
aws ec2 describe-instances \
  --instance-ids <INSTANCE_ID> \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text \
  --region eu-west-1
```

---

## 🆘 Dépannage

### Bot ne répond pas

```bash
# 1. Vérifier que le bot tourne
docker-compose ps

# 2. Voir les logs
docker-compose logs telegram_bot

# 3. Redémarrer le bot
docker-compose restart telegram_bot
```

### Manque de mémoire

```bash
# Activer 1 GB de swap
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Docker ne démarre pas

```bash
# Vérifier le service
sudo systemctl status docker

# Redémarrer Docker
sudo systemctl restart docker

# Voir les logs
sudo journalctl -u docker -f
```

---

## 📚 Documentation Complète

- **Démarrage rapide:** `QUICK_START.md`
- **Guide complet:** `DEPLOYMENT_GUIDE.md`
- **Tests locaux:** `../backend/telegram/LOCAL_TESTING.md`

---

## ✅ Checklist de Déploiement

- [ ] AWS CLI configuré
- [ ] Script de déploiement exécuté
- [ ] Instance EC2 accessible en SSH
- [ ] Repository cloné sur l'instance
- [ ] Fichier `.env` configuré
- [ ] Secrets générés et configurés
- [ ] Services Docker lancés
- [ ] Base de données initialisée
- [ ] Health checks répondent
- [ ] Bot Telegram répond à `/start`
- [ ] Logs vérifiés (pas d'erreurs)

---

**Prêt à déployer ?** 🚀 Consultez `QUICK_START.md` pour commencer !
