#!/usr/bin/env pwsh

# Create IAM role for App Runner to access ECR
Write-Host "Creating IAM role for App Runner ECR access..." -ForegroundColor Green

# Trust policy for App Runner
$trustPolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "build.apprunner.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
"@

# Save trust policy to temporary file
$trustPolicyFile = "trust-policy.json"
$trustPolicy | Out-File -FilePath $trustPolicyFile -Encoding UTF8

try {
    # Create the IAM role
    Write-Host "Creating IAM role: AppRunnerECRAccessRole"
    aws iam create-role `
        --role-name AppRunnerECRAccessRole `
        --assume-role-policy-document file://$trustPolicyFile `
        --description "Role for App Runner to access ECR repositories"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ IAM role created successfully" -ForegroundColor Green
        
        # Attach the AWS managed policy for ECR access
        Write-Host "Attaching ECR access policy..."
        aws iam attach-role-policy `
            --role-name AppRunnerECRAccessRole `
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Policy attached successfully" -ForegroundColor Green
            Write-Host ""
            Write-Host "IAM role setup complete! You can now run the App Runner deployment script." -ForegroundColor Yellow
        } else {
            Write-Host "❌ Failed to attach policy" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Failed to create IAM role" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    # Clean up temporary file
    if (Test-Path $trustPolicyFile) {
        Remove-Item $trustPolicyFile
    }
} 