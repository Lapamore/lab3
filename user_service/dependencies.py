from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from config import SECRET_KEY, ALGORITHM

class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        print("[JWT DEBUG] Raw token:", credentials.credentials)
        if credentials:
            try:
                payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
                print("[JWT DEBUG] Decoded payload:", payload)
                request.state.user = payload
                return payload
            except jwt.ExpiredSignatureError as e:
                print("[JWT DEBUG] ExpiredSignatureError:", e)
                raise HTTPException(status_code=401, detail="Token expired")
            except jwt.InvalidTokenError as e:
                print("[JWT DEBUG] InvalidTokenError:", e)
                raise HTTPException(status_code=401, detail="Invalid token")
        else:
            print("[JWT DEBUG] Authorization header missing!")
            raise HTTPException(status_code=403, detail="Authorization header missing")

def role_required(required_role: str):
    def role_checker(payload=Depends(JWTBearer())):
        if payload["role"] != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return payload
    return role_checker

def roles_required(roles: list):
    def role_checker(payload=Depends(JWTBearer())):
        if payload["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return payload
    return role_checker
