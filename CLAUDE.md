# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Starting the Development Stack

```bash
# Start all services with live reload
docker compose watch

# Start specific services
docker compose up -d backend db

# Stop all services
docker compose down
```

### Backend Development

```bash
# Install dependencies
cd backend
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run backend locally (without Docker)
fastapi dev app/main.py

# Run backend tests
bash ./scripts/test.sh

# Run specific test module
pytest tests/pdca/test_engine.py -v

# Run tests with coverage
pytest --cov=app

# Run linting and formatting
uv run ruff check --fix
uv run ruff format
```

### Frontend Development

```bash
# Install dependencies
bun install

# Run frontend locally
bun run dev

# Run frontend tests
bun run test

# Run E2E tests with Playwright
bunx playwright test

# Generate frontend API client from backend
bash ./scripts/generate-client.sh
```

### Code Quality

```bash
# Run pre-commit hooks manually
uv run prek run --all-files

# Install pre-commit hooks
uv run prek install -f
```

## Architecture Overview

### Technology Stack

**Backend:**
- FastAPI with SQLModel for ORM
- PostgreSQL database with Alembic migrations
- JWT authentication with password hashing
- LangGraph for PDCA workflow state machine
- Multiple agent executors (OpenAI, Python, HTTP, Shell)
- MinIO for object storage (screenshots)
- Redis for caching
- Prometheus for metrics

**Frontend:**
- React with TypeScript and Vite
- TanStack Router for routing
- TanStack Query for data fetching
- Tailwind CSS with shadcn/ui components
- Auto-generated API client from OpenAPI spec

**Testing:**
- Backend: Pytest
- Frontend E2E: Playwright
- Additional E2E: Puppeteer-based framework in `e2e-agent-tests/`

### Key Features

1. **PDCA Workflow Management** (`backend/app/pdca/`)
   - LangGraph-based state machine for Plan-Do-Check-Act cycles
   - Pluggable agent executor system
   - RESTful API for CRUD operations and execution
   - Supports nested cycles and detailed execution logging

2. **Web Automation Testing** (`backend/app/web_tests/`)
   - Natural language test descriptions
   - Claude CLI integration for browser automation
   - Real-time WebSocket log streaming
   - Screenshot capture with MinIO storage
   - User-isolated test management

3. **Multi-Environment Support**
   - Docker Compose configurations for local, dev, staging, production
   - Traefik reverse proxy for load balancing and TLS
   - Environment-specific `.env` files

### Project Structure

```
backend/
├── app/
│   ├── api/          # API routes and dependencies
│   ├── core/         # Configuration, security, database
│   ├── crud.py       # CRUD operations
│   ├── models.py     # SQLModel database models
│   ├── pdca/         # PDCA workflow system
│   ├── web_tests/    # Web automation testing
│   └── email-templates/  # Email templates
├── scripts/          # Utility scripts
└── tests/            # Backend tests

frontend/
├── src/
│   ├── client/       # Auto-generated API client
│   ├── components/   # React components
│   ├── routes/       # Page routes and layouts
│   └── hooks/        # Custom React hooks
└── tests/            # Playwright E2E tests

e2e-agent-tests/      # Additional E2E testing framework
scripts/              # Root-level utility scripts
```

## Development Workflows

### Database Migrations

```bash
# Enter backend container
docker compose exec backend bash

# Create migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations to database
alembic upgrade head
```

### Frontend Client Generation

After changing backend API endpoints, regenerate the frontend client:

```bash
bash ./scripts/generate-client.sh
```

This is also automatically run by pre-commit hooks when backend files change.

### Testing Strategy

1. **Backend Tests**: Run `bash ./scripts/test.sh` or use Pytest directly
2. **Frontend Tests**: Use `bun run test` for unit tests, `bunx playwright test` for E2E
3. **Integration Tests**: Ensure Docker Compose stack is running before testing

### Environment Configuration

- Default environment variables in `.env`
- Environment-specific files: `.env.dev`, `.env.staging`, `.env.prod`
- Required changes before deployment:
  - `SECRET_KEY`
  - `FIRST_SUPERUSER_PASSWORD`
  - `POSTGRES_PASSWORD`

### Local Development URLs

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Adminer (DB): http://localhost:8080
- Traefik UI: http://localhost:8090
- MailCatcher: http://localhost:1080

## Important Notes

- The project uses `uv` for Python dependency management
- The project uses `bun` for frontend dependency management (Node.js also works)
- Pre-commit hooks automatically run linting, formatting, and client generation
- Backend runs on port 8000, frontend on port 5173 in local development
- Database migrations are mandatory when changing models
- All API changes require regenerating the frontend client
- The PDCA system requires proper LangGraph and agent configuration
- Web automation tests require Claude CLI installed on the server