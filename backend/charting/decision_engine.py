import pandas as pd
from typing import Dict


"""
Given a df:

df = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 22],
    "department": ["HR", "IT", "Finance"]
    "salary": [50000, 60000, 45000],
})
"""


def decide_chart(df: pd.DataFrame) -> Dict:
    """
    Returns a configuration dictionary like:
    {
        "chart_type": "bar",
        "x": "department",
        "y": "total_sales"
    }
    """


    if df.empty:
        return {"chart_type": "none"}

    # None of these care about the columns' positions at all
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist() # ['age', 'salary']
    datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Case 1: Single numeric column → histogram
    if len(df.columns) == 1 and len(numeric_cols) == 1:
        return {
            "chart_type": "histogram",
            "x": numeric_cols[0]
        }

    # Case 2: datetime + numeric → line
    if datetime_cols and numeric_cols:
        return {
            "chart_type": "line",
            "x": datetime_cols[0],
            "y": numeric_cols[0]
        }

    # Case 3: categorical + numeric → bar
    if categorical_cols and numeric_cols:
        return {
            "chart_type": "bar",
            "x": categorical_cols[0],
            "y": numeric_cols[0]
        }

    # Case 4: numeric + numeric → scatter
    if len(numeric_cols) >= 2:
        return {
            "chart_type": "scatter",
            "x": numeric_cols[0],
            "y": numeric_cols[1]
        }

    # Fallback
    return {
        "chart_type": "table"
    }