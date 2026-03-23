import json

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..models.base import get_session
from ..models.user import User
from .jwt import verify_token

_bearer_scheme = HTTPBearer(auto_error=False)
_bearer_scheme_required = HTTPBearer()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer_scheme_required),
    session: Session = Depends(get_session),
) -> User:
    """FastAPI dependency: extracts and validates the JWT, returns the User."""
    payload = verify_token(creds.credentials, expected_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: Session = Depends(get_session),
) -> User | None:
    """Same as get_current_user but returns None instead of 401 when no token is present."""
    if creds is None:
        return None
    payload = verify_token(creds.credentials, expected_type="access")
    if payload is None:
        return None
    user_id: str | None = payload.get("sub")
    if user_id is None:
        return None
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def require_role(*role_names: str):
    """Returns a dependency that checks the user has at least one of the given roles."""

    def _checker(user: User = Depends(get_current_user)) -> User:
        user_role_names = set()
        for ur in user.roles:
            user_role_names.add(ur.role.name)
        if not user_role_names.intersection(role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(role_names)}",
            )
        return user

    return _checker


def require_permission(*permissions: str):
    """Returns a dependency that checks the user has all given permissions."""

    def _checker(user: User = Depends(get_current_user)) -> User:
        user_permissions: set[str] = set()
        for ur in user.roles:
            try:
                perms = json.loads(ur.role.permissions)
                user_permissions.update(perms)
            except (json.JSONDecodeError, TypeError):
                pass
        missing = set(permissions) - user_permissions
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        return user

    return _checker
