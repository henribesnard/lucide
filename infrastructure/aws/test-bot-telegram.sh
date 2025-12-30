#!/bin/bash
# Script pour tester le bot Telegram après résolution du conflit

echo "=== Test du Bot Telegram Lucide ==="
echo ""

# Arrêter toutes les instances locales potentielles
echo "[1/4] Arrêt de toutes les instances Python locales..."
pkill -f "python.*telegram" || echo "Aucune instance locale trouvée"

echo ""
echo "[2/4] Attente de 5 secondes..."
sleep 5

echo ""
echo "[3/4] Redémarrage du bot sur AWS..."
ssh -o StrictHostKeyChecking=no -i ~/.ssh/lucide-key-2025.pem ec2-user@52.16.82.16 << 'ENDSSH'
cd /opt/lucide/lucide/infrastructure/aws
docker-compose -f docker-compose.aws-minimal.yml restart telegram_bot
sleep 5
ENDSSH

echo ""
echo "[4/4] Vérification des logs..."
ssh -o StrictHostKeyChecking=no -i ~/.ssh/lucide-key-2025.pem ec2-user@52.16.82.16 << 'ENDSSH'
echo "Logs du bot (dernières 25 lignes):"
docker logs lucide_telegram_bot --tail 25 2>&1 | tail -25

echo ""
echo "Vérification du statut:"
if docker logs lucide_telegram_bot --tail 10 2>&1 | grep -q "Conflict"; then
    echo "❌ CONFLIT DÉTECTÉ - Une autre instance tourne encore"
    echo ""
    echo "Actions à faire:"
    echo "1. Arrêtez toutes les instances Python sur votre PC"
    echo "2. Vérifiez: Get-Process python (PowerShell)"
    echo "3. Arrêtez: Get-Process python | Stop-Process -Force"
else
    echo "✅ Bot démarré avec succès - Aucun conflit"
    echo ""
    echo "Testez maintenant sur Telegram:"
    echo "1. Ouvrez Telegram"
    echo "2. Cherchez @lucidebot"
    echo "3. Envoyez /start"
fi
ENDSSH

echo ""
echo "=== Test terminé ==="
