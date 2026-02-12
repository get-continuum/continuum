# Continuum Slack Bot Example

A thin Slack bot that demonstrates cross-surface clarification via Continuum.

## How it works

1. A user asks a question in a Slack channel (e.g., "what does revenue mean?")
2. The bot calls `POST /resolve` on the Continuum API
3. If the answer is already decided, the bot replies with the resolved context
4. If clarification is needed, the bot posts interactive buttons for each option
5. When a user clicks a button, the bot calls `POST /commit_from_clarification`
6. Future queries in any surface (UI, CLI, Cursor, Slack) respect the committed decision

## Setup

### 1. Create a Slack App

Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app.

**Bot Token Scopes** (OAuth & Permissions):
- `chat:write`
- `app_mentions:read`

**Event Subscriptions** (Socket Mode recommended):
- `app_mention`

**Interactivity & Shortcuts**:
- Enable interactivity (the bot uses Block Kit interactive messages)

### 2. Environment Variables

```bash
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_SIGNING_SECRET="..."
export SLACK_APP_TOKEN="xapp-..."       # For Socket Mode
export CONTINUUM_API_URL="http://localhost:8787"
export CONTINUUM_SCOPE="team:general"   # Default scope for decisions
```

### 3. Run

```bash
pip install -r requirements.txt
python app.py
```

## Example Interaction

```
@continuum-bot what does revenue mean?
```

Bot responds with interactive buttons:
- **Gross revenue (marketing)** — Total gross revenue including returns
- **Net revenue (finance)** — Net revenue after returns and refunds

User clicks "Net revenue (finance)" → bot commits the decision and confirms.
