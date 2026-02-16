# Push Notifications - Development Setup

**Date**: February 2026  
**Purpose**: Configure Firebase and run backend with push notification support locally

---

## 1. Firebase Console Setup

### Create/Select Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select existing **WordBattle** project or create a new one
3. If creating new: Add your app (iOS/Android) when ready

### Enable Cloud Messaging

1. In Firebase Console: **Build** → **Cloud Messaging**
2. Cloud Messaging is enabled by default for Firebase projects
3. For iOS: You'll need to upload APNs key/certificate (see iOS setup in frontend plan)

### Get Service Account Credentials

1. **Project Settings** (gear icon) → **Service Accounts** tab
2. Click **Generate New Private Key** → Confirm
3. Download the JSON file (e.g. `wordbattle-firebase-adminsdk-xxxxx.json`)
4. **Rename** to `firebase-credentials.json` for consistency

---

## 2. Local Configuration

### Place Credentials

```bash
cd /Users/janbinge/git/wordbattle/wordbattle-backend

# Copy downloaded file to config directory
cp ~/Downloads/wordbattle-firebase-adminsdk-*.json config/firebase-credentials.json

# Verify (file should exist, never commit it)
ls -la config/firebase-credentials.json
```

### Update .env

Add or update in your `.env`:

```bash
# Push Notifications (Development)
ENABLE_PUSH_NOTIFICATIONS=true
# FIREBASE_CREDENTIALS_PATH is set by docker-compose to /app/config/firebase-credentials.json
```

---

## 3. Start Development Docker

```bash
cd /Users/janbinge/git/wordbattle/wordbattle-backend

# Build and start
docker compose -f docker-compose.dev.yml up -d --build

# View logs
docker compose -f docker-compose.dev.yml logs -f app

# Verify
curl http://localhost:8000/health
```

### Without Firebase (Push Disabled)

If you don't have credentials yet, the backend will start with push notifications disabled:

```bash
# In .env - leave as default
ENABLE_PUSH_NOTIFICATIONS=false

# Backend will start normally, push features will be no-op
docker compose -f docker-compose.dev.yml up -d
```

---

## 4. Verify Firebase Installation

```bash
# Check Firebase SDK is installed in container
docker exec wordbattle-backend-dev pip list | grep firebase

# Expected: firebase-admin  6.3.0

# If credentials are present, test initialization (when FirebaseService is implemented)
# curl http://localhost:8000/api/v1/health
# Should include push notification status when implemented
```

---

## 5. Directory Structure

```
wordbattle-backend/
├── config/
│   ├── .gitkeep
│   └── firebase-credentials.json   # You add this (gitignored)
├── docker-compose.dev.yml          # Development Docker setup
├── .env                            # Your local env (gitignored)
└── ...
```

---

## 6. Troubleshooting

### "No such file or directory" for firebase-credentials.json

- Ensure file exists: `ls config/firebase-credentials.json`
- Backend starts without it when `ENABLE_PUSH_NOTIFICATIONS=false`
- When `true`, the file must exist

### Firebase Admin SDK not found

```bash
docker compose -f docker-compose.dev.yml build --no-cache app
docker compose -f docker-compose.dev.yml up -d
```

### Database connection refused

- Wait for PostgreSQL to be healthy (~10 seconds)
- Check: `docker compose -f docker-compose.dev.yml ps`

---

## 7. Next Steps

After development setup:

1. Implement `FirebaseService` in backend (see `PUSH_NOTIFICATIONS_IMPLEMENTATION_PLAN.md`)
2. Add push token registration API
3. Add database migrations for push tables
4. Integrate notification sending into game logic
