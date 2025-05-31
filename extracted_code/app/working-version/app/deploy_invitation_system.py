#!/usr/bin/env python3
"""
Deployment script for the invitation system update
"""
import subprocess
import sys
import time
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False

def deploy_invitation_system():
    """Deploy the invitation system with database management"""
    print("🚀 Deploying WordBattle Invitation System")
    print("=" * 50)
    print(f"Deployment started at: {datetime.now().isoformat()}")
    
    # Step 1: Build Docker image
    build_success = run_command(
        'docker build -t wordbattle-backend:invitation-system .',
        "Building Docker image with invitation system"
    )
    
    if not build_success:
        print("\n❌ Docker build failed. Please check Docker Desktop is running.")
        return False
    
    # Step 2: Tag for ECR
    tag_success = run_command(
        'docker tag wordbattle-backend:invitation-system 598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:invitation-system',
        "Tagging image for ECR"
    )
    
    if not tag_success:
        return False
    
    # Step 3: Login to ECR
    login_success = run_command(
        'aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 598510278922.dkr.ecr.eu-central-1.amazonaws.com',
        "Logging into ECR"
    )
    
    if not login_success:
        return False
    
    # Step 4: Push to ECR
    push_success = run_command(
        'docker push 598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:invitation-system',
        "Pushing image to ECR"
    )
    
    if not push_success:
        return False
    
    # Step 5: Update App Runner service
    print(f"\n🔄 Updating App Runner service...")
    
    # Create update configuration
    update_config = {
        "ImageRepository": {
            "ImageIdentifier": "598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:invitation-system",
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
                    "SMTP_USE_SSL": "true"
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
    import json
    with open('update-invitation-config.json', 'w') as f:
        json.dump(update_config, f, indent=2)
    
    # Update App Runner service
    update_success = run_command(
        'aws apprunner update-service --service-arn "arn:aws:apprunner:eu-central-1:598510278922:service/wordbattle-backend/9112212ab18243638c181fdf7da4a9a2" --source-configuration file://update-invitation-config.json',
        "Updating App Runner service"
    )
    
    if not update_success:
        return False
    
    print(f"\n✅ Deployment initiated successfully!")
    print(f"🕐 App Runner is now updating the service...")
    print(f"📊 You can monitor the deployment status with:")
    print(f"   aws apprunner describe-service --service-arn arn:aws:apprunner:eu-central-1:598510278922:service/wordbattle-backend/9112212ab18243638c181fdf7da4a9a2")
    
    return True

def wait_for_deployment():
    """Wait for deployment to complete and test"""
    print(f"\n⏳ Waiting for deployment to complete...")
    
    max_wait = 600  # 10 minutes
    wait_time = 0
    
    while wait_time < max_wait:
        print(f"⏳ Checking deployment status... ({wait_time}s elapsed)")
        
        # Check service status
        result = subprocess.run(
            'aws apprunner describe-service --service-arn "arn:aws:apprunner:eu-central-1:598510278922:service/wordbattle-backend/9112212ab18243638c181fdf7da4a9a2" --query "Service.Status" --output text',
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode == 0:
            status = result.stdout.strip()
            print(f"📊 Service status: {status}")
            
            if status == "RUNNING":
                print(f"✅ Deployment completed successfully!")
                return True
            elif status in ["CREATE_FAILED", "UPDATE_FAILED"]:
                print(f"❌ Deployment failed with status: {status}")
                return False
        
        time.sleep(30)
        wait_time += 30
    
    print(f"⏰ Deployment timeout after {max_wait} seconds")
    return False

def test_deployment():
    """Test the deployed invitation system"""
    print(f"\n🧪 Testing Deployed Invitation System")
    print("=" * 40)
    
    import requests
    
    backend_url = "https://mnirejmq3g.eu-central-1.awsapprunner.com"
    
    # Test health endpoint
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test database status endpoint
    try:
        response = requests.get(f"{backend_url}/database/status", timeout=10)
        if response.status_code == 200:
            print("✅ Database status endpoint available")
            data = response.json()
            status = data.get('status', {})
            print(f"   Database initialized: {status.get('is_initialized', 'unknown')}")
            word_counts = status.get('word_counts', {})
            if word_counts:
                total_words = sum(word_counts.values())
                print(f"   Total words: {total_words:,}")
        else:
            print(f"❌ Database status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Database status error: {e}")
    
    # Test invitation endpoints
    try:
        response = requests.get(f"{backend_url}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            setup_endpoints = [path for path in paths.keys() if "setup" in path or "invitation" in path]
            if setup_endpoints:
                print("✅ Invitation endpoints available:")
                for endpoint in setup_endpoints:
                    print(f"   {endpoint}")
            else:
                print("❌ No invitation endpoints found")
        else:
            print(f"❌ OpenAPI spec failed: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenAPI spec error: {e}")

if __name__ == "__main__":
    print("🎮 WordBattle Invitation System Deployment")
    print("=" * 60)
    
    # Deploy
    success = deploy_invitation_system()
    
    if success:
        # Wait for deployment
        if wait_for_deployment():
            # Test deployment
            test_deployment()
            print(f"\n🎉 Invitation system deployment completed successfully!")
            print(f"🔗 Backend URL: https://mnirejmq3g.eu-central-1.awsapprunner.com")
            print(f"📚 API Docs: https://mnirejmq3g.eu-central-1.awsapprunner.com/docs")
        else:
            print(f"\n❌ Deployment failed or timed out")
    else:
        print(f"\n❌ Deployment failed")
    
    print(f"\nDeployment finished at: {datetime.now().isoformat()}") 