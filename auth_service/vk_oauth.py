import requests
from fastapi import HTTPException
from config import VK_CLIENT_ID, VK_CLIENT_SECRET, VK_REDIRECT_URI

def get_vk_auth_url():
    return (
        f"https://oauth.vk.com/authorize?"
        f"client_id={VK_CLIENT_ID}&"
        f"redirect_uri={VK_REDIRECT_URI}&"
        f"display=page&scope=email&response_type=code&v=5.131"
    )

def exchange_code_for_token(code: str):
    token_url = (
        f"https://oauth.vk.com/access_token?"
        f"client_id={VK_CLIENT_ID}&"
        f"client_secret={VK_CLIENT_SECRET}&"
        f"redirect_uri={VK_REDIRECT_URI}&"
        f"code={code}"
    )
    response = requests.get(token_url)
    print("VK TOKEN EXCHANGE URL:", token_url, flush=True)
    print("VK TOKEN EXCHANGE RESPONSE:", response.status_code, response.text, flush=True)
    if not response.ok:
        raise HTTPException(status_code=400, detail="VK token exchange failed")
    return response.json()

def get_vk_user_info(access_token: str, user_id: str):
    user_info_url = (
        f"https://api.vk.com/method/users.get?"
        f"user_ids={user_id}&fields=first_name,last_name,email&"
        f"access_token={access_token}&v=5.131"
    )
    response = requests.get(user_info_url)
    if not response.ok:
        raise HTTPException(status_code=400, detail="VK user info fetch failed")
    return response.json()
