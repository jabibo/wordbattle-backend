# WordBattle API Documentation

## Authentication

### Register a new user
```
POST /users/register
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "id": "integer",
  "username": "string"
}
```

### Login
```
POST /auth/token
```

**Request Body (form data):**
```
username: string
password: string
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### Get current user
```
GET /me
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "integer",
  "username": "string"
}
```

## Games

### Create a new game
```
POST /games/
```

**Response:**
```json
{
  "id": "string",
  "state": "string"
}
```

### Get a game
```
GET /games/{game_id}
```

**Response:**
```json
{
  "id": "string",
  "state": "string",
  "current_player_id": "integer"
}
```

### Join a game
```
POST /games/{game_id}/join
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "rack": "string"
}
```

### Start a game
```
POST /games/{game_id}/start
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "current_player_id": "integer"
}
```

### Make a move
```
POST /games/{game_id}/move
```

**Headers:**
```
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "move_data": [
    {
      "row": "integer",
      "col": "integer",
      "letter": "string"
    }
  ]
}
```

**Response:**
```json
{
  "message": "string",
  "points": "integer",
  "words": [
    ["string", "integer"]
  ],
  "new_state": "array"
}
```

### Pass turn
```
POST /games/{game_id}/pass
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "message": "string",
  "next_player_id": "integer"
}
```

### Deal letters
```
POST /games/{game_id}/deal
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "new_rack": "string",
  "next_player_id": "integer"
}
```

### Exchange letters
```
POST /games/{game_id}/exchange
```

**Headers:**
```
Authorization: Bearer {token}
```

**Query Parameters:**
```
letters: string
```

**Response:**
```json
{
  "new_rack": "string",
  "next_player_id": "integer"
}
```

### Complete a game
```
POST /games/{game_id}/complete
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "message": "string",
  "completion_data": {
    "reason": "string",
    "scores": "object",
    "winner_id": "integer"
  }
}
```

## Rack Management

### Get all racks
```
GET /rack/
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "racks": [
    {
      "game_id": "string",
      "rack": "string"
    }
  ]
}
```

### Get rack for a specific game
```
GET /rack/{game_id}
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "rack": "string"
}
```

### Refill rack
```
POST /rack/{game_id}/refill
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "rack": "string",
  "new_letters": "string",
  "message": "string"
}
```

## Profile

### Get my games
```
GET /games/mine
```

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": "string",
    "state": "string",
    "current_player_id": "integer"
  }
]
```