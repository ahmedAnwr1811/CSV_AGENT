"""
Node 4 – correct_code
If execute_code returned an error, this node asks the LLM to fix the code.
If there was no error it passes through unchanged (no LLM call).
"""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from agents.state import AgentState
from agents.llm_outputs import CorrectCodeLLMOutput
from agents.node_outputs import CorrectCodeOutput
from helpers.config import get_settings

settings = get_settings()

_llm_kwargs = {
    "model": settings.LLM_MODEL,
    "openai_api_key": settings.OPENAI_API_KEY,
    "temperature": 0,
}

if settings.OPENAI_BASE_URL:
    _llm_kwargs["base_url"] = settings.OPENAI_BASE_URL

_headers = settings.llm_default_headers()

if _headers:
    _llm_kwargs["default_headers"] = _headers


_llm = ChatOpenAI(**_llm_kwargs)

_structured_llm = _llm.with_structured_output(CorrectCodeLLMOutput)


def correct_code(state: AgentState) -> dict:
    error = state.get("exec_error")
    if not error:
        return {}   # nothing to fix


    fix_prompt = HumanMessage(
        content=(
            f"The code failed with this error:\n{error}\n\n"
            f"Original code:\n```python\n{state['generated_code']}\n```\n\n"
            "Fix the code and return the corrected code using the structured output schema."
        )
    )

    parsed: CorrectCodeLLMOutput = _structured_llm.invoke(state["messages"] + [fix_prompt])
    
    fixed_code = parsed.fixed_code
    response = AIMessage(content=f"```python\n{fixed_code}\n```")
    
    return CorrectCodeOutput(
        messages=[fix_prompt, response],
        generated_code=fixed_code,
        exec_error=None,
    ).to_update()
