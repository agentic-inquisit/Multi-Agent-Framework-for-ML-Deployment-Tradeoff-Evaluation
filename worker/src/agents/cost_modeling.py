import json

from ..llm import invoke_structured, make_llm
from ..prompts import load_prompt
from ..state import CostModelIntel, EvalState

SYSTEM_PROMPT = load_prompt("cost_modeling")


def cost_modeling_node(state: EvalState) -> dict:
    llm = make_llm(web_search=True)
    payload = {
        "decision_brief": state.decision_brief.model_dump(),
        "agent_1_landscape": state.agent_1_landscape.model_dump() if state.agent_1_landscape else None,
    }
    user_content = json.dumps(payload, indent=2)
    if "agent_4" in state.deepen_research:
        user_content += "\n\n(DEEPEN PASS: widen the search per the system prompt's deepen-pass rule.)"
    result = invoke_structured(llm, SYSTEM_PROMPT, user_content, CostModelIntel)
    return {"agent_4_cost_model": result}
