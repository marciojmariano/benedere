"""
Autenticação Auth0 — validação de JWT e extração de tenant_id

Em AMBIENTE=desenvolvimento sem token → usa tenant_id fixo de dev.
Com token (qualquer ambiente) → valida normalmente via Auth0.
"""
import httpx
from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from app.core.config import settings

NAMESPACE = "https://api.benedere.com.br"

# Tenant fixo pra desenvolvimento
DEV_TENANT_ID = "5afc3d1d-055b-4c5a-8744-98ab532fa6c1"


# ── JWKS (chaves públicas do Auth0) ───────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def _get_signing_key(token: str) -> str:
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
    signing_key = _get_signing_key(token)
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


def _extract_bearer_token(request: Request) -> str | None:
    """Extrai o token Bearer do header Authorization manualmente."""
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def get_token_payload(request: Request) -> TokenPayload:
    """
    Extrai e valida o token do header Authorization.
    Em dev sem token → retorna payload fake com tenant_id fixo.
    """
    token = _extract_bearer_token(request)

    if token is None:
        if settings.is_debug():
            return TokenPayload({
                "sub": "dev|local",
                f"{NAMESPACE}/tenant_id": DEV_TENANT_ID,
                "email": "dev@benedere.local",
            })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
        )

    return TokenPayload(_validar_token(token))


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


def get_current_user(
    payload: TokenPayload = Depends(get_token_payload),
) -> TokenPayload:
    """Retorna o usuário atual autenticado."""
    return payload