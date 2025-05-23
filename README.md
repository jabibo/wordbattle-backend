# WordBattle Backend

[![Coverage](https://img.shields.io/badge/coverage-83%25-green.svg)](https://github.com/yourusername/wordbattle-backend)

A FastAPI backend for a multiplayer word game similar to Scrabble.

## Environment Variables

The application uses environment variables for configuration. Copy the `.env.example` file to `.env` and adjust the values as needed:

```bash
cp .env.example .env
```

Key environment variables:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `SECRET_KEY`: Secret key for JWT token generation
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token expiration time
- `DEFAULT_WORDLIST_PATH`: Path to the wordlist file
- `LETTER_POOL_SIZE`: Number of letters in a player's rack
- `GAME_INACTIVE_DAYS`: Days of inactivity before a game is considered abandoned

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/wordbattle-backend.git
cd wordbattle-backend
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the database:

```bash
# For development/initial setup only
python -m app.create_tables

# For production, use migrations (see docs/MIGRATIONS.md)
```

4. Import wordlists:

```bash
# Import default German wordlist
python import_test_wordlists.py

# Import a custom wordlist
python -m app.wordlist <language_code> <path_to_wordlist>
```

5. Run the application:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## Multi-Language Support

WordBattle now supports multiple languages for wordlists. See [docs/WORDLISTS.md](docs/WORDLISTS.md) for details on:

- Importing wordlists for different languages
- Setting the language for a game
- Managing wordlists through the admin API

## Docker Deployment

You can run the application using Docker:

1. Build and start the container:

```bash
docker-compose up -d
```

2. The API will be available at http://localhost:8000

3. To view logs:

```bash
docker-compose logs -f
```

4. To stop the container:

```bash
docker-compose down
```

For more details, see [docs/DOCKER.md](docs/DOCKER.md).

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run the tests with pytest:

```bash
python -m pytest
```

## Database Management

For database management, see [docs/MIGRATIONS.md](docs/MIGRATIONS.md).

## Game Rules

- Players take turns placing words on the board
- Words must connect to existing words
- Points are awarded based on letter values and board multipliers
- A game ends when:
  - A player uses all their letters and no more are available
  - All players pass three consecutive times
  - The game has been inactive for the configured number of days

## License

MIT