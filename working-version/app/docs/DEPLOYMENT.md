# 🚀 WordBattle Backend Deployment Guide

This guide provides step-by-step instructions for deploying the WordBattle backend to AWS using multiple deployment strategies.

## 📋 Prerequisites

Before deploying, ensure you have:

- **AWS Account** with appropriate permissions
- **AWS CLI** installed and configured
- **Docker** installed and running
- **Terraform** (optional, for infrastructure as code)
- **Git** for version control

## 🎯 Quick Start (Recommended)

The fastest way to deploy is using our automated script:

### For Linux/macOS (Bash):
```bash
# Make the script executable
chmod +x deploy/aws-app-runner.sh

# Run the deployment
./deploy/aws-app-runner.sh
```

### For Windows (PowerShell):
```powershell
# Run the PowerShell deployment script
.\deploy\aws-app-runner.ps1
```

This script will:
- ✅ Create ECR repository
- ✅ Build and push Docker image
- ✅ Create RDS PostgreSQL database
- ✅ Deploy App Runner service
- ✅ Configure networking and security
- ✅ Test the deployment

## 🔧 Manual Deployment Options

### Option 1: AWS App Runner (Simplest)

**Best for**: MVP, quick deployment, low maintenance
**Cost**: ~$25-50/month
**Complexity**: ⭐⭐☆☆☆

#### Step 1: Build and Push Docker Image

```bash
# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="eu-central-1"
REPOSITORY_NAME="wordbattle-backend"

# Create ECR repository
aws ecr create-repository --repository-name $REPOSITORY_NAME --region $REGION

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build and push image
docker build -f Dockerfile.prod -t $REPOSITORY_NAME .
docker tag $REPOSITORY_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:latest
```

#### Step 2: Create Database

```bash
# Generate secure password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier wordbattle-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username postgres \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage 20 \
    --db-name wordbattle \
    --backup-retention-period 7 \
    --storage-encrypted \
    --region $REGION

# Wait for database to be available
aws rds wait db-instance-available --db-instance-identifier wordbattle-db --region $REGION
```

#### Step 3: Create App Runner Service

```bash
# Get database endpoint
DB_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier wordbattle-db --query "DBInstances[0].Endpoint.Address" --output text --region $REGION)

# Create App Runner service configuration
cat > apprunner-config.json << EOF
{
    "ServiceName": "wordbattle-backend",
    "SourceConfiguration": {
        "ImageRepository": {
            "ImageIdentifier": "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME:latest",
            "ImageConfiguration": {
                "Port": "8000",
                "RuntimeEnvironmentVariables": {
                    "DATABASE_URL": "postgresql://postgres:$DB_PASSWORD@$DB_ENDPOINT:5432/wordbattle",
                    "SECRET_KEY": "$(openssl rand -base64 64 | tr -d '=+/' | cut -c1-64)",
                    "SMTP_SERVER": "smtp.strato.de",
                    "SMTP_PORT": "465",
                    "SMTP_USE_SSL": "true",
                    "SMTP_USERNAME": "your-email@domain.com",
                    "SMTP_PASSWORD": "your-email-password",
                    "FROM_EMAIL": "your-email@domain.com",
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

# Create the service
aws apprunner create-service --cli-input-json file://apprunner-config.json --region $REGION
```

### Option 2: Terraform (Infrastructure as Code)

**Best for**: Production environments, team collaboration
**Cost**: ~$30-60/month
**Complexity**: ⭐⭐⭐☆☆

#### Step 1: Configure Terraform

```bash
cd terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
nano terraform.tfvars
```

#### Step 2: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the configuration
terraform apply
```

#### Step 3: Build and Deploy Application

```bash
# Get ECR repository URL from Terraform output
ECR_URL=$(terraform output -raw ecr_repository_url)

# Build and push image
docker build -f Dockerfile.prod -t wordbattle-backend .
docker tag wordbattle-backend:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Trigger App Runner deployment
SERVICE_ARN=$(terraform output -raw app_runner_service_arn)
aws apprunner start-deployment --service-arn $SERVICE_ARN
```

### Option 3: GitHub Actions CI/CD

**Best for**: Automated deployments, team development
**Cost**: Same as base deployment + GitHub Actions minutes
**Complexity**: ⭐⭐⭐⭐☆

#### Step 1: Set up GitHub Secrets

In your GitHub repository, add these secrets:

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_ACCOUNT_ID=your-account-id
SLACK_WEBHOOK_URL=your-slack-webhook (optional)
```

#### Step 2: Push to Main Branch

```bash
git add .
git commit -m "Deploy to AWS"
git push origin main
```

The GitHub Actions workflow will automatically:
- Run tests
- Build Docker image
- Push to ECR
- Deploy to App Runner
- Run health checks

## 🔐 Security Configuration

### Environment Variables

Set these environment variables for production:

```bash
# Required
DATABASE_URL=postgresql://username:password@host:5432/database
SECRET_KEY=your-64-character-secret-key

# Email Configuration
SMTP_SERVER=smtp.your-provider.com
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-email-password
FROM_EMAIL=your-email@domain.com

# Optional
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ENVIRONMENT=production
```

### Database Security

1. **Use strong passwords**: Generate with `openssl rand -base64 32`
2. **Enable encryption**: Always use `storage_encrypted = true`
3. **Restrict access**: Use security groups to limit database access
4. **Regular backups**: Set appropriate backup retention periods

### Network Security

1. **VPC isolation**: Deploy database in private subnets
2. **Security groups**: Restrict traffic to necessary ports only
3. **SSL/TLS**: Use HTTPS for all external communication
4. **WAF**: Consider AWS WAF for additional protection

## 📊 Monitoring and Logging

### CloudWatch Integration

The deployment automatically sets up:

- **Application logs**: `/aws/apprunner/wordbattle-backend`
- **Health checks**: Automatic monitoring of `/health` endpoint
- **Metrics**: CPU, memory, and request metrics

### Custom Monitoring

Add custom metrics to your application:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_custom_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='WordBattle',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
        ]
    )
```

## 🔄 Deployment Strategies

### Blue-Green Deployment

For zero-downtime deployments:

1. Deploy new version to staging environment
2. Run tests against staging
3. Switch traffic to new version
4. Keep old version as backup

### Rolling Updates

App Runner automatically handles rolling updates:

- New instances are created with updated code
- Health checks ensure new instances are healthy
- Old instances are terminated after successful deployment

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check database status
aws rds describe-db-instances --db-instance-identifier wordbattle-db

# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx
```

#### 2. App Runner Service Failed

```bash
# Check service status
aws apprunner describe-service --service-arn your-service-arn

# View logs
aws logs tail /aws/apprunner/wordbattle-backend --follow
```

#### 3. Image Push Failed

```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account-id.dkr.ecr.us-east-1.amazonaws.com

# Check repository exists
aws ecr describe-repositories --repository-names wordbattle-backend
```

### Health Check Endpoints

Test your deployment:

```bash
# Health check
curl https://your-app-url/health

# API documentation
curl https://your-app-url/docs

# Test authentication
curl -X POST https://your-app-url/auth/email-login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## 💰 Cost Optimization

### Development Environment

- Use `db.t3.micro` for database
- Use `0.25 vCPU, 0.5 GB` for App Runner
- Set shorter log retention (7 days)

### Production Environment

- Use `db.t3.small` or larger for database
- Use `0.5 vCPU, 1 GB` or larger for App Runner
- Enable performance insights
- Set longer log retention (30+ days)

### Cost Monitoring

Set up billing alerts:

```bash
aws budgets create-budget \
  --account-id your-account-id \
  --budget file://budget.json
```

## 🔄 Backup and Recovery

### Database Backups

Automated backups are configured with:
- Daily backups during maintenance window
- Point-in-time recovery
- Cross-region backup replication (optional)

### Application Backups

- Docker images are stored in ECR
- Infrastructure code is in Git
- Configuration is in Terraform state

### Disaster Recovery

1. **RTO (Recovery Time Objective)**: < 1 hour
2. **RPO (Recovery Point Objective)**: < 15 minutes
3. **Multi-region deployment**: For critical applications

## 📞 Support

For deployment issues:

1. Check the troubleshooting section above
2. Review AWS CloudWatch logs
3. Consult the [AWS App Runner documentation](https://docs.aws.amazon.com/apprunner/)
4. Open an issue in the GitHub repository

## 🎉 Next Steps

After successful deployment:

1. **Set up monitoring**: Configure CloudWatch alarms
2. **Configure domain**: Set up custom domain with Route 53
3. **SSL certificate**: Use AWS Certificate Manager
4. **CDN**: Set up CloudFront for static assets
5. **Scaling**: Configure auto-scaling policies
6. **Security**: Implement WAF and security headers

---

**Happy Deploying! 🚀**