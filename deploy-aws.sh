#!/bin/bash
set -e

# Load environment variables
source deploy.testing.env

# Set AWS credentials and region
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-west-2}

# Set environment to AWS
export CLOUD_PROVIDER=aws

echo "🚀 Deploying to AWS..."

# Build and tag Docker image
echo "📦 Building Docker image..."
docker build -t wordbattle-backend:latest .

# Login to ECR
echo "🔑 Logging in to ECR..."
aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com

# Tag and push image to ECR
echo "⬆️ Pushing image to ECR..."
docker tag wordbattle-backend:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/wordbattle-backend:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/wordbattle-backend:latest

# Update ECS service
echo "🔄 Updating ECS service..."
aws ecs update-service \
    --cluster wordbattle-cluster \
    --service wordbattle-backend \
    --force-new-deployment

echo "✅ Deployment to AWS complete!" 