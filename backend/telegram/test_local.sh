#!/bin/bash
# Script de test local pour le bot Telegram Lucide
# Usage: ./test_local.sh [polling|webhook|tests]

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Lucide Telegram Bot - Test Local ===${NC}\n"

# Vérifier .env
if [ ! -f .env ]; then
    echo -e "${RED}Erreur: Fichier .env manquant${NC}"
    echo "Copier .env.example vers .env et configurer votre token:"
    echo "  cp .env.example .env"
    echo "  nano .env  # Ajouter votre TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Charger .env
export $(grep -v '^#' .env | xargs)

# Vérifier le token
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
    echo -e "${RED}Erreur: TELEGRAM_BOT_TOKEN non configuré${NC}"
    echo "Obtenez un token via @BotFather sur Telegram"
    exit 1
fi

MODE=${1:-polling}

case $MODE in
    polling)
        echo -e "${GREEN}Mode: Polling (Développement)${NC}"
        echo "Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."
        echo "Press Ctrl+C to stop"
        echo ""
        python -m backend.telegram.run_bot
        ;;

    webhook)
        echo -e "${GREEN}Mode: Webhook (Production Simulée)${NC}"
        echo "Assurez-vous qu'un tunnel (ngrok/localtunnel) est actif"
        echo "WEBHOOK_URL: $TELEGRAM_WEBHOOK_URL"
        echo ""
        python -m backend.telegram.run_bot --webhook --port 8443
        ;;

    tests)
        echo -e "${GREEN}Mode: Tests Automatisés${NC}"
        echo "Exécution de la suite de tests complète..."
        echo ""
        DATABASE_URL="sqlite:///:memory:" pytest -v --cov=. --cov-report=term-missing
        ;;

    quick-test)
        echo -e "${GREEN}Mode: Test Rapide${NC}"
        echo "Tests unitaires uniquement..."
        echo ""
        DATABASE_URL="sqlite:///:memory:" pytest tests/unit/ -v
        ;;

    *)
        echo "Usage: $0 [polling|webhook|tests|quick-test]"
        echo ""
        echo "Modes:"
        echo "  polling     - Lance le bot en mode polling (dev local)"
        echo "  webhook     - Lance le bot en mode webhook (nécessite ngrok)"
        echo "  tests       - Exécute tous les tests avec couverture"
        echo "  quick-test  - Exécute les tests unitaires uniquement"
        exit 1
        ;;
esac
