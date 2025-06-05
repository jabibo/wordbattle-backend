# Test User Email Address Updates

## Summary
Updated the test user email addresses from generic `@test.com` to `@binge.de` domain as requested.

## Changes Made

### 1. Updated Admin Router (`app/routers/admin.py`)
- **File**: `app/routers/admin.py`
- **Function**: `create_test_tokens()`
- **Changes**:
  - Added email mapping for test users:
    - `player01` → `player01@binge.de`
    - `player02` → `player02@binge.de`
  - Updated user creation logic to use the mapped email addresses
  - Added logic to update existing users' email addresses if they differ from the expected ones

### 2. Updated Debug Endpoint (`app/main.py`)
- **File**: `app/main.py`
- **Function**: `debug_tokens()`
- **Changes**:
  - Updated username lookups from uppercase `"PLAYER01"` and `"PLAYER02"` to lowercase `"player01"` and `"player02"`
  - Updated response keys to use lowercase usernames for consistency

### 3. Created Test Script
- **File**: `test_user_creation.py`
- **Purpose**: Verify that test users are created with correct email addresses
- **Features**:
  - Tests the admin endpoint for creating test tokens
  - Validates that email addresses match expected `@binge.de` format
  - Provides clear output showing success/failure for each user

## Usage

### Creating Test Users
To create test users with the correct email addresses, call the admin endpoint:

```bash
curl -X POST http://localhost:8000/admin/debug/create-test-tokens
```

This will create or update:
- Username: `player01`, Email: `player01@binge.de`
- Username: `player02`, Email: `player02@binge.de`

### Getting Debug Tokens
To get debug tokens for existing test users:

```bash
curl http://localhost:8000/debug/tokens
```

### Testing the Changes
Run the test script to verify the changes:

```bash
python3 test_user_creation.py
```

## Benefits
1. **Easier Invitations**: Test users now have proper `@binge.de` email addresses making it easier to test invitation functionality
2. **Consistency**: Both admin and debug endpoints now use consistent lowercase usernames
3. **Automatic Updates**: Existing test users will have their email addresses updated automatically
4. **Verification**: Test script provides easy way to verify the changes work correctly

## Notes
- Other test files using `@example.com` addresses were left unchanged as they are for general testing purposes
- The changes are backward compatible - existing functionality continues to work
- Test users are created with verified email status for immediate use 