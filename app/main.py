from fastapi import FastAPI
from app.routers import users, games, moves, gameplay
from app import auth

app = FastAPI(
    title="Scrabble Backend API",
    description="Rundenbasiertes Multiplayer-Wortspiel Backend mit FastAPI",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Scrabble Backend läuft"}

app.include_router(users.router)
app.include_router(games.router)
app.include_router(moves.router)
app.include_router(gameplay.router)
app.include_router(auth.router)
