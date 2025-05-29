# WordBattle API Reference

## Game Setup Endpoints

### Create New Game
```http
POST /games/setup
```

**Request Body:**
```json
{
    "max_players": 2,      // Number of players (2-4)
    "language": "de",      // Game language
    "invitees": ["user1", "user2"]  // List of usernames to invite
}
```

**Response:**
```json
{
    "game_id": "uuid",
    "invitations_sent": 2
}
```

### Get Pending Invitations
```http
GET /games/invitations
```

**Response:**
```json
[
    {
        "invitation_id": 1,
        "game_id": "uuid",
        "inviter": "username",
        "created_at": "2024-01-01T12:00:00Z"
    }
]
```

### Respond to Invitation
```http
POST /games/invitations/respond
```

**Request Body:**
```json
{
    "game_id": "uuid",
    "response": true  // true to accept, false to decline
}
```

**Response:**
```json
{
    "message": "Invitation response recorded"
}
```

### Start Game
```http
POST /games/{game_id}/start
```

**Response:**
```json
{
    "message": "Game started",
    "current_player_id": 1,
    "player_count": 2
}
```

## Game Play Endpoints

### Make Move
```http
POST /games/{game_id}/move
```

**Request Body:**
```json
[
    {
        "row": 7,
        "col": 7,
        "letter": "A",
        "is_blank": false
    }
]
```

**Response:**
```json
{
    "message": "Move successful",
    "points": 10,
    "next_player_id": 2
}
```

### Pass Turn
```http
POST /games/{game_id}/pass
```

**Response:**
```json
{
    "message": "Turn passed",
    "next_player_id": 2
}
```

### Exchange Letters
```http
POST /games/{game_id}/exchange
```

**Request Body:**
```json
{
    "letters": ["A", "B", "C"]
}
```

**Response:**
```json
{
    "message": "Letters exchanged",
    "new_rack": "DEFGHIJ",
    "next_player_id": 2
}
```

## WebSocket Connection

### Connect to Game
```javascript
ws://your-server/ws/games/{game_id}?token=your_auth_token
```

### WebSocket Messages

#### Game Update Event
```json
{
    "type": "game_update",
    "game_id": "uuid",
    "state": {
        "board": [...],
        "current_player_id": 1,
        "phase": "in_progress"
    },
    "last_move": {
        "player_id": 1,
        "move_data": [...],
        "points": 10
    }
}
```

#### Game Status Change Event
```json
{
    "type": "status_change",
    "game_id": "uuid",
    "status": "ready"
}
```

## Game States

1. **SETUP**: Initial state when game is created
2. **READY**: All invitations responded, waiting to start
3. **IN_PROGRESS**: Game is being played
4. **COMPLETED**: Game has ended
5. **CANCELLED**: Game was cancelled or expired

## Error Responses

All endpoints may return the following error responses:

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Not authorized to perform action
- `404 Not Found`: Resource not found

## Rate Limits

- WebSocket connections: Maximum 1 connection per game per user
- API endpoints: 100 requests per minute per user 