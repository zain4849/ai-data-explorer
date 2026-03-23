import pandas as pd

"""
Given a df (After NL query -> SQL query result):

df = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 22],
    "department": ["HR", "IT", "Finance"],
    "salary": [50000, 60000, 45000],
})
"""


def decide_chart(df: pd.DataFrame) -> dict:
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
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()  # ['age', 'salary']
    datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    num_rows = len(df)
    num_unique_cat = df[categorical_cols[0]].nunique() if categorical_cols else 0

    # Case 1: Single numeric column → histogram
    if len(df.columns) == 1 and len(numeric_cols) == 1:
        return {"chart_type": "histogram", "x": numeric_cols[0]}

    # Case 2: datetime + numeric → line or area
    if datetime_cols and numeric_cols:
        # Use area chart if there are many data points and values are cumulative-looking
        if num_rows > 20:
            return {"chart_type": "area", "x": datetime_cols[0], "y": numeric_cols[0]}
        return {"chart_type": "line", "x": datetime_cols[0], "y": numeric_cols[0]}

    # Case 3: categorical + numeric
    if categorical_cols and numeric_cols:
        # Pie/donut for proportional data with few categories
        if num_unique_cat <= 8 and len(numeric_cols) == 1:
            return {"chart_type": "pie", "names": categorical_cols[0], "values": numeric_cols[0]}

        # Stacked/grouped bar when there are 2+ categorical columns
        if len(categorical_cols) >= 2 and numeric_cols:
            return {
                "chart_type": "grouped_bar",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "color": categorical_cols[1],
            }

        return {"chart_type": "bar", "x": categorical_cols[0], "y": numeric_cols[0]}

    # Case 4: Two categoricals + numeric → heatmap
    if len(categorical_cols) >= 2 and len(numeric_cols) >= 1:
        return {
            "chart_type": "heatmap",
            "x": categorical_cols[0],
            "y": categorical_cols[1],
            "z": numeric_cols[0],
        }

    # Case 5: numeric + numeric → scatter
    if len(numeric_cols) >= 2:
        color_col = categorical_cols[0] if categorical_cols else None
        config = {"chart_type": "scatter", "x": numeric_cols[0], "y": numeric_cols[1]}
        if color_col:
            config["color"] = color_col
        return config

    # Fallback
    return {"chart_type": "table"}
