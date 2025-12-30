#!/bin/bash
# Script de déploiement AWS MINIMAL pour Lucide
# Utilise le Free Tier pour minimiser les coûts

set -e

# Configuration
REGION="eu-west-1"
INSTANCE_TYPE="t3a.small"  # Production légère - 2 vCPU, 2 GB RAM
KEY_NAME="lucide-key-2025"
INSTANCE_NAME="lucide-bot"
ACCOUNT_ID="204093577928"

echo "=== Déploiement Lucide sur AWS (Production Légère) ==="
echo "Instance: $INSTANCE_TYPE (2 vCPU, 2 GB RAM)"
echo "Région: $REGION"
echo "Coût estimé: ~$13.50/mois"
echo ""

# 1. Créer la clé SSH si elle n'existe pas
if [ ! -f ~/.ssh/$KEY_NAME.pem ]; then
    echo "Création de la clé SSH..."
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --region $REGION \
        --query 'KeyMaterial' \
        --output text > ~/.ssh/$KEY_NAME.pem

    chmod 400 ~/.ssh/$KEY_NAME.pem
    echo "Clé SSH créée: ~/.ssh/$KEY_NAME.pem"
else
    echo "Clé SSH existante trouvée"
fi

# 2. Créer Security Group
echo "Création du Security Group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name lucide-sg \
    --description "Security group for Lucide Telegram Bot" \
    --region $REGION \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=lucide-sg" \
        --query 'SecurityGroups[0].GroupId' \
        --output text \
        --region $REGION)

echo "Security Group: $SG_ID"

# 3. Configurer les règles (idempotent)
echo "Configuration des règles du Security Group..."

# SSH
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "  SSH déjà configuré"

# HTTP
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "  HTTP déjà configuré"

# HTTPS
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "  HTTPS déjà configuré"

# Backend API (8000)
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "  Port 8000 déjà configuré"

# 4. Trouver l'AMI Amazon Linux 2023
echo "Recherche de l'AMI..."
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023.*-x86_64" \
              "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text \
    --region $REGION)

echo "AMI: $AMI_ID"

# 5. Créer le script d'initialisation
cat > /tmp/lucide-user-data.sh << 'USERDATA'
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
USERDATA

# 6. Lancer l'instance
echo "Lancement de l'instance EC2..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --block-device-mappings '[
        {
            "DeviceName":"/dev/xvda",
            "Ebs":{
                "VolumeSize":30,
                "VolumeType":"gp3",
                "DeleteOnTermination":true
            }
        }
    ]' \
    --tag-specifications "ResourceType=instance,Tags=[
        {Key=Name,Value=$INSTANCE_NAME},
        {Key=Project,Value=Lucide},
        {Key=Environment,Value=development}
    ]" \
    --region $REGION \
    --user-data file:///tmp/lucide-user-data.sh \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance créée: $INSTANCE_ID"

# 7. Attendre démarrage
echo "Attente du démarrage de l'instance..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
echo "Instance démarrée!"

# 8. Récupérer l'IP publique
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text \
    --region $REGION)

# 9. Résumé
echo ""
echo "======================================"
echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
echo "======================================"
echo ""
echo "Instance ID: $INSTANCE_ID"
echo "Security Group: $SG_ID"
echo "IP Publique: $PUBLIC_IP"
echo "Type: $INSTANCE_TYPE (FREE TIER)"
echo ""
echo "Connexion SSH:"
echo "  ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo ""
echo "IMPORTANT:"
echo "  1. Attendre 2-3 minutes pour l'initialisation complète"
echo "  2. Vérifier les logs: ssh ... 'cat /var/log/user-data.log'"
echo "  3. L'IP publique changera si vous arrêtez/redémarrez l'instance"
echo "     (Utilisez Elastic IP pour une IP fixe - coût: $3.60/mois)"
echo ""
echo "Coût estimé:"
echo "  - Instance t3a.small: ~$13.50/mois"
echo "  - EBS 30 GB gp3: ~$2.40/mois"
echo "  - Bande passante: ~$0-2/mois"
echo "  TOTAL: ~$16-18/mois"
echo ""
echo "Budget disponible: $38"
echo "Durée avec budget: ~2 mois de test complet"
echo ""
