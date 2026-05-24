import pandas as pd
from agents.state import AgentState
from agents.node_outputs import InspectCSVOutput
from helpers.config import get_settings

settings = get_settings()


def inspect_csv(state: AgentState) -> dict:
    df = pd.read_csv(state["csv_path"], nrows=settings.MAX_CSV_ROWS)

    rows, cols = df.shape
    col_info = "\n".join(
        f"  - {col} ({dtype})" for col, dtype in df.dtypes.items()
    )
    sample = df.head(5).to_string(index=False)

    csv_info = (
        f"Shape: {rows} rows × {cols} columns\n\n"
        f"Columns:\n{col_info}\n\n"
        f"First 5 rows:\n{sample}\n\n"
        f"Basic stats:\n{df.describe(include='all').to_string()}"
    )

    return InspectCSVOutput(csv_info=csv_info).to_update()
