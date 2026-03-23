import io
from unittest.mock import patch

from tests.conftest import make_csv_upload

CSV_CONTENT = "name,age,department\nAlice,25,HR\nBob,30,IT\nCharlie,22,HR\n"


class TestHealth:
    def test_health_returns_ok_after_upload(self, client):
        client.post("/upload_csv", files=make_csv_upload(CSV_CONTENT))
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_returns_503_before_any_upload(self):
        """Without any data loaded, get_schema raises, so health returns 503."""
        from backend.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as c:
            from backend.main import db as main_db

            with patch.object(main_db, "get_schema", side_effect=Exception("no table")):
                resp = c.get("/health")
                assert resp.status_code == 503


class TestUploadCSV:
    def test_upload_valid_csv(self, client):
        resp = client.post("/upload_csv", files=make_csv_upload(CSV_CONTENT))
        assert resp.status_code == 200
        data = resp.json()
        assert data["row_count"] == 3
        assert set(data["columns"]) == {"name", "age", "department"}
        assert len(data["preview"]) <= 5

    def test_upload_invalid_csv(self, client):
        resp = client.post(
            "/upload_csv",
            files=make_csv_upload("not,valid\x00\x01\x02csv", filename="bad.csv"),
        )
        # Should either parse it or return 400 -- not crash
        assert resp.status_code in (200, 400)

    def test_upload_rejects_non_csv_extension(self, client):
        files = {"file": ("data.exe", io.BytesIO(b"fake"), "application/octet-stream")}
        resp = client.post("/upload_csv", files=files)
        assert resp.status_code == 400
        assert "csv" in resp.json()["detail"].lower() or "allowed" in resp.json()["detail"].lower()

    def test_upload_rejects_oversized_file(self, client):
        big_content = "x" * (10 * 1024 * 1024 + 1)
        resp = client.post("/upload_csv", files=make_csv_upload(big_content))
        assert resp.status_code == 413
        assert "large" in resp.json()["detail"].lower()


class TestQuery:
    def _upload_first(self, client):
        client.post("/upload_csv", files=make_csv_upload(CSV_CONTENT))

    def test_query_returns_results(self, client):
        self._upload_first(client)
        resp = client.get("/query", params={"nl_query": "show all data"})
        assert resp.status_code == 200
        data = resp.json()
        assert "sql" in data
        assert "result" in data
        assert "insights" in data
        assert "chart_html" in data

    def test_query_llm_unavailable_returns_503(self, client):
        self._upload_first(client)
        from backend.llm import LLMError

        with patch("backend.main.generate_sql", side_effect=LLMError("down")):
            resp = client.get("/query", params={"nl_query": "show data"})
            assert resp.status_code == 503


class TestSecurityHeaders:
    def test_responses_contain_security_headers(self, client):
        client.post("/upload_csv", files=make_csv_upload(CSV_CONTENT))
        resp = client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


class TestRateLimiting:
    def test_upload_rate_limit(self):
        """Exceeding 5 uploads/min triggers 429."""
        from backend.main import app, limiter
        from fastapi.testclient import TestClient

        limiter.reset()

        with TestClient(app) as c:
            for i in range(6):
                resp = c.post("/upload_csv", files=make_csv_upload(CSV_CONTENT))
                if resp.status_code == 429:
                    break
            assert resp.status_code == 429
            assert "too many" in resp.json()["detail"].lower()

    def test_query_rate_limit(self):
        """Exceeding 10 queries/min triggers 429."""
        from backend.main import app, limiter
        from fastapi.testclient import TestClient

        limiter.reset()

        with (
            patch("backend.main.generate_sql", return_value="SELECT * FROM data LIMIT 10"),
            patch("backend.main.generate_insights", return_value="ok"),
            patch("backend.main.generate_chart", return_value="<div></div>"),
            TestClient(app) as c,
        ):
            c.post("/upload_csv", files=make_csv_upload(CSV_CONTENT))
            limiter.reset()

            for i in range(11):
                resp = c.get("/query", params={"nl_query": "show data"})
                if resp.status_code == 429:
                    break
            assert resp.status_code == 429
