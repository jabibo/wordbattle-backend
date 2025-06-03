# Exchange Rules Documentation

## New Exchange Rules (Implemented)

The exchange functionality in WordBattle now enforces stricter rules to make the game more challenging and strategic:

### Rules

1. **Bag must have at least 7 tiles**: Players cannot exchange letters if there are fewer than 7 tiles remaining in the letter bag.

2. **Must exchange exactly 7 letters**: Players must exchange all 7 letters from their rack. Partial exchanges (fewer than 7 letters) are no longer allowed.

### Implementation Details

- **Location**: `app/game_logic/game_state.py` - `make_move()` method
- **Validation Order**: 
  1. Check if bag has at least 7 tiles
  2. Check if exactly 7 letters are being exchanged
  3. Proceed with exchange if both conditions are met

### Error Messages

- **Insufficient bag tiles**: `"Cannot exchange tiles - not enough letters remaining in the bag (need at least 7 letters in bag for exchange)."`
- **Wrong number of letters**: `"Cannot exchange tiles - you must exchange exactly 7 letters."`

### Testing

The rules have been tested with the following scenarios:

✅ **Normal exchange**: 7 letters with sufficient bag tiles - **WORKS**
✅ **Less than 7 letters**: Trying to exchange 1-6 letters - **REJECTED**
✅ **More than 7 letters**: Trying to exchange 8+ letters - **REJECTED** 
✅ **Insufficient bag**: 7 letters but bag has < 7 tiles - **REJECTED**
✅ **Edge case**: 7 letters with exactly 7 tiles in bag - **WORKS**

### Code Changes

```python
elif move_type == MoveType.EXCHANGE:
    if len(self.letter_bag) < 7:
        return False, "Cannot exchange tiles - not enough letters remaining in the bag (need at least 7 letters in bag for exchange).", []
    if len(move_data) != 7:
        return False, "Cannot exchange tiles - you must exchange exactly 7 letters.", []
    success, msg, new_rack = self._handle_exchange(player_id, move_data)
    if success:
        # Reset consecutive passes since an exchange was made
        self.consecutive_passes = 0
    return success, msg, new_rack
```

### Impact on Game Strategy

This change makes letter exchanges more strategic:

- Players can no longer make small tactical exchanges (e.g., exchanging just 1-2 bad letters)
- Exchanges become a bigger commitment, requiring players to give up their entire rack
- Late in the game when the bag is nearly empty, exchanges become impossible
- This increases the importance of word placement and rack management

### Deployment Status

- ✅ **Implemented**: Changes made to `game_state.py`
- ✅ **Tested Locally**: All test scenarios pass
- ✅ **Deployed**: Live on production backend
- ✅ **Active**: New rules are now enforced for all games

### Backward Compatibility

This is a breaking change that affects existing game mechanics. All new games will use the new rules immediately. Any games in progress at the time of deployment will also enforce the new rules on subsequent exchange attempts. 