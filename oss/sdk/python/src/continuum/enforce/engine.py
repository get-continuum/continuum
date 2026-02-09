"""Deterministic enforcement engine for Continuum decisions."""

from __future__ import annotations

from continuum.enforce.types import Action, ActionType, EnforcementResult, EnforcementVerdict
from continuum.scope import scope_matches


class EnforcementEngine:
    """Evaluate actions against a set of recorded decisions.

    All logic is deterministic — no LLM calls, no scoring.
    The engine checks each active decision for scope matches and
    returns the most restrictive applicable verdict.
    """

    # Verdict priority: higher index = more restrictive.
    _VERDICT_PRIORITY = {
        EnforcementVerdict.allow: 0,
        EnforcementVerdict.confirm: 1,
        EnforcementVerdict.override: 2,
        EnforcementVerdict.block: 3,
    }

    def __init__(self, decisions: list) -> None:
        """Initialise with a list of decision dicts or Decision-like objects."""
        self._decisions = [
            d if isinstance(d, dict) else d.model_dump() if hasattr(d, "model_dump") else vars(d)
            for d in decisions
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, action: Action) -> EnforcementResult:
        """Evaluate *action* against all active decisions.

        Returns the most restrictive verdict found (block > confirm > allow).
        """
        verdicts: list[tuple[EnforcementVerdict, str, str]] = []

        for decision in self._decisions:
            status = decision.get("status", "")
            if status != "active":
                continue

            decision_scope = self._get_scope(decision)
            if not self._scope_matches(decision_scope, action.scope):
                continue

            decision_id = decision.get("id", "unknown")

            # Rule A: action matches a rejected option → block
            if self._action_matches_rejected_option(action, decision):
                override_policy = self._get_override_policy(decision)
                if override_policy == "allow":
                    # Informational only.
                    continue
                if override_policy == "warn":
                    verdicts.append((
                        EnforcementVerdict.confirm,
                        f"WARNING: Action matches rejected option in decision '{decision_id}' (override_policy=warn)",
                        decision_id,
                    ))
                else:
                    verdicts.append((
                        EnforcementVerdict.block,
                        f"Action matches rejected option in decision '{decision_id}' (override_policy={override_policy})",
                        decision_id,
                    ))
                continue

            # Rule B: migrations and API breaks always require confirmation
            if action.type in (ActionType.migration, ActionType.api_break):
                verdicts.append((
                    EnforcementVerdict.confirm,
                    f"Action type '{action.type.value}' requires confirmation per decision '{decision_id}'",
                    decision_id,
                ))
                continue

        if not verdicts:
            return EnforcementResult(
                verdict=EnforcementVerdict.allow,
                reason="No matching decisions found; action is allowed by default.",
            )

        # Pick the most restrictive verdict
        verdicts.sort(key=lambda v: self._VERDICT_PRIORITY[v[0]], reverse=True)
        most_restrictive = verdicts[0]

        matched_ids = list({v[2] for v in verdicts})
        confirmations = [v[1] for v in verdicts if v[0] == EnforcementVerdict.confirm]

        return EnforcementResult(
            verdict=most_restrictive[0],
            reason=most_restrictive[1],
            matched_decisions=matched_ids,
            required_confirmations=confirmations,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_scope(decision: dict) -> str:
        """Extract scope from a decision dict (may be nested under enforcement)."""
        enforcement = decision.get("enforcement")
        if isinstance(enforcement, dict):
            return enforcement.get("scope", "")
        return decision.get("scope", "")

    @staticmethod
    def _scope_matches(decision_scope: str, action_scope: str) -> bool:
        """Return *True* if *action_scope* falls under *decision_scope*.

        Supports exact match and hierarchical prefix match using scope chains.
        """
        return scope_matches(decision_scope, action_scope)

    @staticmethod
    def _action_matches_rejected_option(action: Action, decision: dict) -> bool:
        """Check whether *action* corresponds to a rejected option in *decision*."""
        options = decision.get("options_considered", [])
        description_lower = action.description.lower()

        for option in options:
            if isinstance(option, dict):
                selected = option.get("selected", True)
                title = option.get("title", "")
            else:
                selected = getattr(option, "selected", True)
                title = getattr(option, "title", "")

            if selected:
                continue

            # Match if the rejected option's title appears in the action description
            # or the action metadata references the option.
            if title and title.lower() in description_lower:
                return True

            option_id = option.get("id", "") if isinstance(option, dict) else getattr(option, "id", "")
            if option_id and action.metadata.get("option_id") == option_id:
                return True

        return False

    @staticmethod
    def _get_override_policy(decision: dict) -> str:
        enforcement = decision.get("enforcement")
        if isinstance(enforcement, dict):
            return str(enforcement.get("override_policy") or "invalid_by_default")
        return "invalid_by_default"
