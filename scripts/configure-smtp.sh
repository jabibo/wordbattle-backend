#!/bin/bash
# SMTP Configuration Script for WordBattle Self-Hosted Server
# This script adds SMTP email configuration to the production server

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         📧 SMTP CONFIGURATION FOR WORDBATTLE 📧              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# SMTP Configuration
SMTP_SERVER="smtp.strato.de"
SMTP_PORT="465"
SMTP_USERNAME="service@binge-wordbattle.de"
SMTP_PASSWORD="z1nUNGrz1ZDmu4J"
FROM_EMAIL="service@binge-wordbattle.de"
SMTP_USE_SSL="true"

echo "📧 SMTP Configuration:"
echo "  Server: $SMTP_SERVER"
echo "  Port: $SMTP_PORT"
echo "  Username: $SMTP_USERNAME"
echo "  From Email: $FROM_EMAIL"
echo "  Use SSL: $SMTP_USE_SSL"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please run this script from the /opt/wordbattle directory on the server"
    exit 1
fi

echo "📝 Adding SMTP configuration to .env file..."

# Backup existing .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"

# Remove old SMTP configuration if exists
sed -i '/^SMTP_/d' .env
sed -i '/^FROM_EMAIL/d' .env

# Add new SMTP configuration
cat >> .env << EOL

# SMTP Configuration (added $(date))
SMTP_SERVER=$SMTP_SERVER
SMTP_PORT=$SMTP_PORT
SMTP_USERNAME=$SMTP_USERNAME
SMTP_PASSWORD=$SMTP_PASSWORD
FROM_EMAIL=$FROM_EMAIL
SMTP_USE_SSL=$SMTP_USE_SSL
EOL

echo "✅ SMTP configuration added to .env"
echo ""
echo "🔄 Restarting backend container..."

# Restart backend container to apply changes
docker-compose restart backend

echo ""
echo "✅ Backend restarted"
echo ""
echo "🧪 Testing SMTP configuration..."
echo "Check backend logs:"
echo "  docker logs wordbattle-backend --tail 50"
echo ""
echo "Look for:"
echo "  ✅ 'SMTP configured' or similar success message"
echo "  ❌ 'SMTP_PASSWORD not set' (means configuration failed)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SMTP Configuration Complete!"
echo ""
echo "Next steps:"
echo "1. Test email login from the app"
echo "2. Check your email for verification code"
echo "3. If no email received, check:"
echo "   - Spam/junk folder"
echo "   - Backend logs: docker logs wordbattle-backend"
echo "   - SMTP server status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

