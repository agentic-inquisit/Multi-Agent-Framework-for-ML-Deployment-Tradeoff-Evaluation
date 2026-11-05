from langgraph.types import interrupt

from .state import DecisionBrief, EvalState

REQUIRED_FIELDS = [
    "decision_name",
    "one_liner",
    "problem",
    "capability",
    "current_approach",
    "deployment_target",
    "hardware_constraints",
    "latency_budget",
    "compliance_constraints",
    "team_context",
    "budget_ceiling",
    "success_metric",
]


def _missing_fields(brief: DecisionBrief | None) -> list[str]:
    if brief is None:
        return REQUIRED_FIELDS
    return [f for f in REQUIRED_FIELDS if not str(getattr(brief, f, "")).strip()]


def orchestrator_node(state: EvalState) -> dict:
    missing = _missing_fields(state.decision_brief)
    if not missing:
        return {}

    answers = interrupt({"reason": "incomplete_decision_brief", "missing_fields": missing})
    base = state.decision_brief.model_dump() if state.decision_brief else {}
    updated_brief = DecisionBrief(**{**base, **answers})
    return {"decision_brief": updated_brief}
