# Create App Runner Service - Simplified Version
param(
    [string]$Region = "eu-central-1",
    [string]$ServiceName = "wordbattle-backend",
    [string]$RepositoryName = "wordbattle-backend",
    [string]$DbEndpoint = "wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com",
    [string]$DbPassword = ""
)

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$NC = "`e[0m"

Write-Host "${Green}🏃 Creating App Runner Service${NC}" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Get AWS account ID
try {
    $AccountId = aws sts get-caller-identity --query Account --output text
    Write-Host "${Green}✅ AWS Account ID: $AccountId${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to get AWS account ID${NC}" -ForegroundColor Red
    exit 1
}

# Get database password if not provided
if ([string]::IsNullOrWhiteSpace($DbPassword)) {
    try {
        $DbPassword = aws ssm get-parameter --name "/wordbattle/db-password" --with-decryption --query "Parameter.Value" --output text --region $Region 2>$null
        if (-not $DbPassword -or $DbPassword -eq "None") {
            throw "Password not found"
        }
        Write-Host "${Green}✅ Database password retrieved from Parameter Store${NC}" -ForegroundColor Green
    } catch {
        Write-Host "${Yellow}⚠️ Database password not found in Parameter Store.${NC}" -ForegroundColor Yellow
        $SecurePassword = Read-Host "Enter database password" -AsSecureString
        $DbPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword))
    }
}

# Generate a secret key
$SecretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})

# Check if service already exists
Write-Host "${Yellow}🔍 Checking if service exists...${NC}" -ForegroundColor Yellow
$ServiceExists = $false
try {
    $ServiceInfo = aws apprunner describe-service --service-arn "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName" --region $Region 2>$null | ConvertFrom-Json
    if ($ServiceInfo -and $ServiceInfo.Service) {
        $ServiceExists = $true
        Write-Host "${Yellow}⚠️ Service already exists${NC}" -ForegroundColor Yellow
        Write-Host "   Status: $($ServiceInfo.Service.Status)" -ForegroundColor White
        Write-Host "   URL: https://$($ServiceInfo.Service.ServiceUrl)" -ForegroundColor White
        
        # Ask if user wants to update
        $Update = Read-Host "Do you want to trigger a new deployment? (y/N)"
        if ($Update -eq "y" -or $Update -eq "Y") {
            try {
                aws apprunner start-deployment --service-arn "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName" --region $Region | Out-Null
                Write-Host "${Green}✅ Deployment started${NC}" -ForegroundColor Green
            } catch {
                Write-Host "${Red}❌ Failed to start deployment: $($_.Exception.Message)${NC}" -ForegroundColor Red
            }
        }
        return
    }
} catch {
    # Service doesn't exist, we'll create it
}

if (-not $ServiceExists) {
    Write-Host "${Yellow}🆕 Creating new App Runner service...${NC}" -ForegroundColor Yellow
    
    # Create service configuration using AWS CLI directly (simpler approach)
    try {
        Write-Host "${Yellow}📝 Creating service configuration...${NC}" -ForegroundColor Yellow
        
        # Use aws apprunner create-service with individual parameters instead of JSON
        $CreateResult = aws apprunner create-service `
            --service-name $ServiceName `
            --source-configuration "ImageRepository={ImageIdentifier=$AccountId.dkr.ecr.$Region.amazonaws.com/${RepositoryName}:latest,ImageConfiguration={Port=8000,RuntimeEnvironmentVariables={DATABASE_URL=postgresql://postgres:$DbPassword@${DbEndpoint}:5432/wordbattle,SECRET_KEY=$SecretKey,SMTP_SERVER=smtp.strato.de,SMTP_PORT=465,SMTP_USE_SSL=true,SMTP_USERNAME=jan@binge-dev.de,SMTP_PASSWORD=q2NvW4J1%tcAyJSg8,FROM_EMAIL=jan@binge-dev.de,CORS_ORIGINS=*,ENVIRONMENT=production}},ImageRepositoryType=ECR,AutoDeploymentsEnabled=true}" `
            --instance-configuration "Cpu=0.25 vCPU,Memory=0.5 GB" `
            --health-check-configuration "Protocol=HTTP,Path=/health,Interval=10,Timeout=5,HealthyThreshold=1,UnhealthyThreshold=5" `
            --region $Region 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "${Green}✅ App Runner service created successfully${NC}" -ForegroundColor Green
        } else {
            Write-Host "${Red}❌ Failed to create App Runner service${NC}" -ForegroundColor Red
            Write-Host "Error: $CreateResult" -ForegroundColor Red
            
            # Try alternative approach with public ECR
            Write-Host "${Yellow}💡 Trying with public image approach...${NC}" -ForegroundColor Yellow
            
            # Let's try creating a simple service first and then update it
            $SimpleResult = aws apprunner create-service `
                --service-name $ServiceName `
                --source-configuration "ImageRepository={ImageIdentifier=public.ecr.aws/aws-containers/hello-app-runner:latest,ImageConfiguration={Port=8000},ImageRepositoryType=ECR_PUBLIC}" `
                --instance-configuration "Cpu=0.25 vCPU,Memory=0.5 GB" `
                --region $Region 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "${Green}✅ Basic App Runner service created${NC}" -ForegroundColor Green
                Write-Host "${Yellow}💡 You can update it later with your custom image${NC}" -ForegroundColor Yellow
            } else {
                Write-Host "${Red}❌ Failed to create basic service: $SimpleResult${NC}" -ForegroundColor Red
                exit 1
            }
        }
    } catch {
        Write-Host "${Red}❌ Failed to create App Runner service: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
}

# Wait for service to be running
Write-Host "${Yellow}⏳ Waiting for service to be ready...${NC}" -ForegroundColor Yellow
try {
    aws apprunner wait service-running --service-arn "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName" --region $Region
    Write-Host "${Green}✅ Service is now running${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Yellow}⚠️ Timeout waiting for service. It may still be starting...${NC}" -ForegroundColor Yellow
}

# Get service information
try {
    $ServiceInfo = aws apprunner describe-service --service-arn "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName" --region $Region | ConvertFrom-Json
    $ServiceUrl = $ServiceInfo.Service.ServiceUrl
    
    Write-Host ""
    Write-Host "${Green}🎉 Service Information:${NC}" -ForegroundColor Green
    Write-Host "   Name: $($ServiceInfo.Service.ServiceName)" -ForegroundColor White
    Write-Host "   Status: $($ServiceInfo.Service.Status)" -ForegroundColor White
    Write-Host "   URL: https://$ServiceUrl" -ForegroundColor White
    Write-Host "   ARN: $($ServiceInfo.Service.ServiceArn)" -ForegroundColor White
    
    # Test health endpoint if service is running
    if ($ServiceInfo.Service.Status -eq "RUNNING") {
        Write-Host ""
        Write-Host "${Yellow}🧪 Testing health endpoint...${NC}" -ForegroundColor Yellow
        try {
            $HealthUrl = "https://$ServiceUrl/health"
            $Response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 10
            if ($Response.StatusCode -eq 200) {
                Write-Host "${Green}✅ Health check passed!${NC}" -ForegroundColor Green
                Write-Host "   Response: $($Response.Content)" -ForegroundColor White
            } else {
                Write-Host "${Red}❌ Health check failed. Status: $($Response.StatusCode)${NC}" -ForegroundColor Red
            }
        } catch {
            Write-Host "${Red}❌ Health check failed: $($_.Exception.Message)${NC}" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "${Red}❌ Failed to get service information: $($_.Exception.Message)${NC}" -ForegroundColor Red
}

Write-Host ""
Write-Host "${Green}🚀 App Runner service setup completed!${NC}" -ForegroundColor Green 