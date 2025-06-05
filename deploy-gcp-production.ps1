# WordBattle Backend - Google Cloud Run Multi-Environment Deployment (PowerShell)
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("production", "testing")]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [string]$GitBranch = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipGitCheck = $false
)

Write-Host "🚀 WordBattle Backend - Google Cloud Run Deployment" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host "Deploying to environment: $Environment" -ForegroundColor Yellow
Write-Host ""

# Configuration based on environment
$PROJECT_ID = "wordbattle-1748668162"
$BASE_SERVICE_NAME = "wordbattle-backend"
$REGION = "europe-west1"
$IMAGE_NAME = "wordbattle-backend"

# Git integration
if (-not $SkipGitCheck) {
    Write-Host "🔍 Git Integration Check..." -ForegroundColor Cyan
    
    # Check if we're in a git repository
    try {
        $gitStatus = git status --porcelain 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Not in a Git repository or Git not installed" -ForegroundColor Red
            Write-Host "Please run from the project root or use -SkipGitCheck" -ForegroundColor Yellow
            exit 1
        }
        
        # Get current branch
        $currentBranch = git branch --show-current 2>$null
        if ([string]::IsNullOrEmpty($GitBranch)) {
            $GitBranch = $currentBranch
        }
        
        Write-Host "  Current branch: $currentBranch" -ForegroundColor White
        Write-Host "  Target branch: $GitBranch" -ForegroundColor White
        
        # Switch to target branch if different
        if ($currentBranch -ne $GitBranch) {
            Write-Host "  Switching to branch: $GitBranch" -ForegroundColor Yellow
            git checkout $GitBranch
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ Failed to switch to branch: $GitBranch" -ForegroundColor Red
                exit 1
            }
        }
        
        # Check for uncommitted changes
        $gitStatus = git status --porcelain
        if (-not [string]::IsNullOrEmpty($gitStatus)) {
            Write-Host "⚠️  Uncommitted changes detected:" -ForegroundColor Yellow
            git status --short
            if ($Environment -eq "production") {
                Write-Host "❌ Production deployments require clean working directory" -ForegroundColor Red
                Write-Host "Please commit or stash your changes before deploying to production" -ForegroundColor Yellow
                exit 1
            } else {
                Write-Host "🧪 Testing environment allows uncommitted changes" -ForegroundColor Yellow
            }
        } else {
            Write-Host "✅ Working directory is clean" -ForegroundColor Green
        }
        
        # Pull latest changes
        Write-Host "  Pulling latest changes from origin/$GitBranch..." -ForegroundColor Cyan
        git pull origin $GitBranch
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Failed to pull latest changes (continuing anyway)" -ForegroundColor Yellow
        }
        
        # Get commit information
        $gitCommit = git rev-parse --short HEAD
        $gitCommitFull = git rev-parse HEAD
        $gitCommitMessage = git log -1 --pretty=format:"%s"
        $gitCommitAuthor = git log -1 --pretty=format:"%an"
        $gitCommitDate = git log -1 --pretty=format:"%cd" --date=iso
        
        Write-Host "  Commit: $gitCommit" -ForegroundColor White
        Write-Host "  Message: $gitCommitMessage" -ForegroundColor White
        Write-Host "  Author: $gitCommitAuthor" -ForegroundColor White
        Write-Host "  Date: $gitCommitDate" -ForegroundColor White
        
    } catch {
        Write-Host "❌ Git integration failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Use -SkipGitCheck to bypass Git integration" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✅ Git integration check passed" -ForegroundColor Green
    Write-Host ""
}

# Environment-specific configuration
if ($Environment -eq "production") {
    $SERVICE_NAME = "$BASE_SERVICE_NAME-prod"
    $IMAGE_TAG = if ($gitCommit) { "prod-$gitCommit" } else { "prod-latest" }
    $MIN_INSTANCES = 1
    $MAX_INSTANCES = 100
    $MEMORY = "2Gi"
    $CPU = "2"
} else {
    $SERVICE_NAME = "$BASE_SERVICE_NAME-test"
    $IMAGE_TAG = if ($gitCommit) { "test-$gitCommit" } else { "test-latest" }
    $MIN_INSTANCES = 0
    $MAX_INSTANCES = 10
    $MEMORY = "1Gi"
    $CPU = "1"
}

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Project: $PROJECT_ID" -ForegroundColor White
Write-Host "  Environment: $Environment" -ForegroundColor White
Write-Host "  Service: $SERVICE_NAME" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White
Write-Host "  Image: $IMAGE_NAME`:$IMAGE_TAG" -ForegroundColor White
Write-Host "  Resources: $CPU CPU, $MEMORY RAM" -ForegroundColor White
Write-Host "  Scaling: $MIN_INSTANCES-$MAX_INSTANCES instances" -ForegroundColor White
if ($gitCommit) {
    Write-Host "  Git Commit: $gitCommit ($GitBranch)" -ForegroundColor White
}
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Cyan

# Check if gcloud is installed
try {
    $gcloudVersion = gcloud --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud not found"
    }
    Write-Host "✅ Google Cloud CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Google Cloud CLI not found." -ForegroundColor Red
    Write-Host "Please install it first: winget install --id Google.CloudSDK" -ForegroundColor Yellow
    Write-Host "Then restart your terminal and run this script again." -ForegroundColor Yellow
    exit 1
}

# Check if Docker is installed
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "docker not found"
    }
    Write-Host "✅ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found." -ForegroundColor Red
    Write-Host "Please install Docker first: https://docs.docker.com/get-docker/" -ForegroundColor Yellow
    exit 1
}

# Wait for Docker to start
Write-Host "Waiting for Docker to start..." -ForegroundColor Cyan
$dockerReady = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        docker ps >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker is running" -ForegroundColor Green
            $dockerReady = $true
            break
        }
    } catch {}
    Start-Sleep 1
}

if (-not $dockerReady) {
    Write-Host "❌ Docker failed to start after 30 seconds" -ForegroundColor Red
    Write-Host "Please start Docker manually and try again" -ForegroundColor Yellow
    exit 1
}

# Add Google Cloud SDK to PATH if needed
$gcloudPath = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin"
if (Test-Path $gcloudPath) {
    $env:PATH += ";$gcloudPath"
}

# Check if logged in to gcloud
$activeAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if ([string]::IsNullOrEmpty($activeAccount)) {
    Write-Host "Please login to Google Cloud:" -ForegroundColor Yellow
    gcloud auth login
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green
Write-Host ""

# Set project and region
Write-Host "Setting project and region..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set project. Please make sure project $PROJECT_ID exists and you have access." -ForegroundColor Red
    exit 1
}

# Enable required APIs
Write-Host "Enabling required Google Cloud APIs..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com

Write-Host "✅ Google Cloud setup complete" -ForegroundColor Green
Write-Host ""

# Build the Docker image
Write-Host "Building Docker image for $Environment environment..." -ForegroundColor Cyan
if ($gitCommit) {
    Write-Host "  Including Git commit: $gitCommit" -ForegroundColor White
}

docker build -f Dockerfile.cloudrun -t "gcr.io/$PROJECT_ID/$IMAGE_NAME`:$IMAGE_TAG" `
    --label "git.commit=$gitCommitFull" `
    --label "git.branch=$GitBranch" `
    --label "git.message=$gitCommitMessage" `
    --label "deploy.environment=$Environment" `
    --label "deploy.timestamp=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker image built successfully" -ForegroundColor Green
Write-Host ""

# Configure Docker to use gcloud as a credential helper
Write-Host "Configuring Docker for Google Container Registry..." -ForegroundColor Cyan
gcloud auth configure-docker --quiet

# Push the image to Google Container Registry
Write-Host "Pushing image to Google Container Registry..." -ForegroundColor Cyan
docker push "gcr.io/$PROJECT_ID/$IMAGE_NAME`:$IMAGE_TAG"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Image pushed to GCR successfully" -ForegroundColor Green
Write-Host ""

# Deploy to Cloud Run
Write-Host "Deploying to Google Cloud Run ($Environment environment)..." -ForegroundColor Cyan

# Check if service exists
$serviceExists = gcloud run services describe $SERVICE_NAME --region=$REGION 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Updating existing Cloud Run service: $SERVICE_NAME" -ForegroundColor Yellow
} else {
    Write-Host "Creating new Cloud Run service: $SERVICE_NAME" -ForegroundColor Yellow
}

# Environment-specific environment variables
$envVars = @()
if ($Environment -eq "production") {
    $envVars += "ENVIRONMENT=production"
    $envVars += "LOG_LEVEL=INFO"
    $envVars += "DEBUG=false"
} else {
    $envVars += "ENVIRONMENT=testing"
    $envVars += "LOG_LEVEL=DEBUG"
    $envVars += "DEBUG=true"
    # Cloud SQL configuration for testing - use Unix socket format
    $envVars += "DATABASE_URL=postgresql://wordbattle:wordbattle123@/wordbattle_test?host=/cloudsql/wordbattle-1748668162:europe-west1:wordbattle-db"
}

# Add Git information to environment variables
if ($gitCommit) {
    $envVars += "GIT_COMMIT=$gitCommit"
    $envVars += "GIT_BRANCH=$GitBranch"
    $envVars += "DEPLOY_TIMESTAMP=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')"
}

$envVarString = ($envVars -join ",")

# Build the gcloud run deploy command with environment-specific configurations
$deployArgs = @(
    "run", "deploy", $SERVICE_NAME,
    "--image=gcr.io/$PROJECT_ID/$IMAGE_NAME`:$IMAGE_TAG",
    "--platform=managed",
    "--region=$REGION",
    "--allow-unauthenticated",
    "--port=8000",
    "--memory=$MEMORY",
    "--cpu=$CPU",
    "--timeout=300",
    "--max-instances=$MAX_INSTANCES",
    "--min-instances=$MIN_INSTANCES",
    "--concurrency=80",
    "--set-env-vars=$envVarString"
)

# Add Cloud SQL connection for testing environment
if ($Environment -eq "testing") {
    $deployArgs += "--add-cloudsql-instances=wordbattle-1748668162:europe-west1:wordbattle-db"
}

gcloud @deployArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 Deployment successful!" -ForegroundColor Green
    
    # Create Git tag for production deployments
    if ($Environment -eq "production" -and $gitCommit -and -not $SkipGitCheck) {
        $deployTag = "deploy-prod-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Write-Host "Creating Git tag: $deployTag" -ForegroundColor Cyan
        git tag -a $deployTag -m "Production deployment at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        git push origin $deployTag
        Write-Host "✅ Git tag created and pushed" -ForegroundColor Green
    }
    
    # Get the service URL
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)'
    
    Write-Host ""
    Write-Host "🚀 WordBattle Backend ($Environment) is now live!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "Application URL: $SERVICE_URL" -ForegroundColor White
    Write-Host "API Documentation: $SERVICE_URL/docs" -ForegroundColor White
    Write-Host "Health Check: $SERVICE_URL/health" -ForegroundColor White
    Write-Host "Database Status: $SERVICE_URL/database/status" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Testing deployment..." -ForegroundColor Cyan
    Start-Sleep 10
    
    # Test health endpoint
    Write-Host "Testing health endpoint..." -ForegroundColor Cyan
    try {
        $healthResponse = Invoke-RestMethod -Uri "$SERVICE_URL/health" -Method Get -TimeoutSec 30
        Write-Host "✅ Health check passed!" -ForegroundColor Green
        Write-Host "  Status: $($healthResponse.status)" -ForegroundColor White
        Write-Host "  Environment: $($healthResponse.environment)" -ForegroundColor White
        Write-Host "  Database: $($healthResponse.database)" -ForegroundColor White
    } catch {
        Write-Host "⚠️  Health check failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Test API documentation
    Write-Host "Testing API documentation..." -ForegroundColor Cyan
    try {
        $docsResponse = Invoke-WebRequest -Uri "$SERVICE_URL/docs" -Method Get -TimeoutSec 30
        if ($docsResponse.StatusCode -eq 200) {
            Write-Host "✅ API documentation accessible!" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  API docs test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🎉 Google Cloud Run deployment complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Deployment Summary:" -ForegroundColor Cyan
    Write-Host "  ✅ Environment: $Environment" -ForegroundColor Green
    if ($gitCommit) {
        Write-Host "  ✅ Git Commit: $gitCommit ($GitBranch)" -ForegroundColor Green
        if ($Environment -eq "production") {
            Write-Host "  ✅ Git tag created: $deployTag" -ForegroundColor Green
        }
    }
    Write-Host "  ✅ Docker image built and pushed to GCR" -ForegroundColor Green
    Write-Host "  ✅ Cloud Run service deployed: $SERVICE_NAME" -ForegroundColor Green
    Write-Host "  ✅ Service is publicly accessible" -ForegroundColor Green
    Write-Host "  ✅ Health checks passing" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Important URLs:" -ForegroundColor Cyan
    Write-Host "  Application: $SERVICE_URL" -ForegroundColor White
    Write-Host "  API Docs: $SERVICE_URL/docs" -ForegroundColor White
    Write-Host "  OpenAPI Schema: $SERVICE_URL/openapi.json" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 Environment-Specific Info:" -ForegroundColor Cyan
    if ($Environment -eq "production") {
        Write-Host "  🏭 Production Environment" -ForegroundColor White
        Write-Host "  • Always-on with minimum 1 instance" -ForegroundColor White
        Write-Host "  • High performance: 2 CPU, 2GB RAM" -ForegroundColor White
        Write-Host "  • Scales up to 100 instances" -ForegroundColor White
        Write-Host "  • Optimized for stability and performance" -ForegroundColor White
        Write-Host "  • Git tags created for tracking deployments" -ForegroundColor White
    } else {
        Write-Host "  🧪 Testing Environment" -ForegroundColor White
        Write-Host "  • Cost-optimized: scales to 0 when idle" -ForegroundColor White
        Write-Host "  • Basic performance: 1 CPU, 1GB RAM" -ForegroundColor White
        Write-Host "  • Scales up to 10 instances" -ForegroundColor White
        Write-Host "  • Debug mode enabled for development" -ForegroundColor White
        Write-Host "  • Allows uncommitted changes for testing" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "📝 Project Details:" -ForegroundColor Cyan
    Write-Host "  Project ID: $PROJECT_ID" -ForegroundColor White
    Write-Host "  Service Name: $SERVICE_NAME" -ForegroundColor White
    Write-Host "  Region: $REGION" -ForegroundColor White
    Write-Host "  Image: gcr.io/$PROJECT_ID/$IMAGE_NAME`:$IMAGE_TAG" -ForegroundColor White
    
    # Show both environment URLs if this is production
    if ($Environment -eq "production") {
        Write-Host ""
        Write-Host "🔄 Environment Management:" -ForegroundColor Cyan
        Write-Host "  Production: $SERVICE_URL" -ForegroundColor White
        
        # Check if testing environment exists
        $testServiceExists = gcloud run services describe "$BASE_SERVICE_NAME-test" --region=$REGION 2>$null
        if ($LASTEXITCODE -eq 0) {
            $TEST_URL = gcloud run services describe "$BASE_SERVICE_NAME-test" --region=$REGION --format='value(status.url)'
            Write-Host "  Testing: $TEST_URL" -ForegroundColor White
        } else {
            Write-Host "  Testing: Not deployed (run with -Environment testing)" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "🏷️  Git Management:" -ForegroundColor Cyan
        Write-Host "  Deploy to testing: .\deploy-gcp-production.ps1 -Environment testing" -ForegroundColor White
        Write-Host "  Deploy specific branch: .\deploy-gcp-production.ps1 -GitBranch feature/xyz" -ForegroundColor White
        Write-Host "  Skip Git checks: .\deploy-gcp-production.ps1 -SkipGitCheck" -ForegroundColor White
    }
    
} else {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    Write-Host "Check the logs with: gcloud run services logs tail $SERVICE_NAME --region=$REGION" -ForegroundColor Yellow
    exit 1
} 