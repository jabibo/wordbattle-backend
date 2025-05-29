#!/usr/bin/env pwsh

$SERVICE_ARN = "arn:aws:apprunner:eu-central-1:598510278922:service/wordbattle-backend/9112212ab18243638c181fdf7da4a9a2"

Write-Host "🔍 App Runner Service Debug Information" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Get service details
Write-Host "📋 Service Details:" -ForegroundColor Yellow
$service = aws apprunner describe-service --service-arn $SERVICE_ARN --region eu-central-1 | ConvertFrom-Json
Write-Host "   Status: $($service.Service.Status)" -ForegroundColor $(if ($service.Service.Status -eq 'RUNNING') { 'Green' } else { 'Red' })
Write-Host "   URL: $($service.Service.ServiceUrl)"
Write-Host "   Created: $($service.Service.CreatedAt)"

# Get application logs
Write-Host "`n📝 Recent Application Logs:" -ForegroundColor Yellow
try {
    $logGroups = aws logs describe-log-groups --log-group-name-prefix "/aws/apprunner/wordbattle-backend/9112212ab18243638c181fdf7da4a9a2" --region eu-central-1 | ConvertFrom-Json
    
    foreach ($logGroup in $logGroups.logGroups) {
        Write-Host "   Log Group: $($logGroup.logGroupName)" -ForegroundColor Cyan
        
        $streams = aws logs describe-log-streams --log-group-name $logGroup.logGroupName --region eu-central-1 | ConvertFrom-Json
        
        foreach ($stream in $streams.logStreams) {
            Write-Host "     Stream: $($stream.logStreamName)" -ForegroundColor White
            
            $events = aws logs get-log-events --log-group-name $logGroup.logGroupName --log-stream-name $stream.logStreamName --region eu-central-1 | ConvertFrom-Json
            
            foreach ($event in $events.events) {
                $timestamp = [DateTimeOffset]::FromUnixTimeMilliseconds($event.timestamp).ToString("yyyy-MM-dd HH:mm:ss")
                Write-Host "       [$timestamp] $($event.message)" -ForegroundColor Gray
            }
        }
    }
} catch {
    Write-Host "   Error retrieving logs: $($_.Exception.Message)" -ForegroundColor Red
}

# Test the URL
Write-Host "`n🌐 Testing Service URL:" -ForegroundColor Yellow
$url = "https://$($service.Service.ServiceUrl)"
Write-Host "   URL: $url"
try {
    $response = Invoke-WebRequest -Uri $url -TimeoutSec 10
    Write-Host "   Status: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test health endpoint
Write-Host "`n🏥 Testing Health Endpoint:" -ForegroundColor Yellow
$healthUrl = "$url/health"
Write-Host "   URL: $healthUrl"
try {
    $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 10
    Write-Host "   Status: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Green
} catch {
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
} 