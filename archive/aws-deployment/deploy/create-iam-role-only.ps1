# Create IAM Role for App Runner ECR Access
param(
    [string]$RoleName = "AppRunnerECRAccessRole"
)

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$NC = "`e[0m"

Write-Host "${Blue}👤 Creating IAM Role for App Runner${NC}" -ForegroundColor Blue
Write-Host "====================================" -ForegroundColor Blue

# Get AWS account ID
try {
    $AccountId = aws sts get-caller-identity --query Account --output text
    Write-Host "${Green}✅ Account ID: $AccountId${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Red}❌ Failed to get AWS account ID${NC}" -ForegroundColor Red
    exit 1
}

# Trust policy for App Runner
Write-Host "${Yellow}📝 Creating trust policy...${NC}" -ForegroundColor Yellow
$TrustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Service = "build.apprunner.amazonaws.com"
            }
            Action = "sts:AssumeRole"
        }
    )
} | ConvertTo-Json -Depth 10

# Check if role already exists
Write-Host "${Yellow}🔍 Checking if role exists...${NC}" -ForegroundColor Yellow
try {
    $RoleInfo = aws iam get-role --role-name $RoleName 2>$null | ConvertFrom-Json
    if ($RoleInfo -and $RoleInfo.Role) {
        Write-Host "${Green}✅ IAM role already exists${NC}" -ForegroundColor Green
        Write-Host "${Green}   Role ARN: $($RoleInfo.Role.Arn)${NC}" -ForegroundColor Green
    } else {
        throw "Role not found"
    }
} catch {
    # Create the role
    Write-Host "${Yellow}🆕 Creating new IAM role...${NC}" -ForegroundColor Yellow
    try {
        $TrustPolicyFile = [System.IO.Path]::GetTempFileName()
        $TrustPolicy | Out-File -FilePath $TrustPolicyFile -Encoding UTF8
        
        $CreateResult = aws iam create-role `
            --role-name $RoleName `
            --assume-role-policy-document "file://$TrustPolicyFile" `
            --description "Role for App Runner to access ECR repositories" | ConvertFrom-Json
        
        Remove-Item $TrustPolicyFile
        Write-Host "${Green}✅ IAM role created successfully${NC}" -ForegroundColor Green
        Write-Host "${Green}   Role ARN: $($CreateResult.Role.Arn)${NC}" -ForegroundColor Green
    } catch {
        Remove-Item $TrustPolicyFile -ErrorAction SilentlyContinue
        Write-Host "${Red}❌ Failed to create IAM role: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
}

# Attach the ECR access policy
Write-Host "${Yellow}🔐 Attaching ECR access policy...${NC}" -ForegroundColor Yellow
try {
    aws iam attach-role-policy `
        --role-name $RoleName `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess" 2>$null | Out-Null
    Write-Host "${Green}✅ ECR access policy attached${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Yellow}⚠️ Policy may already be attached (this is normal)${NC}" -ForegroundColor Yellow
}

# Wait for IAM role to propagate
Write-Host "${Yellow}⏳ Waiting for IAM role to propagate (10 seconds)...${NC}" -ForegroundColor Yellow
Start-Sleep 10

Write-Host ""
Write-Host "${Blue}📋 IAM Role Summary:${NC}" -ForegroundColor Blue
Write-Host "====================================" -ForegroundColor Blue
Write-Host "Role Name: $RoleName" -ForegroundColor White
Write-Host "Role ARN: arn:aws:iam::${AccountId}:role/$RoleName" -ForegroundColor White
Write-Host "Policy: AWSAppRunnerServicePolicyForECRAccess" -ForegroundColor White
Write-Host ""
Write-Host "${Green}✅ IAM role is ready for App Runner service creation${NC}" -ForegroundColor Green 