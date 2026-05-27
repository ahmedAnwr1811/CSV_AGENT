"""
AgentState – shared object flowing through every LangGraph node.
"""
from typing import Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # Full conversation (human + AI + tool messages)
    messages: Annotated[list[BaseMessage], add_messages]

    # Session context
    session_id: str
    csv_path: str           # path to the uploaded CSV file

    # CSV metadata (filled by inspect_csv)
    csv_info: str           # shape, columns, dtypes, sample rows as a string

    # Code produced by code_gen / correct_code
    generated_code: str | None

    # Results from execute_code
    code_output: str | None       # stdout text
    chart_b64:   str | None       # base64 PNG (None if no chart)
    exec_error:  str | None       # traceback if execution failed
