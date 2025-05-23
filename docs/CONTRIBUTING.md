# Contributing to WordBattle

Thank you for considering contributing to WordBattle! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/yourusername/wordbattle-backend.git
cd wordbattle-backend
```

3. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file:
```bash
cp .env.example .env
```

6. Set up the database:
```bash
python -m app.create_tables --create
```

7. Run the development server:
```bash
uvicorn app.main:app --reload
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions, classes, and modules
- Keep functions small and focused on a single task
- Use meaningful variable and function names

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting a pull request:
```bash
python -m pytest
```

- Aim for high test coverage

## Pull Request Process

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:
```bash
git commit -m "Add feature X"
```

3. Push to your fork:
```bash
git push origin feature/your-feature-name
```

4. Create a pull request to the main repository

5. Ensure your PR includes:
   - A clear description of the changes
   - Any relevant issue numbers
   - Tests for new functionality
   - Documentation updates if needed

## Adding New Features

1. **Game Logic**: Place in `app/game_logic/`
2. **API Endpoints**: Add to existing routers or create new ones in `app/routers/`
3. **Database Models**: Add to `app/models/`
4. **Tests**: Add to `tests/` directory

## Database Changes

1. Create a new migration:
```bash
alembic revision -m "description of changes"
```

2. Update the migration file in `migrations/versions/`

3. Test the migration:
```bash
alembic upgrade head
```

## Documentation

- Update API.md when adding or changing endpoints
- Update ARCHITECTURE.md when changing the system structure
- Add comments for complex code sections
- Keep the README.md up to date

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.