# 🚀 NexusAI Quick Start Guide

## What You Now Have

A fully functional **enterprise-grade FastAPI backend** with:
- ✅ User authentication (JWT + OAuth2)
- ✅ PostgreSQL database with 11 tables
- ✅ RESTful API v2 with 30+ endpoints
- ✅ File management with version history
- ✅ Code execution in 20+ languages
- ✅ AI chat integration (streaming & non-streaming)
- ✅ Session state persistence
- ✅ Professional error handling & logging
- ✅ Docker support for scalable deployment

## 5-Minute Setup

### 1. Prerequisites
```bash
# Check Python (need 3.11+)
python --version

# Check Docker (optional but recommended)
docker --version
```

### 2. Install Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Database
```bash
# Start PostgreSQL with Docker
docker run -d \
  --name nexusai-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=nexusai \
  -p 5432:5432 \
  postgres:15-alpine

# Wait 5 seconds for DB to start
sleep 5

# Run migrations
alembic upgrade head
```

### 4. Configure Environment
```bash
# Copy template
cp .env.example .env

# Edit .env (optional - defaults work with local setup):
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/nexusai
# DEBUG=true
# OPENROUTER_API_KEY=your-key-if-you-have-ai
```

### 5. Start Server
```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Test It
```bash
# Terminal 1: Keep server running
# uvicorn app.main:app --reload

# Terminal 2: Test endpoints
# Register user
curl -X POST http://localhost:8000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123"
  }'

# You'll get:
# {
#   "access_token": "eyJ0eXAi...",
#   "refresh_token": "eyJ0eXAi...",
#   "token_type": "bearer",
#   "expires_in": 1800
# }

# Login
curl -X POST http://localhost:8000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 7. Open API Docs
```
http://localhost:8000/docs     # Interactive Swagger UI
http://localhost:8000/redoc    # Readable API documentation
http://localhost:8000/health   # Health check
```

## Docker Compose (One Command)

```bash
# From project root
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI server
│   ├── models.py            # Database models (11 tables)
│   ├── schemas.py           # Request/response validation
│   ├── core/
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # PostgreSQL async setup
│   │   └── security.py     # JWT authentication
│   └── api/v2/             # REST API endpoints
│       ├── auth.py         # User registration/login
│       ├── projects.py     # Project management
│       ├── files.py        # File CRUD & versioning
│       ├── code_execution.py # Code runner
│       ├── chat.py         # AI chat endpoints
│       └── session.py      # Session management
├── migrations/              # Database version control
│   ├── alembic.ini
│   ├── env.py
│   └── versions/001_initial_schema.py
├── tests/                   # Unit + integration tests
├── requirements.txt         # Python dependencies
├── .env.example            # Configuration template
├── README.md               # Full documentation
└── setup.sh                # Auto-setup script
```

---

## Key Features Explained

### Authentication
```python
# Token-based (JWT)
# - Access token: 30-minute expiration
# - Refresh token: 7-day expiration
# - bcrypt password hashing
# - OAuth2 compatible
```

### Database
```python
# PostgreSQL with SQLAlchemy ORM
# 11 tables: users, organizations, projects, files, versions,
#            sessions, code_executions, audit_logs, secrets, etc.
# Automatic indexing for performance
# JSONB support for flexible data
```

### REST API
```python
# 30+ endpoints across 5 domains:
# - Authentication (/api/v2/auth)
# - Projects (/api/v2/projects)
# - Files (/api/v2/projects/{id}/files)
# - Code (/api/v2/projects/{id}/code)
# - Chat (/api/v2/projects/{id}/chat)
# - Sessions (/api/v2/session)

# All endpoints are:
# - Type-safe (Pydantic validation)
# - Well-documented (OpenAPI)
# - Async (high concurrency)
# - Authenticated (JWT required)
```

### Code Execution
```python
# Supports:
# Python, JavaScript, TypeScript, Ruby, PHP, Go, Bash, Perl, Lua
# Java, C++, C, C#, Rust (compiled)
# HTML, CSS, JSON, SQL, XML, YAML (markup)

# Features:
# - 60-second timeout protection
# - Output + error capture
# - Execution history
# - Stdin support for interactive programs
```

### AI Chat
```python
# - Streaming responses (SSE)
# - Multiple model support (LiteLLM)
# - Chat history persistence
# - Code context injection
# - Automatic error handling
```

### Session Management
```python
# Persistent user state:
# - Chat history (100 messages)
# - Code context
# - Execution errors
# - Session expiration (24 hours default)
# - Auto-cleanup of expired sessions
```

---

## Common Tasks

### Register a User
```bash
curl -X POST http://localhost:8000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "password123"
  }'
```

### Create a Project
```bash
# First, get your token from login
TOKEN="your-access-token-here"

curl -X POST http://localhost:8000/api/v2/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "description": "Test project"
  }'
```

### Execute Code
```bash
curl -X POST http://localhost:8000/api/v2/projects/{project_id}/code/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "language": "python"
  }'
```

### Stream AI Response
```bash
curl -X POST http://localhost:8000/api/v2/projects/{project_id}/chat/stream \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "How do I read a file in Python?"}
    ]
  }'
```

---

## Testing

### Run All Tests
```bash
cd backend
pytest
```

### With Coverage
```bash
pytest --cov=app tests/
```

### Specific Test File
```bash
pytest tests/test_auth.py -v
```

---

## Troubleshooting

### "Connection refused"
```bash
# PostgreSQL not running
docker ps  # See if nexusai-postgres is running
docker start nexusai-postgres  # Start if stopped
```

### "Port 8000 already in use"
```bash
# Kill existing process
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8001
```

### "ModuleNotFoundError"
```bash
# Activate virtual environment
source venv/bin/activate  # Unix
venv\Scripts\activate      # Windows
```

### "Alembic migration error"
```bash
# Reset migrations (careful!)
rm migrations/versions/*.py
alembic upgrade head
```

---

## Performance Tips

1. **Use async operations** - The API is optimized for async
2. **Connection pooling** - Automatic, 20 connections default
3. **Request logging** - See response times in console
4. **Index usage** - 20+ indexes on query paths

---

## Security Checklist

Before production:
- [ ] Change `SECRET_KEY` in `.env`
- [ ] Set `DEBUG=false`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `CORS_ORIGINS` for your domain
- [ ] Use strong database password
- [ ] Enable HTTPS/TLS
- [ ] Set up Sentry for error tracking
- [ ] Enable rate limiting
- [ ] Review audit logs regularly

---

## Next Steps

1. **Test the backend**: Run the quick setup above
2. **Connect frontend**: Update frontend to use `/api/v2/` endpoints
3. **Add AI key**: Get `OPENROUTER_API_KEY` for AI chat
4. **Deploy**: Use docker-compose or Kubernetes
5. **Monitor**: Set up Sentry, Prometheus, and Grafana (Phase 7)

---

## Documentation

- **Full API:** backend/README.md
- **Framework:** https://fastapi.tiangolo.com
- **Database:** https://sqlalchemy.org
- **Auth:** https://fastapi.tiangolo.com/tutorial/security/
- **Deployment:** backend/README.md#DevOps

---

## Getting Help

1. Check the OpenAPI docs at `http://localhost:8000/docs`
2. Read endpoint docstrings (hover in Swagger UI)
3. Check implementation status: `IMPLEMENTATION_STATUS.md`
4. Review error messages in console logs

---

**🎉 You now have a professional-grade API backend!**

Next phase (Phase 2): Real-time features with WebSockets
