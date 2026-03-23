import pandas as pd
import pytest
from backend.db import Database


class TestDatabase:
    def test_load_and_query_roundtrip(self, fresh_db):
        result = fresh_db.query("SELECT name, age FROM data ORDER BY age")
        assert len(result) == 3
        assert list(result.columns) == ["name", "age"]
        assert result.iloc[0]["name"] == "Charlie"

    def test_query_strips_trailing_semicolon(self, fresh_db):
        result = fresh_db.query("SELECT COUNT(*) AS cnt FROM data;")
        assert result.iloc[0]["cnt"] == 3

    def test_get_schema_returns_columns(self, fresh_db):
        schema = fresh_db.get_schema()
        names = [col["name"] for col in schema]
        assert "name" in names
        assert "age" in names
        assert "department" in names

    def test_get_schema_types(self, fresh_db):
        schema = fresh_db.get_schema()
        type_map = {col["name"]: col["type"] for col in schema}
        assert "BIGINT" in type_map["age"] or "INTEGER" in type_map["age"]
        assert "VARCHAR" in type_map["name"] or "TEXT" in type_map["name"]

    def test_known_values_for_low_cardinality_text(self, fresh_db):
        schema = fresh_db.get_schema()
        dept_col = next(c for c in schema if c["name"] == "department")
        assert "known_values" in dept_col
        assert set(dept_col["known_values"]) == {"HR", "IT"}

    def test_no_known_values_for_numeric(self, fresh_db):
        schema = fresh_db.get_schema()
        age_col = next(c for c in schema if c["name"] == "age")
        assert "known_values" not in age_col

    def test_load_replaces_previous_data(self):
        db = Database()
        db.load_dataframe(pd.DataFrame({"x": [1, 2]}))
        db.load_dataframe(pd.DataFrame({"y": [10, 20, 30]}))
        result = db.query("SELECT * FROM data")
        assert list(result.columns) == ["y"]
        assert len(result) == 3

    def test_get_schema_before_load_raises(self):
        db = Database()
        with pytest.raises(Exception):
            db.get_schema()
