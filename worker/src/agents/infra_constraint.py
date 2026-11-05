import json

from ..llm import invoke_structured, make_llm
from ..prompts import load_prompt
from ..state import EvalState, InfraConstraintIntel

SYSTEM_PROMPT = load_prompt("infra_constraint")


def infra_constraint_node(state: EvalState) -> dict:
    llm = make_llm(web_search=True)
    payload = {
        "decision_brief": state.decision_brief.model_dump(),
        "agent_1_landscape": state.agent_1_landscape.model_dump() if state.agent_1_landscape else None,
    }
    user_content = json.dumps(payload, indent=2)
    if "agent_3" in state.deepen_research:
        user_content += "\n\n(DEEPEN PASS: re-verify per the system prompt's deepen-pass rule.)"
    result = invoke_structured(llm, SYSTEM_PROMPT, user_content, InfraConstraintIntel)
    return {"agent_3_infra_constraint": result}
