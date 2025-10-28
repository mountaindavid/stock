# Stock Portfolio Management System

A Django REST API for managing stock portfolios with real-time market data integration.

## Features

- **User Management**: Registration, authentication, profile management
- **Portfolio Management**: Create and manage multiple portfolios
- **Stock Transactions**: Buy/sell stocks with automatic price fetching
- **Real-time Data**: Integration with Polygon.io for current stock prices
- **Portfolio Analytics**: Calculate total value, profit/loss, and performance metrics

## Tech Stack

- **Backend**: Django 4.2.7 + Django REST Framework
- **Database**: PostgreSQL + Redis (caching)
- **Authentication**: JWT tokens
- **Market Data**: Polygon.io API
- **Containerization**: Docker + Docker Compose

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Stock
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=stock_portfolio
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Polygon.io API Key (Required for market data)
POLYGON_API_KEY=your-polygon-api-key-here
```

### 3. Get Polygon.io API Key

1. Visit [polygon.io](https://polygon.io/)
2. Sign up for an account
3. Choose a plan (Starter: $99/month)
4. Get your API key from the dashboard
5. Add it to your `.env` file

### 4. Run with Docker

```bash
# Start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### 5. Access the API

- **API Base URL**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/

## API Endpoints

### Authentication
- `POST /api/users/register/` - User registration
- `POST /api/token/` - Get JWT token
- `POST /api/token/refresh/` - Refresh JWT token
- `POST /api/token/verify/` - Verify JWT token

### Users
- `GET /api/users/profile/` - Get user profile
- `PUT /api/users/profile/` - Update user profile
- `POST /api/users/change-password/` - Change password

### Portfolios
- `GET /api/portfolios/` - List user portfolios
- `POST /api/portfolios/` - Create portfolio
- `GET /api/portfolios/{id}/` - Get portfolio details
- `PUT /api/portfolios/{id}/` - Update portfolio
- `DELETE /api/portfolios/{id}/` - Delete portfolio

### Transactions
- `GET /api/portfolios/{id}/transactions/` - List transactions
- `POST /api/portfolios/{id}/transactions/` - Create transaction
- `GET /api/portfolios/{id}/transactions/{id}/` - Get transaction
- `PUT /api/portfolios/{id}/transactions/{id}/` - Update transaction
- `DELETE /api/portfolios/{id}/transactions/{id}/` - Delete transaction

### Stocks
- `GET /api/stocks/` - List all stocks
- `POST /api/stocks/` - Create stock
- `GET /api/stocks/{id}/` - Get stock details
- `PUT /api/stocks/{id}/` - Update stock
- `DELETE /api/stocks/{id}/` - Delete stock

## Usage Examples

### Create a Transaction

```bash
curl -X POST http://localhost:8000/api/portfolios/1/transactions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_ticker": "AAPL",
    "transaction_type": "BUY",
    "quantity": 10,
    "price_per_share": 150.00
  }'
```

### Auto-fetch Price (if not provided)

```bash
curl -X POST http://localhost:8000/api/portfolios/1/transactions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_ticker": "AAPL",
    "transaction_type": "BUY",
    "quantity": 10
  }'
```

## Development

### Run Tests

```bash
docker-compose exec web python manage.py test
```

### Code Quality

```bash
# Format code
docker-compose exec web black .

# Sort imports
docker-compose exec web isort .

# Lint code
docker-compose exec web flake8
```

## Production Deployment

1. Set `DEBUG=False` in production
2. Use environment-specific settings
3. Configure proper database credentials
4. Set up SSL certificates
5. Configure reverse proxy (nginx)
6. Set up monitoring and logging

## Troubleshooting

### Polygon.io API Issues

- **API Key Not Configured**: Make sure `POLYGON_API_KEY` is set in `.env`
- **Rate Limits**: Polygon.io has rate limits based on your plan
- **API Errors**: Check Polygon.io status page for service issues

### Database Issues

- **Connection Failed**: Check database credentials in `.env`
- **Migration Errors**: Run `python manage.py migrate` to apply migrations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
