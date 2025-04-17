from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserOut(UserBase):
    id: int
    role: str
    vk_id: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
