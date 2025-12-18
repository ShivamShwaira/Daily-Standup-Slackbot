# 🚀 Quick Start Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for containerized deployment)
- Slack Workspace with bot creation permissions

## 1️⃣ Setup Slack App

### Create the App
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Daily Standup Bot"
4. Select your workspace

### Configure OAuth & Permissions

**Add these Bot Token Scopes** under "OAuth & Permissions":
```
chat:write
chat:write.public
chat:write.customize
im:history
im:write
channels:read
users:read
```

### Get Your Credentials
1. Copy **Bot Token** (starts with `xoxb-`)
2. Go to "Basic Information" and copy **Signing Secret**
3. Enable **Event Subscriptions** and set Request URL (you'll set this later after deployment)

## 2️⃣ Configure Environment

```bash
cd d:\DailyStandupBot\slack
cp .env.example .env
```

Edit `.env` with your values:
```env
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_DEFAULT_CHANNEL=C0XXXXXXXXXXX    # Report channel ID
DATABASE_URL=postgresql+asyncpg://standup_user:standup_password@localhost:5432/standup_db
DEFAULT_STANDUP_TIME=09:00              # When to send standup DMs
SCHEDULER_TIMEZONE=America/New_York     # Your timezone
ENV=dev
LOG_LEVEL=INFO
ADMIN_TOKEN=your-secret-admin-token     # Long random string
```

### Get Channel ID
In Slack: Right-click channel → Copy link → Extract ID from URL  
(e.g., `C0XXXXXXXXXXX`)

## 3️⃣ Local Development Setup

### Option A: Using Docker (Recommended)

```bash
# Build and start services
docker-compose up -d --build

# Check logs
docker-compose logs -f app

# Migrations run automatically on startup
```

Access at: http://localhost:8000

### Option B: Manual Python Setup

```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate        # Linux/Mac
# OR
venv\Scripts\activate           # Windows

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL (requires Docker)
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Start the app
uvicorn app.main:app --reload
```

Access at: http://localhost:8000

## 4️⃣ Verify Installation

### Check Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "scheduler_running": true
}
```

### Check Readiness
```bash
curl http://localhost:8000/ready
```

## 5️⃣ Add Your First User

### Via API
```bash
curl -X POST http://localhost:8000/admin/users \
  -H "X-Admin-Token: your-secret-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "slack_user_id": "U0XXXXXXXXX",
    "display_name": "Your Name",
    "email": "you@example.com",
    "timezone": "America/New_York"
  }'
```

### Get Your Slack User ID
In Slack: Click your profile → Copy user ID  
(Format: `U0XXXXXXXXX`)

### List All Users
```bash
curl http://localhost:8000/admin/users \
  -H "X-Admin-Token: your-secret-admin-token"
```

## 6️⃣ Configure Slack Events (if deployed)

Once your app is running on a public URL:

1. Go to Slack App settings → Event Subscriptions
2. Enable Events: ON
3. Request URL: `https://your-domain.com/slack/events`
4. Subscribe to Bot Events:
   - `message.im` (direct messages)
   - `app_mention` (mentions)

## 7️⃣ Test the Bot

### Manual Trigger (Staging)
For testing without waiting for scheduler:

```bash
python -c "
import asyncio
from app.db.base import async_session
from app.services.scheduler import dispatch_pending_standups

asyncio.run(dispatch_pending_standups())
"
```

### Real-time Monitoring
```bash
# Watch logs
docker-compose logs -f app

# Or in local dev
# Terminal already shows logs with --reload
```

## 📊 Database

### Run Migrations
```bash
alembic upgrade head
```

### Create New Migration (after model changes)
```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

### Downgrade Last Migration
```bash
alembic downgrade -1
```

### Access Database Directly
```bash
docker-compose exec postgres psql -U standup_user -d standup_db

# List tables
\dt

# Exit
\q
```

## 🧪 Run Tests

```bash
pytest tests/ -v

# Specific test
pytest tests/test_standup_flow.py::TestUserService::test_create_user -v

# With coverage
pytest --cov=app tests/
```

## 📝 Admin Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| POST | `/admin/users` | Create user |
| GET | `/admin/users` | List users |
| GET | `/admin/users/{id}` | Get user |
| PATCH | `/admin/users/{id}` | Update user |
| DELETE | `/admin/users/{id}` | Delete user |
| GET | `/admin/metrics` | Get metrics |
| PATCH | `/admin/settings` | Update settings |

All admin endpoints require `X-Admin-Token` header.

## 🐛 Troubleshooting

### Bot not sending DMs
```bash
# Check logs
docker-compose logs app | grep "send_dm"

# Verify token
echo "SLACK_BOT_TOKEN: " && grep SLACK_BOT_TOKEN .env

# Verify bot is in workspace
# In Slack: @-mention the bot to confirm
```

### Database connection error
```bash
# Check if Postgres is running
docker-compose ps

# Check database URL is correct
grep DATABASE_URL .env

# Reset database
docker-compose down -v postgres
docker-compose up -d postgres
alembic upgrade head
```

### Scheduler not running
```bash
curl http://localhost:8000/health
# Check scheduler_running: true

# If false, check logs
docker-compose logs app | grep "APScheduler"
```

### Port already in use
```bash
# Change port in docker-compose.yml or uvicorn command
# Default: 8000 for app, 5432 for Postgres
```

## 🚀 Production Deployment

### Pre-deployment Checklist
- [ ] `.env` with production secrets (from Secrets Manager)
- [ ] `ADMIN_TOKEN` is a long, random string
- [ ] `DATABASE_URL` points to production Postgres
- [ ] `ENV=prod`
- [ ] `LOG_LEVEL=WARNING` (less verbose)
- [ ] Slack app Request URL configured to your domain
- [ ] HTTPS enabled on your domain

### Deploy with Docker
```bash
# Build image
docker build -t daily-standup-bot:latest .

# Push to registry (AWS ECR, Docker Hub, etc.)
docker tag daily-standup-bot:latest your-registry/daily-standup-bot:latest
docker push your-registry/daily-standup-bot:latest

# Or deploy with docker-compose
docker-compose -f docker-compose.yml up -d
```

### Scale Multiple Instances
For multiple app instances behind a load balancer:
1. Use APScheduler SQLAlchemy job store (see TODO in `scheduler.py`)
2. Or use Celery + Redis for distributed jobs (recommended)
3. See comments in code for production scaling guidance

## 📚 Documentation

- [README.md](README.md) — Full feature docs and architecture
- [PROJECT_GENERATION_SUMMARY.md](PROJECT_GENERATION_SUMMARY.md) — What was generated

## 🆘 Support

1. Check logs: `docker-compose logs -f app`
2. Check database: `docker-compose exec postgres psql -U standup_user -d standup_db`
3. Review code comments marked with `# TODO:` for known limitations
4. See README.md Production Considerations section

---

**You're all set!** Your Daily Standup Bot is ready. 🎉

Next: Add users via the admin API and watch them get DMs at the configured time!
