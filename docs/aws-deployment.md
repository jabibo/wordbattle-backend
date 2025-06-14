# AWS Deployment Guide

This guide provides multiple options for deploying the WordBattle backend to AWS, from simple container deployments to production-ready architectures.

## 🚀 Deployment Options

1. **[AWS App Runner](#option-1-aws-app-runner)** - Simplest, fully managed (Recommended for MVP)
2. **[Amazon ECS with Fargate](#option-2-amazon-ecs-with-fargate)** - Serverless containers
3. **[Amazon EKS](#option-3-amazon-eks)** - Kubernetes for advanced use cases
4. **[AWS Lambda](#option-4-aws-lambda)** - Serverless functions
5. **[EC2 with Docker](#option-5-ec2-with-docker)** - Traditional VPS approach

---

## Option 1: AWS App Runner (Recommended)

**Best for**: Quick deployment, MVP, low maintenance
**Cost**: ~$25-50/month for small apps
**Complexity**: ⭐⭐☆☆☆

### Prerequisites
- AWS CLI configured
- Docker image pushed to ECR or GitHub repository

### Step 1: Prepare Your Container

Create a production Dockerfile:

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory and add sample wordlists
RUN mkdir -p data && \
    echo -e "HALLO\nWELT\nTEST\nSPIEL\nWORT\nTAG\nTAGE\nBAUM" > data/de_words.txt && \
    echo -e "HELLO\nWORLD\nTEST\nGAME\nWORD\nDAY\nDAYS\nTREE" > data/en_words.txt

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Push to Amazon ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name wordbattle-backend --region eu-central-1

# Get login token
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-central-1.amazonaws.com

# Build and tag image
docker build -f Dockerfile.prod -t wordbattle-backend .
docker tag wordbattle-backend:latest <account-id>.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:latest

# Push image
docker push <account-id>.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:latest
```

### Step 3: Create RDS Database

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
    --db-instance-identifier wordbattle-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username postgres \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-name wordbattle \
    --backup-retention-period 7 \
    --storage-encrypted
```

### Step 4: Create App Runner Service

Create `apprunner.yaml`:

```yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "No build commands needed for pre-built image"
run:
  runtime-version: latest
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
    env:
      - name: DATABASE_URL
        value: postgresql://postgres:YourSecurePassword123!@wordbattle-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/wordbattle
      - name: SECRET_KEY
        value: your-super-secret-key-here-make-it-long-and-random
      - name: SMTP_SERVER
        value: smtp.strato.de
      - name: SMTP_PORT
        value: "465"
      - name: SMTP_USE_SSL
        value: "true"
      - name: SMTP_USERNAME
        value: jan@binge-dev.de
      - name: SMTP_PASSWORD
        value: q2NvW4J1%tcAyJSg8
      - name: FROM_EMAIL
        value: jan@binge-dev.de
      - name: CORS_ORIGINS
        value: "*"
```

Deploy with AWS CLI:

```bash
aws apprunner create-service \
    --service-name wordbattle-backend \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/wordbattle-backend:latest",
            "ImageConfiguration": {
                "Port": "8000",
                "RuntimeEnvironmentVariables": {
                    "DATABASE_URL": "postgresql://postgres:YourSecurePassword123!@wordbattle-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/wordbattle",
                    "SECRET_KEY": "your-super-secret-key-here"
                }
            },
            "ImageRepositoryType": "ECR"
        },
        "AutoDeploymentsEnabled": true
    }' \
    --instance-configuration '{
        "Cpu": "0.25 vCPU",
        "Memory": "0.5 GB"
    }'
```

---

## Option 2: Amazon ECS with Fargate

**Best for**: Production apps, auto-scaling, load balancing
**Cost**: ~$30-100/month depending on usage
**Complexity**: ⭐⭐⭐☆☆

### Step 1: Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name wordbattle-cluster --capacity-providers FARGATE
```

### Step 2: Create Task Definition

Create `task-definition.json`:

```json
{
    "family": "wordbattle-backend",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "256",
    "memory": "512",
    "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "wordbattle-backend",
            "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/wordbattle-backend:latest",
            "portMappings": [
                {
                    "containerPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "DATABASE_URL",
                    "value": "postgresql://postgres:password@wordbattle-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/wordbattle"
                },
                {
                    "name": "SECRET_KEY",
                    "value": "your-super-secret-key"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/wordbattle-backend",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 3: Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name wordbattle-alb \
    --subnets subnet-xxxxxxxxx subnet-yyyyyyyyy \
    --security-groups sg-xxxxxxxxx

# Create target group
aws elbv2 create-target-group \
    --name wordbattle-targets \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-xxxxxxxxx \
    --target-type ip \
    --health-check-path /health

# Create listener
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:account-id:loadbalancer/app/wordbattle-alb/xxxxxxxxx \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:account-id:targetgroup/wordbattle-targets/xxxxxxxxx
```

### Step 4: Create ECS Service

```bash
aws ecs create-service \
    --cluster wordbattle-cluster \
    --service-name wordbattle-service \
    --task-definition wordbattle-backend:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxxx,subnet-yyyyyyyyy],securityGroups=[sg-xxxxxxxxx],assignPublicIp=ENABLED}" \
    --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:account-id:targetgroup/wordbattle-targets/xxxxxxxxx,containerName=wordbattle-backend,containerPort=8000
```

---

## Option 3: Amazon EKS

**Best for**: Large-scale applications, microservices, advanced orchestration
**Cost**: ~$75-200/month minimum
**Complexity**: ⭐⭐⭐⭐⭐

### Step 1: Create EKS Cluster

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create cluster
eksctl create cluster \
    --name wordbattle-cluster \
    --region us-east-1 \
    --nodegroup-name standard-workers \
    --node-type t3.medium \
    --nodes 2 \
    --nodes-min 1 \
    --nodes-max 4 \
    --managed
```

### Step 2: Create Kubernetes Manifests

Create `k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: wordbattle
```

Create `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: wordbattle-config
  namespace: wordbattle
data:
  CORS_ORIGINS: "*"
  SMTP_SERVER: "smtp.strato.de"
  SMTP_PORT: "465"
  SMTP_USE_SSL: "true"
  FROM_EMAIL: "jan@binge-dev.de"
```

Create `k8s/secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: wordbattle-secrets
  namespace: wordbattle
type: Opaque
stringData:
  DATABASE_URL: "postgresql://postgres:password@wordbattle-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/wordbattle"
  SECRET_KEY: "your-super-secret-key"
  SMTP_USERNAME: "jan@binge-dev.de"
  SMTP_PASSWORD: "q2NvW4J1%tcAyJSg8"
```

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordbattle-backend
  namespace: wordbattle
spec:
  replicas: 3
  selector:
    matchLabels:
      app: wordbattle-backend
  template:
    metadata:
      labels:
        app: wordbattle-backend
    spec:
      containers:
      - name: wordbattle-backend
        image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/wordbattle-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: wordbattle-config
        - secretRef:
            name: wordbattle-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

Create `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: wordbattle-service
  namespace: wordbattle
spec:
  selector:
    app: wordbattle-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:

```bash
kubectl apply -f k8s/
```

---

## Option 4: AWS Lambda

**Best for**: Serverless, pay-per-request, low traffic
**Cost**: ~$5-20/month for small apps
**Complexity**: ⭐⭐⭐☆☆

### Step 1: Install Mangum

Add to `requirements.txt`:

```txt
mangum==0.17.0
```

### Step 2: Create Lambda Handler

Create `lambda_handler.py`:

```python
from mangum import Mangum
from app.main import app

# Wrap FastAPI app for Lambda
handler = Mangum(app, lifespan="off")
```

### Step 3: Create Deployment Package

```bash
# Create deployment package
pip install -r requirements.txt -t package/
cp -r app/ package/
cp lambda_handler.py package/
cd package && zip -r ../wordbattle-lambda.zip . && cd ..
```

### Step 4: Deploy with AWS CLI

```bash
# Create Lambda function
aws lambda create-function \
    --function-name wordbattle-backend \
    --runtime python3.11 \
    --role arn:aws:iam::<account-id>:role/lambda-execution-role \
    --handler lambda_handler.handler \
    --zip-file fileb://wordbattle-lambda.zip \
    --timeout 30 \
    --memory-size 512 \
    --environment Variables='{
        "DATABASE_URL":"postgresql://postgres:password@wordbattle-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/wordbattle",
        "SECRET_KEY":"your-super-secret-key"
    }'

# Create API Gateway
aws apigatewayv2 create-api \
    --name wordbattle-api \
    --protocol-type HTTP \
    --target arn:aws:lambda:us-east-1:<account-id>:function:wordbattle-backend
```

---

## Option 5: EC2 with Docker

**Best for**: Full control, custom configurations
**Cost**: ~$10-50/month
**Complexity**: ⭐⭐⭐⭐☆

### Step 1: Launch EC2 Instance

```bash
# Launch Ubuntu instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t3.micro \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --associate-public-ip-address
```

### Step 2: Install Docker

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker
```

### Step 3: Deploy Application

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/wordbattle-backend:latest
    ports:
      - "80:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@wordbattle-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/wordbattle
      - SECRET_KEY=your-super-secret-key
      - SMTP_SERVER=smtp.strato.de
      - SMTP_PORT=465
      - SMTP_USE_SSL=true
      - SMTP_USERNAME=jan@binge-dev.de
      - SMTP_PASSWORD=q2NvW4J1%tcAyJSg8
      - FROM_EMAIL=jan@binge-dev.de
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Deploy:

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔧 Additional AWS Services

### RDS Database Setup

```bash
# Create subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name wordbattle-subnet-group \
    --db-subnet-group-description "Subnet group for WordBattle" \
    --subnet-ids subnet-xxxxxxxxx subnet-yyyyyyyyy

# Create parameter group for optimizations
aws rds create-db-parameter-group \
    --db-parameter-group-name wordbattle-params \
    --db-parameter-group-family postgres14 \
    --description "WordBattle PostgreSQL parameters"

# Create database
aws rds create-db-instance \
    --db-instance-identifier wordbattle-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 14.9 \
    --master-username postgres \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --storage-type gp2 \
    --db-subnet-group-name wordbattle-subnet-group \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-name wordbattle \
    --backup-retention-period 7 \
    --storage-encrypted \
    --db-parameter-group-name wordbattle-params \
    --deletion-protection
```

### CloudFront CDN Setup

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
    --distribution-config '{
        "CallerReference": "wordbattle-'$(date +%s)'",
        "Comment": "WordBattle API CDN",
        "DefaultCacheBehavior": {
            "TargetOriginId": "wordbattle-api",
            "ViewerProtocolPolicy": "redirect-to-https",
            "TrustedSigners": {
                "Enabled": false,
                "Quantity": 0
            },
            "ForwardedValues": {
                "QueryString": true,
                "Cookies": {"Forward": "all"},
                "Headers": {
                    "Quantity": 3,
                    "Items": ["Authorization", "Content-Type", "Accept"]
                }
            },
            "MinTTL": 0,
            "DefaultTTL": 0,
            "MaxTTL": 0
        },
        "Origins": {
            "Quantity": 1,
            "Items": [
                {
                    "Id": "wordbattle-api",
                    "DomainName": "your-alb-domain.us-east-1.elb.amazonaws.com",
                    "CustomOriginConfig": {
                        "HTTPPort": 80,
                        "HTTPSPort": 443,
                        "OriginProtocolPolicy": "http-only"
                    }
                }
            ]
        },
        "Enabled": true,
        "PriceClass": "PriceClass_100"
    }'
```

### Route 53 DNS Setup

```bash
# Create hosted zone
aws route53 create-hosted-zone \
    --name api.wordbattle.com \
    --caller-reference wordbattle-$(date +%s)

# Create A record pointing to ALB
aws route53 change-resource-record-sets \
    --hosted-zone-id Z1234567890ABC \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "api.wordbattle.com",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "your-alb-domain.us-east-1.elb.amazonaws.com",
                    "EvaluateTargetHealth": false,
                    "HostedZoneId": "Z35SXDOTRQ7X7K"
                }
            }
        }]
    }'
```

---

## 🔒 Security Best Practices

### 1. Environment Variables

Never hardcode secrets. Use AWS Systems Manager Parameter Store:

```bash
# Store secrets
aws ssm put-parameter \
    --name "/wordbattle/database-url" \
    --value "postgresql://postgres:password@wordbattle-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/wordbattle" \
    --type "SecureString"

aws ssm put-parameter \
    --name "/wordbattle/secret-key" \
    --value "your-super-secret-key" \
    --type "SecureString"
```

### 2. Security Groups

Create restrictive security groups:

```bash
# Create security group for ALB
aws ec2 create-security-group \
    --group-name wordbattle-alb-sg \
    --description "Security group for WordBattle ALB"

# Allow HTTP/HTTPS from anywhere
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# Create security group for ECS tasks
aws ec2 create-security-group \
    --group-name wordbattle-ecs-sg \
    --description "Security group for WordBattle ECS tasks"

# Allow traffic from ALB only
aws ec2 authorize-security-group-ingress \
    --group-id sg-yyyyyyyyy \
    --protocol tcp \
    --port 8000 \
    --source-group sg-xxxxxxxxx
```

### 3. IAM Roles

Create minimal IAM roles:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/wordbattle/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## 📊 Monitoring and Logging

### CloudWatch Setup

```bash
# Create log group
aws logs create-log-group --log-group-name /aws/ecs/wordbattle-backend

# Create custom metrics
aws cloudwatch put-metric-alarm \
    --alarm-name "WordBattle-HighCPU" \
    --alarm-description "WordBattle high CPU usage" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2
```

### Health Check Endpoint

Add to your FastAPI app:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

---

## 💰 Cost Optimization

### 1. Use Spot Instances (ECS/EKS)

```bash
# ECS with Spot instances
aws ecs put-cluster-capacity-providers \
    --cluster wordbattle-cluster \
    --capacity-providers FARGATE_SPOT \
    --default-capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1
```

### 2. Auto Scaling

```bash
# Create auto scaling target
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/wordbattle-cluster/wordbattle-service \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 1 \
    --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id service/wordbattle-cluster/wordbattle-service \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-name wordbattle-scaling-policy \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        }
    }'
```

---

## 🚀 CI/CD Pipeline

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: wordbattle-backend
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -f Dockerfile.prod -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
    
    - name: Update ECS service
      run: |
        aws ecs update-service \
          --cluster wordbattle-cluster \
          --service wordbattle-service \
          --force-new-deployment
```

---

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Create AWS account and configure CLI
- [ ] Generate strong SECRET_KEY
- [ ] Set up email credentials
- [ ] Choose deployment option
- [ ] Create RDS database
- [ ] Configure security groups
- [ ] Set up domain name (optional)

### Post-deployment
- [ ] Test all API endpoints
- [ ] Verify email sending works
- [ ] Set up monitoring and alerts
- [ ] Configure auto-scaling
- [ ] Set up backups
- [ ] Document access URLs
- [ ] Test disaster recovery

### Production Readiness
- [ ] Enable HTTPS/SSL
- [ ] Set up CDN (CloudFront)
- [ ] Configure rate limiting
- [ ] Set up log aggregation
- [ ] Enable database encryption
- [ ] Set up secrets management
- [ ] Configure CORS properly
- [ ] Test load handling

---

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check security groups
   aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx
   
   # Test database connectivity
   psql -h wordbattle-db.xxxxxxxxx.us-east-1.rds.amazonaws.com -U postgres -d wordbattle
   ```

2. **Container Won't Start**
   ```bash
   # Check ECS logs
   aws logs get-log-events \
     --log-group-name /ecs/wordbattle-backend \
     --log-stream-name ecs/wordbattle-backend/task-id
   ```

3. **High Costs**
   ```bash
   # Check resource usage
   aws ce get-cost-and-usage \
     --time-period Start=2024-01-01,End=2024-01-31 \
     --granularity MONTHLY \
     --metrics BlendedCost
   ```

### Support Resources

- [AWS Documentation](https://docs.aws.amazon.com/)
- [AWS Support](https://aws.amazon.com/support/)
- [AWS Cost Calculator](https://calculator.aws/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

---

## 🎯 Recommended Approach

For most users, I recommend starting with **AWS App Runner** for its simplicity and managed nature. As your application grows, you can migrate to ECS with Fargate for more control and features.

**Progression Path:**
1. Start with App Runner for MVP
2. Move to ECS Fargate for production
3. Consider EKS for microservices architecture
4. Add Lambda for specific serverless functions

This approach balances simplicity, cost, and scalability as your application evolves. 