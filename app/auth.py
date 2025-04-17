import jwt
import uuid
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.models import User, RefreshToken
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": str(uuid.uuid4())
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: int = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": str(uuid.uuid4())
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def authenticate_user(db: AsyncSession, username: str, password: str):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

async def save_refresh_token(db: AsyncSession, user_id: int, token: str, expires_at: datetime):
    refresh_token = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
    db.add(refresh_token)
    await db.commit()

async def revoke_refresh_token(db: AsyncSession, token: str):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == token))
    refresh = result.scalars().first()
    if refresh:
        refresh.revoked = True
        await db.commit()

async def is_refresh_token_valid(db: AsyncSession, token: str):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == token, RefreshToken.revoked == False))
    refresh = result.scalars().first()
    if not refresh:
        return False
    if refresh.expires_at < datetime.now(timezone.utc):
        return False
    return True
