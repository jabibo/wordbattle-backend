# WordBattle Backend - Admin Endpoints Documentation

This document provides comprehensive information about all admin endpoints available in the WordBattle backend.

## 🔐 Admin Authentication

Admin privileges are controlled by two database fields in the `users` table:
- `is_admin` (Boolean, default: false) - Full admin access
- `is_word_admin` (Boolean, default: false) - Wordlist management only

To grant admin privileges, update the database directly:
```sql
-- Grant full admin privileges
UPDATE users SET is_admin = true WHERE email = 'admin@example.com';

-- Grant wordlist admin only
UPDATE users SET is_word_admin = true WHERE email = 'wordlist@example.com';
```

### 🚀 Default Admin User

The system automatically creates a default admin user during reset operations:
- **Email**: `jan@binge.de`
- **Username**: `jan_admin`  
- **Password**: `admin123!WordBattle`
- **Admin Status**: Full admin (`is_admin = true`)

This user is automatically created:
- During database reset operations
- When using the manual admin creation endpoint
- If the user already exists, it's updated with admin privileges

## 📋 Available Admin Endpoints

### 🧪 Debug Endpoints

#### `POST /admin/debug/create-test-tokens`
**Purpose**: Create test tokens for development users `player01` and `player02`

**Authentication**: None (disabled in production)

**Request**: No parameters required

**Response**:
```json
{
  "message": "Test tokens created successfully",
  "users": [
    {
      "user_id": 1,
      "username": "player01",
      "email": "player01@binge.de",
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "token_type": "bearer"
    },
    {
      "user_id": 2,
      "username": "player02",
      "email": "player02@binge.de",
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "token_type": "bearer"
    }
  ],
  "usage": {
    "description": "Use these tokens in the Authorization header",
    "format": "Bearer <access_token>",
    "example": "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

**Notes**: 
- Automatically disabled in production environments
- Creates users with password `testpassword123` if they don't exist
- Tokens are valid for 30 days

---

### 📚 Wordlist Management Endpoints

#### `POST /admin/wordlists/import`
**Purpose**: Import a wordlist from an uploaded file

**Authentication**: Requires `is_admin = true`

**Request**: 
- Form data with `language` (string) and `file` (uploaded file)
- Content-Type: `multipart/form-data`

**Example**:
```bash
curl -X POST "https://your-domain.com/admin/wordlists/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "language=de" \
  -F "file=@german_words.txt"
```

**Response**:
```json
{
  "message": "Successfully imported 601565 words for language 'de'",
  "language": "de",
  "word_count": 601565
}
```

#### `GET /admin/wordlists`
**Purpose**: List all available wordlists and their word counts

**Authentication**: Requires `is_admin = true`

**Response**:
```json
[
  {"language": "de", "word_count": 601565},
  {"language": "en", "word_count": 178690}
]
```

#### `DELETE /admin/wordlists/{language}`
**Purpose**: Delete all words for a specific language

**Authentication**: Requires `is_admin = true`

**Parameters**: 
- `language` (path parameter): Language code (e.g., "de", "en")

**Response**:
```json
{
  "message": "Successfully deleted wordlist for language 'de'",
  "language": "de",
  "word_count": 601565
}
```

---

### 🗄️ Database Management Endpoints

#### `POST /admin/database/reset-games`
**Purpose**: Reset only game-related data while preserving users and wordlists

**Authentication**: Requires `is_admin = true`

**⚠️ WARNING**: This will delete:
- All games and their state
- All player records
- All moves history
- All game invitations
- All chat messages

**✅ PRESERVES**:
- User accounts
- WordLists

**Response**:
```json
{
  "message": "Game data reset completed successfully",
  "performed_by": "admin_username",
  "before_counts": {
    "Games": 19,
    "Players": 34,
    "Moves": 32,
    "Game Invitations": 9,
    "Chat Messages": 0
  },
  "deleted_counts": {
    "Chat Messages": 0,
    "Moves": 32,
    "Players": 34,
    "Game Invitations": 9,
    "Games": 19
  },
  "after_counts": {
    "Games": 0,
    "Players": 0,
    "Moves": 0,
    "Game Invitations": 0,
    "Chat Messages": 0
  },
  "reset_sequences": [
    "moves_id_seq",
    "players_id_seq",
    "game_invitations_id_seq"
  ],
  "preserved": ["Users", "WordLists"]
}
```

#### `POST /admin/database/reset-users-and-games`
**Purpose**: Reset ALL user and game data (DANGER: Full reset)

**Authentication**: Requires `is_admin = true`

**🚨 EXTREME DANGER**: This will delete:
- ALL user accounts (including the admin performing this action!)
- All games and their state
- All player records
- All moves history
- All game invitations
- All chat messages

**✅ PRESERVES**:
- WordLists only

**Note**: After this action, you will need to recreate admin accounts using debug endpoints or direct database access.

**Response**:
```json
{
  "message": "FULL reset completed - all users and games deleted",
  "warning": "All user accounts have been deleted, including admin accounts",
  "performed_by": "admin_username",
  "before_counts": {
    "Users": 112,
    "Games": 19,
    "Players": 34,
    "Moves": 32,
    "Game Invitations": 9,
    "Chat Messages": 0
  },
  "deleted_counts": {
    "Chat Messages": 0,
    "Moves": 32,
    "Players": 34,
    "Game Invitations": 9,
    "Games": 19,
    "Users": 112
  },
  "after_counts": {
    "Users": 0,
    "Games": 0,
    "Players": 0,
    "Moves": 0,
    "Game Invitations": 0,
    "Chat Messages": 0
  },
  "reset_sequences": [
    "chat_messages_id_seq",
    "moves_id_seq",
    "players_id_seq",
    "game_invitations_id_seq",
    "users_id_seq"
  ],
  "preserved": ["WordLists"],
  "next_steps": "You will need to recreate admin accounts using debug endpoints or database access"
}
```

#### `POST /admin/database/import-wordlists`
**Purpose**: Import all available wordlists (German and English)

**Authentication**: None (public endpoint for deployment scripts)

**Response**:
```json
{
  "message": "Wordlist import completed successfully",
  "imported_counts": {
    "German (de)": 601565,
    "English (en)": 178690
  },
  "total_words": 780255,
  "expected_total": "~780,255 words (601,565 German + 178,690 English)"
}
```

**Notes**:
- Imports from `data/de_words.txt` and `data/en_words.txt`
- No authentication required for deployment automation
- Replaces existing wordlists if they exist

#### `GET /admin/database/wordlist-status`
**Purpose**: Get current wordlist status and counts

**Authentication**: None (public endpoint for monitoring)

**Response**:
```json
{
  "wordlist_status": {
    "de": 601565,
    "en": 178690
  },
  "total_words": 780255,
  "expected_counts": {
    "German (de)": "~601,565 words",
    "English (en)": "~178,690 words",
    "Total expected": "~780,255 words"
  }
}
```

#### `GET /admin/database/admin-status`
**Purpose**: Get current admin and user statistics

**Authentication**: None (public endpoint for monitoring)

**Response**:
```json
{
  "total_users": 4,
  "admin_users": 1,
  "word_admin_users": 0,
  "has_admins": true,
  "admin_usernames": ["jan_admin"],
  "note": "First 3 admin usernames shown for privacy"
}
```

#### `POST /admin/database/create-default-admin`
**Purpose**: Create the default admin user manually

**Authentication**: None (public endpoint for setup)

**Response**:
```json
{
  "message": "Default admin user created successfully",
  "admin_email": "jan@binge.de",
  "admin_username": "jan_admin",
  "admin_password": "admin123!WordBattle",
  "note": "Please change the password after first login",
  "login_url": "/auth/login"
}
```

**Notes**:
- Creates or updates the default admin user
- If user exists, ensures admin privileges are set
- Returns credentials for immediate use

---

## 🛡️ Security Notes

1. **Production Safety**: Debug endpoints are automatically disabled in production
2. **Admin Requirements**: Most endpoints require `is_admin = true` in the database
3. **Logging**: All admin actions are logged with user information
4. **Dangerous Operations**: Reset endpoints include extensive warnings and confirmations
5. **Public Endpoints**: Only wordlist status and import endpoints are public (for deployment automation)

---

## 🖥️ Recommended Admin UI Sections

For a comprehensive admin interface, consider these sections:

### 📊 Dashboard
- Current user count
- Active games count
- Wordlist status
- Recent activity logs

### 👥 User Management
- List all users
- Toggle admin privileges
- View user activity
- User search and filtering

### 🎮 Game Management
- Active games overview
- Game history
- Reset games functionality
- Game statistics

### 📚 Wordlist Management
- Current wordlist status
- Import new wordlists
- Delete specific languages
- Wordlist statistics

### 🗄️ Database Operations
- Game data reset (safe)
- Full database reset (dangerous)
- Import operations
- Backup status

### 🧪 Development Tools
- Test token generation
- Debug information
- API testing interface
- Log viewer

---

## 📝 Example Usage Scripts

### Import Wordlists After Deployment
```bash
#!/bin/bash
DOMAIN="https://your-domain.com"

echo "Importing wordlists..."
curl -X POST "$DOMAIN/admin/database/import-wordlists"

echo "Checking status..."
curl "$DOMAIN/admin/database/wordlist-status"
```

### Create Admin User (requires database access)
```sql
-- First, register normally through the app, then:
UPDATE users SET is_admin = true WHERE email = 'your-admin@email.com';
```

### Create Default Admin User (immediate setup)
```bash
#!/bin/bash
DOMAIN="https://your-domain.com"

echo "Creating default admin user..."
curl -X POST "$DOMAIN/admin/database/create-default-admin"

echo "Checking admin status..."
curl "$DOMAIN/admin/database/admin-status"
```

### Login as Default Admin
```bash
#!/bin/bash
DOMAIN="https://your-domain.com"

# Login with email verification (recommended)
curl -X POST "$DOMAIN/auth/email-login" \
     -H "Content-Type: application/json" \
     -d '{"email": "jan@binge.de"}'

# Or use legacy token endpoint with username
curl -X POST "$DOMAIN/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=jan_admin&password=admin123!WordBattle"
```

---

## 🔗 Related Documentation

- [API Documentation](https://your-domain.com/docs) - Interactive Swagger UI
- [Environment Configuration](deploy-production.sh) - Deployment scripts
- [Database Schema](app/models.py) - Data models and relationships 