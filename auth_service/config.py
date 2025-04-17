import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "ufhybnehf23")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "lab3")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

VK_CLIENT_ID = os.getenv("VK_CLIENT_ID", "51621714")
VK_CLIENT_SECRET = os.getenv("VK_CLIENT_SECRET", "unqRbLFtmgfSsRKaw0Iz")
VK_REDIRECT_URI = os.getenv("VK_REDIRECT_URI", "https://localhost/auth/vk/callback")
