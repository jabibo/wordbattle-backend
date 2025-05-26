# Check WordBattle Deployment Status
param(
    [string]$Region = "eu-central-1",
    [string]$ServiceName = "wordbattle-backend"
)

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$NC = "`e[0m"

Write-Host "${Green}🔍 WordBattle Deployment Status Check${NC}" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Get AWS account ID
try {
    $AccountId = aws sts get-caller-identity --query Account --output text 2>$null
    if (-not $AccountId) {
        throw "Failed to get account ID"
    }
    Write-Host "${Green}✅ AWS Account ID: $AccountId${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to get AWS account ID. Please configure AWS CLI.${NC}" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "${Yellow}📋 Checking App Runner Services...${NC}" -ForegroundColor Yellow

# List all App Runner services
try {
    $Services = aws apprunner list-services --region $Region --output json 2>$null | ConvertFrom-Json
    if ($Services.ServiceSummaryList.Count -eq 0) {
        Write-Host "${Yellow}⚠️ No App Runner services found in region $Region${NC}" -ForegroundColor Yellow
    } else {
        Write-Host "${Green}✅ Found $($Services.ServiceSummaryList.Count) App Runner service(s):${NC}" -ForegroundColor Green
        foreach ($service in $Services.ServiceSummaryList) {
            Write-Host "   • $($service.ServiceName) - Status: $($service.Status)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "${Red}❌ Failed to list App Runner services: $($_.Exception.Message)${NC}" -ForegroundColor Red
}

Write-Host ""
Write-Host "${Yellow}📋 Checking Specific Service: $ServiceName...${NC}" -ForegroundColor Yellow

# Check specific service
try {
    $ServiceArn = "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName"
    $ServiceDetails = aws apprunner describe-service --service-arn $ServiceArn --region $Region --output json 2>$null | ConvertFrom-Json
    
    if ($ServiceDetails) {
        Write-Host "${Green}✅ Service found!${NC}" -ForegroundColor Green
        Write-Host "   • Name: $($ServiceDetails.Service.ServiceName)" -ForegroundColor White
        Write-Host "   • Status: $($ServiceDetails.Service.Status)" -ForegroundColor White
        Write-Host "   • URL: https://$($ServiceDetails.Service.ServiceUrl)" -ForegroundColor White
        Write-Host "   • Created: $($ServiceDetails.Service.CreatedAt)" -ForegroundColor White
        Write-Host "   • Updated: $($ServiceDetails.Service.UpdatedAt)" -ForegroundColor White
        
        # Test health endpoint if service is running
        if ($ServiceDetails.Service.Status -eq "RUNNING") {
            Write-Host ""
            Write-Host "${Yellow}🧪 Testing health endpoint...${NC}" -ForegroundColor Yellow
            try {
                $HealthUrl = "https://$($ServiceDetails.Service.ServiceUrl)/health"
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
        } else {
            Write-Host "${Yellow}⚠️ Service is not running. Current status: $($ServiceDetails.Service.Status)${NC}" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "${Red}❌ Service '$ServiceName' not found or error occurred${NC}" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "${Yellow}📋 Checking ECR Repository...${NC}" -ForegroundColor Yellow

# Check ECR repository
try {
    $Repository = aws ecr describe-repositories --repository-names wordbattle-backend --region $Region --output json 2>$null | ConvertFrom-Json
    if ($Repository) {
        Write-Host "${Green}✅ ECR Repository found!${NC}" -ForegroundColor Green
        Write-Host "   • URI: $($Repository.repositories[0].repositoryUri)" -ForegroundColor White
        Write-Host "   • Created: $($Repository.repositories[0].createdAt)" -ForegroundColor White
        
        # Check for images
        try {
            $Images = aws ecr list-images --repository-name wordbattle-backend --region $Region --output json 2>$null | ConvertFrom-Json
            if ($Images.imageIds.Count -gt 0) {
                Write-Host "   • Images: $($Images.imageIds.Count) found" -ForegroundColor White
                $LatestImage = $Images.imageIds | Where-Object { $_.imageTag -eq "latest" }
                if ($LatestImage) {
                    Write-Host "   • Latest tag: Available" -ForegroundColor White
                } else {
                    Write-Host "${Yellow}   • Latest tag: Not found${NC}" -ForegroundColor Yellow
                }
            } else {
                Write-Host "${Yellow}   • No images found in repository${NC}" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "${Red}   • Failed to list images: $($_.Exception.Message)${NC}" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "${Red}❌ ECR Repository 'wordbattle-backend' not found${NC}" -ForegroundColor Red
}

Write-Host ""
Write-Host "${Yellow}📋 Checking RDS Database...${NC}" -ForegroundColor Yellow

# Check RDS database
try {
    $Database = aws rds describe-db-instances --db-instance-identifier wordbattle-db --region $Region --output json 2>$null | ConvertFrom-Json
    if ($Database) {
        Write-Host "${Green}✅ RDS Database found!${NC}" -ForegroundColor Green
        Write-Host "   • Status: $($Database.DBInstances[0].DBInstanceStatus)" -ForegroundColor White
        Write-Host "   • Endpoint: $($Database.DBInstances[0].Endpoint.Address)" -ForegroundColor White
        Write-Host "   • Engine: $($Database.DBInstances[0].Engine) $($Database.DBInstances[0].EngineVersion)" -ForegroundColor White
    }
} catch {
    Write-Host "${Red}❌ RDS Database 'wordbattle-db' not found${NC}" -ForegroundColor Red
}

Write-Host ""
Write-Host "${Green}🔧 Troubleshooting Tips:${NC}" -ForegroundColor Green
Write-Host "1. If no services found, run the deployment script: .\deploy\aws-app-runner.ps1" -ForegroundColor White
Write-Host "2. If service exists but not running, check CloudWatch logs" -ForegroundColor White
Write-Host "3. If health check fails, verify the application is properly configured" -ForegroundColor White
Write-Host "4. If ECR repository is empty, build and push the Docker image" -ForegroundColor White
Write-Host ""
Write-Host "${Green}🚀 Status check completed!${NC}" -ForegroundColor Green 