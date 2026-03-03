import plotly.express as px
import pandas as pd

def generate_chart(df: pd.DataFrame) -> str:
    if len(df.columns) < 2:
        return "<p>Not enough columns to generate a chart.</p>"

    # For simplicity, we'll just plot the first two columns.
    x_col = df.columns[0]
    y_col = df.columns[1]

    fig = px.line(df, x=x_col, y=y_col)

    # full_html=False means it only returns the HTML for the chart itself, not a complete HTML document with <html>, <head>, etc.
    return fig.to_html(full_html=False)
