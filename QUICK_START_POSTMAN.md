# 🚀 Quick Start API Testing with Postman

## 📥 Import Files to Postman

### 1. Import Collection
1. Open Postman
2. Click **Import** in the top left corner
3. Select the file `Stock_Portfolio_API.postman_collection.json`
4. Click **Import**

### 2. Import Environment
1. Click **Import** again
2. Select the file `Stock_Portfolio_Environment.postman_environment.json`
3. Click **Import**
4. Select Environment "Stock Portfolio Environment" in the top right corner

## 🐳 Start Server

```bash
# Start Docker containers
docker-compose up -d

# Check status
docker-compose ps
```

## 🧪 Testing

### Step 1: User Registration
1. Open folder **Authentication** → **Register User**
2. Click **Send**
3. Copy `access_token` from the response
4. Paste it into the `access_token` variable in Environment

### Step 2: Create Portfolio
1. Open **Portfolios** → **Create Portfolio**
2. Click **Send**
3. Copy `id` from the response
4. Paste it into the `portfolio_id` variable in Environment

### Step 3: FIFO Testing
1. Open folder **Test Scenarios** → **Complete FIFO Test**
2. Execute requests in order (1-7)
3. Check the result in the last request

## 📊 Expected Results

### FIFO Test should show:
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

## 🔧 Useful Commands

### Check container status:
```bash
docker-compose ps
```

### View logs:
```bash
docker-compose logs web
```

### Restart services:
```bash
docker-compose restart
```

### Stop services:
```bash
docker-compose down
```

## ⚠️ Troubleshooting

### Connection error:
- Make sure Docker containers are running
- Check that port 8000 is free

### Authentication error:
- Check that the token was copied correctly
- Make sure the token hasn't expired (30 minutes)

### Validation error:
- Check the data format in the request
- Make sure all required fields are filled

## 📝 Notes

- Tokens are automatically saved to Environment variables
- IDs of created resources are also saved automatically
- All requests use variables from Environment
- Use invalid data to test error scenarios

Happy testing! 🎯