#!/bin/bash
# Script de configuration automatique de Lucide sur EC2
# À exécuter APRÈS le déploiement de l'instance EC2

set -e

echo "=== Configuration de Lucide sur EC2 ==="
echo ""

# 1. Vérifier que Docker est installé
echo "[1/6] Vérification de Docker..."
if ! command -v docker &> /dev/null; then
    echo "ERREUR: Docker n'est pas installé. Attendez la fin de l'initialisation de l'instance."
    echo "Vérifiez: cat /var/log/user-data.log"
    exit 1
fi
docker --version
echo "[OK] Docker installé"
echo ""

# 2. Vérifier que Docker Compose est installé
echo "[2/6] Vérification de Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "ERREUR: Docker Compose n'est pas installé."
    exit 1
fi
docker-compose --version
echo "[OK] Docker Compose installé"
echo ""

# 3. Cloner le repo Lucide
echo "[3/6] Clonage du repository Lucide..."
cd /opt/lucide

# Demander l'URL du repo
read -p "URL du repository Git (ex: https://github.com/VOTRE_USERNAME/lucide.git): " REPO_URL

if [ -d "lucide" ]; then
    echo "Le dossier lucide existe déjà. Mise à jour..."
    cd lucide
    git pull
else
    git clone "$REPO_URL" lucide
    cd lucide
fi

echo "[OK] Repository cloné/mis à jour"
echo ""

# 4. Créer le fichier .env
echo "[4/6] Configuration de l'environnement..."
cd infrastructure/aws

if [ -f ".env" ]; then
    echo "Le fichier .env existe déjà."
    read -p "Voulez-vous le remplacer ? (y/N): " REPLACE
    if [ "$REPLACE" != "y" ] && [ "$REPLACE" != "Y" ]; then
        echo "Conservation du .env existant"
    else
        rm .env
        cp .env.example .env
        echo "Nouveau .env créé depuis le template"
    fi
else
    cp .env.example .env
    echo "[OK] Fichier .env créé depuis le template"
fi

echo ""
echo "IMPORTANT: Éditez le fichier .env pour configurer vos secrets !"
echo ""
read -p "Voulez-vous éditer le .env maintenant ? (Y/n): " EDIT_ENV
if [ "$EDIT_ENV" != "n" ] && [ "$EDIT_ENV" != "N" ]; then
    nano .env
fi

# Récupérer l'IP publique de l'instance
PUBLIC_IP=$(curl -s ifconfig.me)
echo ""
echo "Votre IP publique: $PUBLIC_IP"
echo ""

# Proposer de configurer le webhook
read -p "Voulez-vous configurer le webhook Telegram avec cette IP ? (y/N): " SETUP_WEBHOOK
if [ "$SETUP_WEBHOOK" = "y" ] || [ "$SETUP_WEBHOOK" = "Y" ]; then
    # Ajouter/modifier TELEGRAM_WEBHOOK_URL dans .env
    if grep -q "^TELEGRAM_WEBHOOK_URL=" .env; then
        sed -i "s|^TELEGRAM_WEBHOOK_URL=.*|TELEGRAM_WEBHOOK_URL=http://$PUBLIC_IP/telegram/webhook|" .env
    else
        echo "TELEGRAM_WEBHOOK_URL=http://$PUBLIC_IP/telegram/webhook" >> .env
    fi
    echo "[OK] Webhook configuré dans .env"
else
    echo "Mode polling sera utilisé (TELEGRAM_WEBHOOK_URL vide)"
fi

echo ""

# 5. Lancer les services Docker
echo "[5/6] Démarrage des services Docker..."
docker-compose -f docker-compose.aws-minimal.yml up -d

echo "[OK] Services Docker démarrés"
echo ""

# 6. Attendre que les services soient prêts
echo "[6/6] Attente du démarrage des services (30 secondes)..."
sleep 30

# Vérifier que les services tournent
echo ""
echo "État des services:"
docker-compose -f docker-compose.aws-minimal.yml ps

echo ""
echo "==================================="
echo "CONFIGURATION TERMINÉE AVEC SUCCÈS"
echo "==================================="
echo ""
echo "Prochaines étapes:"
echo ""
echo "1. Vérifier les logs:"
echo "   docker-compose -f docker-compose.aws-minimal.yml logs -f"
echo ""
echo "2. Tester l'API:"
echo "   curl http://localhost/health"
echo "   curl http://$PUBLIC_IP/health"
echo ""
echo "3. Tester le bot Telegram:"
echo "   Cherchez @lucidebot sur Telegram et envoyez /start"
echo ""
echo "4. Monitoring:"
echo "   docker stats"
echo "   free -h"
echo ""
echo "Services accessibles:"
echo "   - API: http://$PUBLIC_IP"
echo "   - Health: http://$PUBLIC_IP/health"
echo "   - Docs: http://$PUBLIC_IP/docs"
if [ "$SETUP_WEBHOOK" = "y" ] || [ "$SETUP_WEBHOOK" = "Y" ]; then
    echo "   - Webhook: http://$PUBLIC_IP/telegram/webhook"
fi
echo ""
