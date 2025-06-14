# WordBattle API Test Suite

A comprehensive test suite for the WordBattle backend API endpoints, including thorough token generation and authentication testing.

## 🎯 Overview

This test suite provides complete coverage of all WordBattle API endpoints with focus on:

- **Authentication & Token Management**: JWT token generation, validation, expiration handling
- **API Endpoint Coverage**: All major API routes including games, users, admin, moves, etc.
- **Permission Testing**: Admin vs. regular user access control
- **Error Handling**: Comprehensive error scenario testing
- **Data Validation**: Input validation and edge case handling

## 📁 Test Structure

```
tests/
├── test_auth_api.py           # Authentication & token tests
├── test_users_api.py          # User management endpoints
├── test_games_api.py          # Game management (largest module)
├── test_moves_rack_api.py     # Game moves & letter rack
├── test_admin_api.py          # Admin functionality
├── test_comprehensive_api.py  # Additional endpoints & token edge cases
├── run_api_tests.py          # Test runner script
├── conftest.py               # Shared fixtures
└── README_API_TESTS.md       # This file
```

## 🔧 Test Coverage

### Authentication & Token Management (`test_auth_api.py`)
- User registration with validation
- Login with token generation
- Token validation and expiration
- Password reset flows
- Admin vs. regular user permissions
- Concurrent login sessions
- Token payload structure validation

### User Management (`test_users_api.py`)
- User profile operations
- Account management (update, delete)
- User search and discovery
- Privacy settings
- Notification preferences
- User statistics and achievements
- Avatar upload/management

### Game Management (`test_games_api.py`)
- Game creation with various configurations
- Joining and leaving games
- Game state management
- Computer player integration
- Game invitations and notifications
- Move validation and scoring
- Game completion flows

### Moves & Rack (`test_moves_rack_api.py`)
- Word placement moves
- Letter exchange operations
- Turn management
- Rack letter management
- Move validation and scoring
- Move history and statistics
- Undo functionality

### Admin Operations (`test_admin_api.py`)
- User administration
- Game administration
- System statistics and monitoring
- Word list management
- Report handling
- System maintenance functions

### Additional Features (`test_comprehensive_api.py`)
- Chat system
- Profile management
- Word admin operations
- System health endpoints
- Comprehensive token edge cases

## 🚀 Running Tests

### Quick Start

```bash
# Run all API tests
python tests/run_api_tests.py

# Run specific test category
python tests/run_api_tests.py --test-type auth
python tests/run_api_tests.py --test-type games
python tests/run_api_tests.py --test-type admin

# Run with coverage
python tests/run_api_tests.py --coverage --html-report
```

### Direct pytest Usage

```bash
# Run all API tests
pytest tests/test_*_api.py -v

# Run specific test file
pytest tests/test_auth_api.py -v

# Run with coverage
pytest tests/test_*_api.py --cov=app --cov-report=html

# Run tests matching pattern
pytest tests/test_auth_api.py::TestAuthAPI::test_login_success -v
```

### Test Runner Options

The `run_api_tests.py` script provides convenient options:

```bash
# Available test types
--test-type [all|auth|users|games|moves|admin|comprehensive]

# Output options
--verbose, -v          # Verbose output
--fail-fast, -x        # Stop on first failure
--parallel, -p         # Run tests in parallel

# Coverage options
--coverage, -c         # Enable coverage reporting
--html-report          # Generate HTML coverage report

# Test selection
--markers, -m          # Run tests with specific markers
```

## 🔑 Key Features

### Token Testing
- **Generation**: Tests proper JWT token creation with correct payload
- **Validation**: Comprehensive token validation scenarios
- **Expiration**: Tests token expiration and renewal
- **Edge Cases**: Malformed tokens, missing headers, etc.
- **Security**: Tests against token manipulation attacks

### Authentication Flows
- **Registration**: Complete user registration with validation
- **Login**: Secure login with token generation
- **Permissions**: Admin vs. regular user access control
- **Session Management**: Multiple concurrent sessions

### API Endpoint Coverage
- **CRUD Operations**: Create, Read, Update, Delete for all entities
- **Business Logic**: Game rules, scoring, move validation
- **Error Handling**: Proper error responses and status codes
- **Input Validation**: Comprehensive input validation testing

### Real-World Scenarios
- **Game Workflows**: Complete game creation to completion flows
- **User Interactions**: Multi-user game scenarios
- **Admin Operations**: Administrative task workflows
- **Error Recovery**: Error handling and recovery scenarios

## 📊 Test Data Management

### Fixtures
- **`test_user`**: Standard user with valid token
- **`test_user2`**: Second user for multi-user scenarios
- **`admin_user`**: Admin user with elevated permissions
- **`db_session`**: Database session for test isolation
- **`client`**: FastAPI test client

### Database Isolation
- Each test runs in isolated database transaction
- Automatic cleanup after each test
- No test interference or state leakage

## 🎛️ Configuration

### Environment Variables
```bash
# Test database URL
DATABASE_URL=postgresql://test:test@localhost/wordbattle_test

# JWT settings for testing
JWT_SECRET_KEY=test_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    auth: marks tests related to authentication
```

## 🔍 Test Examples

### Authentication Test
```python
def test_login_success(self, client: TestClient, test_user):
    """Test successful login with token generation."""
    response = client.post("/auth/token", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify token is valid
    token = data["access_token"]
    payload = verify_token(token)
    assert payload["sub"] == test_user["username"]
```

### Game API Test
```python
def test_create_game_success(self, client: TestClient, test_user):
    """Test successful game creation."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/games/", json={
        "language": "en",
        "max_players": 2
    }, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    assert data["max_players"] == 2
    assert data["creator_id"] == test_user["id"]
```

## 📈 Coverage Reports

Generate detailed coverage reports:

```bash
# Generate HTML coverage report
python tests/run_api_tests.py --coverage --html-report

# View coverage report
open htmlcov/index.html
```

## 🐛 Debugging Tests

### Running Individual Tests
```bash
# Run specific test class
pytest tests/test_auth_api.py::TestAuthAPI -v

# Run specific test method
pytest tests/test_auth_api.py::TestAuthAPI::test_login_success -v

# Run with pdb debugging
pytest tests/test_auth_api.py::TestAuthAPI::test_login_success -v --pdb
```

### Common Issues

1. **Database Connection**: Ensure test database is running
2. **Import Errors**: Check PYTHONPATH includes project root
3. **Token Issues**: Verify JWT configuration matches application
4. **Fixture Issues**: Check fixture dependencies and scoping

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
- name: Run API Tests
  run: |
    python tests/run_api_tests.py --coverage --test-type all
    
- name: Upload Coverage
  uses: codecov/codecov-action@v2
  with:
    file: ./coverage.xml
```

## 📝 Adding New Tests

### Test Structure
```python
class TestNewFeatureAPI:
    """Test new feature API endpoints."""
    
    def test_new_endpoint_success(self, client: TestClient, test_user):
        """Test successful endpoint usage."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/new-endpoint", json={
            "data": "test"
        }, headers=headers)
        
        assert response.status_code == 200
        assert response.json()["result"] == "expected"
    
    def test_new_endpoint_unauthorized(self, client: TestClient):
        """Test endpoint without authentication."""
        response = client.post("/new-endpoint", json={"data": "test"})
        assert response.status_code == 401
```

### Best Practices
- **Descriptive Names**: Use clear, descriptive test names
- **Comprehensive Coverage**: Test success, failure, and edge cases
- **Token Testing**: Always test authentication scenarios
- **Error Handling**: Test all error conditions
- **Documentation**: Add docstrings explaining test purpose

## 🏆 Success Metrics

A successful test run should show:
- ✅ All authentication flows working
- ✅ All API endpoints responding correctly
- ✅ Proper error handling for invalid requests
- ✅ Token generation and validation working
- ✅ Admin permissions enforced correctly
- ✅ Database operations completing successfully

## 🤝 Contributing

When adding new API endpoints:
1. Add comprehensive tests to appropriate test file
2. Include authentication testing
3. Test both success and failure scenarios
4. Update this documentation
5. Ensure all tests pass before committing 