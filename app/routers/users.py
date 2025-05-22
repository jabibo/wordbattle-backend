from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models import User
from app.auth import get_password_hash
from app.dependencies import get_db
from sqlalchemy.future import select

router = APIRouter(prefix="/users", tags=["users"])

class RegisterUser(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):
    result = db.execute(select(User).where(User.username == user.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")

    new_user = User(username=user.username, hashed_password=get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Benutzer erfolgreich registriert", "id": new_user.id}
