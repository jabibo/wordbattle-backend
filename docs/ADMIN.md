# 🔧 WordBattle Backend Admin Guide

This guide covers administrative tasks, troubleshooting, and maintenance procedures for the WordBattle backend.

## 📋 Table of Contents

- [Admin Endpoints](#admin-endpoints)
- [Word Management](#word-management)
- [Database Management](#database-management)
- [Deployment Issues](#deployment-issues)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Troubleshooting](#troubleshooting)

## 🔑 Admin Endpoints

### Available Admin Operations

The backend provides several admin endpoints for maintenance and debugging:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/database/reset-games` | POST | Reset all game data (keeps users and words) |
| `/admin/alembic/reset-to-current` | POST | Reset Alembic migration state to current schema |
| `/admin/load-all-words` | POST | Load all remaining words into the database |
| `/database/status` | GET | Get comprehensive database status |
| `/debug/tokens` | GET | Generate test tokens for debugging |

### Authentication

Admin endpoints are currently **not protected** and should only be used in development/test environments. For production, implement proper authentication.

## 📚 Word Management

### Loading Complete Wordlists

The application comes with comprehensive German (~601,565 words) and English (~178,691 words) wordlists. 

#### Initial Word Loading

By default, the application loads only 10,000 German words during startup to avoid container timeout issues. To load all words:

```bash
# Use the admin endpoint
curl -X POST "https://your-deployment-url/admin/load-all-words"
```

#### Word Loading Status

Check current word counts:

```bash
curl "https://your-deployment-url/database/status"
```

Expected complete counts:
- **German**: 601,565 words
- **English**: 178,691 words
- **Total**: 780,256 words

### Manual Word Loading

You can also load words manually using the provided scripts:

```bash
# Load specific language with limit
python scripts/import_wordlist.py de --path data/de_words.txt --force

# Load all test wordlists
python scripts/import_test_wordlists.py

# Load all words using custom script
python scripts/load_all_words.py
```

## 💾 Database Management

### Database Health Check

Monitor database connectivity and status:

```bash
curl "https://your-deployment-url/health"
curl "https://your-deployment-url/database/status"
```

### Reset Game Data

To reset all game-related data while preserving users and words:

```bash
curl -X POST "https://your-deployment-url/admin/database/reset-games"
```

This will delete:
- All games
- All players (game participants)
- All moves
- All game invitations
- All chat messages

### Migration Management

If you encounter migration issues:

```bash
curl -X POST "https://your-deployment-url/admin/alembic/reset-to-current"
```

This will:
- Add missing columns if needed
- Reset Alembic migration state to current
- Preserve all existing data

## 🚀 Deployment Issues

### Common Deployment Problems

#### 1. Container Startup Timeouts

**Problem**: Cloud Run deployments fail with container startup timeouts

**Symptoms**:
```
Container failed to start and listen on the port defined by the PORT environment variable
```

**Root Causes**:
- Wordlist loading during startup (10,000+ words)
- Database connectivity issues during startup
- SQLAlchemy table creation at module import level

**Solution Applied**:
```python
# ✅ Fixed in app/main.py
@app.on_event("startup")
async def startup_event():
    # Database operations moved to startup event
    # Wordlist loading deferred to background tasks
```

**What was changed**:
1. Moved `Base.metadata.create_all(bind=engine)` from module level to startup event
2. Deferred large wordlist loading to background after container is ready
3. Made startup process fast and lightweight

#### 2. Database Connectivity Issues

**Problem**: Cloud Run cannot connect to external Google Cloud SQL database

**Symptoms**:
```
psycopg2.OperationalError: connection to server failed: Connection refused
password authentication failed for user "postgres"
```

**Root Causes**:
- Incorrect database IP address (changed from `34.34.95.133` to `35.187.90.105`)
- Password authentication issues between users
- Wrong database configuration environment variables

**Solution Applied**:
1. **Updated database IP**: Found correct IP using `gcloud sql instances list`
2. **Fixed authentication**: Reset passwords for both `postgres` and `wordbattle` users
3. **Corrected environment variables**: Used proper `DATABASE_URL` format

```bash
# ✅ Correct configuration
DATABASE_URL=postgresql://wordbattle:4JKPZvFwUhfCJhBJ@35.187.90.105:5432/wordbattle_test
```

#### 3. Port Configuration Issues

**Problem**: Container expects different ports than what Cloud Run provides

**Symptoms**:
```
Container failed to start and listen on port: 8000
```

**Solution Applied**:
```dockerfile
# ✅ Fixed in Dockerfile
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

This makes the container use Cloud Run's `PORT` environment variable dynamically.

#### 4. Previous Opponents Endpoint Bug

**Problem**: `/users/previous-opponents` endpoint returning empty results despite existing game data

**Symptoms**:
```json
{"previous_opponents":[],"total_count":0}
```

**Root Cause**: SQLAlchemy subquery approach not working with PostgreSQL:
```python
# ❌ Problematic code
user_games = db.query(Player.game_id).filter(Player.user_id == current_user.id).subquery()
```

**Solution Applied**: Replaced with raw SQL approach:
```python
# ✅ Fixed with raw SQL
sql = """
SELECT u.id, u.username, u.allow_invites, u.preferred_languages, opponent_counts.games_together
FROM (
    SELECT p2.user_id, COUNT(p2.game_id) as games_together
    FROM players p2
    WHERE p2.game_id IN (SELECT p1.game_id FROM players p1 WHERE p1.user_id = :current_user_id)
    AND p2.user_id != :current_user_id
    GROUP BY p2.user_id
) opponent_counts
JOIN users u ON u.id = opponent_counts.user_id
WHERE u.allow_invites = true
ORDER BY opponent_counts.games_together DESC
"""
```

### Deployment Best Practices

1. **Always test database connectivity** before deploying
2. **Use environment variables** for all configuration
3. **Monitor container startup time** - should be under 30 seconds
4. **Test all endpoints** after deployment
5. **Check logs** immediately after deployment

### Emergency Recovery

If deployment completely fails:

1. **Delete the service** and start fresh:
```bash
gcloud run services delete service-name --region=region --quiet
```

2. **Use the working Docker image approach**:
```bash
# Build locally first
docker build -t test-image .

# Test locally with correct environment variables
docker run -e DATABASE_URL="correct-url" -p 8080:8080 test-image

# Only deploy if local test passes
gcloud run deploy --source . --region=region
```

3. **Check database connectivity separately**:
```bash
# Test database access
docker run --rm postgres:13 psql "postgresql://user:pass@host:5432/db" -c "SELECT 1;"
```

## 📊 Monitoring & Health Checks

### Health Endpoints

- **Basic Health**: `GET /health`
- **Database Status**: `GET /database/status`
- **Debug Info**: `GET /debug/tokens`

### Expected Responses

**Healthy System**:
```json
{
  "status": "healthy",
  "database": "healthy",
  "timestamp": "2025-06-06T11:29:18.494213"
}
```

**Database Status**:
```json
{
  "status": {
    "tables_exist": true,
    "word_counts": {"de": 601565, "en": 178691},
    "user_count": 2,
    "game_count": 6,
    "is_initialized": true
  }
}
```

### Monitoring Checklist

- [ ] Container startup time < 30 seconds
- [ ] Database connectivity working
- [ ] All word counts match expected values
- [ ] Health endpoints responding
- [ ] Critical endpoints (auth, games, opponents) working

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Issue: Endpoint Returns Empty Results

**Check**:
1. Database connectivity: `curl /health`
2. Data existence: `curl /database/status`
3. Authentication: Check if proper tokens are used
4. SQL query logic: Review logs for SQL errors

#### Issue: Slow Response Times

**Check**:
1. Database query performance
2. Large dataset loading in background
3. Network connectivity between Cloud Run and database
4. Container resource limits

#### Issue: Authentication Failures

**Check**:
1. Token format and expiration
2. Secret key configuration
3. User existence in database
4. JWT algorithm configuration

### Getting Debug Information

```bash
# Get comprehensive debug tokens
curl "https://your-deployment-url/debug/tokens"

# Check database detailed status
curl "https://your-deployment-url/database/status"

# Test specific endpoints with debug tokens
curl -H "Authorization: Bearer TOKEN" "https://your-deployment-url/users/previous-opponents"
```

### Log Analysis

For Cloud Run deployments, check logs:

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" --limit=50

# Filter for errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=10
```

## 📞 Support

For additional support:

1. Check this documentation first
2. Review deployment logs
3. Test endpoints manually
4. Verify database connectivity
5. Check environment variable configuration

---

*Last updated: June 2025*
*This guide covers the deployment infrastructure fixes implemented in June 2025* 