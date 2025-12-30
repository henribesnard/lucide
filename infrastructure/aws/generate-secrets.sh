#!/bin/bash
# Génère des clés sécurisées aléatoires pour le fichier .env

echo "=== Génération de Secrets Sécurisés ==="
echo ""
echo "Copiez ces valeurs dans votre fichier .env:"
echo ""

echo "# Mot de passe PostgreSQL"
echo "DB_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)"
echo ""

echo "# Clé secrète pour l'application"
echo "SECRET_KEY=$(openssl rand -hex 32)"
echo ""

echo "# Secret JWT pour l'authentification"
echo "JWT_SECRET=$(openssl rand -hex 32)"
echo ""

echo "=== Secrets générés avec succès ==="
echo ""
echo "IMPORTANT: Ces secrets sont uniques et sécurisés."
echo "Ne les partagez jamais et stockez-les en sécurité !"
