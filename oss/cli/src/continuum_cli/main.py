"""Continuum CLI — inspect, commit, and manage decisions from the terminal."""

from __future__ import annotations

import json
from typing import Optional

import typer

from continuum.client import ContinuumClient
from continuum.exceptions import ContinuumError

app = typer.Typer(name="continuum", help="Continuum decision-tracking CLI")


def _client() -> ContinuumClient:
    return ContinuumClient()


# ------------------------------------------------------------------
# inspect
# ------------------------------------------------------------------


@app.command()
def inspect(
    decision_id: Optional[str] = typer.Argument(None, help="ID of the decision to inspect"),
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Scope to inspect (returns active binding set)"),
) -> None:
    """Inspect a decision by ID, or the active binding set for a scope."""
    if not decision_id and not scope:
        typer.echo("Error: provide either a decision_id argument or --scope.", err=True)
        raise typer.Exit(code=1)
    if decision_id and scope:
        typer.echo("Error: provide either a decision_id argument or --scope, not both.", err=True)
        raise typer.Exit(code=1)

    try:
        client = _client()
        if scope:
            binding = client.inspect(scope)
            typer.echo(json.dumps(binding, indent=2, default=str))
        else:
            assert decision_id is not None
            decision = client.get(decision_id)
            typer.echo(json.dumps(json.loads(decision.model_dump_json()), indent=2))
    except ContinuumError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# resolve
# ------------------------------------------------------------------


@app.command()
def resolve(
    prompt: str = typer.Argument(..., help="The agent prompt to resolve against prior decisions"),
    scope: str = typer.Option(..., "--scope", "-s", help="Hierarchical scope identifier"),
    candidates: Optional[str] = typer.Option(
        None, "--candidates", "-c", help="JSON array of candidate options (e.g. '[{\"id\":\"a\",\"title\":\"A\"}]')"
    ),
) -> None:
    """Check whether a prior decision covers the given prompt and scope."""
    try:
        client = _client()
        candidate_list = json.loads(candidates) if candidates else None
        result = client.resolve(query=prompt, scope=scope, candidates=candidate_list)
        typer.echo(json.dumps(result, indent=2, default=str))
    except json.JSONDecodeError:
        typer.echo("Error: --candidates must be valid JSON.", err=True)
        raise typer.Exit(code=1)
    except ContinuumError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# enforce
# ------------------------------------------------------------------


@app.command()
def enforce(
    scope: str = typer.Option(..., "--scope", "-s", help="Scope to evaluate enforcement within"),
    action_type: str = typer.Option("generic", "--action-type", "-t", help="Action type (e.g. code_change, migration)"),
    action_detail: str = typer.Option(
        ..., "--action-detail", "-d", help='JSON object describing the action (e.g. \'{"description":"rewrite auth"}\')'
    ),
) -> None:
    """Evaluate enforcement rules for a proposed action in a scope."""
    try:
        action = json.loads(action_detail)
        if isinstance(action, str):
            action = {"description": action}
        action.setdefault("type", action_type)
    except json.JSONDecodeError:
        typer.echo("Error: --action-detail must be valid JSON.", err=True)
        raise typer.Exit(code=1)

    try:
        client = _client()
        result = client.enforce(action=action, scope=scope)
        typer.echo(json.dumps(result, indent=2, default=str))
    except ContinuumError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# list
# ------------------------------------------------------------------


@app.command(name="list")
def list_decisions(
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Filter by enforcement scope"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status (draft, active, superseded, archived)"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON instead of table"),
) -> None:
    """List decisions, optionally filtered by scope and/or status."""
    try:
        client = _client()
        decisions = client.list_decisions(scope=scope)

        if status:
            decisions = [d for d in decisions if str(d.status) == status or d.status == status]

        if output_json:
            typer.echo(json.dumps([json.loads(d.model_dump_json()) for d in decisions], indent=2))
            return

        if not decisions:
            typer.echo("No decisions found.")
            return

        typer.echo(f"{'ID':<20} {'Status':<12} {'Type':<18} {'Title'}")
        typer.echo("-" * 75)
        for d in decisions:
            dec_type = ""
            if d.enforcement is not None:
                dec_type = (
                    d.enforcement.get("decision_type", "")
                    if isinstance(d.enforcement, dict)
                    else str(d.enforcement.decision_type)
                )
            typer.echo(f"{d.id:<20} {str(d.status):<12} {dec_type:<18} {d.title}")
    except ContinuumError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# commit
# ------------------------------------------------------------------


@app.command()
def commit(
    title: str = typer.Argument(..., help="Title of the decision"),
    scope: str = typer.Option(..., "--scope", "-s", help="Enforcement scope (e.g. 'repo:acme/backend')"),
    decision_type: str = typer.Option(
        ...,
        "--type",
        help="Decision type: interpretation, rejection, preference, behavior_rule",
    ),
    rationale: Optional[str] = typer.Option(None, "--rationale", "-r", help="Rationale for the decision"),
    options: Optional[str] = typer.Option(None, "--options", help="JSON array of options considered"),
    stakeholders: Optional[list[str]] = typer.Option(None, "--stakeholder", help="Stakeholder (repeatable)"),
    metadata: Optional[str] = typer.Option(None, "--metadata", help="JSON object of metadata"),
    override_policy: Optional[str] = typer.Option(None, "--override-policy", help="Override policy: invalid_by_default | warn | allow"),
    precedence: Optional[int] = typer.Option(None, "--precedence", help="Precedence for conflict resolution"),
    supersedes: Optional[str] = typer.Option(None, "--supersedes", help="Decision ID this supersedes"),
    activate: bool = typer.Option(False, "--activate", help="Transition to active immediately"),
) -> None:
    """Create and persist a new decision."""
    try:
        parsed_options = json.loads(options) if options else None
    except json.JSONDecodeError:
        typer.echo("Error: --options must be valid JSON array.", err=True)
        raise typer.Exit(code=1)

    try:
        parsed_metadata = json.loads(metadata) if metadata else None
    except json.JSONDecodeError:
        typer.echo("Error: --metadata must be valid JSON object.", err=True)
        raise typer.Exit(code=1)

    try:
        client = _client()
        decision = client.commit(
            title=title,
            scope=scope,
            decision_type=decision_type,
            rationale=rationale,
            options=parsed_options,
            stakeholders=list(stakeholders) if stakeholders else None,
            metadata=parsed_metadata,
            override_policy=override_policy,
            precedence=precedence,
            supersedes=supersedes,
        )
        if activate:
            decision = client.update_status(decision.id, "active")
        typer.echo(json.dumps(json.loads(decision.model_dump_json()), indent=2))
    except ContinuumError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# supersede
# ------------------------------------------------------------------


@app.command()
def supersede(
    decision_id: str = typer.Argument(..., help="ID of the decision to supersede"),
    new_title: Optional[str] = typer.Option(None, "--new-title", help="Title for the replacement decision"),
    rationale: Optional[str] = typer.Option(None, "--rationale", "-r", help="Rationale for replacement"),
    options: Optional[str] = typer.Option(None, "--options", help="JSON array of options considered"),
    stakeholders: Optional[list[str]] = typer.Option(None, "--stakeholder", help="Stakeholder (repeatable)"),
    metadata: Optional[str] = typer.Option(None, "--metadata", help="JSON object of metadata"),
    override_policy: Optional[str] = typer.Option(None, "--override-policy", help="Override policy"),
    precedence: Optional[int] = typer.Option(None, "--precedence", help="Precedence for conflict resolution"),
) -> None:
    """Supersede an existing decision. With --new-title, creates a full replacement."""
    try:
        parsed_options = json.loads(options) if options else None
    except json.JSONDecodeError:
        typer.echo("Error: --options must be valid JSON array.", err=True)
        raise typer.Exit(code=1)

    try:
        parsed_metadata = json.loads(metadata) if metadata else None
    except json.JSONDecodeError:
        typer.echo("Error: --metadata must be valid JSON object.", err=True)
        raise typer.Exit(code=1)

    try:
        client = _client()
        if new_title:
            # Full replacement: new decision + activate
            kwargs: dict = {}
            if rationale is not None:
                kwargs["rationale"] = rationale
            if parsed_options is not None:
                kwargs["options"] = parsed_options
            if stakeholders:
                kwargs["stakeholders"] = list(stakeholders)
            if parsed_metadata is not None:
                kwargs["metadata"] = parsed_metadata
            if override_policy is not None:
                kwargs["override_policy"] = override_policy
            if precedence is not None:
                kwargs["precedence"] = precedence

            new_dec = client.supersede(
                old_id=decision_id,
                new_title=new_title,
                **kwargs,
            )
            typer.echo(json.dumps(json.loads(new_dec.model_dump_json()), indent=2))
        else:
            # Simple status transition (backward-compatible)
            updated = client.update_status(decision_id, "superseded")
            typer.echo(f"Decision {updated.id} is now superseded.")
    except ContinuumError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


# ------------------------------------------------------------------
# scopes
# ------------------------------------------------------------------


@app.command()
def scopes() -> None:
    """List all unique enforcement scopes and their active decision counts."""
    client = _client()
    decisions = client.list_decisions()

    scope_counts: dict[str, int] = {}
    for dec in decisions:
        if dec.enforcement is not None:
            s = (
                dec.enforcement.get("scope", "unknown")
                if isinstance(dec.enforcement, dict)
                else dec.enforcement.scope
            )
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


# ------------------------------------------------------------------
# mine
# ------------------------------------------------------------------


@app.command()
def mine(
    file: str = typer.Argument(..., help="Path to a JSON file containing conversation strings (list of strings)"),
    scope: str = typer.Option(..., "--scope", "-s", help="Default scope for mined candidates"),
    output_json: bool = typer.Option(True, "--json", help="Output as JSON"),
) -> None:
    """Extract facts and decision candidates from a conversation file."""
    import sys
    from pathlib import Path as _Path

    try:
        convo_path = _Path(file)
        if not convo_path.exists():
            typer.echo(f"Error: file not found: {file}", err=True)
            raise typer.Exit(code=1)

        conversations = json.loads(convo_path.read_text())
        if isinstance(conversations, str):
            conversations = [conversations]

        # Import miner
        miner_root = _Path(__file__).resolve().parents[4] / "miner"
        if str(miner_root) not in sys.path:
            sys.path.insert(0, str(miner_root))

        from continuum_miner.extract_facts import extract_facts
        from continuum_miner.extract_decision_candidates import extract_decision_candidates
        from continuum_miner.dedupe_merge import dedupe_candidates

        all_facts = []
        for convo in conversations:
            all_facts.extend(extract_facts(str(convo)))

        candidates = extract_decision_candidates(
            facts=all_facts,
            scope_default=scope,
        )
        deduped = dedupe_candidates(candidates)

        result = {
            "facts": [f.model_dump(mode="json") for f in all_facts],
            "decision_candidates": [c.model_dump(mode="json") for c in deduped],
        }
        typer.echo(json.dumps(result, indent=2, default=str))

    except json.JSONDecodeError:
        typer.echo("Error: file must contain valid JSON.", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
