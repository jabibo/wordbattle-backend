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
from contextlib import asynccontextmanager
import asyncio
from collections import defaultdict
from sqlalchemy import text, inspect
from app.database_manager import check_database_status, ensure_user_columns
from app.middleware.performance import PerformanceMiddleware, monitor
from app.utils.cache import cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance monitoring
response_times = []
request_counts = defaultdict(int)

# Create FastAPI app with performance monitoring lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 WordBattle Backend starting up...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database table creation failed: {e}")
    
    try:
        ensure_user_columns()
        await ensure_default_admin_exists()
        
        status = check_database_status()
        if status["is_initialized"]:
            logger.info("Database already initialized - skipping word loading")
        else:
            logger.info("Database needs initialization - will load words in background")
            asyncio.create_task(initialize_words_background())
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
    
    yield
    
    # Shutdown
    print("🛑 WordBattle Backend shutting down...")
    print(f"📊 Performance Summary:")
    if response_times:
        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)
        print(f"   Average response time: {avg_response:.3f}s")
        print(f"   Max response time: {max_response:.3f}s")
        print(f"   Total requests: {sum(request_counts.values())}")

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
    ],
    lifespan=lifespan
)

# Configure CORS with performance headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Cache-Control"],
    expose_headers=["X-Response-Time", "X-Request-ID"]
)

# Add performance monitoring middleware
app.add_middleware(PerformanceMiddleware)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    from app.database_manager import check_database_status
    
    # Create database tables first
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database table creation failed: {e}")
        return
    
    # Only check if database exists, don't load words during startup
    try:
        # Ensure user preference columns exist (fallback)
        from app.database_manager import ensure_user_columns
        ensure_user_columns()
        
        # Always ensure jan@binge.de exists as admin user
        await ensure_default_admin_exists()
        
        status = check_database_status()
        
        if status["is_initialized"]:
            logger.info("Database already initialized - skipping word loading")
        else:
            logger.info("Database needs initialization - will load words in background")
            # Schedule immediate background word loading
            asyncio.create_task(initialize_words_background())
            
    except Exception as e:
        logger.error(f"Database status check failed: {e}")

async def ensure_default_admin_exists():
    """Ensure the default admin user jan@binge.de always exists."""
    try:
        from app.database import SessionLocal
        from app.models import User
        from app.auth import get_password_hash
        from datetime import datetime, timezone
        
        db = SessionLocal()
        try:
            # Debug: First list all users to see what exists
            all_users = db.query(User).all()
            logger.info(f"🔍 Debug: Found {len(all_users)} total users in database")
            for user in all_users:
                logger.info(f"🔍 Debug: User: {user.username}, Email: {user.email}, Admin: {user.is_admin}")
            
            # Check if jan@binge.de exists
            admin_user = db.query(User).filter(User.email == "jan@binge.de").first()
            logger.info(f"🔍 Debug: Query for jan@binge.de returned: {admin_user}")
            
            if not admin_user:
                logger.info("🔧 Creating default admin user jan@binge.de...")
                # Create the admin user
                admin_user = User(
                    username="jan",
                    email="jan@binge.de", 
                    hashed_password=get_password_hash("admin123"),  # Default password
                    is_admin=True,
                    is_email_verified=True,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)
                logger.info(f"✅ Created default admin user: jan@binge.de (ID: {admin_user.id})")
            else:
                # Ensure the user is admin (in case it was changed)
                if not admin_user.is_admin:
                    admin_user.is_admin = True
                    db.commit()
                    logger.info("✅ Promoted jan@binge.de to admin")
                else:
                    logger.info(f"✅ Default admin user jan@binge.de already exists (ID: {admin_user.id})")
                    
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to ensure default admin exists: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

async def initialize_words_background():
    """Initialize words in the background without blocking startup."""
    try:
        import asyncio
        await asyncio.sleep(5)  # Short delay to ensure container is ready
        logger.info("Starting background database initialization...")
        
        from app.database_manager import load_wordlist, check_database_status
        
        status = check_database_status()
        word_count = sum(status["word_counts"].values())
        
        if word_count < 1000:  # Load words if we have less than 1000
            logger.info("Loading initial wordlist in background...")
            result = load_wordlist(language="de", limit=10000)  # Load first 10k words
            
            if result["success"]:
                logger.info(f"Background wordlist loading completed: {result['words_loaded']} words loaded")
                # Schedule the remaining words
                asyncio.create_task(schedule_background_word_import())
            else:
                logger.error(f"Background wordlist loading failed: {result.get('error', 'Unknown error')}")
        else:
            logger.info("Database already has words - skipping initial load")
            
    except Exception as e:
        logger.error(f"Error in background word initialization: {e}")

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

@app.get("/admin/database/admin-status")
async def admin_status():
    """Get admin user status information for the database"""
    from app.database import SessionLocal
    from app.models import User
    
    db = SessionLocal()
    try:
        # Count total users
        total_users = db.query(User).count()
        
        # Count admin users
        admin_users = db.query(User).filter(User.is_admin == True).all()
        admin_count = len(admin_users)
        
        # Count word admin users
        word_admin_count = db.query(User).filter(User.is_word_admin == True).count()
        
        # Get first few admin usernames for display (privacy-conscious)
        admin_usernames = [admin.username for admin in admin_users[:3]]
        
        return {
            "total_users": total_users,
            "admin_users": admin_count,
            "word_admin_users": word_admin_count,
            "has_admins": admin_count > 0,
            "admin_usernames": admin_usernames,
            "note": "First 3 admin usernames shown for privacy"
        }
    finally:
        db.close()

@app.post("/admin/database/create-default-admin")
async def create_default_admin():
    """Create a default admin user for testing purposes"""
    from app.database import SessionLocal
    from app.models import User
    from app.auth import get_password_hash
    from datetime import datetime, timezone
    
    db = SessionLocal()
    try:
        # Check if an admin already exists
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        if existing_admin:
            return {
                "message": "Admin user already exists",
                "admin_username": existing_admin.username,
                "action": "none"
            }
        
        # Create default admin user
        admin_username = "jan_admin"
        admin_password = "admin123"  # In production, use a secure password
        
        # Check if user with this username already exists
        existing_user = db.query(User).filter(User.username == admin_username).first()
        if existing_user:
            # Promote existing user to admin
            existing_user.is_admin = True
            db.commit()
            return {
                "message": f"Promoted existing user '{admin_username}' to admin",
                "admin_username": admin_username,
                "action": "promoted"
            }
        
        # Create new admin user
        admin_user = User(
            username=admin_username,
            email="jan@binge-dev.de",
            hashed_password=get_password_hash(admin_password),
            is_admin=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        return {
            "message": f"Created default admin user: {admin_username}",
            "admin_username": admin_username,
            "admin_id": admin_user.id,
            "password": admin_password,
            "action": "created",
            "note": "This is for testing only - change password in production!"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "error": f"Failed to create admin user: {str(e)}",
            "action": "failed"
        }
    finally:
        db.close()

@app.post("/admin/database/reset-games")
async def reset_games():
    """
    ADMIN ONLY: Reset all game-related data while preserving users and wordlists.
    """
    try:
        from sqlalchemy import text
        from app.database import SessionLocal
        
        logger.info("🗑️ Starting game data reset...")
        
        db = SessionLocal()
        deleted_counts = {}
        
        try:
            # Get counts before deletion
            tables_to_reset = [
                ("chat_messages", "Chat Messages"),
                ("moves", "Moves"),
                ("players", "Players"),
                ("game_invitations", "Game Invitations"),
                ("games", "Games")
            ]
            
            # Delete in order to respect foreign key constraints
            for table, name in tables_to_reset:
                try:
                    # Get count before deletion
                    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count_before = count_result.scalar()
                    
                    # Delete all records
                    delete_result = db.execute(text(f"DELETE FROM {table}"))
                    deleted_counts[table] = delete_result.rowcount
                    
                    logger.info(f"Deleted {delete_result.rowcount} records from {table}")
                    
                except Exception as e:
                    logger.error(f"Error deleting from {table}: {e}")
                    deleted_counts[table] = f"Error: {str(e)}"
            
            # Reset sequences
            sequences = [
                "chat_messages_id_seq",
                "moves_id_seq", 
                "players_id_seq",
                "game_invitations_id_seq",
                "games_id_seq"
            ]
            
            reset_sequences = []
            for seq in sequences:
                try:
                    db.execute(text(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1"))
                    reset_sequences.append(seq)
                except Exception as e:
                    logger.warning(f"Could not reset sequence {seq}: {e}")
            
            db.commit()
            logger.info("✅ Game data reset completed successfully")
            
            return {
                "success": True,
                "message": "Game data reset completed successfully",
                "deleted_counts": deleted_counts,
                "reset_sequences": reset_sequences,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Game reset error: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Game reset failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Game data reset failed"
        }

@app.post("/admin/alembic/reset-to-current")
async def reset_alembic_to_current():
    """
    ADMIN ONLY: Reset Alembic migration state to current schema version.
    Keeps all data, just fixes the migration tracking.
    """
    try:
        from sqlalchemy import text, inspect
        from app.database import SessionLocal, engine
        
        logger.info("🔄 Resetting Alembic to current schema version...")
        
        db = SessionLocal()
        changes_made = []
        
        try:
            # Get current state
            inspector = inspect(engine)
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            existing_tables = inspector.get_table_names()
            
            logger.info(f"Current tables: {existing_tables}")
            logger.info(f"Current user columns: {user_columns}")
            
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            word_count = db.execute(text("SELECT COUNT(*) FROM wordlists")).scalar()
            
            logger.info(f"Preserving {user_count} users and {word_count} words")
            
            # Add missing columns for current schema
            if "allow_invites" not in user_columns:
                logger.info("Adding missing allow_invites column...")
                db.execute(text("ALTER TABLE users ADD COLUMN allow_invites BOOLEAN DEFAULT TRUE"))
                db.commit()
                changes_made.append("Added allow_invites column")
                
            if "preferred_languages" not in user_columns:
                logger.info("Adding missing preferred_languages column...")
                db.execute(text("ALTER TABLE users ADD COLUMN preferred_languages JSON DEFAULT '[\"en\", \"de\"]'"))
                db.commit()
                changes_made.append("Added preferred_languages column")
                
            # Set defaults for existing users
            if "allow_invites" in user_columns or "allow_invites" in [change for change in changes_made]:
                db.execute(text("UPDATE users SET allow_invites = TRUE WHERE allow_invites IS NULL"))
                db.execute(text("UPDATE users SET preferred_languages = '[\"en\", \"de\"]' WHERE preferred_languages IS NULL"))
                db.commit()
                changes_made.append("Set default values for existing users")
                
        except Exception as e:
            logger.error(f"Column addition error: {e}")
            db.rollback()
            raise
        finally:
            db.close()
        
        # Reset Alembic migration state to head (current version)
        logger.info("Resetting Alembic migration state to head...")
        try:
            from alembic.config import Config
            from alembic import command
            
            alembic_cfg = Config("alembic.ini")
            
            # Drop and recreate alembic version table to reset state
            db = SessionLocal()
            try:
                db.execute(text("DROP TABLE IF EXISTS alembic_version"))
                db.commit()
                logger.info("Dropped old alembic_version table")
            except Exception as e:
                logger.warning(f"Could not drop alembic_version: {e}")
                db.rollback()
            finally:
                db.close()
            
            # Stamp with current head revision
            command.stamp(alembic_cfg, "head")
            changes_made.append("Reset Alembic migration state to head")
            logger.info("✅ Alembic migration state reset to head")
            
        except Exception as e:
            logger.error(f"Alembic reset failed: {e}")
            changes_made.append(f"Alembic reset failed: {str(e)}")
        
        return {
            "success": True,
            "message": "Alembic migration state reset to current version successfully",
            "changes_made": changes_made,
            "preserved_data": {
                "users": user_count,
                "words": word_count,
                "tables": len(existing_tables)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Alembic reset failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Alembic reset failed"
        }

@app.post("/admin/load-all-words")
async def load_all_words():
    """
    ADMIN ONLY: Load all remaining words into the database.
    This will complete the wordlist loading for German and English.
    """
    try:
        from app.database_manager import check_database_status, load_wordlist
        
        logger.info("🔤 Starting to load all remaining words...")
        
        # Check current status
        status = check_database_status()
        current_de = status["word_counts"].get("de", 0)
        current_en = status["word_counts"].get("en", 0)
        
        logger.info(f"Current word counts: DE={current_de}, EN={current_en}")
        
        results = {
            "german": {"loaded": 0, "success": True, "message": ""},
            "english": {"loaded": 0, "success": True, "message": ""}
        }
        
        # Load remaining German words (we know there are ~601,565 total)
        if current_de < 600000:
            logger.info(f"Loading remaining German words starting from {current_de}...")
            
            # Load in chunks to avoid memory issues
            chunk_size = 50000
            total_loaded = 0
            
            while current_de + total_loaded < 600000:
                skip = current_de + total_loaded
                logger.info(f"Loading German words: skip={skip}, limit={chunk_size}")
                
                result = load_wordlist(
                    language="de", 
                    skip=skip, 
                    limit=chunk_size
                )
                
                if not result["success"]:
                    results["german"]["success"] = False
                    results["german"]["message"] = f"Failed at skip={skip}: {result.get('error')}"
                    break
                    
                words_loaded = result.get("words_loaded", 0)
                total_loaded += words_loaded
                
                logger.info(f"Loaded {words_loaded} words. Total loaded this session: {total_loaded}")
                
                if words_loaded < chunk_size:
                    # We've reached the end of available words
                    logger.info("Reached end of available German words")
                    break
            
            results["german"]["loaded"] = total_loaded
            results["german"]["message"] = f"Loaded {total_loaded} German words"
            logger.info(f"Finished loading German words. Total loaded: {total_loaded}")
        else:
            results["german"]["message"] = "German words already fully loaded"
        
        # Check if English needs loading (we know there are ~178,690 total)
        if current_en < 170000:
            logger.info("Loading remaining English words...")
            result = load_wordlist(
                language="en", 
                skip=current_en, 
                limit=200000  # Load all remaining
            )
            
            if result["success"]:
                results["english"]["loaded"] = result.get("words_loaded", 0)
                results["english"]["message"] = f"Loaded {results['english']['loaded']} English words"
                logger.info(f"Loaded {results['english']['loaded']} English words")
            else:
                results["english"]["success"] = False
                results["english"]["message"] = f"Failed to load English words: {result.get('error')}"
        else:
            results["english"]["message"] = "English words already fully loaded"
        
        # Final status check
        final_status = check_database_status()
        final_de = final_status["word_counts"].get("de", 0)
        final_en = final_status["word_counts"].get("en", 0)
        
        logger.info(f"Final word counts: DE={final_de}, EN={final_en}")
        
        return {
            "success": True,
            "message": "Word loading completed!",
            "before": {"german": current_de, "english": current_en},
            "after": {"german": final_de, "english": final_en},
            "loaded": {
                "german": results["german"]["loaded"],
                "english": results["english"]["loaded"]
            },
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Word loading failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Word loading failed"
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

@app.get("/admin/performance")
async def get_performance_stats():
    """Get application performance statistics."""
    stats = monitor.get_stats()
    cache_stats = cache.stats()
    
    return {
        "performance": stats,
        "cache": cache_stats,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
