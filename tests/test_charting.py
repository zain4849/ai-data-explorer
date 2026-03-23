import pandas as pd
from backend.charting.decision_engine import decide_chart


class TestDecideChart:
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        assert decide_chart(df) == {"chart_type": "none"}

    def test_single_numeric_column_histogram(self):
        df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
        config = decide_chart(df)
        assert config["chart_type"] == "histogram"
        assert config["x"] == "value"

    def test_datetime_and_numeric_line(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
                "sales": [100, 200, 150],
            }
        )
        config = decide_chart(df)
        assert config["chart_type"] == "line"
        assert config["x"] == "date"
        assert config["y"] == "sales"

    def test_categorical_and_numeric_bar(self):
        df = pd.DataFrame({"department": ["HR", "IT", "Finance"], "headcount": [10, 20, 15]})
        config = decide_chart(df)
        assert config["chart_type"] == "bar"
        assert config["x"] == "department"
        assert config["y"] == "headcount"

    def test_two_numeric_columns_scatter(self):
        df = pd.DataFrame({"height": [170, 180, 165], "weight": [70, 80, 60]})
        config = decide_chart(df)
        assert config["chart_type"] == "scatter"
        assert config["x"] == "height"
        assert config["y"] == "weight"

    def test_all_categorical_falls_back_to_table(self):
        df = pd.DataFrame({"name": ["Alice", "Bob"], "city": ["NY", "LA"]})
        config = decide_chart(df)
        assert config["chart_type"] == "table"
