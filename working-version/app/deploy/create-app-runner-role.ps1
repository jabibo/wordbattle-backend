# Create IAM Role for App Runner to access ECR
param(
    [string]$Region = "eu-central-1",
    [string]$RoleName = "AppRunnerECRAccessRole"
)

# Colors for output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$NC = "`e[0m"

Write-Host "${Green}🔐 Creating IAM Role for App Runner${NC}" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Create trust policy for App Runner
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

# Create the IAM role
try {
    Write-Host "${Yellow}🆕 Creating IAM role: $RoleName${NC}" -ForegroundColor Yellow
    
    # Save trust policy to temp file
    $TrustPolicyFile = [System.IO.Path]::GetTempFileName()
    $TrustPolicy | Out-File -FilePath $TrustPolicyFile -Encoding UTF8
    
    # Create the role
    $RoleResult = aws iam create-role `
        --role-name $RoleName `
        --assume-role-policy-document "file://$TrustPolicyFile" `
        --description "Role for App Runner to access ECR" `
        --region $Region 2>$null | ConvertFrom-Json
    
    Remove-Item $TrustPolicyFile
    
    if ($RoleResult) {
        Write-Host "${Green}✅ IAM role created successfully${NC}" -ForegroundColor Green
        Write-Host "   Role ARN: $($RoleResult.Role.Arn)" -ForegroundColor White
    }
} catch {
    # Check if role already exists
    try {
        $ExistingRole = aws iam get-role --role-name $RoleName --region $Region 2>$null | ConvertFrom-Json
        if ($ExistingRole) {
            Write-Host "${Yellow}⚠️ IAM role already exists${NC}" -ForegroundColor Yellow
            Write-Host "   Role ARN: $($ExistingRole.Role.Arn)" -ForegroundColor White
        }
    } catch {
        Write-Host "${Red}❌ Failed to create IAM role: $($_.Exception.Message)${NC}" -ForegroundColor Red
        exit 1
    }
}

# Attach the AWS managed policy for ECR access
try {
    Write-Host "${Yellow}🔗 Attaching ECR access policy...${NC}" -ForegroundColor Yellow
    aws iam attach-role-policy `
        --role-name $RoleName `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess" `
        --region $Region 2>$null | Out-Null
    Write-Host "${Green}✅ ECR access policy attached${NC}" -ForegroundColor Green
} catch {
    Write-Host "${Yellow}⚠️ Policy may already be attached${NC}" -ForegroundColor Yellow
}

# Get the role ARN
try {
    $Role = aws iam get-role --role-name $RoleName --region $Region | ConvertFrom-Json
    $RoleArn = $Role.Role.Arn
    Write-Host "${Green}✅ Role ARN: $RoleArn${NC}" -ForegroundColor Green
    
    # Output the ARN for use in other scripts
    Write-Host ""
    Write-Host "${Yellow}📋 Use this ARN in your App Runner configuration:${NC}" -ForegroundColor Yellow
    Write-Host "$RoleArn" -ForegroundColor White
    
    return $RoleArn
} catch {
    Write-Host "${Red}❌ Failed to get role ARN${NC}" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "${Green}🚀 IAM role setup completed!${NC}" -ForegroundColor Green 