from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class NodeOutput(BaseModel):
    """Base class for LangGraph node structured outputs.

    `.to_update()` converts the Pydantic model to a dict suitable for LangGraph
    state updates.

    NOTE: We intentionally include fields set to `None` (exclude_unset=True)
    so nodes can explicitly clear state fields.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_update(self) -> dict:
        data = self.model_dump(mode="python", exclude_unset=True)
        # LangGraph's message channel expects real BaseMessage objects (or dicts
        # with role/content). Pydantic may serialize BaseMessage into partial
        # dicts, so we pass them through unchanged.
        if "messages" in data:
            data["messages"] = getattr(self, "messages")
        return data


# ── Node outputs (one model per node) ─────────────────────────────────────

from langchain_core.messages import BaseMessage


class InspectCSVOutput(NodeOutput):
    csv_info: str


class AnalyzeDataOutput(NodeOutput):
    messages: list[BaseMessage]


class CodeGenOutput(NodeOutput):
    messages: list[BaseMessage]
    generated_code: str | None
    exec_error: str | None


class CorrectCodeOutput(NodeOutput):
    messages: list[BaseMessage]
    generated_code: str
    exec_error: str | None


class ExecuteCodeOutput(NodeOutput):
    messages: list[BaseMessage]
    code_output: str | None
    chart_b64: str | None
    exec_error: str | None
