from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from agents.state import AgentState
from agents.llm_outputs import CodeGenLLMOutput
from agents.node_outputs import CodeGenOutput
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

_structured_llm = _llm.with_structured_output(CodeGenLLMOutput)

SYSTEM = """\
You are an expert data scientist answering questions about a CSV file.

You MUST respond using the provided structured output schema.

Rules when returning code (mode='code'):
- The dataframe is already loaded as `df`. Do NOT read any file.
- Available libraries: pandas (pd), numpy (np), matplotlib.pyplot (plt), seaborn (sns).
- Use print() to output text results.
- If you generate a chart, call plt.show() so it can be captured.
- Do NOT import os, sys, subprocess, or open any files.

If you already have enough information from prior execution results,
return mode='final' with a concise final_answer.
"""


def code_gen(state: AgentState) -> dict:
    system = SystemMessage(content=SYSTEM)
    context = SystemMessage(content=f"CSV metadata:\n{state['csv_info']}")

    parsed: CodeGenLLMOutput = _structured_llm.invoke([system, context] + state["messages"])

    if parsed.mode == "final":
        response = AIMessage(content=parsed.final_answer or "")
        return CodeGenOutput(
            messages=[response],
            generated_code=None,
            exec_error=None,
        ).to_update()

    # parsed.mode == "code"
    code = parsed.python_code or ""
    response = AIMessage(content=f"```python\n{code}\n```")
    return CodeGenOutput(
        messages=[response],
        generated_code=code,
        exec_error=None,
    ).to_update()
