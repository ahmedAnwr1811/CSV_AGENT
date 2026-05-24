"""
Safe Python code execution sandbox.
Runs generated pandas/matplotlib code in an isolated namespace.
Captures:
  - stdout (print output, df.describe(), etc.)
  - Any matplotlib figure → base64-encoded PNG string
"""
import io
import base64
import traceback
import contextlib
import matplotlib
matplotlib.use("Agg")           # non-interactive backend – no GUI window
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns


def run_code(code: str, csv_path: str) -> dict:
    """
    Execute `code` with the CSV pre-loaded as `df`.
    Returns:
        {
        "output": str,          # stdout text
        "chart":  str | None,   # base64 PNG (if a figure was created)
        "error":  str | None,   # traceback if execution failed
        }
    """
    # ── pre-load the dataframe so the LLM can always use `df` ─────────────
    df = pd.read_csv(csv_path)

    # ── safe globals – data-science libs only, no os/subprocess ───────────
    safe_globals = {
        "__builtins__": {
            "print": print, "len": len, "range": range, "enumerate": enumerate,
            "zip": zip, "list": list, "dict": dict, "set": set, "tuple": tuple,
            "str": str, "int": int, "float": float, "bool": bool,
            "round": round, "sorted": sorted, "sum": sum, "min": min, "max": max,
            "abs": abs, "type": type, "isinstance": isinstance,
        },
        "df": df,
        "pd": pd,
        "np": np,
        "plt": plt,
        "sns": sns,
    }

    stdout_capture = io.StringIO()
    chart_b64: str | None = None
    error: str | None = None

    plt.close("all")   # clear any previous figures

    try:
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, safe_globals)   # noqa: S102

        # ── capture matplotlib figure if one was created ───────────────────
        fig = plt.gcf()
        if fig.get_axes():
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
            buf.seek(0)
            chart_b64 = base64.b64encode(buf.read()).decode()
    except Exception:
        error = traceback.format_exc()
    finally:
        plt.close("all")

    return {
        "output": stdout_capture.getvalue().strip(),
        "chart":  chart_b64,
        "error":  error,
    }
