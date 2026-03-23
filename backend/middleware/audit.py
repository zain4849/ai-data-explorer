"""Audit logging middleware: logs all API calls to the audit_logs table."""

import json
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..auth.jwt import verify_token
from ..logger_config import logger
from ..models.audit import AuditLog
from ..models.base import get_engine

# Paths to skip audit logging for
SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}

# Map HTTP methods + path patterns to action names
ACTION_MAP = {
    ("POST", "/upload_csv"): "upload",
    ("GET", "/query"): "query",
    ("POST", "/query/execute"): "query_execute",
    ("POST", "/execute/python"): "python_execute",
    ("POST", "/auth/register"): "register",
    ("POST", "/auth/login"): "login",
    ("POST", "/connections"): "connection_create",
    ("DELETE", "/connections"): "connection_delete",
    ("POST", "/export"): "export",
}


def _determine_action(method: str, path: str) -> str:
    for (m, p), action in ACTION_MAP.items():
        if method == m and path.startswith(p):
            return action
    return f"{method.lower()}:{path}"


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in SKIP_PATHS or path.startswith("/static"):
            return await call_next(request)

        start = time.time()
        try:
            response: Response = await call_next(request)
        except Exception:
            from starlette.responses import JSONResponse as _JSONResp
            logger.exception("Unhandled error in request %s %s", request.method, path)
            response = _JSONResp(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        elapsed_ms = int((time.time() - start) * 1000)

        # Extract user ID from Authorization header if present
        user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = verify_token(token)
            if payload:
                user_id = payload.get("sub")

        # Get client IP
        ip_address = request.client.host if request.client else None

        action = _determine_action(request.method, path)

        details = {
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        }

        try:
            from sqlalchemy.orm import Session
            engine = get_engine()
            with Session(engine) as session:
                log = AuditLog(
                    user_id=user_id,
                    action=action,
                    resource=path,
                    details_json=json.dumps(details),
                    ip_address=ip_address,
                )
                session.add(log)
                session.commit()
        except Exception as exc:
            logger.debug("Audit log write failed (DB may not be available): %s", exc)

        return response
