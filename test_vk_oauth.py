import pytest
import requests
from fastapi.testclient import TestClient
from auth_service.main import app


BASE_AUTH = "http://localhost:8000"

# Тестируем редирект на VK OAuth
def test_vk_auth_redirect():
    print("\n[VK TEST] --- Проверка редиректа на VK OAuth ---")
    resp = requests.get(f"{BASE_AUTH}/auth/vk", allow_redirects=False)
    print(f"[VK TEST] Запрос: GET /auth/vk")
    print(f"[VK TEST] Статус: {resp.status_code}")
    print(f"[VK TEST] Location: {resp.headers.get('Location')}")
    assert resp.status_code in (302, 307)
    assert resp.headers.get('Location', '').startswith('https://oauth.vk.com/authorize')
    print("[VK TEST] --- OK ---")

# Тестируем callback с некорректным code
def test_vk_callback_invalid_code():
    print("\n[VK TEST] --- Проверка ошибки при неверном VK code ---")
    resp = requests.get(f"{BASE_AUTH}/auth/vk/callback?code=INVALID_CODE")
    print(f"[VK TEST] Запрос: GET /auth/vk/callback?code=INVALID_CODE")
    print(f"[VK TEST] Статус: {resp.status_code}")
    print(f"[VK TEST] Ответ: {resp.text}")
    assert resp.status_code == 400 or resp.status_code == 500
    print("[VK TEST] --- OK ---")

@pytest.fixture
def client():
    return TestClient(app)

# Мок-тест успешного VK OAuth (без реального VK)
def test_vk_callback_success(client, requests_mock):
    print("\n[VK TEST] --- Успешный сценарий VK OAuth (моки) ---")
    print("[VK TEST] Мокаем запрос https://oauth.vk.com/access_token → access_token, user_id, email")
    requests_mock.get(
        "https://oauth.vk.com/access_token",
        json={
            "access_token": "vk_access_token_123",
            "user_id": "vk_user_999",
            "email": "vkuser@example.com"
        }
    )
    print("[VK TEST] Мокаем запрос https://api.vk.com/method/users.get → имя и фамилия")
    requests_mock.get(
        "https://api.vk.com/method/users.get",
        json={"response": [{"first_name": "Ivan", "last_name": "Ivanov"}]}
    )
    print("[VK TEST] Запрос: GET /auth/vk/callback?code=TEST_CODE (через TestClient)")
    resp = client.get("/auth/vk/callback?code=TEST_CODE")
    print(f"[VK TEST] Статус: {resp.status_code}")
    print(f"[VK TEST] Тело: {resp.text}")
    assert resp.status_code == 200
    data = resp.json()
    print(f"[VK TEST] access_token: {data.get('access_token')}")
    print(f"[VK TEST] refresh_token: {data.get('refresh_token')}")
    print(f"[VK TEST] vk_name: {data.get('vk_name')}")
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["vk_name"] == "Ivan Ivanov"
    print("[VK TEST] --- OK ---")


# def test_vk_callback_real():
#     code = :"0a65eeeb0af2c2b0a9"
#     resp = requests.get(f"{BASE_AUTH}/auth/vk/callback?code={code}")
#     print("[VK REAL] Статус:", resp.status_code)
#     print("[VK REAL] Ответ:", resp.text)
#     assert resp.status_code == 200
#     data = resp.json()
#     print("[VK REAL] access_token:", data.get("access_token"))
#     print("[VK REAL] refresh_token:", data.get("refresh_token"))
#     print("[VK REAL] vk_name:", data.get("vk_name"))
#     assert "access_token" in data
#     assert "refresh_token" in data
#     assert "vk_name" in data
#     print("[VK REAL] --- OK ---")
