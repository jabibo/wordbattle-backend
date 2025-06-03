# Backend Game Start Logic Fixes Needed

## Problem Summary

The frontend reports that `currentPlayerId` is null when games are started, but testing reveals:

1. **Individual Game API** (`/games/{game_id}`) ✅ **WORKS CORRECTLY** - Returns proper `current_player_id`
2. **Games List API** (`/games/my-games`) ❌ **MISSING FIELD** - Doesn't include `current_player_id` in response
3. **Turn Number** starts at 0 instead of 1

## Testing Results

```
🔍 Game info AFTER starting:
   Status: in_progress
   Current Player ID: 44  ✅ CORRECT - Individual API works
   Turn Number: 0         ❌ SHOULD BE 1
   Players: ['43', '44']

🔍 Checking via my-games API:
   Status: in_progress
   KeyError: 'current_player_id'  ❌ FIELD MISSING
```

## Required Fixes

### 1. Fix Turn Number in Game Start Logic

**Files to modify:** `app/routers/games.py`

**Lines 946 and 1778:** In both `start_game()` and `auto_start_game()` functions:

```python
# CHANGE FROM:
"turn_number": 0,

# CHANGE TO:
"turn_number": 1,  # Start at turn 1, not 0
```

### 2. Ensure Current Player ID in Games List Response

**File:** `app/routers/games.py`
**Line 706:** The fix is already in the code but may not be deployed:

```python
game_info = {
    "id": game.id,
    "status": game.status.value,
    "language": game.language,
    "max_players": game.max_players,
    "current_players": len(players),
    "created_at": game.created_at.isoformat(),
    "started_at": game.started_at.isoformat() if game.started_at else None,
    "completed_at": game.completed_at.isoformat() if game.completed_at else None,
    "current_player_id": game.current_player_id,  # ← This line must be present
    "turn_number": turn_number,
    "is_user_turn": is_user_turn,
    # ... rest of fields
}
```

## Current State

- **Game Start Logic**: ✅ Working correctly - sets `current_player_id` properly
- **Database Schema**: ✅ Correct - `current_player_id` field exists and is populated
- **Individual Game API**: ✅ Working - returns `current_player_id` correctly
- **Games List API**: ❌ Missing `current_player_id` field in response
- **Turn Number**: ❌ Starts at 0 instead of 1

## Deployment Status

The local code has the fixes, but they don't appear to be deployed to production at:
`https://wordbattle-backend-441752988736.europe-west1.run.app`

## Next Steps

1. **Deploy the updated code** with both fixes
2. **Verify** that both APIs return consistent data
3. **Test** that turn numbers start at 1
4. **Confirm** frontend receives proper `currentPlayerId` data

## Test Script

The `test_game_start_debug.py` script can be used to verify the fixes work after deployment. 