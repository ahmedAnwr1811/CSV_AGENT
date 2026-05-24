from langchain_core.messages import HumanMessage
from helpers.code_runner import run_code
from agents.state import AgentState
from agents.node_outputs import ExecuteCodeOutput


def execute_code(state: AgentState) -> dict:
    code = state.get("generated_code", "")
    result = run_code(code, state["csv_path"])

    if result["error"]:
        # Tell the LLM what went wrong so it can fix it
        error_msg = HumanMessage(
            content=f"Code execution failed:\n{result['error']}"
        )
        return ExecuteCodeOutput(
            messages=[error_msg],
            exec_error=result["error"],
            code_output=None,
            chart_b64=None,
        ).to_update()

    # Build a summary message so code_gen can compose the final answer
    summary_parts = []
    if result["output"]:
        summary_parts.append(f"Output:\n{result['output']}")
    if result["chart"]:
        summary_parts.append("A chart was generated successfully.")

    summary = "\n\n".join(summary_parts) or "Code ran with no output."
    result_msg = HumanMessage(content=f"Execution result:\n{summary}")

    return ExecuteCodeOutput(
        messages=[result_msg],
        code_output=result["output"],
        chart_b64=result["chart"],
        exec_error=None,
    ).to_update()
