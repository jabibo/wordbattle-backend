from fastapi import FastAPI
from app.routers import users, games, moves

app = FastAPI()

app.include_router(users.router)
app.include_router(games.router)
app.include_router(moves.router)
