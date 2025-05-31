#!/bin/bash

echo "EC2 Deployment Alternative to App Runner"
echo "========================================"

# Configuration
INSTANCE_TYPE="t3.micro"
KEY_NAME="wordbattle-key"
SECURITY_GROUP_NAME="wordbattle-sg"
IMAGE_TAG="working-exact"

echo "This script will:"
echo "1. Create a security group allowing HTTP traffic"
echo "2. Launch an EC2 instance"
echo "3. Install Docker and deploy the application"
echo ""

# Create security group
echo "Creating security group..."
aws ec2 create-security-group \
  --group-name $SECURITY_GROUP_NAME \
  --description "Security group for WordBattle backend"

# Add rules to security group
aws ec2 authorize-security-group-ingress \
  --group-name $SECURITY_GROUP_NAME \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name $SECURITY_GROUP_NAME \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name $SECURITY_GROUP_NAME \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Create user data script for EC2 instance
cat > user-data.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Login to ECR
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 598510278922.dkr.ecr.eu-central-1.amazonaws.com

# Pull and run the application
docker pull 598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:working-exact

docker run -d \
  --name wordbattle-backend \
  --restart unless-stopped \
  -p 80:8000 \
  -e DB_HOST=wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com \
  -e DB_NAME=wordbattle \
  -e DB_USER=postgres \
  -e DB_PASSWORD=Wordbattle2024 \
  598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:working-exact

# Create a simple health check script
cat > /home/ec2-user/health-check.sh << 'HEALTH_EOF'
#!/bin/bash
curl -f http://localhost/health || echo "Health check failed"
HEALTH_EOF

chmod +x /home/ec2-user/health-check.sh
EOF

echo "Launching EC2 instance..."

# Launch EC2 instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id ami-0e04bcbe83a83792e \
  --count 1 \
  --instance-type $INSTANCE_TYPE \
  --security-groups $SECURITY_GROUP_NAME \
  --user-data file://user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=wordbattle-backend}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Instance ID: $INSTANCE_ID"
echo "Waiting for instance to be running..."

aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo ""
echo "Deployment completed!"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Application URL: http://$PUBLIC_IP"
echo "Health check: http://$PUBLIC_IP/health"
echo "Debug tokens: http://$PUBLIC_IP/debug/tokens"
echo ""
echo "Note: It may take a few minutes for the application to start."
echo "You can SSH to the instance using: ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"

# Clean up user data file
rm -f user-data.sh 