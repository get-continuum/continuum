"""Continuum CLI — inspect, commit, and manage decisions from the terminal."""

from __future__ import annotations

import json

import typer

from continuum.client import ContinuumClient
from continuum.exceptions import ContinuumError

app = typer.Typer(name="continuum", help="Continuum decision-tracking CLI")


def _client() -> ContinuumClient:
    return ContinuumClient()


@app.command()
def inspect(decision_id: str = typer.Argument(..., help="ID of the decision to inspect")) -> None:
    """Print a decision's details as formatted JSON."""
    try:
        client = _client()
        decision = client.get(decision_id)
        typer.echo(json.dumps(json.loads(decision.model_dump_json()), indent=2))
    except ContinuumError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def commit(
    title: str = typer.Argument(..., help="Title of the decision"),
    scope: str = typer.Option(..., help="Enforcement scope (e.g. 'api', 'sdk')"),
    decision_type: str = typer.Option(
        ...,
        "--type",
        help="Decision type: interpretation, rejection, preference, behavior_rule",
    ),
    rationale: str | None = typer.Option(None, help="Rationale for the decision"),
) -> None:
    """Create and persist a new decision."""
    try:
        client = _client()
        decision = client.commit(
            title=title,
            scope=scope,
            decision_type=decision_type,
            rationale=rationale,
        )
        typer.echo(json.dumps(json.loads(decision.model_dump_json()), indent=2))
    except ContinuumError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def supersede(decision_id: str = typer.Argument(..., help="ID of the decision to supersede")) -> None:
    """Transition a decision to the 'superseded' status."""
    try:
        client = _client()
        updated = client.update_status(decision_id, "superseded")
        typer.echo(f"Decision {updated.id} is now superseded.")
    except ContinuumError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def scopes() -> None:
    """List all unique enforcement scopes and their active decision counts."""
    client = _client()
    decisions = client.list_decisions()

    scope_counts: dict[str, int] = {}
    for dec in decisions:
        if dec.enforcement is not None:
            s = dec.enforcement.get("scope", "unknown") if isinstance(dec.enforcement, dict) else dec.enforcement.scope
            if dec.status == "active":
                scope_counts[s] = scope_counts.get(s, 0) + 1
            else:
                scope_counts.setdefault(s, 0)

    if not scope_counts:
        typer.echo("No scopes found.")
        return

    typer.echo("Scope            Active Decisions")
    typer.echo("-" * 35)
    for scope, count in sorted(scope_counts.items()):
        typer.echo(f"{scope:<17}{count}")


if __name__ == "__main__":
    app()
