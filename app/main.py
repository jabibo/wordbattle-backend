# app/main.py
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, games, moves, rack, profile, admin, auth
from app.auth import router as auth_router
from app.config import CORS_ORIGINS, RATE_LIMIT
import time
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WordBattle API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    from app.initialize import initialize_database
    if initialize_database():
        logger.info("Database initialized successfully")
    else:
        logger.error("Database initialization failed")

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

# Include routers
app.include_router(users.router)
app.include_router(games.router)
app.include_router(moves.router)
app.include_router(rack.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to WordBattle API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


