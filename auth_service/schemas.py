from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    username: str
    password: str

from pydantic import ConfigDict

class UserOut(UserBase):
    id: int
    role: str
    vk_id: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenPayload(BaseModel):
    sub: int
    role: str
    exp: int
    iat: int
    jti: str

class VKAuthCode(BaseModel):
    code: str
