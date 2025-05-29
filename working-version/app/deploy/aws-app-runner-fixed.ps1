# AWS App Runner Deployment Script for WordBattle Backend (PowerShell) - Fixed Version
# Usage: .\deploy\aws-app-runner-fixed.ps1

param(
    [string]$Region = "eu-central-1",
    [string]$RepositoryName = "wordbattle-backend",
    [string]$ServiceName = "wordbattle-backend",
    [string]$DbInstanceId = "wordbattle-db"
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$NC = "`e[0m"

Write-Host "${Green}🚀 WordBattle AWS App Runner Deployment (Fixed)${NC}" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
    Write-Host "${Green}✅ AWS CLI found${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ AWS CLI is not installed. Please install it first.${NC}" -ForegroundColor Red
    Write-Host "Download from: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "${Green}✅ Docker found${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Docker is not installed. Please install it first.${NC}" -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Get AWS account ID
try {
    $AccountId = aws sts get-caller-identity --query Account --output text
    if (-not $AccountId -or $AccountId -eq "None") {
        throw "Failed to get account ID"
    }
    Write-Host "${Green}✅ AWS Account ID: $AccountId${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to get AWS account ID. Please configure AWS CLI.${NC}" -ForegroundColor Red
    Write-Host "Run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Step 1: Create ECR repository if it doesn't exist
Write-Host "${Yellow}📦 Creating ECR repository...${NC}" -ForegroundColor Yellow
try {
    $RepoExists = aws ecr describe-repositories --repository-names $RepositoryName --region $Region 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "${Green}✅ ECR repository already exists${NC}" -ForegroundColor Green
    } else {
        throw "Repository not found"
    }
} catch {
    try {
        Write-Host "${Yellow}🆕 Creating new ECR repository...${NC}" -ForegroundColor Yellow
        aws ecr create-repository --repository-name $RepositoryName --region $Region | Out-Null
        Write-Host "${Green}✅ ECR repository created successfully${NC}" -ForegroundColor Green
    } catch {
        Write-Host "${Red}❌ Failed to create ECR repository: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Login to ECR
Write-Host "${Yellow}🔐 Logging into ECR...${NC}" -ForegroundColor Yellow
try {
    $LoginPassword = aws ecr get-login-password --region $Region
    $LoginPassword | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"
    Write-Host "${Green}✅ Successfully logged into ECR${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to login to ECR: $($_.Exception.Message)${NC}" -ForegroundColor Red
    exit 1
}

# Step 3: Build and push Docker image
Write-Host "${Yellow}🏗️ Building Docker image...${NC}" -ForegroundColor Yellow
try {
    docker build -f Dockerfile.prod -t $RepositoryName .
    Write-Host "${Green}✅ Docker image built successfully${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to build Docker image: $($_.Exception.Message)${NC}" -ForegroundColor Red
    exit 1
}

Write-Host "${Yellow}🏷️ Tagging image...${NC}" -ForegroundColor Yellow
try {
    docker tag "${RepositoryName}:latest" "$AccountId.dkr.ecr.$Region.amazonaws.com/${RepositoryName}:latest"
    Write-Host "${Green}✅ Image tagged successfully${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to tag image: $($_.Exception.Message)${NC}" -ForegroundColor Red
    exit 1
}

Write-Host "${Yellow}📤 Pushing image to ECR...${NC}" -ForegroundColor Yellow
try {
    docker push "$AccountId.dkr.ecr.$Region.amazonaws.com/${RepositoryName}:latest"
    Write-Host "${Green}✅ Image pushed successfully to ECR${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to push image to ECR: $($_.Exception.Message)${NC}" -ForegroundColor Red
    exit 1
}

# Step 4: Create RDS database if it doesn't exist
Write-Host "${Yellow}🗄️ Checking RDS database...${NC}" -ForegroundColor Yellow
$DbPassword = ""
$DbEndpoint = ""

try {
    $DbInfo = aws rds describe-db-instances --db-instance-identifier $DbInstanceId --region $Region 2>$null | ConvertFrom-Json
    if ($DbInfo -and $DbInfo.DBInstances.Count -gt 0) {
        Write-Host "${Green}✅ RDS database already exists${NC}" -ForegroundColor Green
        $DbEndpoint = $DbInfo.DBInstances[0].Endpoint.Address
        
        # Try to get password from Parameter Store
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
    } else {
        throw "Database not found"
    }
} catch {
    Write-Host "${Yellow}📊 Creating RDS database...${NC}" -ForegroundColor Yellow
    
    # Generate a random password
    $DbPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 25 | ForEach-Object {[char]$_})
    Write-Host "${Green}🔑 Generated database password: $DbPassword${NC}" -ForegroundColor Green
    Write-Host "${Yellow}⚠️ Please save this password securely!${NC}" -ForegroundColor Yellow
    
    # Get default VPC and subnets
    try {
        $VpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $Region
        $SubnetIds = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" --query "Subnets[*].SubnetId" --output text --region $Region
        $SubnetArray = $SubnetIds -split "`t"
        
        if ($SubnetArray.Count -lt 2) {
            throw "Need at least 2 subnets for RDS"
        }
        
        Write-Host "${Green}✅ Found VPC: $VpcId with $($SubnetArray.Count) subnets${NC}" -ForegroundColor Green
    } catch {
        Write-Host "${Red}❌ Failed to get VPC information: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
    
    # Create DB subnet group
    try {
        aws rds create-db-subnet-group `
            --db-subnet-group-name wordbattle-subnet-group `
            --db-subnet-group-description "Subnet group for WordBattle" `
            --subnet-ids $SubnetArray `
            --region $Region 2>$null | Out-Null
        Write-Host "${Green}✅ DB subnet group created${NC}" -ForegroundColor Green
    } catch {
        Write-Host "${Yellow}⚠️ DB subnet group already exists${NC}" -ForegroundColor Yellow
    }
    
    # Create security group for RDS
    try {
        $SgId = aws ec2 create-security-group `
            --group-name wordbattle-db-sg `
            --description "Security group for WordBattle database" `
            --vpc-id $VpcId `
            --region $Region `
            --query "GroupId" --output text 2>$null
        Write-Host "${Green}✅ Security group created: $SgId${NC}" -ForegroundColor Green
    } catch {
        $SgId = aws ec2 describe-security-groups `
            --filters "Name=group-name,Values=wordbattle-db-sg" `
            --query "SecurityGroups[0].GroupId" --output text --region $Region
        Write-Host "${Yellow}⚠️ Security group already exists: $SgId${NC}" -ForegroundColor Yellow
    }
    
    # Allow PostgreSQL access from anywhere (you should restrict this in production)
    try {
        aws ec2 authorize-security-group-ingress `
            --group-id $SgId `
            --protocol tcp `
            --port 5432 `
            --cidr 0.0.0.0/0 `
            --region $Region 2>$null | Out-Null
        Write-Host "${Green}✅ Security group rule added${NC}" -ForegroundColor Green
    } catch {
        Write-Host "${Yellow}⚠️ Security group rule already exists${NC}" -ForegroundColor Yellow
    }
    
    # Create RDS instance
    try {
        Write-Host "${Yellow}🚀 Creating RDS instance (this will take several minutes)...${NC}" -ForegroundColor Yellow
        aws rds create-db-instance `
            --db-instance-identifier $DbInstanceId `
            --db-instance-class db.t3.micro `
            --engine postgres `
            --master-username postgres `
            --master-user-password $DbPassword `
            --allocated-storage 20 `
            --db-subnet-group-name wordbattle-subnet-group `
            --vpc-security-group-ids $SgId `
            --db-name wordbattle `
            --backup-retention-period 7 `
            --storage-encrypted `
            --region $Region | Out-Null
        
        Write-Host "${Yellow}⏳ Waiting for database to be available (this may take 5-10 minutes)...${NC}" -ForegroundColor Yellow
        aws rds wait db-instance-available --db-instance-identifier $DbInstanceId --region $Region
        
        # Get database endpoint
        $DbInfo = aws rds describe-db-instances --db-instance-identifier $DbInstanceId --region $Region | ConvertFrom-Json
        $DbEndpoint = $DbInfo.DBInstances[0].Endpoint.Address
        Write-Host "${Green}✅ Database created successfully${NC}" -ForegroundColor Green
        
    } catch {
        Write-Host "${Red}❌ Failed to create RDS instance: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
    
    # Store password in Systems Manager Parameter Store
    try {
        aws ssm put-parameter `
            --name "/wordbattle/db-password" `
            --value $DbPassword `
            --type "SecureString" `
            --region $Region `
            --overwrite 2>$null | Out-Null
        Write-Host "${Green}✅ Database password stored in Parameter Store${NC}" -ForegroundColor Green
    } catch {
        Write-Host "${Yellow}⚠️ Failed to store password in Parameter Store${NC}" -ForegroundColor Yellow
    }
}

Write-Host "${Green}✅ Database endpoint: $DbEndpoint${NC}" -ForegroundColor Green

# Step 5: Generate a secret key
$SecretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})

# Step 6: Create App Runner service
Write-Host "${Yellow}🏃 Creating App Runner service...${NC}" -ForegroundColor Yellow

# Check if service already exists
$ServiceExists = $false
try {
    $ServiceInfo = aws apprunner describe-service --service-arn "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName" --region $Region 2>$null | ConvertFrom-Json
    if ($ServiceInfo -and $ServiceInfo.Service) {
        $ServiceExists = $true
        Write-Host "${Yellow}🔄 Service exists, updating...${NC}" -ForegroundColor Yellow
        aws apprunner start-deployment `
            --service-arn "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName" `
            --region $Region | Out-Null
        Write-Host "${Green}✅ Deployment started${NC}" -ForegroundColor Green
    }
} catch {
    # Service doesn't exist, we'll create it
}

if (-not $ServiceExists) {
    Write-Host "${Yellow}🆕 Creating new service...${NC}" -ForegroundColor Yellow
    
    # Create new service configuration
    $AppRunnerConfig = @{
        ServiceName = $ServiceName
        SourceConfiguration = @{
            ImageRepository = @{
                ImageIdentifier = "$AccountId.dkr.ecr.$Region.amazonaws.com/${RepositoryName}:latest"
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
    
    try {
        $ConfigJson = $AppRunnerConfig | ConvertTo-Json -Depth 10
        $ConfigFile = [System.IO.Path]::GetTempFileName()
        $ConfigJson | Out-File -FilePath $ConfigFile -Encoding UTF8
        
        aws apprunner create-service --cli-input-json "file://$ConfigFile" --region $Region | Out-Null
        Remove-Item $ConfigFile
        Write-Host "${Green}✅ App Runner service created${NC}" -ForegroundColor Green
    } catch {
        Write-Host "${Red}❌ Failed to create App Runner service: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
}

# Step 7: Wait for service to be running
Write-Host "${Yellow}⏳ Waiting for App Runner service to be ready...${NC}" -ForegroundColor Yellow
try {
    aws apprunner wait service-running --service-arn "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName" --region $Region
    Write-Host "${Green}✅ App Runner service is now running${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Timeout waiting for service to be ready${NC}" -ForegroundColor Red
    Write-Host "${Yellow}💡 The service may still be starting. Check AWS Console for status.${NC}" -ForegroundColor Yellow
}

# Get service URL
Write-Host "${Yellow}🔍 Retrieving service URL...${NC}" -ForegroundColor Yellow
try {
    $ServiceInfo = aws apprunner describe-service --service-arn "arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName" --region $Region | ConvertFrom-Json
    $ServiceUrl = $ServiceInfo.Service.ServiceUrl
    
    if ([string]::IsNullOrWhiteSpace($ServiceUrl) -or $ServiceUrl -eq "None") {
        Write-Host "${Yellow}⚠️ Service URL not immediately available. Service may still be starting...${NC}" -ForegroundColor Yellow
        $ServiceUrl = ""
    } else {
        Write-Host "${Green}✅ Service URL retrieved: $ServiceUrl${NC}" -ForegroundColor Green
    }
} catch {
    Write-Host "${Red}❌ Failed to retrieve service URL: $($_.Exception.Message)${NC}" -ForegroundColor Red
    $ServiceUrl = ""
}

Write-Host "${Green}🎉 Deployment completed successfully!${NC}" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
if (-not [string]::IsNullOrWhiteSpace($ServiceUrl)) {
    Write-Host "${Green}📍 Service URL: https://$ServiceUrl${NC}" -ForegroundColor Green
    Write-Host "${Green}📚 API Documentation: https://$ServiceUrl/docs${NC}" -ForegroundColor Green
    Write-Host "${Green}❤️ Health Check: https://$ServiceUrl/health${NC}" -ForegroundColor Green
} else {
    Write-Host "${Yellow}📍 Service URL: Not yet available${NC}" -ForegroundColor Yellow
    Write-Host "${Yellow}💡 Check AWS Console for service status${NC}" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "${Yellow}📝 Important Information:${NC}" -ForegroundColor Yellow
Write-Host "   • Database Password: $DbPassword" -ForegroundColor White
Write-Host "   • Secret Key: $SecretKey" -ForegroundColor White
Write-Host "   • Database Endpoint: $DbEndpoint" -ForegroundColor White
Write-Host ""
Write-Host "${Yellow}⚠️ Security Notes:${NC}" -ForegroundColor Yellow
Write-Host "   • Change the database password in production" -ForegroundColor White
Write-Host "   • Restrict database security group to App Runner only" -ForegroundColor White
Write-Host "   • Store secrets in AWS Systems Manager Parameter Store" -ForegroundColor White
Write-Host "   • Configure proper CORS origins for production" -ForegroundColor White

# Test the deployment
Write-Host "${Yellow}🧪 Testing deployment...${NC}" -ForegroundColor Yellow

# Check if ServiceUrl is valid
if ([string]::IsNullOrWhiteSpace($ServiceUrl) -or $ServiceUrl -eq "None") {
    Write-Host "${Red}❌ Service URL not found. The App Runner service may not have deployed successfully.${NC}" -ForegroundColor Red
    Write-Host "${Yellow}💡 Please check the AWS Console for App Runner service status and logs.${NC}" -ForegroundColor Yellow
    Write-Host "${Yellow}   Service ARN: arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName${NC}" -ForegroundColor Yellow
} else {
    try {
        Write-Host "${Yellow}🔍 Testing health endpoint: https://$ServiceUrl/health${NC}" -ForegroundColor Yellow
        $Response = Invoke-WebRequest -Uri "https://$ServiceUrl/health" -UseBasicParsing -TimeoutSec 30
        if ($Response.StatusCode -eq 200 -and $Response.Content -like "*healthy*") {
            Write-Host "${Green}✅ Health check passed!${NC}" -ForegroundColor Green
        } else {
            Write-Host "${Red}❌ Health check failed. Status: $($Response.StatusCode)${NC}" -ForegroundColor Red
            Write-Host "${Yellow}Response: $($Response.Content)${NC}" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "${Red}❌ Health check failed. Check the logs in AWS Console.${NC}" -ForegroundColor Red
        Write-Host "${Red}Error: $($_.Exception.Message)${NC}" -ForegroundColor Red
        Write-Host "${Yellow}💡 The service might still be starting up. Please wait a few minutes and try again.${NC}" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "${Yellow}🔧 Troubleshooting Information:${NC}" -ForegroundColor Yellow
Write-Host "   • Region: $Region" -ForegroundColor White
Write-Host "   • Account ID: $AccountId" -ForegroundColor White
Write-Host "   • Service Name: $ServiceName" -ForegroundColor White
Write-Host "   • Repository Name: $RepositoryName" -ForegroundColor White
Write-Host "   • Service ARN: arn:aws:apprunner:${Region}:${AccountId}:service/$ServiceName" -ForegroundColor White
if (-not [string]::IsNullOrWhiteSpace($ServiceUrl)) {
    Write-Host "   • Service URL: https://$ServiceUrl" -ForegroundColor White
}
Write-Host ""
Write-Host "${Yellow}📋 Next Steps:${NC}" -ForegroundColor Yellow
Write-Host "   1. Check AWS Console > App Runner for service status" -ForegroundColor White
Write-Host "   2. Review CloudWatch logs for any errors" -ForegroundColor White
Write-Host "   3. Verify ECR image was pushed successfully" -ForegroundColor White
Write-Host "   4. Test health endpoint manually once service is running" -ForegroundColor White
Write-Host ""
Write-Host "${Green}🚀 Deployment script completed!${NC}" -ForegroundColor Green 