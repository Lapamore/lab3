from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import RedirectResponse
from database import get_db
from models import User
from schemas import UserCreate, UserOut, Token, TokenRefresh
from auth import (
    authenticate_user, get_password_hash, create_access_token, create_refresh_token,
    save_refresh_token, is_refresh_token_valid, revoke_refresh_token, decode_token
)
from dependencies import get_current_user, role_required
from vk_oauth import get_vk_auth_url, exchange_code_for_token, get_vk_user_info
from datetime import datetime, timedelta, timezone

app = FastAPI(title="Auth Service")

@app.get("/")
def root():
    return {"service": "auth"}

@app.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем, есть ли уже admin
    result = await db.execute(select(User).where(User.role == "admin"))
    admin_exists = result.scalars().first() is not None
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pw = get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed_pw, role="user" if admin_exists else "admin", email=user.email)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
async def login(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_payload = {"sub": db_user.id, "role": db_user.role}
    access_token = create_access_token(access_payload)
    refresh_token = create_refresh_token(access_payload, expires_delta=60*60*24*7)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await save_refresh_token(db, db_user.id, refresh_token, expires_at)
    return Token(access_token=access_token, refresh_token=refresh_token)

@app.post("/token/refresh", response_model=Token)
async def refresh_token(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    valid = await is_refresh_token_valid(db, data.refresh_token)
    if not valid:
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")
    access_payload = {"sub": payload["sub"], "role": payload["role"]}
    access_token = create_access_token(access_payload)
    refresh_token = create_refresh_token(access_payload, expires_delta=60*60*24*7)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await save_refresh_token(db, int(payload["sub"]), refresh_token, expires_at)
    await revoke_refresh_token(db, data.refresh_token)
    return Token(access_token=access_token, refresh_token=refresh_token)

@app.get("/auth/vk")
def auth_vk():
    return RedirectResponse(get_vk_auth_url())

@app.get("/auth/vk/callback")
async def vk_callback(request: Request, db: AsyncSession = Depends(get_db)):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Code not provided")
    token_data = exchange_code_for_token(code)
    vk_user_id = token_data["user_id"]
    email = token_data.get("email")
    access_token_vk = token_data["access_token"]
    user_info = get_vk_user_info(access_token_vk, vk_user_id)
    first_name = user_info["response"][0]["first_name"]
    last_name = user_info["response"][0]["last_name"]
    # Поиск или создание пользователя
    result = await db.execute(select(User).where(User.vk_id == str(vk_user_id)))
    user = result.scalars().first()
    if not user:
        user = User(username=None, password_hash=None, role="user", vk_id=str(vk_user_id), email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    access_payload = {"sub": user.id, "role": user.role}
    access_token = create_access_token(access_payload)
    refresh_token = create_refresh_token(access_payload, expires_delta=60*60*24*7)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await save_refresh_token(db, int(user.id), refresh_token, expires_at)
    return {"access_token": access_token, "refresh_token": refresh_token, "vk_name": f"{first_name} {last_name}"}
