from ..llm import invoke_structured, make_llm
from ..prompts import load_prompt
from ..state import EvalState, LandscapeIntel

SYSTEM_PROMPT = load_prompt("landscape")


def landscape_node(state: EvalState) -> dict:
    llm = make_llm(web_search=True)
    user_content = state.decision_brief.model_dump_json(indent=2)
    result = invoke_structured(llm, SYSTEM_PROMPT, user_content, LandscapeIntel)
    return {"agent_1_landscape": result}
