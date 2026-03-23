"""Admin endpoints: audit logs, compliance reports, user management."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user, require_role
from ..models.audit import AuditLog
from ..models.base import get_session
from ..models.role import Role, UserRole
from ..models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None
    user_email: str | None = None
    action: str
    resource: str | None
    details: str | None
    ip_address: str | None
    created_at: str


class ComplianceReportResponse(BaseModel):
    total_users: int
    total_queries: int
    total_uploads: int
    total_connections: int
    generated_at: str


class UserAdminResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    roles: list[str]
    created_at: str


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------

@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    action: str | None = None,
    user_id: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    admin: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        q = q.where(AuditLog.action == action)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    q = q.offset(offset).limit(limit)
    logs = session.execute(q).scalars().all()
    result = []
    for log in logs:
        user_email = None
        if log.user_id:
            u = session.get(User, log.user_id)
            user_email = u.email if u else None
        result.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_email=user_email,
            action=log.action,
            resource=log.resource,
            details=log.details_json,
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat(),
        ))
    return result


# ---------------------------------------------------------------------------
# Compliance report
# ---------------------------------------------------------------------------

@router.get("/compliance/report", response_model=ComplianceReportResponse)
def compliance_report(
    admin: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    total_users = session.execute(select(func.count(User.id))).scalar() or 0
    total_queries = session.execute(
        select(func.count(AuditLog.id)).where(AuditLog.action == "query")
    ).scalar() or 0
    total_uploads = session.execute(
        select(func.count(AuditLog.id)).where(AuditLog.action == "upload")
    ).scalar() or 0
    from ..models.connection import DataConnection
    total_connections = session.execute(select(func.count(DataConnection.id))).scalar() or 0

    return ComplianceReportResponse(
        total_users=total_users,
        total_queries=total_queries,
        total_uploads=total_uploads,
        total_connections=total_connections,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[UserAdminResponse])
def list_users(
    admin: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    users = session.execute(select(User).order_by(User.created_at.desc())).scalars().all()
    return [
        UserAdminResponse(
            id=u.id, email=u.email, name=u.name, is_active=u.is_active,
            roles=[ur.role.name for ur in u.roles],
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.put("/users/{uid}/deactivate")
def deactivate_user(
    uid: str,
    admin: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    user = session.get(User, uid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    session.commit()
    return {"status": "deactivated"}


@router.put("/users/{uid}/activate")
def activate_user(
    uid: str,
    admin: User = Depends(require_role("admin")),
    session: Session = Depends(get_session),
):
    user = session.get(User, uid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    session.commit()
    return {"status": "activated"}
