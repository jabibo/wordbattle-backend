#!/bin/bash

# AWS App Runner Deployment Script for WordBattle Backend
# Usage: ./deploy/aws-app-runner.sh

set -e

# Configuration
REGION="eu-central-1"
REPOSITORY_NAME="wordbattle-backend"
SERVICE_NAME="wordbattle-backend"
DB_INSTANCE_ID="wordbattle-db"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 WordBattle AWS App Runner Deployment${NC}"
echo "=================================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}❌ Failed to get AWS account ID. Please configure AWS CLI.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS Account ID: $ACCOUNT_ID${NC}"

# Step 1: Create ECR repository if it doesn't exist
echo -e "${YELLOW}📦 Creating ECR repository...${NC}"
aws ecr describe-repositories --repository-names $REPOSITORY_NAME --region $REGION 2>/dev/null || \
aws ecr create-repository --repository-name $REPOSITORY_NAME --region $REGION

# Step 2: Login to ECR
echo -e "${YELLOW}🔐 Logging into ECR...${NC}"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Step 3: Build and push Docker image
echo -e "${YELLOW}🏗️ Building Docker image...${NC}"
docker build -f Dockerfile.prod -t $REPOSITORY_NAME .

echo -e "${YELLOW}🏷️ Tagging image...${NC}"
docker tag $REPOSITORY_NAME:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:latest

echo -e "${YELLOW}📤 Pushing image to ECR...${NC}"
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:latest

# Step 4: Create RDS database if it doesn't exist
echo -e "${YELLOW}🗄️ Checking RDS database...${NC}"
if ! aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --region $REGION 2>/dev/null; then
    echo -e "${YELLOW}📊 Creating RDS database...${NC}"
    
    # Generate a random password
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    echo -e "${GREEN}🔑 Generated database password: $DB_PASSWORD${NC}"
    echo -e "${YELLOW}⚠️ Please save this password securely!${NC}"
    
    # Get default VPC and subnets
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $REGION)
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text --region $REGION)
    
    # Create DB subnet group
    aws rds create-db-subnet-group \
        --db-subnet-group-name wordbattle-subnet-group \
        --db-subnet-group-description "Subnet group for WordBattle" \
        --subnet-ids $SUBNET_IDS \
        --region $REGION 2>/dev/null || echo "Subnet group already exists"
    
    # Create security group for RDS
    SG_ID=$(aws ec2 create-security-group \
        --group-name wordbattle-db-sg \
        --description "Security group for WordBattle database" \
        --vpc-id $VPC_ID \
        --region $REGION \
        --query "GroupId" --output text 2>/dev/null || \
        aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=wordbattle-db-sg" \
        --query "SecurityGroups[0].GroupId" --output text --region $REGION)
    
    # Allow PostgreSQL access from anywhere (you should restrict this in production)
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 5432 \
        --cidr 0.0.0.0/0 \
        --region $REGION 2>/dev/null || echo "Security group rule already exists"
    
    # Create RDS instance
    aws rds create-db-instance \
        --db-instance-identifier $DB_INSTANCE_ID \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --master-username postgres \
        --master-user-password "$DB_PASSWORD" \
        --allocated-storage 20 \
        --db-subnet-group-name wordbattle-subnet-group \
        --vpc-security-group-ids $SG_ID \
        --db-name wordbattle \
        --backup-retention-period 7 \
        --storage-encrypted \
        --region $REGION
    
    echo -e "${YELLOW}⏳ Waiting for database to be available (this may take 5-10 minutes)...${NC}"
    aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_ID --region $REGION
    
    # Store password in Systems Manager Parameter Store
    aws ssm put-parameter \
        --name "/wordbattle/db-password" \
        --value "$DB_PASSWORD" \
        --type "SecureString" \
        --region $REGION \
        --overwrite 2>/dev/null || echo "Parameter already exists"
else
    echo -e "${GREEN}✅ RDS database already exists${NC}"
    # Get password from Parameter Store
    DB_PASSWORD=$(aws ssm get-parameter --name "/wordbattle/db-password" --with-decryption --query "Parameter.Value" --output text --region $REGION 2>/dev/null || echo "")
    if [ -z "$DB_PASSWORD" ]; then
        echo -e "${RED}❌ Database password not found in Parameter Store. Please set it manually.${NC}"
        read -s -p "Enter database password: " DB_PASSWORD
        echo
    fi
fi

# Get database endpoint
DB_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --query "DBInstances[0].Endpoint.Address" --output text --region $REGION)
echo -e "${GREEN}✅ Database endpoint: $DB_ENDPOINT${NC}"

# Step 5: Generate a secret key
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)

# Step 6: Create App Runner service
echo -e "${YELLOW}🏃 Creating App Runner service...${NC}"

# Check if service already exists
if aws apprunner describe-service --service-arn "arn:aws:apprunner:$REGION:$ACCOUNT_ID:service/$SERVICE_NAME" --region $REGION 2>/dev/null; then
    echo -e "${YELLOW}🔄 Service exists, updating...${NC}"
    # Update existing service
    aws apprunner start-deployment \
        --service-arn "arn:aws:apprunner:$REGION:$ACCOUNT_ID:service/$SERVICE_NAME" \
        --region $REGION
else
    echo -e "${YELLOW}🆕 Creating new service...${NC}"
    # Create new service
    cat > /tmp/apprunner-config.json << EOF
{
    "ServiceName": "$SERVICE_NAME",
    "SourceConfiguration": {
        "ImageRepository": {
            "ImageIdentifier": "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:latest",
            "ImageConfiguration": {
                "Port": "8000",
                "RuntimeEnvironmentVariables": {
                    "DATABASE_URL": "postgresql://postgres:$DB_PASSWORD@$DB_ENDPOINT:5432/wordbattle",
                    "SECRET_KEY": "$SECRET_KEY",
                    "SMTP_SERVER": "smtp.strato.de",
                    "SMTP_PORT": "465",
                    "SMTP_USE_SSL": "true",
                    "SMTP_USERNAME": "jan@binge-dev.de",
                    "SMTP_PASSWORD": "q2NvW4J1%tcAyJSg8",
                    "FROM_EMAIL": "jan@binge-dev.de",
                    "CORS_ORIGINS": "*",
                    "ENVIRONMENT": "production"
                }
            },
            "ImageRepositoryType": "ECR"
        },
        "AutoDeploymentsEnabled": true
    },
    "InstanceConfiguration": {
        "Cpu": "0.25 vCPU",
        "Memory": "0.5 GB"
    },
    "HealthCheckConfiguration": {
        "Protocol": "HTTP",
        "Path": "/health",
        "Interval": 10,
        "Timeout": 5,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 5
    }
}
EOF

    aws apprunner create-service --cli-input-json file:///tmp/apprunner-config.json --region $REGION
    rm /tmp/apprunner-config.json
fi

# Step 7: Wait for service to be running
echo -e "${YELLOW}⏳ Waiting for App Runner service to be ready...${NC}"
aws apprunner wait service-running --service-arn "arn:aws:apprunner:$REGION:$ACCOUNT_ID:service/$SERVICE_NAME" --region $REGION

# Get service URL
SERVICE_URL=$(aws apprunner describe-service --service-arn "arn:aws:apprunner:$REGION:$ACCOUNT_ID:service/$SERVICE_NAME" --query "Service.ServiceUrl" --output text --region $REGION)

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "=================================================="
echo -e "${GREEN}📍 Service URL: https://$SERVICE_URL${NC}"
echo -e "${GREEN}📚 API Documentation: https://$SERVICE_URL/docs${NC}"
echo -e "${GREEN}❤️ Health Check: https://$SERVICE_URL/health${NC}"
echo ""
echo -e "${YELLOW}📝 Important Information:${NC}"
echo -e "   • Database Password: $DB_PASSWORD"
echo -e "   • Secret Key: $SECRET_KEY"
echo -e "   • Database Endpoint: $DB_ENDPOINT"
echo ""
echo -e "${YELLOW}⚠️ Security Notes:${NC}"
echo -e "   • Change the database password in production"
echo -e "   • Restrict database security group to App Runner only"
echo -e "   • Store secrets in AWS Systems Manager Parameter Store"
echo -e "   • Configure proper CORS origins for production"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -s "https://$SERVICE_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${RED}❌ Health check failed. Check the logs in AWS Console.${NC}"
fi 