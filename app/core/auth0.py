"""
Autenticação Auth0 — validação de JWT e extração de tenant_id
"""
import httpx
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

# ── Bearer scheme ─────────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer()

NAMESPACE = "https://api.benedere.com.br"


# ── JWKS (chaves públicas do Auth0) ───────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Busca as chaves públicas do Auth0 (cached)."""
    url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    print(f"DEBUG BACKEND: Tentando acessar a URL: {url}") # <-- ADICIONE ISSO
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def _get_signing_key(token: str) -> str:
    """Extrai a chave de assinatura correta do JWKS baseado no kid do token."""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido — header malformado",
        )

    jwks = _get_jwks()
    kid = unverified_header.get("kid")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Chave de assinatura não encontrada",
    )


# ── Validação do token ────────────────────────────────────────────────────────

def _validar_token(token: str) -> dict:
    """Valida o JWT e retorna o payload."""
    signing_key = _get_signing_key(token)
    print(f"DEBUG SIGNING KEY: {signing_key}")
    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=settings.auth0_algorithms_list,
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
        return payload
    except JWTError as e:
        print(f"DEBUG JWT ERROR: {e}")  # ← adicione esta linha
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Dependencies FastAPI ──────────────────────────────────────────────────────

class TokenPayload:
    def __init__(self, payload: dict):
        self.sub: str = payload.get("sub", "")
        self.tenant_id: str | None = payload.get(f"{NAMESPACE}/tenant_id")
        self.email: str | None = payload.get("email")
        self.raw: dict = payload


def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> TokenPayload:
    """Valida o Bearer token e retorna o payload."""
    return TokenPayload(_validar_token(credentials.credentials))


def get_tenant_id(
    payload: TokenPayload = Depends(get_token_payload),
) -> str:
    """Extrai o tenant_id do JWT. Lança 403 se não encontrado."""
    if not payload.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant_id não encontrado no token. Usuário não está associado a um tenant.",
        )
    return payload.tenant_id

def get_tenant_id(
    payload: TokenPayload = Depends(get_token_payload),
) -> str:
    print(f"DEBUG TENANT PAYLOAD: {payload.raw}")
    if not payload.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant_id não encontrado no token.",
        )
    return payload.tenant_id

def get_current_user(
    payload: TokenPayload = Depends(get_token_payload),
) -> TokenPayload:
    """Retorna o usuário atual autenticado."""
    return payload
