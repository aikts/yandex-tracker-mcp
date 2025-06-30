from mcp.server.auth.provider import AuthorizationCode
from pydantic import AnyUrl, BaseModel


class YandexOAuthState(BaseModel):
    redirect_uri: AnyUrl
    code_challenge: str
    scopes: list[str] | None = None
    redirect_uri_provided_explicitly: bool
    client_id: str
    resource: str | None = None  # RFC 8707 resource indicator


class YandexCallbackRequest(BaseModel):
    code: str
    state: str
    cid: str | None = None


class YandexOauthAuthorizationCode(AuthorizationCode):
    yandex_auth_code: str
