# Endgame Testing Mode for WordBattle 🧪

This feature provides a test switch to reduce the letter bag from 100 tiles to only 24 tiles containing the most common letters. This allows for rapid testing of endgame scenarios without playing through entire games.

## Quick Setup

### 1. **Environment Variable Method** (Production)
```bash
# Enable test mode
export TEST_MODE_ENDGAME=true

# Start your application
# Letter bags will now contain only 24 tiles

# Disable test mode
unset TEST_MODE_ENDGAME
```

### 2. **Programmatic Method** (Local Testing)
```python
from app.game_logic.game_state import GameState

# Create game with test mode
game = GameState("en", test_mode=True)
print(f"Letter bag size: {len(game.letter_bag)}")  # Will be 24
```

### 3. **Automated Test Script**
```bash
# Run the automated endgame test setup
python create_endgame_test.py
```

## Letter Distribution

### Normal Mode (100 tiles)
**English:** E(12), A(9), I(9), O(8), N(6), R(6), T(6), S(4), and others...

### Test Mode (24 tiles)
**English:** E(5), A(4), I(4), O(3), N(3), R(2), T(2), S(1)
**German:** E(6), N(4), S(3), A(3), R(3), I(2), T(2), ?(1)

## Endgame Scenarios to Test

### 1. **Empty Letter Bag**
- After distributing initial racks (14 tiles for 2 players)
- Only 10 tiles remain in bag
- Game ends when bag is empty AND one player uses all tiles

### 2. **Final Tile Bonus**
- Player who empties their rack gets bonus points
- Bonus = sum of remaining tiles in other players' racks

### 3. **Consecutive Passes**
- Game ends after 6 consecutive passes
- Test by having players pass instead of making moves

### 4. **Score Calculation**
- Final scores include remaining rack penalties
- Each remaining tile subtracts its point value

## Testing Commands

```bash
# Enable test mode for current session
export TEST_MODE_ENDGAME=true

# Create and start a test game (use debug tokens)
TOKEN=$(curl -s https://wordbattle-backend-441752988736.europe-west1.run.app/debug/tokens | jq -r '.tokens.player01.token')

# Create game
GAME=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"language":"en","max_players":2}' "https://wordbattle-backend-441752988736.europe-west1.run.app/games/" | jq -r '.id')

# Check letter bag in game state
curl -s -H "Authorization: Bearer $TOKEN" "https://wordbattle-backend-441752988736.europe-west1.run.app/games/$GAME" | jq '.state.letter_bag | length'
# Should return 24 instead of 100
```

## Verification Script

Run the local verification to ensure everything works:

```bash
python test_endgame_locally.py
```

Expected output:
```
🧪 ENDGAME TEST MODE VERIFICATION
Distribution test: ✅ PASS
GameState test:    ✅ PASS  
LetterBag test:    ✅ PASS
Overall: ✅ ALL TESTS PASSED
```

## Production Usage

### Deploy with Test Mode
```bash
# Set environment variable and deploy
export TEST_MODE_ENDGAME=true
gcloud run deploy wordbattle-backend --source . --region europe-west1 --allow-unauthenticated

# Or set via Cloud Run environment variables in console
```

### Monitor Test Games
```bash
# Check if test mode is active (look for debug message in logs)
gcloud logs read --project=wordbattle-1748668162 --filter="resource.type=cloud_run_revision" --limit=50 | grep "TEST MODE"
```

## Important Notes

⚠️ **WARNING:** This is for testing only!
- DO NOT use in production with real players
- Letter distribution is NOT balanced for real gameplay
- Endgame triggers much faster than normal

✅ **Benefits:**
- Rapid endgame testing
- Consistent test conditions
- Easy to enable/disable
- Works with existing game logic

🎯 **Use Cases:**
- Testing endgame bonus calculations
- Verifying game end conditions
- Testing UI behavior when bag is empty
- Performance testing with frequent game endings

## Reset to Normal Mode

```bash
# Disable test mode
unset TEST_MODE_ENDGAME

# Redeploy without test mode
gcloud run deploy wordbattle-backend --source . --region europe-west1 --allow-unauthenticated
``` 