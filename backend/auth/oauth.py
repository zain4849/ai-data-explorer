"""OAuth2 provider configurations for Google, GitHub, and Microsoft."""

from authlib.integrations.starlette_client import OAuth

from ..config import settings

oauth = OAuth()

# Google
if settings.oauth_google_client_id:
    oauth.register(
        name="google",
        client_id=settings.oauth_google_client_id,
        client_secret=settings.oauth_google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

# GitHub
if settings.oauth_github_client_id:
    oauth.register(
        name="github",
        client_id=settings.oauth_github_client_id,
        client_secret=settings.oauth_github_client_secret,
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},
    )

# Microsoft (Azure AD)
if settings.oauth_microsoft_client_id:
    oauth.register(
        name="microsoft",
        client_id=settings.oauth_microsoft_client_id,
        client_secret=settings.oauth_microsoft_client_secret,
        server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
