import pytest
import requests
import time
import sqlalchemy
from sqlalchemy import text
import jwt
from auth_service.config import SECRET_KEY, ALGORITHM

# Автоочистка users перед всеми тестами (работает только если БД локальная и доступна напрямую)
@pytest.fixture(scope="session", autouse=True)
def clean_users_table():
    from user_service.config import DATABASE_URL
    engine = sqlalchemy.create_engine(DATABASE_URL.replace('+asyncpg', ''))
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM users"))
        conn.commit()

BASE_AUTH = "https://localhost:8000"
BASE_USER = "https://localhost:8001"
BASE_PRODUCT = "https://localhost:8002"

@pytest.fixture(scope="module")
def unique_user():
    suffix = str(int(time.time()))
    return {
        "username": f"user_{suffix}",
        "email": f"user_{suffix}@mail.com",
        "password": "password1"
    }

@pytest.fixture(scope="module")
def admin_user():
    suffix = str(int(time.time()) + 100)
    return {
        "username": f"admin_{suffix}",
        "email": f"admin_{suffix}@mail.com",
        "password": "adminpass1"
    }

# Сначала создаётся admin, потом обычный пользователь!
@pytest.fixture(scope="module")
def register_and_login_admin(admin_user):
    r = requests.post(f"{BASE_AUTH}/register", json={
        "username": admin_user["username"],
        "password": admin_user["password"],
        "email": admin_user["email"]
    })
    assert r.status_code == 200 or r.status_code == 400
    r = requests.post(f"{BASE_AUTH}/login", json={
        "username": admin_user["username"],
        "password": admin_user["password"]
    })
    assert r.status_code == 200
    tokens = r.json()
    return tokens, admin_user

@pytest.fixture(scope="module")
def register_and_login(unique_user, register_and_login_admin):
    print("\n[FIXTURE] === РЕГИСТРАЦИЯ USER ===")
    print(f"[FIXTURE] Данные для регистрации: {unique_user}")
    r = requests.post(f"{BASE_AUTH}/register", json=unique_user)
    print(f"[FIXTURE] Ответ регистрации user: {r.status_code} {r.text}")
    assert r.status_code == 200 or r.status_code == 400
    print("[FIXTURE] Логинимся как user...")
    r = requests.post(f"{BASE_AUTH}/login", json={"username": unique_user["username"], "password": unique_user["password"]})
    print(f"[FIXTURE] Ответ логина user: {r.status_code} {r.text}")
    assert r.status_code == 200
    tokens = r.json()
    print(f"[FIXTURE] access_token(user): {tokens['access_token']}")
    print(f"[FIXTURE] refresh_token(user): {tokens['refresh_token']}")
    return tokens

@pytest.fixture(scope="module")
def register_and_login_admin(admin_user):
    print("\n[FIXTURE] === РЕГИСТРАЦИЯ АДМИНА ===")
    print(f"[FIXTURE] Данные для регистрации: {admin_user}")
    r = requests.post(f"{BASE_AUTH}/register", json=admin_user)
    print(f"[FIXTURE] Ответ регистрации admin: {r.status_code} {r.text}")
    assert r.status_code == 200 or r.status_code == 400
    print("[FIXTURE] Логинимся как admin...")
    r = requests.post(f"{BASE_AUTH}/login", json={"username": admin_user["username"], "password": admin_user["password"]})
    print(f"[FIXTURE] Ответ логина admin: {r.status_code} {r.text}")
    assert r.status_code == 200
    tokens = r.json()
    print(f"[FIXTURE] access_token(admin): {tokens['access_token']}")
    print(f"[FIXTURE] refresh_token(admin): {tokens['refresh_token']}")
    return tokens, admin_user

# --- Тесты ---

def test_register_and_login(register_and_login):
    assert "access_token" in register_and_login
    assert "refresh_token" in register_and_login


def test_get_me(register_and_login):
    access_token = register_and_login["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{BASE_USER}/users/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "username" in data


def test_get_users_forbidden(register_and_login):
    print("\n[TEST] --- Тест: user не может получить список пользователей ---")
    access_token = register_and_login["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"[TEST] access_token(user): {access_token}")
    r = requests.get(f"{BASE_USER}/users", headers=headers)
    print(f"[TEST] Ответ: {r.status_code} {r.text}")
    assert r.status_code == 403

def test_refresh_token(register_and_login):
    print("\n[TEST] --- Тест: refresh_token ---")
    refresh_token = register_and_login["refresh_token"]
    print(f"[TEST] refresh_token(user): {refresh_token}")
    r = requests.post(f"{BASE_AUTH}/token/refresh", json={"refresh_token": refresh_token})
    print(f"[TEST] Ответ: {r.status_code} {r.text}")
    assert r.status_code == 200
    tokens = r.json()
    print(f"[TEST] Новый access_token: {tokens['access_token']}")
    print(f"[TEST] Новый refresh_token: {tokens['refresh_token']}")
    assert "access_token" in tokens
    assert "refresh_token" in tokens

def test_products_list(register_and_login):
    print("\n[TEST] --- Тест: список продуктов ---")
    access_token = register_and_login["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"[TEST] access_token(user): {access_token}")
    r = requests.get(f"{BASE_PRODUCT}/products", headers=headers)
    print(f"[TEST] Ответ: {r.status_code} {r.text}")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_privileges(register_and_login_admin):
    print("\n[TEST] --- Тест: права администратора ---")
    tokens, admin = register_and_login_admin
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"[TEST] access_token(admin): {access_token}")
    r = requests.get(f"{BASE_USER}/users", headers=headers)
    print(f"[TEST] Ответ: {r.status_code} {r.text}")
    assert r.status_code == 200
    users = r.json()
    print(f"[TEST] Количество пользователей: {len(users)}")
    assert isinstance(users, list)


def test_product_crud(register_and_login_admin):
    tokens, admin = register_and_login_admin
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    # Create product
    product = {"name": "Test Product", "description": "pytest", "price": 99.99}
    r = requests.post(f"{BASE_PRODUCT}/products", json=product, headers=headers)
    assert r.status_code == 200
    prod = r.json()
    product_id = prod["id"]
    # Get product
    r = requests.get(f"{BASE_PRODUCT}/products/{product_id}", headers=headers)
    assert r.status_code == 200
    # Update product
    upd = {"name": "Updated Product", "description": "upd", "price": 199.99}
    r = requests.put(f"{BASE_PRODUCT}/products/{product_id}", json=upd, headers=headers)
    assert r.status_code == 200
    # Delete product
    r = requests.delete(f"{BASE_PRODUCT}/products/{product_id}", headers=headers)
    assert r.status_code == 200


def test_delete_user_forbidden(register_and_login):
    print("\n[TEST] --- Тест: user не может удалить пользователя ---")
    access_token = register_and_login["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"[TEST] access_token(user): {access_token}")
    r = requests.delete(f"{BASE_USER}/users/1", headers=headers)
    print(f"[TEST] Ответ: {r.status_code} {r.text}")
    assert r.status_code in (403, 401, 404)


def test_delete_user_admin(register_and_login_admin):
    print("\n[TEST] --- Тест: админ может удалить себя ---")
    tokens, admin = register_and_login_admin
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"[TEST] access_token(admin): {access_token}")
    r_me = requests.get(f"{BASE_USER}/users/me", headers=headers)
    print(f"[TEST] Ответ /users/me: {r_me.status_code} {r_me.text}")
    if r_me.status_code == 200:
        admin_id = r_me.json()["id"]
        print(f"[TEST] id админа: {admin_id}")
        r = requests.delete(f"{BASE_USER}/users/{admin_id}", headers=headers)
        print(f"[TEST] Ответ удаления админа: {r.status_code} {r.text}")
        assert r.status_code == 200 or r.status_code == 404

def test_jwt_payload_structure(register_and_login):
    access_token = register_and_login["access_token"]
    payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    for field in ("sub", "role", "exp", "iat", "jti"):
        assert field in payload

def test_user_cannot_get_users(register_and_login):
    access_token = register_and_login["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(f"{BASE_USER}/users", headers=headers)
    assert resp.status_code == 403

def test_admin_can_get_users(register_and_login_admin):
    tokens, admin = register_and_login_admin
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(f"{BASE_USER}/users", headers=headers)
    assert resp.status_code == 200
