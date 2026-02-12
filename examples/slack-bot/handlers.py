"""Slack event handlers for the Continuum bot.

Calls the Continuum API for resolve / commit_from_clarification
and renders Slack Block Kit messages for clarification.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

CONTINUUM_API_URL = os.environ.get("CONTINUUM_API_URL", "http://localhost:8787")
DEFAULT_SCOPE = os.environ.get("CONTINUUM_SCOPE", "team:general")


def _api_post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    """POST to the Continuum API and return JSON response."""
    resp = requests.post(f"{CONTINUUM_API_URL}{path}", json=body, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _strip_mention(text: str) -> str:
    """Remove the @bot mention from the message text."""
    return re.sub(r"<@[A-Z0-9]+>", "", text).strip()


def handle_mention(event: dict[str, Any], say: Any) -> None:
    """Resolve the user's query against Continuum decisions.

    If resolved, reply with the answer.
    If clarification is needed, post interactive buttons.
    """
    raw_text = event.get("text", "")
    query = _strip_mention(raw_text)
    user_id = event.get("user", "")

    if not query:
        say("Please ask a question after mentioning me!")
        return

    try:
        result = _api_post("/resolve", {
            "prompt": query,
            "scope": DEFAULT_SCOPE,
        })
    except Exception as exc:
        say(f"Error resolving query: {exc}")
        return

    resolution = result.get("resolution", {})

    if resolution.get("status") == "resolved":
        ctx = resolution.get("resolved_context", {})
        title = ctx.get("title", "prior decision")
        rationale = ctx.get("rationale", "")
        say(
            f"Already decided: *{title}*"
            + (f"\n>{rationale}" if rationale else "")
        )
        return

    # Needs clarification — build interactive message
    clarification = resolution.get("clarification", {})
    question = clarification.get("question", "Please clarify your intent.")
    candidates = clarification.get("candidates", [])

    if not candidates:
        say(f"{question}\n\n_No candidates available. Please commit a decision manually._")
        return

    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Clarification needed* for: _{query}_\n\n{question}"},
        },
        {"type": "divider"},
    ]

    # Add a button for each candidate
    actions_elements: list[dict[str, Any]] = []
    for cand in candidates:
        actions_elements.append({
            "type": "button",
            "text": {"type": "plain_text", "text": cand.get("title", cand.get("id", "?"))[:75]},
            "action_id": "continuum_clarify",
            "value": json.dumps({
                "chosen_option_id": cand.get("id", ""),
                "title": cand.get("title", ""),
                "scope": DEFAULT_SCOPE,
                "query": query,
                "user_id": user_id,
            }),
        })

    blocks.append({"type": "actions", "elements": actions_elements})

    say(blocks=blocks, text=question)


def handle_clarification_action(body: dict[str, Any], say: Any) -> None:
    """Commit a decision from an interactive button click."""
    actions = body.get("actions", [])
    if not actions:
        return

    value = json.loads(actions[0].get("value", "{}"))
    chosen_id = value.get("chosen_option_id", "")
    title = value.get("title", f"Clarification: {chosen_id}")
    scope = value.get("scope", DEFAULT_SCOPE)
    user_id = value.get("user_id", "unknown")

    try:
        result = _api_post("/commit_from_clarification", {
            "chosen_option_id": chosen_id,
            "scope": scope,
            "title": title,
            "rationale": f"Selected by <@{user_id}> via Slack",
        })
    except Exception as exc:
        say(f"Error committing decision: {exc}")
        return

    dec = result.get("decision", {})
    say(
        f"Committed: *{dec.get('title', title)}* (scope: `{scope}`)\n"
        f"Decision ID: `{dec.get('id', '?')}`\n\n"
        f"_This decision will now be enforced across all surfaces._"
    )
