import os

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

MODEL_NAME = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search"}


def make_llm(*, web_search: bool = False) -> ChatAnthropic:
    llm = ChatAnthropic(model=MODEL_NAME, max_tokens=4096)
    if web_search:
        llm = llm.bind_tools([WEB_SEARCH_TOOL])
    return llm


def invoke_structured(
    llm: ChatAnthropic,
    system_prompt: str,
    user_content: str,
    schema: type[BaseModel],
    *,
    max_retries: int = 1,
) -> BaseModel:
    structured_llm = llm.with_structured_output(schema)
    messages = [("system", system_prompt), ("human", user_content)]
    last_error: Exception | None = None
    for _ in range(max_retries + 1):
        try:
            return structured_llm.invoke(messages)
        except Exception as exc:
            last_error = exc
            messages.append((
                "human",
                f"Your previous response did not match the required schema: {exc}. "
                "Return corrected output that matches the schema exactly.",
            ))
    raise RuntimeError(f"{schema.__name__} structured output failed after retries") from last_error
