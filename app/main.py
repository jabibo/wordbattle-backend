from fastapi import FastAPI, Request, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, games, moves, rack, profile, admin, auth, chat, game_setup
from app.config import CORS_ORIGINS, RATE_LIMIT, BACKEND_URL, FRONTEND_URL
import time
import os
import logging
import json
from datetime import datetime, timezone
from app.database import engine, Base

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
        {
            "name": "config",
            "description": "Configuration operations",
        },
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for maximum compatibility
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language", 
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Cache-Control",
        "Pragma",
    ],
    expose_headers=[
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers",
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

@app.post("/debug-tokens")
async def create_debug_tokens():
    """
    DEBUG ENDPOINT: Create tokens for test users player01 and player02.
    This endpoint creates the users if they don't exist and returns their tokens.
    
    ⚠️ WARNING: This is for development/testing only!
    """
    try:
        from app.database import SessionLocal
        from app.models import User
        from app.auth import create_access_token
        from passlib.context import CryptContext
        from datetime import timedelta
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        db = SessionLocal()
        
        try:
            test_users = []
            
            for username in ["player01", "player02"]:
                # Check if user exists
                user = db.query(User).filter(User.username == username).first()
                
                if not user:
                    # Create the user
                    hashed_password = pwd_context.hash("testpassword123")
                    user = User(
                        username=username,
                        email=f"{username}@test.com",
                        hashed_password=hashed_password,
                        is_email_verified=True
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                
                # Create token for the user
                access_token = create_access_token(
                    data={"sub": str(user.id)},
                    expires_delta=timedelta(days=30)  # Long-lived token for testing
                )
                
                test_users.append({
                    "user_id": user.id,
                    "username": username,
                    "email": user.email,
                    "access_token": access_token,
                    "token_type": "bearer"
                })
            
            return {
                "message": "Test tokens created successfully",
                "users": test_users,
                "usage": {
                    "description": "Use these tokens in the Authorization header",
                    "format": "Bearer <access_token>",
                    "example": f"Authorization: Bearer {test_users[0]['access_token'][:50]}..."
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating test tokens: {str(e)}")

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

@app.get("/config", tags=["config"])
def get_frontend_config():
    """
    Get frontend configuration including backend URL and other settings.
    
    This endpoint provides configuration information that the frontend needs,
    such as the correct backend URL, environment info, and feature flags.
    
    Returns:
        dict: Configuration object with frontend-relevant settings
    """
    # Determine the actual backend URL from the request if possible
    # For deployed environments, use the configured BACKEND_URL
    backend_url = BACKEND_URL
    
    # If we're in production and have a specific URL, use it
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        # Use the deployed backend URL
        backend_url = "https://mnirejmq3g.eu-central-1.awsapprunner.com"
    
    return {
        "backend_url": backend_url,
        "frontend_url": FRONTEND_URL,
        "environment": environment,
        "version": "1.0.0",
        "features": {
            "email_invitations": True,
            "game_chat": True,
            "real_time_updates": True,
            "multi_language": True,
            "push_notifications": os.getenv("ENABLE_PUSH_NOTIFICATIONS", "false").lower() == "true"
        },
        "supported_languages": ["en", "de"],
        "api_docs": f"{backend_url}/docs" if backend_url else "/docs",
        "websocket_url": f"{backend_url.replace('http', 'ws')}/ws" if backend_url else None
    }

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
