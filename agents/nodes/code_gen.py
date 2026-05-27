from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from agents.state import AgentState
from agents.llm_outputs import CodeGenLLMOutput
from agents.node_outputs import CodeGenOutput
from agents.prompts import CODE_GEN_SYSTEM
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


def code_gen(state: AgentState) -> dict:
    system = SystemMessage(content=CODE_GEN_SYSTEM)
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
