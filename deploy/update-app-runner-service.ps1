# Update App Runner Service to use WordBattle Backend Image
param(
    [string]$Region = "eu-central-1",
    [string]$RepositoryName = "wordbattle-backend",
    [string]$ServiceName = "wordbattle-backend",
    [string]$DbInstanceId = "wordbattle-db"
)

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$NC = "`e[0m"

Write-Host "${Blue}🔄 Updating App Runner Service${NC}" -ForegroundColor Blue
Write-Host "=================================" -ForegroundColor Blue

# Get AWS account ID
try {
    $AccountId = aws sts get-caller-identity --query Account --output text
    Write-Host "${Green}✅ Account ID: $AccountId${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to get AWS account ID${NC}" -ForegroundColor Red
    exit 1
}

# Get database password from Parameter Store
Write-Host "${Yellow}🔑 Retrieving database password...${NC}" -ForegroundColor Yellow
try {
    $DbPassword = aws ssm get-parameter --name "/wordbattle/db-password" --with-decryption --query "Parameter.Value" --output text --region $Region
    if ([string]::IsNullOrWhiteSpace($DbPassword) -or $DbPassword -eq "None") {
        throw "Password not found"
    }
    Write-Host "${Green}✅ Database password retrieved${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to retrieve database password from Parameter Store${NC}" -ForegroundColor Red
    exit 1
}

# Get database endpoint
Write-Host "${Yellow}🗄️ Getting database endpoint...${NC}" -ForegroundColor Yellow
try {
    $DbInfo = aws rds describe-db-instances --db-instance-identifier $DbInstanceId --region $Region | ConvertFrom-Json
    $DbEndpoint = $DbInfo.DBInstances[0].Endpoint.Address
    Write-Host "${Green}✅ Database endpoint: $DbEndpoint${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to get database endpoint${NC}" -ForegroundColor Red
    exit 1
}

# Generate a new secret key
$SecretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host "${Green}🔐 Generated new secret key${NC}" -ForegroundColor Green

# Create service configuration
Write-Host "${Yellow}📝 Creating service configuration...${NC}" -ForegroundColor Yellow

$ServiceArn = "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName"
$ImageUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/${RepositoryName}:latest"

# Create the update configuration JSON
$UpdateConfig = @{
    ServiceArn = $ServiceArn
    SourceConfiguration = @{
        ImageRepository = @{
            ImageIdentifier = $ImageUri
            ImageConfiguration = @{
                Port = "8000"
                RuntimeEnvironmentVariables = @{
                    DATABASE_URL = "postgresql://postgres:$DbPassword@${DbEndpoint}:5432/wordbattle"
                    SECRET_KEY = $SecretKey
                    SMTP_SERVER = "smtp.strato.de"
                    SMTP_PORT = "465"
                    SMTP_USE_SSL = "true"
                    SMTP_USERNAME = "jan@binge-dev.de"
                    SMTP_PASSWORD = "q2NvW4J1%tcAyJSg8"
                    FROM_EMAIL = "jan@binge-dev.de"
                    CORS_ORIGINS = "*"
                    ENVIRONMENT = "production"
                }
            }
            ImageRepositoryType = "ECR"
        }
        AutoDeploymentsEnabled = $true
    }
    InstanceConfiguration = @{
        Cpu = "0.25 vCPU"
        Memory = "0.5 GB"
    }
    HealthCheckConfiguration = @{
        Protocol = "HTTP"
        Path = "/health"
        Interval = 10
        Timeout = 5
        HealthyThreshold = 1
        UnhealthyThreshold = 5
    }
}

# Convert to JSON and save to temp file
$ConfigJson = $UpdateConfig | ConvertTo-Json -Depth 10
$ConfigFile = [System.IO.Path]::GetTempFileName()
$ConfigJson | Out-File -FilePath $ConfigFile -Encoding UTF8

Write-Host "${Yellow}🚀 Updating App Runner service...${NC}" -ForegroundColor Yellow
try {
    aws apprunner update-service --cli-input-json "file://$ConfigFile" --region $Region | Out-Null
    Remove-Item $ConfigFile
    Write-Host "${Green}✅ Service update initiated${NC}" -ForegroundColor Green
} catch {
    Remove-Item $ConfigFile -ErrorAction SilentlyContinue
    Write-Host "${Red}❌ Failed to update service: $($_.Exception.Message)${NC}" -ForegroundColor Red
    exit 1
}

# Wait for the update to complete
Write-Host "${Yellow}⏳ Waiting for service update to complete...${NC}" -ForegroundColor Yellow
Write-Host "${Yellow}   This may take 5-10 minutes...${NC}" -ForegroundColor Yellow

$MaxWaitTime = 600 # 10 minutes
$WaitInterval = 30 # 30 seconds
$ElapsedTime = 0

while ($ElapsedTime -lt $MaxWaitTime) {
    try {
        $ServiceInfo = aws apprunner describe-service --service-arn $ServiceArn --region $Region | ConvertFrom-Json
        $Status = $ServiceInfo.Service.Status
        
        Write-Host "${Yellow}   Current status: $Status (${ElapsedTime}s elapsed)${NC}" -ForegroundColor Yellow
        
        if ($Status -eq "RUNNING") {
            Write-Host "${Green}✅ Service is now running with updated configuration${NC}" -ForegroundColor Green
            break
        } elseif ($Status -eq "CREATE_FAILED" -or $Status -eq "UPDATE_FAILED") {
            Write-Host "${Red}❌ Service update failed${NC}" -ForegroundColor Red
            exit 1
        }
        
        Start-Sleep $WaitInterval
        $ElapsedTime += $WaitInterval
    } catch {
        Write-Host "${Red}❌ Error checking service status: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
}

if ($ElapsedTime -ge $MaxWaitTime) {
    Write-Host "${Yellow}⚠️ Timeout waiting for service to be ready${NC}" -ForegroundColor Yellow
    Write-Host "${Yellow}   The service may still be updating. Check AWS Console for status.${NC}" -ForegroundColor Yellow
}

# Get the final service URL and test it
Write-Host "${Yellow}🔍 Getting service URL...${NC}" -ForegroundColor Yellow
try {
    $ServiceInfo = aws apprunner describe-service --service-arn $ServiceArn --region $Region | ConvertFrom-Json
    $ServiceUrl = $ServiceInfo.Service.ServiceUrl
    $Status = $ServiceInfo.Service.Status
    
    if ($Status -eq "RUNNING" -and -not [string]::IsNullOrWhiteSpace($ServiceUrl)) {
        Write-Host "${Green}✅ Service URL: https://$ServiceUrl${NC}" -ForegroundColor Green
        
        # Test the health endpoint
        Write-Host "${Yellow}🧪 Testing health endpoint...${NC}" -ForegroundColor Yellow
        try {
            $Response = Invoke-WebRequest -Uri "https://$ServiceUrl/health" -UseBasicParsing -TimeoutSec 30
            if ($Response.StatusCode -eq 200) {
                Write-Host "${Green}✅ Health check passed!${NC}" -ForegroundColor Green
                Write-Host "${Green}🎉 Service update completed successfully!${NC}" -ForegroundColor Green
            } else {
                Write-Host "${Red}❌ Health check failed (Status: $($Response.StatusCode))${NC}" -ForegroundColor Red
            }
        } catch {
            Write-Host "${Red}❌ Health check failed: $($_.Exception.Message)${NC}" -ForegroundColor Red
            Write-Host "${Yellow}💡 The service may still be starting up. Try again in a few minutes.${NC}" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "${Blue}📋 Service Information:${NC}" -ForegroundColor Blue
        Write-Host "=================================" -ForegroundColor Blue
        Write-Host "Service URL: https://$ServiceUrl" -ForegroundColor White
        Write-Host "API Documentation: https://$ServiceUrl/docs" -ForegroundColor White
        Write-Host "Health Check: https://$ServiceUrl/health" -ForegroundColor White
        Write-Host "Image: $ImageUri" -ForegroundColor White
        Write-Host "Database: $DbEndpoint" -ForegroundColor White
        
    } else {
        Write-Host "${Yellow}⚠️ Service not ready yet or URL not available${NC}" -ForegroundColor Yellow
    }
} catch {
    Write-Host "${Red}❌ Failed to get service information: $($_.Exception.Message)${NC}" -ForegroundColor Red
} 