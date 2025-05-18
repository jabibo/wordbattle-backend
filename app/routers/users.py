from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db

router = APIRouter(prefix="/users", tags=["users"])

class RegisterUser(BaseModel):
    username: str
    password: str

@router.post("/register")
async def register(user: RegisterUser, db: AsyncSession = Depends(get_db)):
    # Dummy-Erstellung, echte Logik sollte Passwörter hashen
    existing = await db.execute(
        "SELECT * FROM users WHERE username = :u", {"u": user.username}
    )
    if existing.first():
        raise HTTPException(status_code=400, detail="User exists")
    new_user = User(username=user.username, hashed_password=user.password)
    db.add(new_user)
    await db.commit()
    return {"message": "User registered"}
