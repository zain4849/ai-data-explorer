from unittest.mock import patch

import pytest
from backend.llm import (
    LLMError,
    _build_schema_text,
    call_llm,
    clean_sql_output,
    has_unresolved_placeholders,
)


class TestCleanSQLOutput:
    def test_strips_markdown_sql_fence(self):
        assert clean_sql_output("```sql\nSELECT 1\n```") == "SELECT 1"

    def test_strips_plain_fence(self):
        assert clean_sql_output("```\nSELECT 1\n```") == "SELECT 1"

    def test_strips_sql_comments(self):
        result = clean_sql_output("SELECT 1 -- this is a comment\nFROM data")
        assert "--" not in result
        assert "SELECT 1" in result

    def test_strips_whitespace(self):
        assert clean_sql_output("  SELECT 1  ") == "SELECT 1"

    def test_passthrough_clean_sql(self):
        assert clean_sql_output("SELECT * FROM data LIMIT 10") == "SELECT * FROM data LIMIT 10"


class TestHasUnresolvedPlaceholders:
    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT [column] FROM data",
            "SELECT * FROM data WHERE x = <value>",
            "SELECT TODO FROM data",
            "SELECT * FROM data WHERE x = ???",
        ],
    )
    def test_detects_placeholders(self, sql):
        assert has_unresolved_placeholders(sql) is True

    def test_clean_sql_has_no_placeholders(self):
        assert has_unresolved_placeholders("SELECT * FROM data LIMIT 10") is False


class TestBuildSchemaText:
    def test_basic_columns(self):
        cols = [{"name": "id", "type": "INTEGER"}, {"name": "name", "type": "TEXT"}]
        result = _build_schema_text(cols)
        assert "- id (INTEGER)" in result
        assert "- name (TEXT)" in result

    def test_includes_known_values(self):
        cols = [{"name": "status", "type": "TEXT", "known_values": ["active", "inactive"]}]
        result = _build_schema_text(cols)
        assert "known_values" in result
        assert "'active'" in result
        assert "'inactive'" in result


class TestCallLLMRouting:
    @patch("backend.llm._call_ollama", return_value="SELECT 1")
    def test_routes_to_ollama(self, mock_ollama):
        with patch("backend.llm.settings") as mock_settings:
            mock_settings.llm_provider = "ollama"
            result = call_llm("test")
        assert result == "SELECT 1"
        mock_ollama.assert_called_once_with("test")

    @patch("backend.llm._call_openai_compatible", return_value="SELECT 2")
    def test_routes_to_openai(self, mock_openai):
        with patch("backend.llm.settings") as mock_settings:
            mock_settings.llm_provider = "openai_compatible"
            result = call_llm("test")
        assert result == "SELECT 2"
        mock_openai.assert_called_once_with("test")

    @patch("backend.llm._call_gemini", return_value="SELECT 3")
    def test_routes_to_gemini(self, mock_gemini):
        with patch("backend.llm.settings") as mock_settings:
            mock_settings.llm_provider = "gemini"
            result = call_llm("test")
        assert result == "SELECT 3"
        mock_gemini.assert_called_once_with("test")

    def test_unsupported_provider_raises(self):
        with patch("backend.llm.settings") as mock_settings:
            mock_settings.llm_provider = "unknown_provider"
            with pytest.raises(LLMError, match="Unsupported"):
                call_llm("test")
