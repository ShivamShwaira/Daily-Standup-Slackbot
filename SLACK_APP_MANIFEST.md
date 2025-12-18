```json
{
  "display_information": {
    "name": "Daily Standup Bot",
    "description": "Enterprise Slack Standup Bot that collects daily standup reports via DMs",
    "background_color": "#4a90e2"
  },
  "features": {
    "bot_user": {
      "display_name": "Standup Bot",
      "always_online": false
    }
  },
  "oauth_config": {
    "scopes": {
      "bot": [
        "chat:write",
        "chat:write.public",
        "chat:write.customize",
        "im:history",
        "im:write",
        "channels:read",
        "users:read",
        "commands"
      ]
    }
  },
  "event_subscriptions": {
    "bot_events": [
      "message.im",
      "app_mention"
    ]
  },
  "interactivity": {
    "is_enabled": true,
    "request_url": "https://your-domain.com/slack/events"
  },
  "slash_commands": [
    {
      "command": "/standup",
      "url": "https://your-domain.com/slack/commands/standup",
      "description": "Manually submit a standup report",
      "usage_hint": "submit [text]",
      "should_escape": false
    }
  ],
  "shortcut": [
    {
      "type": "message",
      "name": "Report Standup",
      "callback_id": "report_standup_shortcut",
      "description": "Quick access to submit a standup"
    }
  ]
}
```

## 🔐 Scope Explanations

| Scope | Purpose |
|-------|---------|
| `chat:write` | Post messages in channels and DMs |
| `chat:write.public` | Post in public channels |
| `chat:write.customize` | Customize bot name/avatar in message |
| `im:history` | Read message history in DMs (for context) |
| `im:write` | Send direct messages to users |
| `channels:read` | List and read channel information |
| `users:read` | Fetch user display names and info |
| `commands` | Handle slash commands (future) |

## 📋 How to Use This Manifest

### Method 1: Manual Configuration (Current Setup)
The scope list above is already configured in your Slack app. You've added them via the web UI.

### Method 2: JSON Upload (If Re-creating App)
1. Go to https://api.slack.com/apps
2. Click your app
3. Go to "App Manifest" (sidebar)
4. Copy the JSON above
5. Paste and save

### Notes
- Replace `https://your-domain.com` with your actual domain
- Event Subscriptions Request URL must match your app's `/slack/events` endpoint
- The bot must have proper permissions in channels where it posts
- Interactivity (buttons) requires this configuration enabled

## 🧪 Test Events

Once installed, test with:

```bash
# Invite bot to a channel
/invite @Standup Bot

# Test direct message
# Send any message to the bot - it will acknowledge

# Test interactive buttons
# Click buttons in DM flow - should work without errors
```

## 🔄 Update Manifest

If you add new features, update the manifest:
1. Slack App Settings → App Manifest
2. Copy updated JSON from above
3. Paste and save
4. Slack will notify of new scopes needed (click "Install")
