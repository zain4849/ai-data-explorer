import pandas as pd
from .decision_engine import decide_chart
from .chart_builders import build_chart


def generate_chart(df: pd.DataFrame) -> str:
    """
    Main chart generation entry point.
    """

    config = decide_chart(df)
    chart_html = build_chart(df, config)

    return chart_html