"""
Schemas Pydantic — Tenant
Responsabilidade: validar entrada e formatar saída da API.
O tenant_id NUNCA é exposto como campo editável.
"""
import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.infra.database.models.base import TenantPlano, TenantStatus


# ── Requests (entrada) ────────────────────────────────────────────────────────

class TenantCreateRequest(BaseModel):
    nome: str
    slug: str
    email_dono: EmailStr
    plano: TenantPlano = TenantPlano.FREE

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        if len(v) > 255:
            raise ValueError("Nome deve ter no máximo 255 caracteres")
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError(
                "Slug deve conter apenas letras minúsculas, números e hífens "
                "(ex: minha-empresa)"
            )
        if len(v) < 2:
            raise ValueError("Slug deve ter pelo menos 2 caracteres")
        if len(v) > 100:
            raise ValueError("Slug deve ter no máximo 100 caracteres")
        return v


class LabelDimensionsSchema(BaseModel):
    w: int = Field(ge=20, le=300, description="Largura em mm")
    h: int = Field(ge=20, le=300, description="Altura em mm")


class LabelSettingsUpdateRequest(BaseModel):
    template_delta: Any | None = None
    html_output: str | None = None
    dimensions: LabelDimensionsSchema | None = None

    @field_validator("html_output")
    @classmethod
    def sanitize_html(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) > 50_000:
            raise ValueError("html_output excede o limite de 50KB")
        # Strip tags e atributos perigosos
        import re as _re
        v = _re.sub(r"<script[\s\S]*?</script>", "", v, flags=_re.IGNORECASE)
        v = _re.sub(r"<iframe[\s\S]*?</iframe>", "", v, flags=_re.IGNORECASE)
        v = _re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', "", v, flags=_re.IGNORECASE)
        return v


class TenantUpdateRequest(BaseModel):
    """Apenas campos editáveis pelo usuário."""
    nome: str | None = None
    email_dono: EmailStr | None = None
    markup_id_padrao: uuid.UUID | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        return v


# ── Responses (saída) ─────────────────────────────────────────────────────────

class TenantResponse(BaseModel):
    """
    ⚠️ Não expõe tenant_id — o frontend usa slug para identificar o tenant.
    """
    slug: str
    nome: str
    email_dono: str
    plano: TenantPlano
    status: TenantStatus
    markup_id_padrao: uuid.UUID | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class TenantDetailResponse(TenantResponse):
    """Resposta detalhada — inclui id apenas para uso interno/admin."""
    id: uuid.UUID
    ativo: bool
    updated_at: datetime
    etiqueta_template_delta: Any | None = None
    etiqueta_html_output: str | None = None
    etiqueta_largura_mm: int | None = None
    etiqueta_altura_mm: int | None = None
