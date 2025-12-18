# User Onboarding & Subscription Workflow

## Overview

When the Daily Standup Bot is installed to a Slack workspace, it implements a **3-phase onboarding flow** to enable a frictionless user experience:

1. **Workspace Installation** - Initialize workspace in database
2. **User Opt-In** - Users subscribe via slash command
3. **Scheduled Standups** - Bot sends standups only to subscribed, active users

## Phase 1: Workspace Installation

### What Happens
When the bot is installed to a Slack workspace:

```
┌─────────────────────────────────┐
│  Bot Installed to Workspace     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  app_installed event triggered  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Create Workspace record in DB  │
│  - slack_team_id               │
│  - report_channel_id (default) │
│  - default_time: "09:00"       │
│  - timezone: "America/New_York"│
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Post welcome message to channel │
└─────────────────────────────────┘
```

**Handler**: `register_installation_handler()` in [app/slack/onboarding_handlers.py](app/slack/onboarding_handlers.py)

### Files Involved
- **Model**: [Workspace](app/db/models.py)
- **Repository**: [WorkspaceRepository](app/db/repository.py)
- **Service**: [workspace_service.py](app/services/workspace_service.py)

---

## Phase 2: User Opt-In (Subscription)

### Slash Commands

Users interact with the bot using the `/standup` command:

#### `/standup subscribe`
Subscribe to daily standups.

**What happens**:
1. Get or create workspace for the team
2. Fetch user info from Slack (display name, email)
3. Create User record in database with:
   - `workspace_id` (links to workspace)
   - `slack_user_id` (Slack user ID)
   - `display_name` (from Slack profile)
   - `email` (from Slack profile, optional)
   - `active = true` (enabled by default)
4. Confirm subscription to user

**Result**: User is added to database and will receive scheduled standups

```python
# Example flow
@app.command("/standup")
async def handle_standup_command(ack, body, respond, client):
    subcommand = body.get("text", "").strip().lower()  # "subscribe"
    user_id = body["user_id"]
    team_id = body["team_id"]
    
    # Create user in database
    workspace = await get_or_create_workspace(session, team_id, channel_id)
    user_create = UserCreate(slack_user_id=user_id, display_name=display_name)
    result = await create_user(session, workspace["workspace_id"], user_create)
    
    await respond("✅ You're subscribed to daily standups!")
```

#### `/standup unsubscribe`
Stop receiving standups (sets `active = false`, doesn't delete record).

```python
# User record is preserved, just marked inactive
await repo.update(user.id, active=False)
```

#### `/standup status`
Show count and list of current subscribers in the workspace.

#### `/standup help`
Show available commands.

### Handler
[register_onboarding_handlers()](app/slack/onboarding_handlers.py#L15) in `app/slack/onboarding_handlers.py`

---

## Phase 3: Scheduled Standups

### How It Works

1. **Scheduler starts** at app startup
   - Configured via `settings.default_standup_time` (default: "09:00")
   - Runs on weekdays only (Mon-Fri)
   - User timezone-aware

2. **Standup dispatch job runs** at scheduled time
   - Queries all **active** users in workspace
   - Checks if user has report for today
   - Sends initial standup prompt via DM
   - Creates StandupState record to track progress

3. **User responds** via multi-step interactive flow
   - Each step stored in StandupState
   - Culminates in StandupReport record

### Database Schema

```
workspaces
  ├── id (primary key)
  ├── slack_team_id (unique)
  ├── report_channel_id
  ├── default_time
  └── timezone

users (NEW workspace_id foreign key!)
  ├── id (primary key)
  ├── workspace_id ⭐ (foreign key → workspaces)
  ├── slack_user_id
  ├── display_name
  ├── email
  ├── active ⭐ (subscription status)
  ├── timezone
  ├── created_at
  └── updated_at
```

### Key Queries

```python
# Get active users in a workspace
users = await repo.list_active_by_workspace(workspace_id)

# Find user by Slack ID in specific workspace
user = await repo.get_by_slack_id_and_workspace(slack_user_id, workspace_id)

# Deactivate/unsubscribe
await repo.update(user.id, active=False)

# Reactivate/subscribe
await repo.update(user.id, active=True)
```

### Scheduler Code
[scheduler.py](app/services/scheduler.py) - APScheduler configuration
[standup_service.py](app/services/standup_service.py) - `send_pending_standups()`

---

## Data Flow Diagram

```
┌──────────────────────────────────────┐
│     Bot Installed to Workspace       │
└────────────────┬─────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │  app_installed │
        └────────┬───────┘
                 │
    ┌────────────▼──────────────┐
    │ Create Workspace Record   │
    │ in database               │
    └────────────┬──────────────┘
                 │
    ┌────────────▼──────────────────┐
    │ Post welcome message           │
    │ "Use /standup subscribe"       │
    └────────────┬──────────────────┘
                 │
┌────────────────▼─────────────────┐
│      User Types: /standup        │
│           subscribe              │
└────────────┬─────────────────────┘
             │
   ┌─────────▼─────────┐
   │ Fetch user from   │
   │ Slack API         │
   └─────────┬─────────┘
             │
   ┌─────────▼──────────────────┐
   │ Create User record         │
   │ - workspace_id             │
   │ - slack_user_id            │
   │ - display_name             │
   │ - active = true            │
   └─────────┬──────────────────┘
             │
   ┌─────────▼──────────────────┐
   │ Confirm subscription       │
   │ "You're subscribed!"       │
   └─────────┬──────────────────┘
             │
┌────────────▼────────────────────────┐
│  At 09:00 (default), scheduled job  │
│  checks active users                │
└────────────┬─────────────────────────┘
             │
   ┌─────────▼──────────────────┐
   │ Query active users:        │
   │ SELECT * FROM users        │
   │ WHERE workspace_id = X     │
   │ AND active = true          │
   └─────────┬──────────────────┘
             │
   ┌─────────▼──────────────────┐
   │ For each user:             │
   │ - Check if report exists   │
   │ - Send DM standup prompt   │
   │ - Create StandupState      │
   └────────────┬───────────────┘
                │
        ┌───────▼───────┐
        │ User responds │
        │ via buttons   │
        └───────┬───────┘
                │
        ┌───────▼───────────┐
        │ Create report     │
        │ Update state      │
        └───────────────────┘
```

---

## Important Notes

### ✅ What's Fixed
- **workspace_id foreign key** added to User model
- **Migration created** to add column to existing databases
- **UserRepository** updated to accept `workspace_id` on create
- **New methods** for querying users by workspace
- **Onboarding handlers** implement complete subscription flow

### ⚠️ Key Design Decisions
1. **Opt-in model**: Users must actively subscribe (not automatic)
2. **Soft delete**: Unsubscribing sets `active=false`, preserves history
3. **Workspace scoped**: Users are per-workspace (multi-team ready)
4. **Timezone aware**: Users can have individual timezones

### 🔧 Configuration
Edit workspace settings via admin endpoints:
```python
# Update workspace settings
await update_workspace(
    session,
    workspace_id=1,
    default_time="14:00",  # 2:00 PM
    timezone="America/Los_Angeles"
)
```

---

## Testing the Flow

### 1. Install bot to test workspace
- Go to Slack App settings
- Install to workspace

### 2. Subscribe a user
```
/standup subscribe
→ "✅ You're now subscribed to daily standups!"
```

### 3. Check subscribers
```
/standup status
→ Shows count and list of subscribers
```

### 4. Verify database
```bash
# Check users were created
SELECT * FROM users WHERE workspace_id = 1 AND active = true;
```

### 5. Test scheduler (optional, manual dispatch)
```bash
cd /workspace
uv run python -c "
import asyncio
from app.db.base import async_session
from app.services.scheduler import dispatch_pending_standups

asyncio.run(dispatch_pending_standups())
"
```

---

## Files Changed/Added

### New Files
- [app/services/workspace_service.py](app/services/workspace_service.py) - Workspace management
- [app/slack/onboarding_handlers.py](app/slack/onboarding_handlers.py) - Installation & subscription handlers
- [alembic/versions/002_add_workspace_fk.py](alembic/versions/002_add_workspace_fk.py) - Database migration

### Modified Files
- [app/db/models.py](app/db/models.py) - Added workspace_id FK to User
- [app/db/repository.py](app/db/repository.py) - Updated UserRepository, added workspace query methods
- [app/services/user_service.py](app/services/user_service.py) - Updated create_user, added workspace list
- [app/main.py](app/main.py) - Register onboarding handlers at startup

---

## Migration Steps

### For Fresh Install
```bash
# Run migrations
alembic upgrade head

# App will handle workspace creation on installation
```

### For Existing Database
```bash
# Run migration to add workspace_id column
alembic upgrade head

# Must set workspace_id for existing users or recreate them
# Option 1: Manual SQL
UPDATE users SET workspace_id = 1 WHERE workspace_id IS NULL;

# Option 2: Reinstall bot and have users resubscribe
```

---

## Next Steps (Optional Improvements)

1. **Admin Dashboard**: View subscribers, manage settings
2. **User Preferences**: Individual timezone/time preferences
3. **Report History**: View past standups
4. **Analytics**: Completion rates, trends
5. **Notifications**: Reminders for missed standups
6. **Bulk Add**: Admin add multiple users at once
