from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from agents.state import AgentState
from agents.llm_outputs import AnalyzeDataLLMOutput
from agents.node_outputs import AnalyzeDataOutput
from agents.prompts import ANALYZE_DATA_SYSTEM
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

_structured_llm = _llm.with_structured_output(AnalyzeDataLLMOutput)


def analyze_data(state: AgentState) -> dict:
    system = SystemMessage(content=ANALYZE_DATA_SYSTEM)
    context = SystemMessage(
        content=f"CSV metadata:\n{state['csv_info']}"
    )
    parsed: AnalyzeDataLLMOutput = _structured_llm.invoke([system, context] + state["messages"])
    response = AIMessage(content=parsed.to_text())
    return AnalyzeDataOutput(messages=[response]).to_update()
