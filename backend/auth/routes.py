"""Authentication routes: register, login, refresh, OAuth callbacks, profile."""

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models.base import get_session
from ..models.role import Role, UserRole
from ..models.user import User
from .dependencies import get_current_user
from .jwt import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from .oauth import oauth

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    roles: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assign_default_role(session: Session, user: User):
    """Assign the 'analyst' role to new users, creating it if needed."""
    role = session.execute(select(Role).where(Role.name == "analyst")).scalar_one_or_none()
    if role is None:
        role = Role(
            name="analyst",
            permissions=json.dumps([
                "execute_queries", "view_dashboards", "export_data", "manage_connections"
            ]),
        )
        session.add(role)
        session.flush()
    session.add(UserRole(user_id=user.id, role_id=role.id))


def _build_token_response(user: User) -> TokenResponse:
    data = {"sub": user.id, "email": user.email}
    return TokenResponse(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
    )


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        roles=[ur.role.name for ur in user.roles],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    session.flush()
    _assign_default_role(session, user)
    session.commit()
    session.refresh(user)
    return _build_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    user = session.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if user is None or user.password_hash is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    return _build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, session: Session = Depends(get_session)):
    payload = verify_token(body.refresh_token, expected_type="refresh")
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user_id = payload.get("sub")
    user = session.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return _build_token_response(user)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return _user_response(user)


# ---------------------------------------------------------------------------
# OAuth2 routes
# ---------------------------------------------------------------------------

SUPPORTED_PROVIDERS = {"google", "github", "microsoft"}


@router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    client = oauth.create_client(provider)
    if client is None:
        raise HTTPException(status_code=400, detail=f"Provider {provider} is not configured")
    redirect_uri = str(request.url_for("oauth_callback", provider=provider))
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(
    provider: str,
    request: Request,
    session: Session = Depends(get_session),
):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    client = oauth.create_client(provider)
    if client is None:
        raise HTTPException(status_code=400, detail=f"Provider {provider} is not configured")

    token = await client.authorize_access_token(request)

    if provider == "google":
        user_info = token.get("userinfo", {})
        email = user_info.get("email")
        name = user_info.get("name", email)
        provider_id = user_info.get("sub")
    elif provider == "github":
        resp = await client.get("user", token=token)
        user_info = resp.json()
        email = user_info.get("email")
        if not email:
            emails_resp = await client.get("user/emails", token=token)
            emails = emails_resp.json()
            primary = next((e for e in emails if e.get("primary")), None)
            email = primary["email"] if primary else None
        name = user_info.get("name") or user_info.get("login", "")
        provider_id = str(user_info.get("id"))
    elif provider == "microsoft":
        user_info = token.get("userinfo", {})
        email = user_info.get("email") or user_info.get("preferred_username")
        name = user_info.get("name", email)
        provider_id = user_info.get("sub")
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from OAuth provider")

    user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            name=name,
            oauth_provider=provider,
            oauth_provider_id=provider_id,
        )
        session.add(user)
        session.flush()
        _assign_default_role(session, user)
        session.commit()
        session.refresh(user)
    elif user.oauth_provider is None:
        user.oauth_provider = provider
        user.oauth_provider_id = provider_id
        session.commit()

    token_resp = _build_token_response(user)
    # Return tokens as JSON; the frontend will read them and store.
    return token_resp
