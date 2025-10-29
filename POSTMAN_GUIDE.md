# 🚀 Postman Collection for Stock Portfolio API

## 📋 Postman Setup

### 1. Basic Settings
- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`
- **Authorization**: Bearer Token (for protected endpoints)

### 2. Environment Variables
Create an Environment in Postman with the following variables:
```
base_url: http://localhost:8000/api
access_token: (will be filled after login)
refresh_token: (will be filled after login)
portfolio_id: 1
transaction_id: 1
```

---

## 🔐 Authentication

### 1. User Registration
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

**Expected Response:**
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

### 2. Login
```http
POST {{base_url}}/users/login/
Content-Type: application/json

{
    "username": "testuser",
    "password": "testpass123"
}
```

**Expected Response:**
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

### 3. Token Refresh
```http
POST {{base_url}}/token/refresh/
Content-Type: application/json

{
    "refresh": "{{refresh_token}}"
}
```

### 4. Token Verification
```http
POST {{base_url}}/token/verify/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "token": "{{access_token}}"
}
```

---

## 👤 User Management

### 1. Get Profile
```http
GET {{base_url}}/users/profile/
Authorization: Bearer {{access_token}}
```

### 2. Update Profile (PUT - all fields)
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

### 3. Partial Profile Update (PATCH)
```http
PATCH {{base_url}}/users/profile/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "first_name": "New Name"
}
```

### 4. Change Password
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

## 📊 Portfolio Management

### 1. Get Portfolio List
```http
GET {{base_url}}/portfolios/
Authorization: Bearer {{access_token}}
```

### 2. Create Portfolio
```http
POST {{base_url}}/portfolios/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "name": "My Investment Portfolio",
    "description": "Main investment portfolio"
}
```

### 3. Get Portfolio Details
```http
GET {{base_url}}/portfolios/{{portfolio_id}}/
Authorization: Bearer {{access_token}}
```

### 4. Update Portfolio
```http
PUT {{base_url}}/portfolios/{{portfolio_id}}/
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
    "name": "Updated Portfolio Name",
    "description": "Updated portfolio description"
}
```

### 5. Delete Portfolio
```http
DELETE {{base_url}}/portfolios/{{portfolio_id}}/
Authorization: Bearer {{access_token}}
```

---

## 💰 Transaction Management

### 1. Get Portfolio Transactions
```http
GET {{base_url}}/portfolios/{{portfolio_id}}/transactions/
Authorization: Bearer {{access_token}}
```

### 2. Create Buy Transaction
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

### 3. Create Sell Transaction
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

### 4. Create Transaction with Automatic Price Fetching
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

**Note:** If the `price` field is not specified, the system will automatically fetch the current price from cache or via Finnhub API.

### 5. Get Transaction Details
```http
GET {{base_url}}/portfolios/{{portfolio_id}}/transactions/{{transaction_id}}/
Authorization: Bearer {{access_token}}
```

### 6. Update Transaction
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

### 7. Delete Transaction
```http
DELETE {{base_url}}/portfolios/{{portfolio_id}}/transactions/{{transaction_id}}/
Authorization: Bearer {{access_token}}
```

---

## 📈 FIFO Calculation

### 1. Get FIFO Calculation for Portfolio
```http
GET {{base_url}}/portfolios/{{portfolio_id}}/fifo/
Authorization: Bearer {{access_token}}
```

**Expected Response:**
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

## 🏢 Stock Price Retrieval

### 1. Get Current Stock Price
```http
GET {{base_url}}/stocks/AAPL/price/
Authorization: Bearer {{access_token}}
```

**Expected Response:**
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

## 🧪 Test Scenarios

### Scenario 1: Complete Portfolio Workflow

1. **User Registration**
2. **Portfolio Creation**
3. **Adding Buy Transactions:**
   - 100 AAPL shares at $50 (October 1st)
   - 50 AAPL shares at $55 (October 5th)
4. **Adding Sell Transactions:**
   - 80 AAPL shares at $60 (October 10th)
   - 40 AAPL shares at $65 (October 15th)
5. **FIFO Calculation Check** - should show $1300 profit and 30 shares remaining at $55

### Scenario 2: Error Testing

1. **Invalid Credentials:**
```http
POST {{base_url}}/users/login/
{
    "username": "wronguser",
    "password": "wrongpass"
}
```

2. **Creating Portfolio with Existing Name:**
```http
POST {{base_url}}/portfolios/
{
    "name": "Existing Portfolio Name"
}
```

3. **Transaction with Negative Quantity:**
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

## 🔧 Postman Collection Setup

### 1. Creating Collection
1. Create a new Collection "Stock Portfolio API"
2. Add all the requests above
3. Configure environment variables

### 2. Automatic Token Saving
Add to the Tests section for login requests:
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("access_token", response.access);
    pm.environment.set("refresh_token", response.refresh);
}
```

### 3. Automatic ID Saving
Add to the Tests section for portfolio creation:
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("portfolio_id", response.id);
}
```

---

## 📊 Response Status Check

### Success Responses:
- **200 OK** - Successful GET, PUT, PATCH
- **201 Created** - Successful POST
- **204 No Content** - Successful DELETE

### Client Errors:
- **400 Bad Request** - Invalid data
- **401 Unauthorized** - Invalid token
- **403 Forbidden** - No access
- **404 Not Found** - Resource not found

### Server Errors:
- **500 Internal Server Error** - Server error

---

## 🚀 Quick Start

1. **Start Docker containers:**
```bash
docker-compose up -d
```

2. **Import Collection into Postman**
3. **Create Environment with variables**
4. **Start with user registration**
5. **Save tokens to variables**
6. **Test all endpoints in order**

This set of requests will allow you to fully test all API functions and ensure the system works correctly!