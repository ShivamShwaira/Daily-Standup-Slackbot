# 🏗️ Architecture & Design Decisions

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   SLACK WORKSPACE                            │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   User DMs       │         │ Report Channel   │          │
│  └────────┬─────────┘         └────────▲─────────┘          │
│           │                           │                      │
│           │ message.im events         │ post_message         │
└───────────┼───────────────────────────┼──────────────────────┘
            │                           │
            └───┬───────────────────────┘
                │
                │ HTTPS
                │
    ┌───────────▼──────────────┐
    │  FastAPI Application     │
    │  ┌────────────────────┐  │
    │  │  Slack Bolt        │  │
    │  │  AsyncApp          │  │
    │  └──────────┬─────────┘  │
    │             │            │
    │  ┌──────────▼──────────┐ │
    │  │  Event Handlers    │ │
    │  │  & Message Builders│ │
    │  └────────────────────┘ │
    │             │            │
    │  ┌──────────▼──────────┐ │
    │  │ Standup Service    │ │
    │  │ & User Service     │ │
    │  └────────────────────┘ │
    │             │            │
    │  ┌──────────▼──────────┐ │
    │  │ Repository Layer   │ │
    │  │ (async CRUD ops)   │ │
    │  └────────────────────┘ │
    │             │            │
    │  ┌──────────▼──────────┐ │
    │  │ APScheduler        │ │
    │  │ (Daily Job)        │ │
    │  └────────────────────┘ │
    └────────────┬─────────────┘
                 │
                 │
    ┌────────────▼──────────────┐
    │  PostgreSQL Database      │
    │  ┌────────────────────┐   │
    │  │ users              │   │
    │  │ workspaces         │   │
    │  │ standup_reports    │   │
    │  │ standup_states     │   │
    │  └────────────────────┘   │
    └───────────────────────────┘
```

## Component Responsibilities

### 1. **Slack Bolt Integration** (`app/slack/`)
- **bolt_app.py**: AsyncApp instance, credentials, client management
- **handlers.py**: Event listeners for messages and button interactions
- **messages.py**: Block Kit builders for DM and channel messages

### 2. **Services Layer** (`app/services/`)
- **standup_service.py**: Core standup workflow orchestration
  - `send_pending_standups()`: Daily job to dispatch standups
  - `handle_user_answer()`: Process DM responses
  - `handle_skip_today()`: Skip workflow
  - `post_report_to_channel()`: Format and post compiled report
  
- **user_service.py**: User CRUD operations
  - Create/read/update/delete users
  - Deactivate (pause) users
  
- **scheduler.py**: APScheduler configuration
  - Initialize AsyncIOScheduler
  - Register daily job
  - Startup/shutdown management

### 3. **Repository Layer** (`app/db/repository.py`)
All database operations are async and follow the repository pattern:
- **UserRepository**: User CRUD, list active users
- **StandupReportRepository**: Report creation, retrieval, completion
- **StandupStateRepository**: State management (question tracking)
- **WorkspaceRepository**: Workspace settings

### 4. **Database Models** (`app/db/models.py`)
- **User**: Slack user registration with timezone
- **StandupReport**: Daily report with unique(user_id, report_date)
- **StandupState**: Tracks pending standup progress
- **Workspace**: Workspace config (time, channel, timezone)

### 5. **API Routes** (`app/api/`)
- **health.py**: `/health` and `/ready` endpoints
- **admin_routes.py**: User management, settings, metrics
  - Protected with X-Admin-Token header

### 6. **Utilities** (`app/utils/`)
- **timeutils.py**: Timezone conversions, date calculations
- **slack_utils.py**: Message formatting, user mentions, entity escaping

## Data Flow

### Daily Standup Dispatch

```
APScheduler Job (9:00 AM daily, weekdays)
    ↓
standup_service.send_pending_standups()
    ├─ Fetch all active users
    ├─ For each user:
    │  ├─ Get user's timezone (default to scheduler TZ)
    │  ├─ Check if report exists for today in user's TZ
    │  └─ If not:
    │     ├─ Check for missed reports from previous days
    │     ├─ If missed: send catch-up message with date context
    │     └─ If new: send initial standup DM
    └─ Create StandupState with question_index=0
```

### User Responds to Question

```
Slack message.im event
    ↓
handlers.handle_message()
    ├─ Extract user ID and text
    ├─ Call standup_service.handle_user_answer()
    │  ├─ Get StandupState for user
    │  ├─ Get/create StandupReport for pending date
    │  ├─ Store answer in report
    │  ├─ Increment question_index
    │  └─ If all questions answered:
    │     ├─ Mark report completed_at
    │     ├─ Delete state
    │     └─ Return action: "complete_report"
    │
    └─ If more questions:
       └─ Send next question DM
       
    └─ If all answered:
       └─ Post compiled report to channel
```

### Skip Today Flow

```
Button click: "Skip Today"
    ↓
handlers.handle_skip_button()
    ├─ Acknowledge interaction
    ├─ Call standup_service.handle_skip_today()
    │  ├─ Create StandupReport with skipped=True
    │  ├─ Delete StandupState
    │  └─ If configured: post skip notification to channel
    └─ Send confirmation DM
```

## Design Decisions

### 1. **Async Throughout**
- **Why**: Slack API, database, and HTTP are I/O bound
- **How**: AsyncSession, AsyncApp, async/await everywhere
- **Benefit**: Thousands of concurrent users without thread overhead

### 2. **Repository Pattern**
- **Why**: Centralize DB logic, easy to mock for tests
- **How**: Base class + specific repos (User, Report, State)
- **Benefit**: Testable, DRY, single responsibility

### 3. **State Machine for Questions**
- **Why**: Need to track user progress across async messages
- **How**: StandupState table with `current_question_index`
- **Benefit**: Resilient to bot restarts, recoverable state

### 4. **Unique Constraint on (user_id, report_date)**
- **Why**: One report per user per calendar day
- **How**: SQLAlchemy UniqueConstraint at DB level
- **Benefit**: Data integrity, no accidental duplicates

### 5. **Timezone Awareness**
- **Why**: Users in different timezones need local time standups
- **How**: Per-user timezone + scheduler timezone
- **Benefit**: "09:00" means 9 AM in user's local time

### 6. **Missed Standup Detection**
- **Why**: Users may not respond same day; need to catch up
- **How**: Compare latest report date with today; if gap, show catch-up message
- **Benefit**: Never lose standup data, support async workflows

### 7. **APScheduler with Cron Triggers**
- **Why**: Simple, reliable scheduling with timezone support
- **How**: CronTrigger for weekdays at configured time
- **Benefit**: No external job queue needed (for single-instance)
- **TODO**: For multi-instance, use Celery + Redis

### 8. **Block Kit for UI**
- **Why**: Rich, interactive Slack experience without JavaScript
- **How**: Python dict builders that return valid Block Kit JSON
- **Benefit**: Professional UX, buttons, formatted text

### 9. **Pydantic v2**
- **Why**: Type validation, JSON serialization, IDE support
- **How**: BaseModel for all request/response schemas
- **Benefit**: Runtime validation, OpenAPI docs

### 10. **Docker + docker-compose**
- **Why**: Easy local dev + production consistency
- **How**: Dockerfile for app, docker-compose for app+Postgres
- **Benefit**: One-command setup, no environment surprises

## Error Handling Strategy

```
User Action
    ↓
Try-except in handler/service
    ├─ Log detailed error with context
    ├─ Send user-friendly message in DM
    └─ Return error dict to caller
```

Example:
```python
try:
    await handle_answer(user_id, text)
except UserNotFound:
    await send_dm(user_id, build_error_message("User not registered"))
except DatabaseError as e:
    logger.error(f"DB error: {e}")
    await send_dm(user_id, build_error_message("System error, please try again"))
```

## Security Considerations

1. **Slack Signing Secret**: Bolt validates all requests
2. **Admin Token**: X-Admin-Token header on protected endpoints
3. **Database Credentials**: Via .env (not in code)
4. **User Data**: Slack user IDs, not stored emails
5. **Rate Limiting**: TODO in production (see code comments)

## Scalability Path

### Single Instance (Current)
- In-memory APScheduler
- SQLite or Postgres
- Suitable for small teams

### Multi-Instance (Future)
```
Load Balancer
    ├─ Instance 1 (no scheduler)
    ├─ Instance 2 (no scheduler)
    └─ Instance 3 (scheduler only)
         ↓
    Celery + Redis
         ↓
    Distributed job queue
    (Each job acquired by one worker)
```

Or use APScheduler SQLAlchemy job store (less ideal but simpler).

## Testing Strategy

### Unit Tests
- Mock Slack client
- In-memory SQLite database
- Test services in isolation

### Integration Tests
- Use docker-compose for full stack
- Test Slack → DB → Channel flow
- Verify scheduler triggers

### Manual Testing
- Deploy to staging
- Configure test Slack workspace
- Run standups through manually

## Monitoring & Observability

### Logs
- Structured logging (JSON in prod)
- Key events: user creation, report submission, errors
- Log level configurable via ENV

### Health Checks
- `/health` endpoint: app status, scheduler status
- `/ready` endpoint: database connectivity
- Use in Kubernetes liveness/readiness probes

### Metrics (TODO)
- User count, report completion rate
- Average response time
- Failed DM sends
- Database query timing

### Alerting (TODO)
- Missing reports for users
- Scheduler job failures
- Database connection issues
- Slack API quota warnings
