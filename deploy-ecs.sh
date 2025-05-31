#!/bin/bash

echo "Starting ECS deployment as alternative to App Runner..."

# Set variables
STACK_NAME="wordbattle-ecs"
IMAGE_TAG="working-exact"
REGION="eu-central-1"

echo "Deploying CloudFormation stack: $STACK_NAME"

# Deploy the CloudFormation stack
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://ecs-deployment.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=ImageTag,ParameterValue=$IMAGE_TAG \
  --region $REGION

if [ $? -eq 0 ]; then
    echo "CloudFormation stack creation initiated successfully"
    echo "Waiting for stack to complete..."
    
    # Wait for stack creation to complete
    aws cloudformation wait stack-create-complete \
      --stack-name $STACK_NAME \
      --region $REGION
    
    if [ $? -eq 0 ]; then
        echo "Stack created successfully!"
        
        # Get the load balancer URL
        ALB_URL=$(aws cloudformation describe-stacks \
          --stack-name $STACK_NAME \
          --region $REGION \
          --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
          --output text)
        
        echo "Application deployed successfully!"
        echo "Load Balancer URL: $ALB_URL"
        echo "Health check: $ALB_URL/health"
        echo "Debug tokens: $ALB_URL/debug/tokens"
        
    else
        echo "Stack creation failed. Check CloudFormation console for details."
        exit 1
    fi
else
    echo "Failed to initiate stack creation"
    exit 1
fi 