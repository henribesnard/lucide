#!/bin/bash
# Script d'initialisation Lucide

# Logs
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "=== Initialisation Lucide $(date) ==="

# Mise à jour système
yum update -y

# Installer Docker
yum install -y docker git

# Démarrer Docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Installer Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Créer structure
mkdir -p /opt/lucide
chown ec2-user:ec2-user /opt/lucide

# Installer outils utiles
yum install -y htop tmux nano

echo "=== Initialisation terminée $(date) ===" >> /var/log/user-data.log
