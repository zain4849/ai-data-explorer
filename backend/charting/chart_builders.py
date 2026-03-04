import plotly.express as px
import pandas as pd
from typing import Dict


def build_chart(df: pd.DataFrame, config: Dict): # Returns html
    chart_type = config.get("chart_type")

    if chart_type == "none":
        return "<p>No data available.</p>"

    if chart_type == "histogram":
        fig = px.histogram(df, x=config["x"]) # Returns plotly.graph_objs._figure.Figure <- Figure obj containing data points, axis info, layout settings, styling info, interactivity configs

    elif chart_type == "line":
        fig = px.line(df, x=config["x"], y=config["y"])

    elif chart_type == "bar":
        fig = px.bar(df, x=config["x"], y=config["y"])

    elif chart_type == "scatter":
        fig = px.scatter(df, x=config["x"], y=config["y"])

    elif chart_type == "table":
        return "<p>Data returned but no suitable chart type detected.</p>"

    else:
        return "<p>Unsupported chart type.</p>"

    return fig.to_html(full_html=False)