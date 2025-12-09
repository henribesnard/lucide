# Lucide Docker Setup Guide

## Overview

This guide explains how to deploy Lucide using Docker with PostgreSQL for user management and conversation history, and Redis for caching.

## Architecture

The Lucide application consists of 4 Docker containers:

1. **PostgreSQL** - Database for users and conversations
2. **Redis** - Caching and session management
3. **Backend** - FastAPI application
4. **Frontend** - Next.js application

## Prerequisites

- Docker Desktop installed
- Docker Compose installed
- API keys for:
  - API-Football
  - DeepSeek (or OpenAI)

## Quick Start

### 1. Clone and Navigate to Project

```bash
cd C:\Users\henri\Projets\lucide
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
copy .env.example .env
```

Edit `.env` and set your API keys:

```env
# Required API Keys
API_FOOTBALL_KEY=your-api-football-key-here
DEEPSEEK_API_KEY=your-deepseek-api-key-here

# Security (generate secure random strings)
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Email (optional, for email verification)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Build and Start Services

```bash
docker-compose up --build
```

This will:
- Build the backend and frontend images
- Start PostgreSQL and Redis
- Initialize the database
- Start all services

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    subscription_start_date TIMESTAMP,
    subscription_end_date TIMESTAMP,
    trial_end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    verification_token VARCHAR(255),
    verification_token_expires TIMESTAMP
);
```

### Conversations Table

```sql
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    title VARCHAR(255),
    is_archived BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Messages Table

```sql
CREATE TABLE messages (
    message_id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(conversation_id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(100),
    tools_used TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_id": "uuid-here",
  "is_active": true,
  "is_verified": false,
  "subscription_tier": "free",
  "subscription_status": "active",
  "created_at": "2025-12-06T...",
  "verification_url": "http://localhost:3000/verify-email?token=..."
}
```

#### Verify Email
```http
POST /auth/verify-email
Content-Type: application/json

{
  "token": "verification-token-from-email"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid-here",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_verified": true,
    "subscription_tier": "free"
  }
}
```

### Conversations (Requires Authentication)

All conversation endpoints require the `Authorization: Bearer <token>` header.

#### Create Conversation
```http
POST /conversations
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Match Analysis"
}
```

#### List Conversations
```http
GET /conversations?archived=false
Authorization: Bearer <access_token>
```

#### Get Conversation with Messages
```http
GET /conversations/{conversation_id}
Authorization: Bearer <access_token>
```

#### Update Conversation
```http
PATCH /conversations/{conversation_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "New Title",
  "is_archived": true
}
```

#### Delete Conversation
```http
DELETE /conversations/{conversation_id}
Authorization: Bearer <access_token>
```

### Chat Endpoint

The existing chat endpoint remains available for backward compatibility. In the future, it will be integrated with conversation management.

```http
POST /chat
Content-Type: application/json

{
  "message": "Analyse le match PSG vs Marseille",
  "session_id": "optional-session-id"
}
```

## Development Workflow

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Accessing Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U lucide_user -d lucide_db

# Run queries
\dt  # List tables
SELECT * FROM users;
SELECT * FROM conversations;
SELECT * FROM messages;
```

### Accessing Redis

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Redis commands
KEYS *
GET key_name
```

### Rebuilding Containers

```bash
# Rebuild after code changes
docker-compose up --build

# Rebuild specific service
docker-compose up --build backend
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Email Verification Setup

For email verification to work, you need to configure SMTP settings:

### Gmail Example

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Create a new app password
   - Copy the password

3. Update `.env`:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

### Development Mode (No Email)

If SMTP is not configured, verification URLs will be logged to the backend console instead of being sent via email.

## Security Considerations

### Production Deployment

For production, update the following in `.env`:

1. Generate secure random keys:
```bash
# Linux/Mac
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

2. Update `.env`:
```env
SECRET_KEY=your-generated-secure-key
JWT_SECRET=your-generated-jwt-secret
DEBUG=false
```

3. Update CORS in `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

4. Use environment-specific docker-compose files:
```bash
docker-compose -f docker-compose.prod.yml up
```

## Troubleshooting

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker-compose ps

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Backend Fails to Start

```bash
# Check logs
docker-compose logs backend

# Verify environment variables
docker-compose exec backend env | grep DATABASE_URL

# Rebuild
docker-compose up --build backend
```

### Frontend Can't Connect to Backend

1. Check if backend is running:
```bash
curl http://localhost:8000/health
```

2. Verify `NEXT_PUBLIC_API_URL` in frontend `.env`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database Migrations

If you need to reset the database:

```bash
# Stop services
docker-compose down

# Remove volumes
docker volume rm lucide_postgres_data

# Restart
docker-compose up
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "llm_provider": "deepseek",
  "llm_model": "deepseek-chat"
}
```

### Database Connection

```bash
# Check active connections
docker-compose exec postgres psql -U lucide_user -d lucide_db -c "SELECT count(*) FROM pg_stat_activity;"
```

## Next Steps

1. Implement frontend authentication UI (login, register pages)
2. Add conversation history to sidebar
3. Integrate chat endpoint with conversation persistence
4. Add user profile management
5. Implement subscription tier features
6. Add analytics and usage tracking

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review API docs: http://localhost:8000/docs
- Verify environment variables in `.env`
