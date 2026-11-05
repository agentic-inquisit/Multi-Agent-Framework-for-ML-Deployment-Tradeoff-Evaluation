import json

from ..llm import invoke_structured, make_llm
from ..prompts import load_prompt
from ..state import EvalState, IntegrationStrategy

SYSTEM_PROMPT = load_prompt("integration_strategist")


def integration_strategist_node(state: EvalState) -> dict:
    llm = make_llm(web_search=False)
    payload = {
        "decision_brief": state.decision_brief.model_dump(),
        "agent_1_landscape": state.agent_1_landscape.model_dump() if state.agent_1_landscape else None,
        "agent_2_benchmark": state.agent_2_benchmark.model_dump() if state.agent_2_benchmark else None,
        "agent_3_infra_constraint": (
            state.agent_3_infra_constraint.model_dump() if state.agent_3_infra_constraint else None
        ),
        "agent_4_cost_model": state.agent_4_cost_model.model_dump() if state.agent_4_cost_model else None,
    }
    result = invoke_structured(llm, SYSTEM_PROMPT, json.dumps(payload, indent=2), IntegrationStrategy)
    return {
        "agent_5_integration_strategy": result,
        "deepen_research": [],
    }
