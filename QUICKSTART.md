# Quick Start Guide

Get the agentic platform running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Anthropic API key (get one at https://console.anthropic.com/)

## Step 1: Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Generate secure keys (on Mac/Linux)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Edit .env and set these values:
# - SECRET_KEY=<your-generated-secret>
# - JWT_SECRET=<your-generated-jwt-secret>
# - ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Step 2: Start the Platform

```bash
# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
docker-compose logs -f api
```

## Step 3: Initialize Database

```bash
# Create initial database migration
docker-compose exec api alembic revision --autogenerate -m "Initial schema"

# Apply migrations
docker-compose exec api alembic upgrade head

# Seed development data (creates demo tenant and admin user)
docker-compose exec api python scripts/seed_dev_data.py
```

## Step 4: Test the API

### Access API Documentation

Open in your browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Login

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.com",
    "password": "admin123"
  }'
```

Save the `access_token` from the response.

### Execute the Sample Agent

```bash
# Get agent ID from seed script output, or list agents:
curl -X GET http://localhost:8000/v1/agents \
  -H "Authorization: Bearer <your-access-token>"

# Execute agent
curl -X POST http://localhost:8000/v1/agents/<agent-id>/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-access-token>" \
  -d '{
    "input": "Hello! Can you help me understand what you can do?",
    "stream": false
  }'
```

## Step 5: Create Your Own Agent

```bash
curl -X POST http://localhost:8000/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-access-token>" \
  -d '{
    "name": "My First Agent",
    "slug": "my-first-agent",
    "description": "A helpful assistant",
    "model_provider": "anthropic",
    "model_name": "claude-sonnet-4-5",
    "system_prompt": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "max_tokens": 4096
  }'
```

## Useful Commands

```bash
# View API logs
docker-compose logs -f api

# View all logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d agentic_platform

# Access Redis CLI
docker-compose exec redis redis-cli

# Run migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "your message"
```

## Default Credentials

After running `seed_dev_data.py`:

- **Email**: admin@demo.com
- **Password**: admin123
- **Tenant**: Demo Tenant (demo-tenant)

## Troubleshooting

### "Connection refused" errors

Wait a bit longer for services to start:
```bash
docker-compose ps  # Check if services are up
docker-compose logs postgres  # Check PostgreSQL logs
```

### Migration errors

Reset database:
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d
# Run migration steps again
```

### Agent execution fails

Check your ANTHROPIC_API_KEY in `.env` is correct and has credits.

## Next Steps

1. Explore the API documentation at http://localhost:8000/docs
2. Read the full README.md for detailed information
3. Check out the architecture and specifications in the `docs/` folder
4. Start building your agents!

## Need Help?

- Check the logs: `docker-compose logs -f`
- Review [README.md](README.md) for detailed documentation
- Check the [docs/](docs/) folder for specifications
