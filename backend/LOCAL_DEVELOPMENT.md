# Local Development Guide

This guide explains how to set up and run the TODO backend locally.

## Quick Start

1. **Copy environment configuration:**
   ```bash
   cp .env.local .env
   ```

2. **Run the setup script:**
   ```bash
   chmod +x scripts/setup-local.sh
   ./scripts/setup-local.sh
   ```

3. **Start the development server:**
   ```bash
   source venv/bin/activate
   uvicorn src.main:app --reload --port 8000
   ```

## Manual Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for PostgreSQL)
- Git

### Step 1: Environment Configuration

Copy the local environment template:
```bash
cp .env.local .env
```

Edit `.env` and update the following values if needed:
- Database URL (if not using Docker)
- Clerk keys (if using Clerk authentication)
- CORS origins (for frontend integration)

### Step 2: Python Environment

Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Database Setup

#### Option A: Docker PostgreSQL (Recommended)

Start PostgreSQL container:
```bash
cd ..
docker-compose up -d db
cd backend
```

Wait for the database to be ready, then run migrations:
```bash
alembic upgrade head
```

#### Option B: Neon PostgreSQL (Cloud)

1. Create a Neon database at https://neon.tech
2. Update `DATABASE_URL` in `.env` with your Neon connection string
3. Run migrations:
   ```bash
   alembic upgrade head
   ```

#### Option C: Local PostgreSQL Installation

1. Install PostgreSQL locally
2. Create a database named `todolist`
3. Update `DATABASE_URL` in `.env`
4. Run migrations:
   ```bash
   alembic upgrade head
   ```

### Step 4: Start the Server

```bash
uvicorn src.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Authentication Options

### Option 1: Development Authentication (No Setup Required)

The backend includes built-in development authentication that works without external services.

**Available endpoints:**
- `GET /api/auth/dev/help` - Get authentication help
- `GET /api/auth/dev/users` - List available dev users
- `POST /api/auth/dev/token` - Get development token
- `POST /api/auth/dev/guest-session` - Create guest session

**Example usage:**

1. **Get a development token:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/dev/token \
        -H "Content-Type: application/json" \
        -d '{"username": "dev_user_1"}'
   ```

2. **Use the token for authenticated requests:**
   ```bash
   curl -X GET http://localhost:8000/api/todos \
        -H "Authorization: Bearer <your_dev_token>"
   ```

3. **Create guest session:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/dev/guest-session
   ```

4. **Use guest session:**
   ```bash
   curl -X GET http://localhost:8000/api/todos \
        -H "X-Session-ID: <your_session_id>"
   ```

**Available development users:**
- `dev_user_1`: Regular development user (dev@example.com)
- `admin`: Admin development user (admin@example.com)

### Option 2: Clerk Authentication (Production-like)

1. Create a Clerk account at https://dashboard.clerk.com
2. Create a new application
3. Get your API keys from the dashboard
4. Update `.env` with your Clerk keys:
   ```
   CLERK_SECRET_KEY=sk_test_...
   CLERK_PUBLISHABLE_KEY=pk_test_...
   ```

## Testing

Run the test suite:
```bash
# All tests
pytest

# Contract tests only
pytest tests/contract/

# Integration tests only
pytest tests/integration/

# With coverage
pytest --cov=src
```

## Database Management

### View current migration status:
```bash
alembic current
```

### Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback to previous migration:
```bash
alembic downgrade -1
```

## Troubleshooting

### Database Connection Issues

1. **PostgreSQL container not running:**
   ```bash
   docker-compose up -d db
   docker-compose logs db
   ```

2. **Wrong DATABASE_URL:**
   - Check the connection string in `.env`
   - Ensure database exists and is accessible

3. **Migration issues:**
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

### Authentication Issues

1. **Development auth not working:**
   - Ensure `ENVIRONMENT=development` in `.env`
   - Check `/api/auth/dev/help` endpoint

2. **Clerk auth not working:**
   - Verify Clerk keys are correct
   - Check Clerk dashboard for application status

### Import Errors

1. **Module not found:**
   - Ensure virtual environment is activated
   - Install requirements: `pip install -r requirements.txt`

2. **Python path issues:**
   - Run from backend directory
   - Use `python -m src.main` instead of direct execution

## Development Workflow

1. **Start services:**
   ```bash
   docker-compose up -d db  # Start database
   source venv/bin/activate  # Activate Python env
   uvicorn src.main:app --reload  # Start API server
   ```

2. **Make changes to code**

3. **Test changes:**
   ```bash
   pytest tests/
   ```

4. **Create database migrations if needed:**
   ```bash
   alembic revision --autogenerate -m "Your change description"
   alembic upgrade head
   ```

5. **Test API endpoints:**
   - Use `/docs` for interactive testing
   - Use development auth for quick testing
   - Use Postman/curl for manual testing

## Production Considerations

When deploying to production:

1. **Environment variables:**
   - Set `ENVIRONMENT=production`
   - Use strong `SECRET_KEY`
   - Use real Clerk credentials
   - Set proper `CORS_ORIGINS`

2. **Database:**
   - Use managed PostgreSQL (Neon, RDS, etc.)
   - Enable connection pooling
   - Set up backup strategy

3. **Security:**
   - Development auth routes are automatically disabled in production
   - Enable HTTPS
   - Set up proper logging and monitoring