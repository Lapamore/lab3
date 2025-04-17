from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import User
from schemas import UserOut
from dependencies import JWTBearer, role_required
from sqlalchemy import select as sync_select
from fastapi import status
from models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from schemas import UserOut
from dependencies import JWTBearer, role_required
from fastapi import FastAPI, Depends, HTTPException, Body
from pydantic import BaseModel, EmailStr

app = FastAPI(title="User Service")

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

@app.post("/register", status_code=status.HTTP_200_OK)
async def register_user(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Проверяем, есть ли уже admin
    result = await db.execute(select(User).where(User.role == "admin"))
    admin_exists = result.scalars().first() is not None
    # Проверяем, есть ли пользователь с таким username/email
    result = await db.execute(select(User).where((User.username == data.username) | (User.email == data.email)))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User already exists")
    # Создаём пользователя
    user = User(
        username=data.username,
        email=data.email,
        role="user" if admin_exists else "admin"
    )
    # Пароль не сохраняется (заглушка, т.к. обычно хешируется и хранится отдельно)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}

@app.get("/")
def root():
    return {"service": "user"}

@app.get("/users/me", response_model=UserOut)
async def get_me(payload=Depends(JWTBearer()), db: AsyncSession = Depends(get_db)):
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users", response_model=list[UserOut], dependencies=[Depends(role_required("admin"))])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

@app.delete("/users/{user_id}", dependencies=[Depends(role_required("admin"))])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"detail": "User deleted"}

@app.patch("/users/{user_id}/role", dependencies=[Depends(role_required("admin"))])
async def change_user_role(user_id: int, new_role: str = Body(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = new_role
    await db.commit()
    return {"detail": f"Role updated to {new_role}"}
