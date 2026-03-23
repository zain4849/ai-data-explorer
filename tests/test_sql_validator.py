import pytest
from backend.sql_validator import ensure_limit, validate_sql


class TestValidateSQL:
    def test_simple_select_passes(self):
        assert validate_sql("SELECT * FROM data LIMIT 10") is True

    def test_select_with_trailing_semicolon_passes(self):
        assert validate_sql("SELECT * FROM data LIMIT 10;") is True

    def test_cte_with_keyword_passes(self):
        assert validate_sql("WITH cte AS (SELECT id FROM data) SELECT * FROM cte LIMIT 5") is True

    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TABLE data",
            "DELETE FROM data WHERE id = 1",
            "INSERT INTO data VALUES (1)",
            "ALTER TABLE data ADD COLUMN x INT",
            "UPDATE data SET age = 99",
            "CREATE TABLE evil (id INT)",
            "TRUNCATE TABLE data",
            "RENAME TABLE data TO hacked",
        ],
    )
    def test_forbidden_keywords_blocked(self, sql):
        with pytest.raises(ValueError):
            validate_sql(sql)

    @pytest.mark.parametrize(
        "keyword",
        ["drop", "delete", "alter", "truncate", "insert", "update", "create", "rename"],
    )
    def test_forbidden_keyword_inside_select(self, keyword):
        """Forbidden keywords are caught even when disguised inside a SELECT."""
        with pytest.raises(ValueError, match="(?i)forbidden"):
            validate_sql(f"SELECT * FROM data WHERE note = '{keyword} this'")

    def test_multiple_statements_blocked(self):
        with pytest.raises(ValueError, match="Multiple SQL"):
            validate_sql("SELECT 1; DROP TABLE data")

    def test_must_start_with_select_or_with(self):
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_sql("EXPLAIN SELECT * FROM data")

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT [column_name] FROM data",
            "SELECT * FROM data WHERE x = <value>",
            "SELECT TODO FROM data",
            "SELECT * FROM data WHERE x = ???",
        ],
    )
    def test_placeholder_patterns_blocked(self, sql):
        with pytest.raises(ValueError, match="placeholder"):
            validate_sql(sql)


class TestEnsureLimit:
    def test_adds_limit_when_missing(self):
        result = ensure_limit("SELECT * FROM data", default_limit=50)
        assert result == "SELECT * FROM data LIMIT 50"

    def test_preserves_existing_limit(self):
        result = ensure_limit("SELECT * FROM data LIMIT 20", default_limit=50)
        assert result == "SELECT * FROM data LIMIT 20"

    def test_handles_trailing_semicolon(self):
        result = ensure_limit("SELECT * FROM data;", default_limit=50)
        assert result == "SELECT * FROM data LIMIT 50;"

    def test_preserves_existing_limit_with_semicolon(self):
        result = ensure_limit("SELECT * FROM data LIMIT 20;", default_limit=50)
        assert result == "SELECT * FROM data LIMIT 20;"

    def test_uses_settings_default_when_none(self):
        result = ensure_limit("SELECT * FROM data")
        assert "LIMIT" in result
