# Update App Runner Service to use correct image
param(
    [string]$Region = "eu-central-1",
    [string]$ServiceName = "wordbattle-backend"
)

Write-Host "Updating App Runner service to use wordbattle-backend image..." -ForegroundColor Green

# Get AWS Account ID
$AccountId = aws sts get-caller-identity --query Account --output text
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to get AWS Account ID" -ForegroundColor Red
    exit 1
}

# Construct ECR image URI
$ImageUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/wordbattle-backend:latest"
Write-Host "Using image: $ImageUri" -ForegroundColor Yellow

# Get RDS endpoint for environment variables
Write-Host "Getting RDS endpoint..." -ForegroundColor Yellow
$RdsEndpoint = aws rds describe-db-instances --db-instance-identifier wordbattle-db --region $Region --query 'DBInstances[0].Endpoint.Address' --output text
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to get RDS endpoint" -ForegroundColor Red
    exit 1
}

# Get database password from Parameter Store
Write-Host "Getting database password..." -ForegroundColor Yellow
$DbPassword = aws ssm get-parameter --name "/wordbattle/db/password" --with-decryption --region $Region --query 'Parameter.Value' --output text
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to get database password" -ForegroundColor Red
    exit 1
}

# Create service configuration JSON
$ServiceConfig = @{
    ServiceArn = "arn:aws:apprunner:$Region:$AccountId`:service/$ServiceName/3f6e2e76705f42d5b90449f60156b1d7"
    SourceConfiguration = @{
        ImageRepository = @{
            ImageIdentifier = $ImageUri
            ImageConfiguration = @{
                Port = "8000"
                RuntimeEnvironmentVariables = @{
                    DATABASE_URL = "postgresql://wordbattle_user:$DbPassword@$RdsEndpoint`:5432/wordbattle_db"
                    SECRET_KEY = "your-secret-key-here-change-in-production"
                    ALGORITHM = "HS256"
                    ACCESS_TOKEN_EXPIRE_MINUTES = "30"
                }
            }
            ImageRepositoryType = "ECR"
        }
        AutoDeploymentsEnabled = $false
    }
    InstanceConfiguration = @{
        Cpu = "512"
        Memory = "1024"
    }
    HealthCheckConfiguration = @{
        Protocol = "HTTP"
        Path = "/health"
        Interval = 10
        Timeout = 5
        HealthyThreshold = 1
        UnhealthyThreshold = 5
    }
} | ConvertTo-Json -Depth 10

# Save configuration to temporary file
$ConfigFile = "temp-service-config.json"
$ServiceConfig | Out-File -FilePath $ConfigFile -Encoding UTF8

Write-Host "Updating App Runner service..." -ForegroundColor Yellow
aws apprunner update-service --cli-input-json file://$ConfigFile --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "Service update initiated successfully!" -ForegroundColor Green
    Write-Host "Waiting for service to be ready..." -ForegroundColor Yellow
    
    # Wait for service to be running
    do {
        Start-Sleep -Seconds 30
        $Status = aws apprunner describe-service --service-arn "arn:aws:apprunner:$Region:$AccountId`:service/$ServiceName/3f6e2e76705f42d5b90449f60156b1d7" --region $Region --query 'Service.Status' --output text
        Write-Host "Current status: $Status" -ForegroundColor Yellow
    } while ($Status -eq "OPERATION_IN_PROGRESS")
    
    if ($Status -eq "RUNNING") {
        Write-Host "Service is now running!" -ForegroundColor Green
        $ServiceUrl = aws apprunner describe-service --service-arn "arn:aws:apprunner:$Region:$AccountId`:service/$ServiceName/3f6e2e76705f42d5b90449f60156b1d7" --region $Region --query 'Service.ServiceUrl' --output text
        Write-Host "Service URL: https://$ServiceUrl" -ForegroundColor Green
        
        # Test health endpoint
        Write-Host "Testing health endpoint..." -ForegroundColor Yellow
        try {
            $Response = Invoke-WebRequest -Uri "https://$ServiceUrl/health" -Method GET -TimeoutSec 30
            Write-Host "Health check response: $($Response.StatusCode)" -ForegroundColor Green
        } catch {
            Write-Host "Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "Service update failed. Status: $Status" -ForegroundColor Red
    }
} else {
    Write-Host "Failed to update service" -ForegroundColor Red
}

# Clean up temporary file
Remove-Item $ConfigFile -ErrorAction SilentlyContinue 