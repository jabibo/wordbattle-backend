#!/bin/bash

echo "Fly.io Deployment - Non-AWS Alternative"
echo "======================================="

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "Installing Fly.io CLI..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "Please login to Fly.io:"
    flyctl auth login
fi

# Create fly.toml configuration
cat > fly.toml << 'EOF'
app = "wordbattle-backend"
primary_region = "fra"

[build]
  dockerfile = "Dockerfile.prod"

[env]
  PORT = "8000"
  DB_HOST = "wordbattle-db.c9wokmyok9ty.eu-central-1.rds.amazonaws.com"
  DB_NAME = "wordbattle"
  DB_USER = "postgres"
  DB_PASSWORD = "Wordbattle2024"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/health"

[vm]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
EOF

echo "Creating Fly.io app..."
flyctl apps create wordbattle-backend --org personal

echo "Setting secrets..."
flyctl secrets set DB_PASSWORD=Wordbattle2024

echo "Deploying to Fly.io..."
flyctl deploy

echo ""
echo "Deployment completed!"

# Get the app URL
APP_URL="https://wordbattle-backend.fly.dev"

echo "Application URL: $APP_URL"
echo "Health check: $APP_URL/health"
echo "Debug tokens: $APP_URL/debug/tokens"

echo ""
echo "Fly.io deployment complete!"
echo "Your application is now running globally on Fly.io!"

# Show status
flyctl status 