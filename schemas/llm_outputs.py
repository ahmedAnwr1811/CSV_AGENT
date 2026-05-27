from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalyzeDataLLMOutput(BaseModel):
    """Structured output returned by the LLM for the analyze_data node."""

    relevant_columns: list[str] = Field(default_factory=list)
    computation: str = Field(..., description="What calculations/steps are needed to answer the question")
    chart: bool = Field(..., description="Whether a chart would help")
    cleaning_notes: str | None = Field(
        default=None,
        description="Any data cleaning or caveats (missing values, types, outliers)",
    )

    def to_text(self) -> str:
        parts: list[str] = []
        if self.relevant_columns:
            parts.append("Relevant columns: " + ", ".join(self.relevant_columns))
        parts.append("Computation: " + self.computation)
        parts.append("Chart: " + ("yes" if self.chart else "no"))
        if self.cleaning_notes:
            parts.append("Notes: " + self.cleaning_notes)
        return "\n".join(parts)


class CodeGenLLMOutput(BaseModel):
    """Structured output returned by the LLM for the code_gen node.

    The LLM must either:
    - return Python code to run (mode='code')
    - or return the final answer directly (mode='final')
    """

    mode: Literal["code", "final"]

    python_code: str | None = Field(
        default=None,
        description="Runnable Python code that assumes a dataframe named df already exists",
    )
    final_answer: str | None = Field(
        default=None,
        description="Final plain-text answer for the user when no more code execution is needed",
    )

    @model_validator(mode="after")
    def _check_consistency(self):
        if self.mode == "code" and not self.python_code:
            raise ValueError("python_code is required when mode='code'")
        if self.mode == "final" and not self.final_answer:
            raise ValueError("final_answer is required when mode='final'")
        return self


class CorrectCodeLLMOutput(BaseModel):
    """Structured output returned by the LLM for the correct_code node."""

    fixed_code: str = Field(..., description="Corrected runnable Python code")
