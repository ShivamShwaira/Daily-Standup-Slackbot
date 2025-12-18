# Daily Standup Bot

A production-ready Slack standup bot built with FastAPI, SQLAlchemy (async), APScheduler, and Slack Bolt for Python. Inspired by GeekBot, this bot automates daily standup collection via DMs, compiles responses, and posts them to a configured channel.

## Features

- **Automated Scheduling**: Sends DMs to users every workday at a configured time
- **Multi-Question Flow**: Asks "How are you feeling?", "What did you do yesterday?", "What are you doing today?", and "Any blockers?"
- **Instant Report Posting**: Compiles and posts user reports immediately upon completion
- **Skip & Catch-Up**: Users can skip standups; bot detects missed standups and asks for combined updates
- **Timezone Support**: Per-user timezone configuration
- **Admin API**: Endpoints to manage users, settings, and view metrics
- **Async-First**: Full async FastAPI backend with asyncpg and SQLAlchemy AsyncSession
- **Docker Ready**: Includes Dockerfile and docker-compose for easy deployment
- **Database Migrations**: Alembic for version-controlled schema changes
- **Comprehensive Tests**: pytest fixtures and test cases with mocking

## Architecture

```
app/
├── main.py                 # FastAPI entrypoint & Slack Bolt mounting
├── config.py              # Pydantic BaseSettings for environment
├── logging_config.py      # Logging setup
├── db/                    # Database layer
│   ├── base.py           # AsyncEngine, AsyncSession factories
│   ├── models.py         # SQLAlchemy ORM models
│   └── repository.py     # Async CRUD operations (repository pattern)
├── schemas/              # Pydantic models for request/response
│   ├── user.py
│   └── standup.py
├── slack/                # Slack integration
│   ├── bolt_app.py       # AsyncApp instance & client management
│   ├── handlers.py       # Message & interaction event handlers
│   └── messages.py       # Block Kit message builders
├── services/             # Business logic layer
│   ├── scheduler.py      # APScheduler job definitions
│   ├── standup_service.py # Standup workflow orchestration
│   └── user_service.py   # User management
├── api/                  # HTTP API endpoints
│   ├── admin_routes.py   # User/settings management
│   └── health.py         # Health & readiness checks
├── utils/                # Helper functions
│   ├── timeutils.py      # Timezone & date utilities
│   └── slack_utils.py    # Slack API helpers
└── tests/                # Test suite
    └── test_standup_flow.py
```

## Database Schema

### Workspaces (Optional)
- `id` (PK)
- `slack_team_id` (unique)
- `report_channel_id`
- `default_time`
- `timezone`
- `created_at`, `updated_at`

### Users
- `id` (PK)
- `slack_user_id` (unique)
- `display_name`
- `email` (nullable)
- `timezone` (nullable)
- `active` (bool)
- `created_at`, `updated_at`

### StandupReports
- `id` (PK)
- `user_id` (FK)
- `report_date` (date, unique per user per date)
- `feeling` (text, nullable)
- `yesterday` (text, nullable)
- `today` (text, nullable)
- `blockers` (text, nullable)
- `skipped` (bool)
- `completed_at` (timestamp, nullable)
- `created_at`, `updated_at`

### StandupStates
- `id` (PK)
- `user_id` (FK, unique)
- `pending_report_date` (date)
- `current_question_index` (int, 0-3)
- `created_at`, `updated_at`

## Setup & Installation

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized setup)
- PostgreSQL (or use docker-compose)
- Slack App & Bot Token

### Local Development (Without Docker)

1. **Clone and navigate to the project:**
   ```bash
   cd d:\DailyStandupBot\slack
   ```

2. **Create a Python virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Slack credentials and database URL
   ```

5. **Run PostgreSQL locally** (or use docker-compose for just the DB):
   ```bash
   docker-compose up -d postgres
   ```

6. **Run Alembic migrations:**
   ```bash
   alembic upgrade head
   ```

7. **Run the app:**
   ```bash
   uvicorn app.main:app --reload
   ```

   The app will be available at `http://localhost:8000`.

### Production Deployment (Docker Compose)

1. **Prepare environment:**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Build and start services:**
   ```bash
   docker-compose up -d --build
   ```

3. **Run migrations (one-time or on new versions):**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

4. **Check logs:**
   ```bash
   docker-compose logs -f app
   ```

## Slack App Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app
2. Choose "From scratch" and name it "Daily Standup Bot"
3. Select your workspace

### 2. Configure OAuth & Permissions

**Scopes needed (Bot Token Scopes):**
- `chat:write` — post messages to channels and DMs
- `chat:write.public` — post to public channels
- `chat:write.customize` — customize bot appearance
- `im:history` — read message history in DMs
- `im:write` — send DMs
- `channels:read` — list channels
- `users:read` — fetch user info
- `commands` — support slash commands (future)

**Redirect URL for OAuth (if needed):**
- `https://your-domain.com/slack/oauth_redirect` (if implementing OAuth flow)

### 3. Set Event Subscriptions

1. Enable Events
2. Request URL: `https://your-domain.com/slack/events`
3. Subscribe to bot events:
   - `message.im` — direct messages
   - `app_mention` — mentions
4. Subscribe to workspace events (optional):
   - `team_join` — new user detection

### 4. Install App to Workspace

Go to "Install App" and authorize it.

### 5. Copy Bot Token and Signing Secret

- Bot Token: `xoxb-...` → set as `SLACK_BOT_TOKEN` in `.env`
- Signing Secret: found under "Basic Information" → set as `SLACK_SIGNING_SECRET` in `.env`

### 6. Configure Slash Command (Optional)

If you want to support `/standup submit` for manual submissions:
1. Create a slash command `/standup`
2. Request URL: `https://your-domain.com/slack/commands/standup`

## Configuration

Edit `.env` or set environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | *(required)* | Slack bot OAuth token |
| `SLACK_SIGNING_SECRET` | *(required)* | Slack signing secret |
| `SLACK_DEFAULT_CHANNEL` | *(required)* | Report channel ID (e.g., `C01234567890`) |
| `DATABASE_URL` | `postgresql+asyncpg://standup_user:standup_password@localhost:5432/standup_db` | Async SQLAlchemy DB URL |
| `DEFAULT_STANDUP_TIME` | `09:00` | Default daily standup time (HH:MM format) |
| `SCHEDULER_TIMEZONE` | `America/New_York` | Timezone for scheduler |
| `ENV` | `dev` | Environment: `dev` or `prod` |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `ADMIN_TOKEN` | *(required for admin endpoints)* | Bearer token for admin API |

## API Endpoints

### Health Checks

- `GET /health` — Application health status
- `GET /ready` — Readiness probe (DB connectivity)

### Admin Endpoints (Require `X-Admin-Token` header)

- `POST /admin/users` — Add a user
  ```json
  {
    "slack_user_id": "U123456",
    "display_name": "John Doe",
    "email": "john@example.com",
    "timezone": "America/New_York"
  }
  ```

- `GET /admin/users` — List all active users

- `PATCH /admin/users/{user_id}` — Update user (timezone, active status)

- `DELETE /admin/users/{user_id}` — Remove user

- `GET /admin/metrics` — Get standup completion metrics

- `PATCH /admin/settings` — Update workspace settings (time, channel, timezone)

## Slack Workflow

### User Flow

1. **Scheduler triggers** → checks for users without a report for today
2. **DM sent** → Q1: "How are you feeling?" with [Skip Today] button
3. **User responds** → answer recorded, Q2 shown
4. **Q2 & Q3 answered** → report compiled and posted to channel
5. **Skip button** → creates skipped report, optionally posts notification

### Missed Standup Handling

- If user doesn't respond by day end, bot skips them for that day
- Next day, when scheduler detects a missed report:
  - Asks: "Looks like you missed your last report on YYYY-MM-DD. What did you do since then?"
  - User replies → combined answer recorded as "yesterday" field
  - Follow normal flow for remaining questions

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

Tests use `pytest-asyncio` and mock Slack API calls to avoid external dependencies.

## Development Workflow

### Add a New User

```bash
curl -X POST http://localhost:8000/admin/users \
  -H "X-Admin-Token: your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "slack_user_id": "U123456",
    "display_name": "Jane Smith",
    "timezone": "America/Los_Angeles"
  }'
```

### Update Standup Time

```bash
curl -X PATCH http://localhost:8000/admin/settings \
  -H "X-Admin-Token: your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "default_time": "10:30",
    "timezone": "America/Chicago"
  }'
```

### Manually Trigger Scheduler

For testing, run:

```bash
python -c "
import asyncio
from app.services.standup_service import dispatch_pending_standups
from app.db.base import async_session
asyncio.run(dispatch_pending_standups(async_session))
"
```

## Migration Management

Alembic is configured to auto-detect model changes.

### Create a migration

```bash
alembic revision --autogenerate -m "describe your change"
```

### Apply migrations

```bash
alembic upgrade head
```

### Downgrade (if needed)

```bash
alembic downgrade -1
```

## Logging

- Logs are output to `stdout` (JSON format in production, human-readable in dev)
- Log level controlled by `LOG_LEVEL` environment variable
- Structured logging for key events: user registration, report submission, scheduler runs

## Production Considerations

### Horizontal Scaling (Multiple App Instances)

Currently, APScheduler uses an in-memory scheduler. For multiple instances:

1. **Recommended**: Use **Celery** with **Redis** for job queue
   - Each instance can safely process jobs
   - Redis handles distributed locks

2. **Alternative**: Use APScheduler's **SQLAlchemy job store**
   - Configure in `app/services/scheduler.py`
   - Adds one extra job-lookup query per schedule interval
   - See TODO comments in code

### Secrets Management

- Use **AWS Secrets Manager**, **Google Secret Manager**, or **HashiCorp Vault**
- Never commit `.env` to version control
- Rotate tokens regularly

### Database Backups

- Set up automated PostgreSQL backups (AWS RDS, GCP Cloud SQL, or manual snapshots)
- Test restore procedures

### Monitoring & Alerts

- Use APM tools (Datadog, New Relic, or similar)
- Monitor scheduler health: `GET /health` should check job queue size
- Set alerts for failed DM sends or report posting

### Rate Limiting

- Slack API rate limits: ~60 requests/minute per workspace
- The bot batches user fetches but sends one DM per user per day
- Add rate limiting middleware in `main.py` if needed

### Security Notes

- **Verify Slack requests** using `SignatureVerifier` (Slack Bolt handles this)
- **Admin endpoints** are protected with `X-Admin-Token` header — use a long, random token in production
- **Database credentials** should be in secrets manager, not in `.env` on production servers
- **HTTPS only** in production — Slack requires it

## Troubleshooting

### Bot not sending DMs

1. Check `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are correct
2. Verify bot is invited to DM users (usually automatic)
3. Check logs: `docker-compose logs app | grep "send_dm"`
4. Ensure scheduler is running: check logs for `APScheduler started`

### Database connection fails

1. Verify `DATABASE_URL` is correct
2. Check PostgreSQL is running: `docker-compose ps`
3. Run migrations: `alembic upgrade head`
4. Test connection: `docker-compose exec app python -c "from app.db.base import engine; print(engine)"`

### Reports not posted to channel

1. Verify `SLACK_DEFAULT_CHANNEL` is the correct channel ID (starts with `C`)
2. Check bot has `chat:write` permission in that channel
3. See logs for `post_standup_report` errors

## License

MIT
