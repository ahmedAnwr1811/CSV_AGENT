"""
Node 2 – analyze_data (LLM node)
The LLM reads the CSV metadata and the user question,
then writes a plain-English analysis plan:
  - which columns are relevant
  - what kind of answer is expected (number, chart, table…)
  - any data-cleaning concerns
This plan is stored in messages so code_gen can use it.
"""
from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from agents.state import AgentState
from agents.llm_outputs import AnalyzeDataLLMOutput
from agents.node_outputs import AnalyzeDataOutput
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

SYSTEM = """\
You are an expert data scientist. You have been given:
1. A CSV dataset description (shape, columns, sample rows, statistics).
2. A user question about that data.

Your job RIGHT NOW is NOT to write code yet.
Just analyse: which columns are relevant, what computation is needed,
and whether a chart would help answer the question.
Be concise (3-5 sentences).
"""


def analyze_data(state: AgentState) -> dict:
    system = SystemMessage(content=SYSTEM)
    context = SystemMessage(
        content=f"CSV metadata:\n{state['csv_info']}"
    )
    parsed: AnalyzeDataLLMOutput = _structured_llm.invoke([system, context] + state["messages"])
    response = AIMessage(content=parsed.to_text())
    return AnalyzeDataOutput(messages=[response]).to_update()
