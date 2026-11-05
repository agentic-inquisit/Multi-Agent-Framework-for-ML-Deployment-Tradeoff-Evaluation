import json

from langgraph.graph import END

from ..llm import invoke_structured, make_llm
from ..prompts import load_prompt
from ..state import DeepenTag, EvalState, TradeoffReport

SYSTEM_PROMPT = load_prompt("synthesis")

MAX_RETRIES = 2
MIN_BENCHMARK_RESULTS = 2
MIN_FEASIBLE_CANDIDATES = 1

_NODE_FOR_TAG = {
    "agent_2": "agent_2_benchmark",
    "agent_3": "agent_3_infra_constraint",
    "agent_4": "agent_4_cost_model",
}


def synthesis_node(state: EvalState) -> dict:
    llm = make_llm(web_search=False)
    payload = state.model_dump(mode="json")
    report = invoke_structured(llm, SYSTEM_PROMPT, json.dumps(payload, indent=2), TradeoffReport)

    weak_benchmark = (
        len(state.agent_2_benchmark.results) < MIN_BENCHMARK_RESULTS
        or state.agent_2_benchmark.confidence == "low"
    )
    weak_infra = sum(f.feasible for f in state.agent_3_infra_constraint.feasibility) < MIN_FEASIBLE_CANDIDATES
    weak_cost = state.agent_4_cost_model.cost_confidence == "low"

    deepen: list[DeepenTag] = []
    if state.retry_count < MAX_RETRIES:
        if weak_benchmark:
            deepen.append("agent_2")
        if weak_infra:
            deepen.append("agent_3")
        if weak_cost:
            deepen.append("agent_4")

    return {
        "agent_6_tradeoff_report": report,
        "deepen_research": deepen,
        "retry_count": state.retry_count + 1 if deepen else state.retry_count,
    }


def route_after_synthesis(state: EvalState) -> list[str]:
    targets = [_NODE_FOR_TAG[tag] for tag in state.deepen_research]
    return targets or [END]
