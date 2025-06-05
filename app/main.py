from fastapi import FastAPI, Request, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, games, moves, rack, profile, admin, auth, chat, game_setup
from app.config import CORS_ORIGINS, RATE_LIMIT, SECRET_KEY, ALGORITHM
import time
import os
import logging
import json
from datetime import datetime, timezone, timedelta
from app.database import engine, Base
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WordBattle API",
    description="""
    WordBattle is a multiplayer word game API that allows users to play Scrabble-like games online.
    
    ## Features
    * User authentication and registration
    * Game creation and management
    * Real-time gameplay with WebSocket support
    * Move validation and scoring
    * Player statistics and profiles
    * Multiple language support
    
    ## Authentication
    Most endpoints require authentication using a Bearer token. To get a token:
    1. Register a new user at `/users/register`
    2. Login at `/auth/token` to get your access token
    3. Include the token in the Authorization header: `Bearer <your_token>`
    """,
    version="1.0.0",
    contact={
        "name": "WordBattle Support",
        "url": "https://github.com/yourusername/wordbattle-backend",
        "email": "support@wordbattle.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication and token operations",
        },
        {
            "name": "users",
            "description": "User registration and management",
        },
        {
            "name": "games",
            "description": "Game creation, joining, and state management",
        },
        {
            "name": "moves",
            "description": "Game moves and actions",
        },
        {
            "name": "rack",
            "description": "Letter rack management",
        },
        {
            "name": "profile",
            "description": "User profile and statistics",
        },
        {
            "name": "admin",
            "description": "Administrative operations",
        },
        {
            "name": "chat",
            "description": "Chat operations",
        },
    ]
)

# Add CORS middleware with environment-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Use configured origins, not wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    expose_headers=[
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials",
    ],
    max_age=600,
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    from app.database_manager import initialize_database_if_needed
    result = initialize_database_if_needed()
    
    if result["success"]:
        if result["action"] == "skipped":
            logger.info("Database already initialized - skipping word loading")
        else:
            logger.info("Database initialized successfully")
            # Schedule background word import only if we just initialized
            import asyncio
            asyncio.create_task(schedule_background_word_import())
    else:
        logger.error(f"Database initialization failed: {result.get('error', 'Unknown error')}")

async def schedule_background_word_import():
    """Schedule background import of remaining words after startup delay."""
    try:
        import asyncio
        await asyncio.sleep(60)  # Wait 60 seconds after startup
        logger.info("Starting background import of remaining German words...")
        
        # Use the database manager to check and load words
        from app.database_manager import check_database_status, load_wordlist
        
        status = check_database_status()
        de_count = status["word_counts"].get("de", 0)
        
        if de_count < 100000:  # If we have less than 100k words, continue importing
            logger.info(f"Current German word count: {de_count}, loading more...")
            result = load_wordlist(language="de", skip=de_count, limit=100000)
            
            if result["success"]:
                logger.info(f"Background import completed: {result['words_loaded']} words loaded")
            else:
                logger.error(f"Background import failed: {result.get('error', 'Unknown error')}")
        else:
            logger.info("Word import already complete, skipping background import")
            
    except Exception as e:
        logger.error(f"Error in background word import: {e}")

# Simple rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting in tests
    if os.environ.get("TESTING") == "1":
        return await call_next(request)
    
    # Get client IP
    client_ip = request.client.host
    
    # Check if this IP has made too many requests
    current_time = time.time()
    request.app.state.request_timestamps = getattr(request.app.state, "request_timestamps", {})
    timestamps = request.app.state.request_timestamps.get(client_ip, [])
    
    # Clean up old timestamps
    timestamps = [ts for ts in timestamps if current_time - ts < 60]
    
    # Check rate limit
    if len(timestamps) >= RATE_LIMIT:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"}
        )
    
    # Add current timestamp
    timestamps.append(current_time)
    request.app.state.request_timestamps[client_ip] = timestamps
    
    # Process the request
    response = await call_next(request)
    return response

# Health check endpoint for AWS load balancers
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    try:
        # Test database connection
        from app.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "healthy"
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/database/status")
async def database_status():
    """Get detailed database status information"""
    from app.database_manager import get_database_info
    return get_database_info()

@app.post("/admin/database/reset")
async def reset_database_admin():
    """
    ADMIN ONLY: Reset and reinitialize the database completely.
    This will drop all tables and recreate them with current schema.
    """
    try:
        from app.database_manager import reset_database, load_wordlist
        from app.database import Base, engine
        
        logger.info("🔄 Starting complete database reset...")
        
        # Drop and recreate all tables using current models
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        
        logger.info("Creating all tables with current schema...")
        Base.metadata.create_all(bind=engine)
        
        # Reset alembic version table to head
        logger.info("Setting up migration state...")
        try:
            from alembic.config import Config
            from alembic import command
            alembic_cfg = Config("alembic.ini")
            command.stamp(alembic_cfg, "head")
            logger.info("✅ Migration state set to head")
        except Exception as e:
            logger.warning(f"Could not set migration state: {e}")
        
        # Load initial words
        logger.info("Loading initial wordlist...")
        word_result = load_wordlist(language="de", limit=10000)
        
        return {
            "success": True,
            "message": "Database reset and reinitialized successfully",
            "wordlist": word_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Database reset failed"
        }

@app.get("/debug/tokens")
async def debug_tokens():
    """Debug endpoint that provides test tokens for player01 and player02"""
    try:
        from datetime import datetime, timezone, timedelta
        import jwt
        from app.config import SECRET_KEY, ALGORITHM
        from app.database import SessionLocal
        from app.models.user import User
        
        db = SessionLocal()
        try:
            # Find or get info about test users
            player01 = db.query(User).filter(User.username == "player01").first()
            player02 = db.query(User).filter(User.username == "player02").first()
            
            # If users don't exist, find any existing users for testing
            if not player01:
                player01 = db.query(User).filter(User.id.in_([1, 2, 3, 4, 5])).first()
            if not player02:
                player02 = db.query(User).filter(User.id.in_([6, 7, 8, 9, 10])).first()
                
            # Fallback to any users if still none found
            if not player01:
                player01 = db.query(User).first()
            if not player02:
                player02 = db.query(User).offset(1).first()
                
            if not player01 or not player02:
                return {
                    "error": "No users found in database for testing",
                    "suggestion": "Create some users first"
                }
            
            # Generate tokens that expire in 30 days (reasonable for testing)
            future_time = datetime.now(timezone.utc) + timedelta(days=30)
            exp_timestamp = int(future_time.timestamp())
            
            # Create fresh tokens for available users - using USERNAME in sub field
            player01_token = jwt.encode({"sub": player01.username, "exp": exp_timestamp}, SECRET_KEY, algorithm=ALGORITHM)
            player02_token = jwt.encode({"sub": player02.username, "exp": exp_timestamp}, SECRET_KEY, algorithm=ALGORITHM)
            
            # Get current service URL
            service_url = "https://wordbattle-backend-test-441752988736.europe-west1.run.app"
            
            return {
                "message": "Fresh debug tokens (30 days expiry) - WORKING TOKENS!",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": future_time.isoformat(),
                "tokens": {
                    "player01": {
                        "user_id": player01.id,
                        "username": player01.username, 
                        "email": player01.email,
                        "token": player01_token
                    },
                    "player02": {
                        "user_id": player02.id,
                        "username": player02.username,
                        "email": player02.email,
                        "token": player02_token
                    }
                },
                "testing": {
                    "test_auth": f"curl -H 'Authorization: Bearer {player01_token}' {service_url}/auth/me",
                    "test_games": f"curl -H 'Authorization: Bearer {player01_token}' {service_url}/games/my-games",
                    "note": "Tokens use USERNAME in sub field for proper authentication"
                },
                "usage": {
                    "authorization_header": "Authorization: Bearer <token>",
                    "example_test": f"curl -H 'Authorization: Bearer {player01_token}' {service_url}/auth/me"
                }
            }
        finally:
            db.close()
    except Exception as e:
        # Return error details for debugging
        return {
            "error": "Debug tokens endpoint failed",
            "details": str(e),
            "type": type(e).__name__
        }

@app.get("/debug/test-auth/{username}")
async def debug_test_auth(username: str):
    """Simple debug endpoint to test user lookup by username"""
    from app.database import SessionLocal
    from app.models import User
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return {
                "found": True,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        else:
            return {"found": False, "username": username}
    finally:
        db.close()

# Include routers
app.include_router(users.router)
app.include_router(game_setup.router)  # Include game_setup before games to avoid route conflicts
app.include_router(games.router)
# app.include_router(moves.router)  # Commented out - conflicts with games.router move endpoint
app.include_router(rack.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/", tags=["root"])
def read_root():
    """
    Root endpoint that provides basic API information.
    
    Returns:
        dict: A welcome message and basic API information
    """
    return {
        "message": "Welcome to WordBattle API",
        "version": "1.0.0",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "health": "/health"
    }

@app.websocket("/ws/games/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    game_id: str, 
    token: str = Query(None, description="JWT access token for authentication")
):
    """
    WebSocket endpoint for real-time game updates and chat.
    
    This endpoint establishes a WebSocket connection for a specific game, enabling:
    * Real-time game state updates
    * Chat messages between players
    * Move notifications
    * Game events (start, end, etc.)
    
    The connection requires authentication via a JWT token and the user must be a participant in the game.
    """
    from app.websocket import manager
    from app.auth import get_user_from_token
    from app.database import SessionLocal
    from app.models import Game, ChatMessage
    from datetime import datetime, timezone
    
    if not token:
        await websocket.close(code=1008)
        return
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Validate token and get user
        user = get_user_from_token(token, db)
        if not user:
            await websocket.close(code=1008)
            return
        
        # Accept the connection before any database operations
        await websocket.accept()
        
        try:
            # Connect to the game
            await manager.connect(websocket, game_id, user)
            
            # Send initial game state
            game = db.query(Game).filter(Game.id == game_id).first()
            if game:
                await websocket.send_json({
                    "type": "connection_established",
                    "game_state": {
                        "game_id": game_id,
                        "state": json.loads(game.state),
                        "current_player_id": game.current_player_id
                    }
                })
            
            # Keep connection open and handle messages
            try:
                while True:
                    data = await websocket.receive_json()
                    logger.debug(f"Received WebSocket message on game {game_id} from {user.username}: {data}")
                    
                    if data.get("type") == "chat_message":
                        message_text = data.get("message", "").strip()
                        if message_text:  # Only process non-empty messages
                            # Store message in database
                            chat_message = ChatMessage(
                                game_id=game_id,
                                sender_id=user.id,
                                message=message_text,
                                timestamp=datetime.now(timezone.utc)
                            )
                            db.add(chat_message)
                            db.commit()
                            db.refresh(chat_message)
                            
                            # Broadcast to all connected players
                            await manager.broadcast_to_game(
                                game_id,
                                {
                                    "type": "chat_message",
                                    "message_id": chat_message.id,
                                    "sender_id": user.id,
                                    "sender_username": user.username,
                                    "message": message_text,
                                    "timestamp": chat_message.timestamp.isoformat()
                                }
                            )
            except WebSocketDisconnect:
                manager.disconnect(websocket, game_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.close(code=1008)
            manager.disconnect(websocket, game_id)
    except Exception as e:
        logger.error(f"WebSocket setup error: {e}")
        await websocket.close(code=1008)
    finally:
        db.close()
