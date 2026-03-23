import io
from unittest.mock import patch

import pandas as pd
import pytest
from backend.db import Database
from fastapi.testclient import TestClient


@pytest.fixture()
def sample_df():  # Now sample_df can be used w/out calling the function
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 22],
            "department": ["HR", "IT", "HR"],
        }
    )


@pytest.fixture()
def fresh_db(sample_df):
    database = Database()
    database.load_dataframe(sample_df)
    return database


@pytest.fixture()
def client():
    """FastAPI TestClient with all LLM calls mocked out."""

    # What the code wants to test is:
    #  - does the endpoint work?
    #  - does it call the database?
    #  - does it return JSON correctly?
    #  - does the API crash?
    # NOT whether the LLM generates good SQL.
    with (
        patch("backend.main.generate_sql", return_value="SELECT * FROM data LIMIT 10"),
        patch("backend.main.generate_insights", return_value="Sample insights."),
        patch("backend.main.generate_chart", return_value="<div>chart</div>"),
    ):
        # 1. What “import” does in Python

        # When Python sees:
        # from backend.main import app
        # it runs all the code in backend.main once and “remembers” the functions and variables.

        # That means:
        # If backend.main has generate_sql(), Python creates a reference to it.
        # If you change generate_sql() after the import, the code in app still uses the old function.

        # 2. What patch() does
        # patch("backend.main.generate_sql", return_value=...) temporarily replaces the function with a fake one.
        # If the import happens before the patch, app already has the old function attached, so the patch won’t affect the app.
        from backend.main import app

        # TestClient comes from FastAPI, and it lets you pretend to be a web browser or HTTP client that talks to your API.
        with TestClient(app) as c:
            yield c


def make_csv_upload(content: str, filename: str = "test.csv", content_type: str = "text/csv"):
    """Helper to create an in-memory CSV file for upload tests."""
    return {"file": (filename, io.BytesIO(content.encode()), content_type)}
