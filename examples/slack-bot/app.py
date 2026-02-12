"""Continuum Slack Bot — cross-surface clarification example.

Listens for @mentions, resolves queries via the Continuum API,
and posts interactive clarification buttons when ambiguity is detected.
"""

from __future__ import annotations

import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from handlers import handle_mention, handle_clarification_action

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")

app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


@app.event("app_mention")
def on_mention(event, say):
    """Handle @bot mentions — resolve the user's query."""
    handle_mention(event, say)


@app.action("continuum_clarify")
def on_clarification(ack, body, say):
    """Handle clarification button clicks."""
    ack()
    handle_clarification_action(body, say)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Starting Continuum Slack Bot (Socket Mode)...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
