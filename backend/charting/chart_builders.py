import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_chart(df: pd.DataFrame, config: dict):  # Returns html
    chart_type = config.get("chart_type")

    if chart_type == "none":
        return "<p>No data available.</p>"

    if chart_type == "histogram":
        fig = px.histogram(
            df, x=config["x"]
        )  # Returns plotly.graph_objs._figure.Figure <- Figure obj containing data points, axis info, layout settings, styling info, interactivity configs

    elif chart_type == "line":
        fig = px.line(df, x=config["x"], y=config["y"])

    elif chart_type == "area":
        fig = px.area(df, x=config["x"], y=config["y"])

    elif chart_type == "bar":
        fig = px.bar(df, x=config["x"], y=config["y"])

    elif chart_type == "grouped_bar":
        fig = px.bar(
            df,
            x=config["x"],
            y=config["y"],
            color=config.get("color"),
            barmode="group",
        )

    elif chart_type == "stacked_bar":
        fig = px.bar(
            df,
            x=config["x"],
            y=config["y"],
            color=config.get("color"),
            barmode="stack",
        )

    elif chart_type == "pie":
        fig = px.pie(df, names=config["names"], values=config["values"], hole=0.35)

    elif chart_type == "scatter":
        fig = px.scatter(
            df,
            x=config["x"],
            y=config["y"],
            color=config.get("color"),
        )

    elif chart_type == "heatmap":
        try:
            pivot = df.pivot_table(
                values=config["z"],
                index=config["y"],
                columns=config["x"],
                aggfunc="mean",
            )
            fig = px.imshow(
                pivot,
                aspect="auto",
                color_continuous_scale="Viridis",
            )
        except Exception:
            return "<p>Could not generate heatmap from this data.</p>"

    elif chart_type == "table":
        return "<p>Data returned but no suitable chart type detected.</p>"

    else:
        return "<p>Unsupported chart type.</p>"

    # Common layout improvements
    fig.update_layout(
        margin=dict(l=40, r=20, t=30, b=40),
        template="plotly_white",
        hoverlabel=dict(bgcolor="white", font_size=12),
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")
