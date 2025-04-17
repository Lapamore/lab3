# Лабораторная работа №3: JWT и OAuth (FastAPI + PostgreSQL, микросервисы)

## Архитектура

В проекте реализовано **3 микросервиса**:
- **auth_service** — аутентификация, авторизация, VK OAuth, refresh-токены
- **user_service** — работа с пользователями (CRUD, только для admin), получение своих данных
- **product_service** — работа с товарами (CRUD, только для admin, просмотр — для всех)

Все сервисы используют одну БД PostgreSQL (`lab3`).

---

## Запуск каждого сервиса

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Создайте базу данных PostgreSQL `lab3`** (если не создана).
   - user: `postgres`, password: `ufhybnehf23`

3. **Создайте таблицы** (см. SQL ниже)

4. **Запустите сервисы в отдельных терминалах:**
   ```bash
   uvicorn auth_service.main:app --reload --port 8000
   uvicorn user_service.main:app --reload --port 8001
   uvicorn product_service.main:app --reload --port 8002
   ```

5. **Swagger UI:**
   - Auth: [http://localhost:8000/docs](http://localhost:8000/docs)
   - User: [http://localhost:8001/docs](http://localhost:8001/docs)
   - Product: [http://localhost:8002/docs](http://localhost:8002/docs)

---

## Основные возможности
- JWT access/refresh токены (выдаёт только auth_service)
- Ролевая модель (user, admin)
- Ограничение доступа к эндпоинтам по ролям (user — только свои данные и просмотр товаров, admin — всё)
- VK OAuth (auth_service)
- Все защищённые эндпоинты требуют JWT (Authorization: Bearer ...)

---

## Примеры запросов

### Auth-сервис (порт 8000)
- **POST /register** — регистрация
- **POST /login** — логин (выдаёт access/refresh токены)
- **POST /token/refresh** — обновление токенов
- **GET /auth/vk** — начало VK OAuth
- **GET /auth/vk/callback** — callback VK OAuth

### User-сервис (порт 8001)
- **GET /users/me** — свои данные (user, admin)
- **GET /users** — список всех (только admin)
- **DELETE /users/{user_id}** — удалить пользователя (только admin)

### Product-сервис (порт 8002)
- **GET /products** — список товаров (все)
- **POST /products** — создать товар (только admin)
- **GET /products/{id}** — получить товар (все)
- **PUT /products/{id}** — изменить товар (только admin)
- **DELETE /products/{id}** — удалить товар (только admin)

---

## VK OAuth
- Используются твои реальные данные:
  - `client_id`: 51621714
  - `client_secret`: unqRbLFtmgfSsRKaw0Iz
- Redirect URI должен совпадать с настройками VK: `http://localhost:8000/auth/vk/callback`
- Для теста авторизации — перейдите по [http://localhost:8000/auth/vk](http://localhost:8000/auth/vk)

---

## Миграции (SQL для всех сервисов)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    vk_id VARCHAR(50) UNIQUE,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(512) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1024),
    price FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

**Вопросы по коду, тестированию и запуску — пиши!**
