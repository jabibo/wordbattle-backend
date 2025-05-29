#!/usr/bin/env python3

import subprocess
import json
import time

def run_command(command, description):
    """Run a shell command and return success status."""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def deploy_frontend_url_fix():
    """Deploy the frontend URL fix to AWS App Runner"""
    
    print("🚀 Deploying Frontend URL Fix to AWS App Runner")
    print("=" * 60)
    
    # Build and push Docker image
    print("\n📦 Building Docker image...")
    
    # Build image
    build_success = run_command(
        'docker build -t wordbattle-backend:frontend-url-fix .',
        "Building Docker image"
    )
    
    if not build_success:
        return False
    
    # Tag for ECR
    tag_success = run_command(
        'docker tag wordbattle-backend:frontend-url-fix 598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:frontend-url-fix',
        "Tagging image for ECR"
    )
    
    if not tag_success:
        return False
    
    # Login to ECR
    login_success = run_command(
        'aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 598510278922.dkr.ecr.eu-central-1.amazonaws.com',
        "Logging in to ECR"
    )
    
    if not login_success:
        return False
    
    # Push image
    push_success = run_command(
        'docker push 598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:frontend-url-fix',
        "Pushing image to ECR"
    )
    
    if not push_success:
        return False
    
    # Create update configuration with FRONTEND_URL
    update_config = {
        "ImageRepository": {
            "ImageIdentifier": "598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:frontend-url-fix",
            "ImageConfiguration": {
                "RuntimeEnvironmentVariables": {
                    "CORS_ORIGINS": "*",
                    "DATABASE_URL": "postgresql://postgres:Y3RHlw7BACKDFNg6QWmkirhPu@wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com:5432/wordbattle",
                    "ENVIRONMENT": "production",
                    "FROM_EMAIL": "jan@binge-dev.de",
                    "SECRET_KEY": "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
                    "SMTP_PASSWORD": "q2NvW4J1%tcAyJSg8",
                    "SMTP_PORT": "465",
                    "SMTP_SERVER": "smtp.strato.de",
                    "SMTP_USERNAME": "jan@binge-dev.de",
                    "SMTP_USE_SSL": "true",
                    "FRONTEND_URL": "https://your-frontend-domain.com",  # Configure this with your actual frontend URL
                    "BACKEND_URL": "https://mnirejmq3g.eu-central-1.awsapprunner.com"  # Add backend URL for reference
                },
                "Port": "8000"
            },
            "ImageRepositoryType": "ECR"
        },
        "AutoDeploymentsEnabled": True,
        "AuthenticationConfiguration": {
            "AccessRoleArn": "arn:aws:iam::598510278922:role/AppRunnerECRAccessRole"
        }
    }
    
    # Write config to file
    with open('update-frontend-url-config.json', 'w') as f:
        json.dump(update_config, f, indent=2)
    
    # Update App Runner service
    update_success = run_command(
        'aws apprunner update-service --service-arn "arn:aws:apprunner:eu-central-1:598510278922:service/wordbattle-backend/9112212ab18243638c181fdf7da4a9a2" --source-configuration file://update-frontend-url-config.json',
        "Updating App Runner service"
    )
    
    if not update_success:
        return False
    
    print(f"\n✅ Deployment initiated successfully!")
    print(f"🕐 App Runner is now updating the service...")
    print(f"📧 Email links will now use the frontend URL (port 3000)")
    print(f"🔗 Frontend URL: http://localhost:3000")
    print(f"🔗 Backend URL: https://mnirejmq3g.eu-central-1.awsapprunner.com")
    
    # Wait for deployment to complete
    print(f"\n⏳ Waiting for deployment to complete...")
    time.sleep(30)
    
    # Check service status
    status_success = run_command(
        'aws apprunner describe-service --service-arn "arn:aws:apprunner:eu-central-1:598510278922:service/wordbattle-backend/9112212ab18243638c181fdf7da4a9a2" --query "Service.Status" --output text',
        "Checking service status"
    )
    
    print(f"\n🎯 Deployment Summary:")
    print(f"   • Frontend URL configuration added")
    print(f"   • Email templates now use frontend URL for join links")
    print(f"   • Default base_url changed from port 8000 to port 3000")
    print(f"   • Environment variables: FRONTEND_URL and BACKEND_URL")
    
    return True

if __name__ == "__main__":
    success = deploy_frontend_url_fix()
    if success:
        print(f"\n🎉 Frontend URL fix deployed successfully!")
    else:
        print(f"\n💥 Deployment failed!")
        exit(1) 