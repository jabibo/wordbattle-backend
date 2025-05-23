# WordBattle Architecture

This document describes the architecture of the WordBattle backend.

## Overview

WordBattle is a multiplayer word game similar to Scrabble, built with FastAPI and SQLAlchemy. The application follows a layered architecture with clear separation of concerns.

## Directory Structure

```
wordbattle-backend/
├── app/                    # Main application package
│   ├── game_logic/         # Game rules and logic
│   ├── models/             # Database models
│   ├── routers/            # API endpoints
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database connection
│   ├── main.py             # Application entry point
│   └── wordlist.py         # Word dictionary management
├── data/                   # Data files (wordlists)
├── tests/                  # Test suite
├── .env                    # Environment variables (not in repo)
├── .env.example            # Example environment variables
├── API.md                  # API documentation
├── ARCHITECTURE.md         # This file
├── MIGRATIONS.md           # Database migration guide
└── README.md               # Project overview
```

## Components

### Models

- **User**: Authentication and user management
- **Game**: Game state and metadata
- **Player**: Player information, rack, and score
- **Move**: Record of moves made in a game

### Routers

- **auth.py**: Authentication endpoints
- **users.py**: User management
- **games.py**: Game creation and management
- **moves.py**: Move validation and execution
- **profile.py**: User profile and game history
- **rack.py**: Rack management

### Game Logic

- **validate_move.py**: Validates move legality
- **full_points.py**: Calculates points for moves
- **board_utils.py**: Board manipulation utilities
- **rules.py**: Game rules implementation
- **letter_bag.py**: Letter distribution and rack management
- **game_completion.py**: Game completion conditions

## Data Flow

1. Client authenticates via `/auth/token`
2. Client creates or joins a game
3. Game starts when enough players join
4. Players take turns making moves:
   - Client sends move data
   - Server validates the move
   - Server calculates points
   - Server updates the game state
   - Server updates the player's rack
5. Game completes when end conditions are met

## Database Schema

### User
- id: Integer (PK)
- username: String (Unique)
- hashed_password: String

### Game
- id: String (PK)
- state: JSON
- current_player_id: Integer (FK to User)

### Player
- id: Integer (PK)
- game_id: String (FK to Game)
- user_id: Integer (FK to User)
- rack: String
- score: Integer

### Move
- id: Integer (PK)
- game_id: String (FK to Game)
- player_id: Integer (FK to User)
- move_data: JSON
- timestamp: DateTime

## Authentication

The application uses JWT (JSON Web Tokens) for authentication. Tokens are issued upon successful login and must be included in the Authorization header for protected endpoints.

## Configuration

Configuration is managed through environment variables, with defaults defined in `config.py`. This allows for easy deployment in different environments without code changes.