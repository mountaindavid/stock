# Stock Portfolio Management System

A Django REST API for managing stock portfolios with real-time market data integration and FIFO calculations.

## Features

- **User Management**: Registration, authentication, profile management
- **Portfolio Management**: Create and manage multiple portfolios
- **Stock Transactions**: Buy/sell stocks with automatic price fetching
- **Real-time Data**: Integration with Finnhub.io for current stock prices
- **FIFO Calculations**: First-In-First-Out profit/loss calculations
- **Portfolio Analytics**: Calculate total value, profit/loss, and performance metrics
- **Caching**: Redis-based caching for improved performance
- **Transaction Validation**: Prevents selling more shares than owned
- **Automatic Stock Creation**: Creates stock records automatically from transactions

## Tech Stack

- **Backend**: Django 4.2.7 + Django REST Framework
- **Database**: PostgreSQL + Redis (caching)
- **Authentication**: JWT tokens
- **Market Data**: Finnhub.io API
- **Containerization**: Docker + Docker Compose

## Architecture

The system follows a clean architecture pattern with:

- **Models**: Django ORM models for data persistence
- **Serializers**: Data validation and serialization
- **Views**: API endpoints and business logic
- **Services**: Business logic and external API integration
- **Caching**: Redis for performance optimization

### Key Components

- **FIFOCalculator**: Centralized service for FIFO calculations with caching
- **FinnhubService**: Integration with Finnhub.io for real-time stock prices
- **Transaction Validation**: Ensures data integrity and prevents invalid transactions

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

# Finnhub.io API Key (Required for market data)
FINNHUB_API_KEY=your-finnhub-api-key-here
```

### 3. Get Finnhub.io API Key

1. Visit [finnhub.io](https://finnhub.io/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to your `.env` file

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
- `GET /api/portfolios/{id}/` - Get portfolio details with total value
- `PUT /api/portfolios/{id}/` - Update portfolio
- `DELETE /api/portfolios/{id}/` - Delete portfolio
- `GET /api/portfolios/{id}/fifo/` - Get FIFO profit/loss calculations
- `GET /api/portfolios/{id}/stocks/{stock_id}/` - Get specific stock in portfolio

### Transactions
- `GET /api/portfolios/{id}/transactions/` - List transactions
- `POST /api/portfolios/{id}/transactions/` - Create transaction
- `GET /api/portfolios/{id}/transactions/{id}/` - Get transaction
- `PUT /api/portfolios/{id}/transactions/{id}/` - Update transaction
- `DELETE /api/portfolios/{id}/transactions/{id}/` - Delete transaction

### Stock Prices
- `GET /api/stocks/{ticker}/price/` - Get current stock price

## Usage Examples

### Create a Transaction

```bash
curl -X POST http://localhost:8000/api/portfolios/1/transactions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "transaction_type": "BUY",
    "quantity": 10,
    "price": 150.00,
    "date": "2025-10-29T10:00:00Z"
  }'
```

### Auto-fetch Price (if not provided)

```bash
curl -X POST http://localhost:8000/api/portfolios/1/transactions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "transaction_type": "BUY",
    "quantity": 10,
    "date": "2025-10-29T10:00:00Z"
  }'
```

### Get FIFO Calculations

```bash
curl -X GET http://localhost:8000/api/portfolios/1/fifo/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Current Stock Price

```bash
curl -X GET http://localhost:8000/api/stocks/AAPL/price/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
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

### Finnhub.io API Issues

- **API Key Not Configured**: Make sure `FINNHUB_API_KEY` is set in `.env`
- **Rate Limits**: Finnhub.io has rate limits (free tier: 60 calls/minute)
- **API Errors**: Check Finnhub.io status page for service issues

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
