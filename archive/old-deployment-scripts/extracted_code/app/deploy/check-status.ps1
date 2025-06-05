# WordBattle Deployment Status Check
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

Write-Host "${Blue}🔍 WordBattle Deployment Status Check${NC}" -ForegroundColor Blue
Write-Host "=============================================" -ForegroundColor Blue

# Check AWS credentials
Write-Host "${Yellow}🔐 Checking AWS credentials...${NC}" -ForegroundColor Yellow
try {
    $AccountId = aws sts get-caller-identity --query Account --output text
    if (-not $AccountId -or $AccountId -eq "None") {
        throw "Failed to get account ID"
    }
    Write-Host "${Green}✅ AWS credentials working (Account: $AccountId)${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ AWS credentials not configured${NC}" -ForegroundColor Red
    exit 1
}

# Check ECR repository
Write-Host "${Yellow}📦 Checking ECR repository...${NC}" -ForegroundColor Yellow
try {
    $RepoInfo = aws ecr describe-repositories --repository-names $RepositoryName --region $Region 2>$null | ConvertFrom-Json
    if ($RepoInfo -and $RepoInfo.repositories.Count -gt 0) {
        Write-Host "${Green}✅ ECR repository exists${NC}" -ForegroundColor Green
        
        # Check for images
        $Images = aws ecr list-images --repository-name $RepositoryName --region $Region | ConvertFrom-Json
        if ($Images.imageIds.Count -gt 0) {
            Write-Host "${Green}   📸 Found $($Images.imageIds.Count) images${NC}" -ForegroundColor Green
            $LatestImage = $Images.imageIds | Where-Object { $_.imageTag -eq "latest" }
            if ($LatestImage) {
                Write-Host "${Green}   🏷️ Latest tag available${NC}" -ForegroundColor Green
            } else {
                Write-Host "${Yellow}   ⚠️ No 'latest' tag found${NC}" -ForegroundColor Yellow
            }
        } else {
            Write-Host "${Red}   ❌ No images found in repository${NC}" -ForegroundColor Red
        }
    } else {
        throw "Repository not found"
    }
} catch {
    Write-Host "${Red}❌ ECR repository not found${NC}" -ForegroundColor Red
}

# Check RDS database
Write-Host "${Yellow}🗄️ Checking RDS database...${NC}" -ForegroundColor Yellow
try {
    $DbInfo = aws rds describe-db-instances --db-instance-identifier $DbInstanceId --region $Region 2>$null | ConvertFrom-Json
    if ($DbInfo -and $DbInfo.DBInstances.Count -gt 0) {
        $DbStatus = $DbInfo.DBInstances[0].DBInstanceStatus
        $DbEndpoint = $DbInfo.DBInstances[0].Endpoint.Address
        Write-Host "${Green}✅ RDS database exists${NC}" -ForegroundColor Green
        Write-Host "${Green}   📊 Status: $DbStatus${NC}" -ForegroundColor Green
        Write-Host "${Green}   🌐 Endpoint: $DbEndpoint${NC}" -ForegroundColor Green
        
        # Check if password is in Parameter Store
        try {
            $DbPassword = aws ssm get-parameter --name "/wordbattle/db-password" --with-decryption --query "Parameter.Value" --output text --region $Region 2>$null
            if (-not [string]::IsNullOrWhiteSpace($DbPassword) -and $DbPassword -ne "None") {
                Write-Host "${Green}   🔑 Password found in Parameter Store${NC}" -ForegroundColor Green
            } else {
                Write-Host "${Yellow}   ⚠️ Password not found in Parameter Store${NC}" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "${Yellow}   ⚠️ Password not found in Parameter Store${NC}" -ForegroundColor Yellow
        }
    } else {
        throw "Database not found"
    }
} catch {
    Write-Host "${Red}❌ RDS database not found${NC}" -ForegroundColor Red
}

# Check App Runner service
Write-Host "${Yellow}🏃 Checking App Runner service...${NC}" -ForegroundColor Yellow
try {
    $ServiceArn = "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName"
    $ServiceInfo = aws apprunner describe-service --service-arn $ServiceArn --region $Region 2>$null | ConvertFrom-Json
    if ($ServiceInfo -and $ServiceInfo.Service) {
        $ServiceStatus = $ServiceInfo.Service.Status
        $ServiceUrl = $ServiceInfo.Service.ServiceUrl
        Write-Host "${Green}✅ App Runner service exists${NC}" -ForegroundColor Green
        Write-Host "${Green}   📊 Status: $ServiceStatus${NC}" -ForegroundColor Green
        
        if (-not [string]::IsNullOrWhiteSpace($ServiceUrl) -and $ServiceUrl -ne "None") {
            Write-Host "${Green}   🌐 URL: https://$ServiceUrl${NC}" -ForegroundColor Green
            
            # Test health endpoint if service is running
            if ($ServiceStatus -eq "RUNNING") {
                Write-Host "${Yellow}   🧪 Testing health endpoint...${NC}" -ForegroundColor Yellow
                try {
                    $Response = Invoke-WebRequest -Uri "https://$ServiceUrl/health" -UseBasicParsing -TimeoutSec 10
                    if ($Response.StatusCode -eq 200) {
                        Write-Host "${Green}   ✅ Health check passed${NC}" -ForegroundColor Green
                    } else {
                        Write-Host "${Red}   ❌ Health check failed (Status: $($Response.StatusCode))${NC}" -ForegroundColor Red
                    }
                } catch {
                    Write-Host "${Red}   ❌ Health check failed: $($_.Exception.Message)${NC}" -ForegroundColor Red
                }
            } else {
                Write-Host "${Yellow}   ⏳ Service not running, skipping health check${NC}" -ForegroundColor Yellow
            }
        } else {
            Write-Host "${Yellow}   ⚠️ Service URL not available${NC}" -ForegroundColor Yellow
        }
    } else {
        throw "Service not found"
    }
} catch {
    Write-Host "${Red}❌ App Runner service not found${NC}" -ForegroundColor Red
}

Write-Host ""
Write-Host "${Blue}📋 Summary:${NC}" -ForegroundColor Blue
Write-Host "=============================================" -ForegroundColor Blue
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "Account ID: $AccountId" -ForegroundColor White
Write-Host ""
Write-Host "${Yellow}💡 Next steps:${NC}" -ForegroundColor Yellow
Write-Host "• If resources are missing, run the deployment script" -ForegroundColor White
Write-Host "• If App Runner service exists but not running, check AWS Console logs" -ForegroundColor White
Write-Host "• If health check fails, verify database connectivity and environment variables" -ForegroundColor White 