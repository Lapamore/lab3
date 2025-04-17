from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth import decode_token

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            payload = decode_token(credentials.credentials)
            request.state.user = payload
            return payload
        else:
            raise HTTPException(status_code=403, detail="Authorization header missing")

def get_current_user(payload=Depends(JWTBearer())):
    return payload

def role_required(required_role: str):
    def role_checker(payload=Depends(JWTBearer())):
        if payload["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return payload
    return role_checker

def roles_required(roles: list):
    def role_checker(payload=Depends(JWTBearer())):
        if payload["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return payload
    return role_checker
