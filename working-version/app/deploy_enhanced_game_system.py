#!/usr/bin/env python3
"""
Deployment script for the enhanced game creation system with email invitations
"""
import subprocess
import sys
import time
import json
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

def deploy_enhanced_game_system():
    """Deploy the enhanced game creation system"""
    print("🚀 Deploying WordBattle Enhanced Game Creation System")
    print("=" * 60)
    print(f"Deployment started at: {datetime.now().isoformat()}")
    
    # Step 1: Build Docker image with new tag
    build_success = run_command(
        'docker build -t wordbattle-backend:enhanced-game-system .',
        "Building Docker image with enhanced game creation system"
    )
    
    if not build_success:
        print("\n❌ Docker build failed. Please check Docker Desktop is running.")
        return False
    
    # Step 2: Tag for ECR
    tag_success = run_command(
        'docker tag wordbattle-backend:enhanced-game-system 598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:enhanced-game-system',
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
        'docker push 598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:enhanced-game-system',
        "Pushing image to ECR"
    )
    
    if not push_success:
        return False
    
    # Step 5: Update App Runner service
    print(f"\n🔄 Updating App Runner service...")
    
    # Create update configuration with enhanced features
    update_config = {
        "ImageRepository": {
            "ImageIdentifier": "598510278922.dkr.ecr.eu-central-1.amazonaws.com/wordbattle-backend:enhanced-game-system",
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
                    # Enhanced game creation settings
                    "VERIFICATION_CODE_EXPIRE_MINUTES": "10",
                    "PERSISTENT_TOKEN_EXPIRE_DAYS": "30",
                    "ACCESS_TOKEN_EXPIRE_MINUTES": "30"
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
    with open('update-enhanced-game-config.json', 'w') as f:
        json.dump(update_config, f, indent=2)
    
    # Update App Runner service
    update_success = run_command(
        'aws apprunner update-service --service-arn "arn:aws:apprunner:eu-central-1:598510278922:service/wordbattle-backend/9112212ab18243638c181fdf7da4a9a2" --source-configuration file://update-enhanced-game-config.json',
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
    """Wait for deployment to complete"""
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

def run_database_migration():
    """Run database migration to add join_token field"""
    print(f"\n🗄️ Running Database Migration")
    print("=" * 40)
    
    backend_url = "https://mnirejmq3g.eu-central-1.awsapprunner.com"
    
    # First, let's check if we can connect to the database via the API
    import requests
    
    try:
        # Check database status
        response = requests.get(f"{backend_url}/database/status", timeout=30)
        if response.status_code == 200:
            print("✅ Database connection successful")
            data = response.json()
            print(f"   Current status: {data.get('status', {})}")
        else:
            print(f"❌ Database status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    
    # Run migration via AWS CLI (connecting to RDS directly)
    print(f"\n🔄 Running Alembic migration...")
    
    # Create a temporary script to run the migration
    migration_script = """
import os
import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config

# Database URL for production
DATABASE_URL = "postgresql://postgres:Y3RHlw7BACKDFNg6QWmkirhPu@wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com:5432/wordbattle"

try:
    # Test connection
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    
    # Run Alembic migration
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    
    print("🔄 Running migration to add join_token field...")
    command.upgrade(alembic_cfg, "head")
    print("✅ Migration completed successfully!")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
"""
    
    # Write migration script
    with open('run_migration.py', 'w') as f:
        f.write(migration_script)
    
    # Run migration
    migration_success = run_command(
        'python run_migration.py',
        "Running database migration"
    )
    
    # Clean up
    try:
        import os
        os.remove('run_migration.py')
    except:
        pass
    
    return migration_success

def test_enhanced_features():
    """Test the enhanced game creation features"""
    print(f"\n🧪 Testing Enhanced Game Creation Features")
    print("=" * 50)
    
    import requests
    
    backend_url = "https://mnirejmq3g.eu-central-1.awsapprunner.com"
    
    # Test health endpoint
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            health_data = response.json()
            print(f"   Version: {health_data.get('version', 'unknown')}")
            print(f"   Environment: {health_data.get('environment', 'unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test database status
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
            print(f"❌ Database status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Database status error: {e}")
    
    # Test OpenAPI spec for new endpoints
    try:
        response = requests.get(f"{backend_url}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            # Check for enhanced game creation endpoints
            enhanced_endpoints = [
                "/games/create-with-invitations",
                "/games/{game_id}/join-with-token",
                "/games/{game_id}/invitations",
                "/games/{game_id}/auto-start"
            ]
            
            print("✅ Checking enhanced game creation endpoints:")
            for endpoint in enhanced_endpoints:
                if endpoint in paths:
                    print(f"   ✅ {endpoint}")
                else:
                    print(f"   ❌ {endpoint} - NOT FOUND")
        else:
            print(f"❌ OpenAPI spec failed: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenAPI spec error: {e}")
    
    print(f"\n🎉 Enhanced game creation system deployment test completed!")

def main():
    """Main deployment function"""
    print("🚀 WordBattle Enhanced Game Creation System Deployment")
    print("=" * 70)
    
    # Step 1: Deploy the application
    if not deploy_enhanced_game_system():
        print("\n❌ Deployment failed!")
        sys.exit(1)
    
    # Step 2: Wait for deployment to complete
    if not wait_for_deployment():
        print("\n❌ Deployment did not complete successfully!")
        sys.exit(1)
    
    # Step 3: Run database migration
    if not run_database_migration():
        print("\n❌ Database migration failed!")
        sys.exit(1)
    
    # Step 4: Test enhanced features
    test_enhanced_features()
    
    print(f"\n🎉 Enhanced Game Creation System Deployed Successfully!")
    print(f"🌐 Backend URL: https://mnirejmq3g.eu-central-1.awsapprunner.com")
    print(f"📚 API Documentation: https://mnirejmq3g.eu-central-1.awsapprunner.com/docs")
    print(f"🎮 New Features Available:")
    print(f"   • Enhanced game creation with email invitations")
    print(f"   • Secure join tokens for game access")
    print(f"   • Auto-start functionality")
    print(f"   • Invitation management")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Deployment failed with error: {e}")
        sys.exit(1) 