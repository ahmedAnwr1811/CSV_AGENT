"""
LangGraph – CSV Data Science Agent

  __start__
      ↓
  inspect_csv        (loads CSV, builds metadata string)
      ↓
  analyze_data       (LLM reads metadata + question, plans approach)
      ↓
  code_gen           (LLM writes pandas/chart code)
      ↓  ← conditional edge
  ┌── __end__        if LLM gave plain-text final answer (no code block)
  └── correct_code   if LLM produced a ```python block
          ↓
      execute_code   (runs code safely, captures output + chart PNG)
          ↓ (loops back)
      code_gen
"""
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.nodes.inspect_csv   import inspect_csv
from agents.nodes.analyze_data  import analyze_data
from agents.nodes.code_gen      import code_gen
from agents.nodes.correct_code  import correct_code
from agents.nodes.execute_code  import execute_code


# ── Conditional edge ───────────────────────────────────────────────────────

def should_execute_or_end(state: AgentState) -> str:
    """
    After code_gen:
      - generated_code is set  →  run the code pipeline
      - generated_code is None →  LLM already gave a final answer → end
    """
    if state.get("generated_code"):
        return "correct_code"
    return END


# ── Build the graph ────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("inspect_csv",  inspect_csv)
    graph.add_node("analyze_data", analyze_data)
    graph.add_node("code_gen",     code_gen)
    graph.add_node("correct_code", correct_code)
    graph.add_node("execute_code", execute_code)

    graph.set_entry_point("inspect_csv")

    graph.add_edge("inspect_csv",  "analyze_data")
    graph.add_edge("analyze_data", "code_gen")

    graph.add_conditional_edges(
        "code_gen",
        should_execute_or_end,
        {"correct_code": "correct_code", END: END},
    )

    graph.add_edge("correct_code", "execute_code")
    graph.add_edge("execute_code", "code_gen")   # loop back

    return graph.compile()


csv_agent = build_graph()
