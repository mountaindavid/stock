# 🚀 Postman Collection для Stock Portfolio API

## 📋 Настройка Postman

### 1. Базовые настройки
- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **Authorization**: Bearer Token (для защищенных endpoints)

### 2. Переменные окружения
Создайте Environment в Postman со следующими переменными:
```
base_url: http://localhost:8000/api
access_token: (будет заполнен после логина)
refresh_token: (будет заполнен после логина)
portfolio_id: 1
transaction_id: 1
```

---

## 🔐 Аутентификация

### 1. Регистрация пользователя
```http
POST {{base_url}}/users/register/
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "date_of_birth": "1990-01-01",
    "password": "testpass123",
    "password_confirmation": "testpass123"
}
```

**Ожидаемый ответ:**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 2,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
}
```

### 2. Логин
```http
POST {{base_url}}/users/login/
Content-Type: application/json

{
    "username": "testuser",
    "password": "testpass123"
}
```

**Ожидаемый ответ:**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 2,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
}
```

### 3. Обновление токена
```http
POST {{base_url}}/token/refresh/
Content-Type: application/json

{
    "refresh": "{{refresh_token}}"
}
```

### 4. Проверка токена
```http
POST {{base_url}}/token/verify/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "token": "{{access_token}}"
}
```

---

## 👤 Управление пользователями

### 1. Получение профиля
```http
GET {{base_url}}/users/profile/
Authorization: Bearer {{access_token}}
```

### 2. Обновление профиля (PUT - все поля)
```http
PUT {{base_url}}/users/profile/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Updated",
    "last_name": "Name",
    "date_of_birth": "1990-01-01"
}
```

### 3. Частичное обновление профиля (PATCH)
```http
PATCH {{base_url}}/users/profile/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "first_name": "New Name"
}
```

### 4. Смена пароля
```http
POST {{base_url}}/users/change-password/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "old_password": "testpass123",
    "new_password": "newpass123",
    "new_password_confirmation": "newpass123"
}
```

---

## 📊 Управление портфелями

### 1. Получение списка портфелей
```http
GET {{base_url}}/portfolios/
Authorization: Bearer {{access_token}}
```

### 2. Создание портфеля
```http
POST {{base_url}}/portfolios/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "name": "My Investment Portfolio",
    "description": "Основной инвестиционный портфель"
}
```

### 3. Получение деталей портфеля
```http
GET {{base_url}}/portfolios/{{portfolio_id}}/
Authorization: Bearer {{access_token}}
```

### 4. Обновление портфеля
```http
PUT {{base_url}}/portfolios/{{portfolio_id}}/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "name": "Updated Portfolio Name",
    "description": "Обновленное описание портфеля"
}
```

### 5. Удаление портфеля
```http
DELETE {{base_url}}/portfolios/{{portfolio_id}}/
Authorization: Bearer {{access_token}}
```

---

## 💰 Управление транзакциями

### 1. Получение списка транзакций портфеля
```http
GET {{base_url}}/portfolios/{{portfolio_id}}/transactions/
Authorization: Bearer {{access_token}}
```

### 2. Создание транзакции покупки
```http
POST {{base_url}}/portfolios/{{portfolio_id}}/transactions/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "ticker": "AAPL",
    "quantity": 100,
    "price": 150.00,
    "date": "2024-10-01T10:00:00Z",
    "transaction_type": "BUY"
}
```

### 3. Создание транзакции продажи
```http
POST {{base_url}}/portfolios/{{portfolio_id}}/transactions/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "ticker": "AAPL",
    "quantity": 50,
    "price": 160.00,
    "date": "2024-10-15T10:00:00Z",
    "transaction_type": "SELL"
}
```

### 4. Создание транзакции с автоматическим получением цены
```http
POST {{base_url}}/portfolios/{{portfolio_id}}/transactions/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "ticker": "MSFT",
    "quantity": 25,
    "date": "2024-10-20T10:00:00Z",
    "transaction_type": "BUY"
}
```

**Примечание:** Если поле `price` не указано, система автоматически получит текущую цену из кеша или через Finnhub API.

### 5. Получение деталей транзакции
```http
GET {{base_url}}/portfolios/{{portfolio_id}}/transactions/{{transaction_id}}/
Authorization: Bearer {{access_token}}
```

### 6. Обновление транзакции
```http
PUT {{base_url}}/portfolios/{{portfolio_id}}/transactions/{{transaction_id}}/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "ticker": "AAPL",
    "quantity": 75,
    "price": 155.00,
    "date": "2024-10-01T10:00:00Z",
    "transaction_type": "BUY"
}
```

### 7. Удаление транзакции
```http
DELETE {{base_url}}/portfolios/{{portfolio_id}}/transactions/{{transaction_id}}/
Authorization: Bearer {{access_token}}
```

---

## 📈 FIFO Расчет

### 1. Получение FIFO расчета для портфеля
```http
GET {{base_url}}/portfolios/{{portfolio_id}}/fifo/
Authorization: Bearer {{access_token}}
```

**Ожидаемый ответ:**
```json
{
    "total_profit": "1300.00",
    "positions": [
        {
            "ticker": "AAPL",
            "remaining_qty": "30.000000",
            "buy_price": "55.00"
        }
    ]
}
```

---

## 🏢 Управление акциями

### 1. Получение списка акций
```http
GET {{base_url}}/stocks/
Authorization: Bearer {{access_token}}
```

### 2. Создание акции
```http
POST {{base_url}}/stocks/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "ticker": "GOOGL",
    "name": "Alphabet Inc.",
    "current_price": 2800.00
}
```

### 3. Получение деталей акции
```http
GET {{base_url}}/stocks/1/
Authorization: Bearer {{access_token}}
```

### 4. Обновление акции
```http
PUT {{base_url}}/stocks/1/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "current_price": 175.00
}
```

### 5. Удаление акции
```http
DELETE {{base_url}}/stocks/1/
Authorization: Bearer {{access_token}}
```

### 6. Получение текущей цены акции
```http
GET {{base_url}}/stocks/AAPL/price/
Authorization: Bearer {{access_token}}
```

**Ожидаемый ответ:**
```json
{
    "ticker": "AAPL",
    "price": 175.25,
    "change": 2.15,
    "percent_change": 1.24,
    "high": 176.50,
    "low": 173.10,
    "open": 174.00,
    "previous_close": 173.10,
    "timestamp": 1698765432,
    "source": "finnhub.io"
}
```

---

## 🧪 Тестовые сценарии

### Сценарий 1: Полный цикл работы с портфелем

1. **Регистрация пользователя**
2. **Создание портфеля**
3. **Добавление транзакций покупки:**
   - 100 акций AAPL по $50 (1 октября)
   - 50 акций AAPL по $55 (5 октября)
4. **Добавление транзакций продажи:**
   - 80 акций AAPL по $60 (10 октября)
   - 40 акций AAPL по $65 (15 октября)
5. **Проверка FIFO расчета** - должен показать прибыль $1300 и остаток 30 акций по $55

### Сценарий 2: Тестирование ошибок

1. **Неверные учетные данные:**
```http
POST {{base_url}}/users/login/
{
    "username": "wronguser",
    "password": "wrongpass"
}
```

2. **Создание портфеля с существующим именем:**
```http
POST {{base_url}}/portfolios/
{
    "name": "Existing Portfolio Name"
}
```

3. **Транзакция с отрицательным количеством:**
```http
POST {{base_url}}/portfolios/1/transactions/
{
    "ticker": "AAPL",
    "quantity": -10,
    "price": 150.00,
    "transaction_type": "BUY"
}
```

---

## 🔧 Настройка Postman Collection

### 1. Создание Collection
1. Создайте новую Collection "Stock Portfolio API"
2. Добавьте все запросы выше
3. Настройте переменные окружения

### 2. Автоматическое сохранение токенов
Добавьте в Tests секцию для запросов логина:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("access_token", response.access);
    pm.environment.set("refresh_token", response.refresh);
}
```

### 3. Автоматическое сохранение ID
Добавьте в Tests секцию для создания портфеля:
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("portfolio_id", response.id);
}
```

---

## 📊 Проверка статусов ответов

### Успешные ответы:
- **200 OK** - Успешный GET, PUT, PATCH
- **201 Created** - Успешный POST
- **204 No Content** - Успешный DELETE

### Ошибки клиента:
- **400 Bad Request** - Неверные данные
- **401 Unauthorized** - Неверный токен
- **403 Forbidden** - Нет доступа
- **404 Not Found** - Ресурс не найден

### Ошибки сервера:
- **500 Internal Server Error** - Ошибка сервера

---

## 🚀 Быстрый старт

1. **Запустите Docker контейнеры:**
```bash
docker-compose up -d
```

2. **Импортируйте Collection в Postman**
3. **Создайте Environment с переменными**
4. **Начните с регистрации пользователя**
5. **Сохраните токены в переменные**
6. **Тестируйте все endpoints по порядку**

Этот набор запросов позволит вам полностью протестировать все функции API и убедиться в корректной работе системы!
