# NexusAI Backend - FastAPI Enterprise Edition

Professional, production-ready API for NexusAI platform with PostgreSQL, JWT authentication, and async/await patterns.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Docker (optional, for easy setup)

### Local Development

1. **Clone and setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings (especially DATABASE_URL)
```

3. **Start PostgreSQL (Docker):**
```bash
docker run -d \
  --name nexusai-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=nexusai \
  -p 5432:5432 \
  postgres:15-alpine
```

4. **Run migrations:**
```bash
# From backend directory
alembic upgrade head
```

5. **Start FastAPI server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access API:**
- OpenAPI Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Docker Compose (All-in-One)

```bash
# From project root
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Project Structure

```
backend/
├── app/
│   ├── api/v2/            # API v2 routes
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── projects.py    # Project management
│   │   ├── files.py       # File management
│   │   └── code_execution.py  # Code execution
│   ├── core/
│   │   ├── config.py      # Configuration
│   │   ├── database.py    # Database setup
│   │   └── security.py    # Auth & JWT
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic request/response schemas
│   └── main.py            # FastAPI app initialization
├── migrations/            # Alembic database migrations
│   ├── env.py
│   ├── alembic.ini
│   └── versions/          # Migration scripts
├── tests/                 # Unit & integration tests
├── requirements.txt       # Python dependencies
└── .env.example          # Environment template
```

## API Endpoints

### Authentication (`/api/v2/auth`)
- `POST /register` - Register new user
- `POST /login` - Login with credentials
- `POST /refresh` - Refresh access token
- `GET /me` - Get current user profile
- `POST /logout` - Logout

### Projects (`/api/v2/projects`)
- `POST /` - Create project
- `GET /` - List projects
- `GET /{id}` - Get project details
- `PUT /{id}` - Update project
- `DELETE /{id}` - Delete project

### Files (`/api/v2/projects/{id}/files`)
- `POST /` - Create file
- `GET /` - List files
- `GET /{id}` - Get file content
- `PUT /{id}` - Update file
- `DELETE /{id}` - Delete file
- `GET /{id}/versions` - File version history
- `POST /{id}/versions/{version_id}/restore` - Restore version

### Code Execution (`/api/v2/projects/{id}/code`)
- `POST /execute` - Execute code
- `GET /executions` - Execution history
- `GET /executions/{id}` - Get execution result

## Authentication

All protected endpoints require JWT token in `Authorization` header:

```bash
curl -H "Authorization: Bearer {access_token}" \
     http://localhost:8000/api/v2/projects
```

### Get Tokens

```bash
# Register
curl -X POST http://localhost:8000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "securepassword123"
  }'

# Login
curl -X POST http://localhost:8000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'

# Refresh Token
curl -X POST http://localhost:8000/api/v2/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token"}'
```

## Database Migrations

### Create Migration
```bash
# After modifying models.py
alembic revision --autogenerate -m "Add new field"
```

### Apply Migrations
```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# View current revision
alembic current
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/nexusai` | PostgreSQL connection |
| `DEBUG` | `false` | Enable debug mode |
| `ENVIRONMENT` | `development` | App environment |
| `SECRET_KEY` | Generated | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `OPENROUTER_API_KEY` | - | AI API key |
| `CODE_EXECUTION_TIMEOUT` | `60` | Code execution timeout |

## Performance & Security

- Async/await throughout for high concurrency
- Connection pooling with SQLAlchemy
- Password hashing with bcrypt
- JWT tokens with automatic expiration
- CORS + trusted host middleware
- Request logging and error tracking
- SQL injection prevention via ORM

## Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Make changes and test: `pytest`
3. Format code: `black app/`
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`

## Troubleshooting

### Database Connection Error
```
Error: could not connect to server: Connection refused

✅ Solution: Ensure PostgreSQL is running and DATABASE_URL is correct
docker ps  # Check if postgres container is running
```

### Alembic Migration Error
```
✅ Solution: Make sure models.py imports are in app/__init__.py
✅ Restart migrations: rm -rf migrations/versions/*.py && regenerate
```

### Port Already in Use
```
lsof -i :8000  # Find process using port
kill -9 <PID>   # Kill process
```

## Monitoring & Logging

- All requests logged to console
- Response times tracked in X-Process-Time header
- Errors logged with full stack trace
- Async performance monitored automatically

## Next Steps

- [ ] Implement WebSocket endpoints for real-time features
- [ ] Add Redis caching layer
- [ ] Set up Sentry error tracking
- [ ] Configure production deployment
- [ ] Add more comprehensive tests
- [ ] Set up GraphQL layer (optional)

---

**Built with ❤️ using FastAPI, SQLAlchemy, and PostgreSQL**
