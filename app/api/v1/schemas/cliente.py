"""
Schemas Pydantic — Cliente
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────

class ClienteCreateRequest(BaseModel):
    nome: str
    email: EmailStr | None = None
    telefone: str | None = None
    endereco: str | None = None
    observacoes: str | None = None
    nutricionista_id: uuid.UUID | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        if len(v) > 255:
            raise ValueError("Nome deve ter no máximo 255 caracteres")
        return v

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = "".join(filter(str.isdigit, v))
        if len(digits) < 10 or len(digits) > 11:
            raise ValueError("Telefone deve ter 10 ou 11 dígitos")
        return v.strip()


class ClienteUpdateRequest(BaseModel):
    nome: str | None = None
    email: EmailStr | None = None
    telefone: str | None = None
    endereco: str | None = None
    observacoes: str | None = None
    nutricionista_id: uuid.UUID | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        return v


# ── Responses ─────────────────────────────────────────────────────────────────

class ClienteResponse(BaseModel):
    id: uuid.UUID
    nome: str
    email: str | None
    telefone: str | None
    endereco: str | None
    observacoes: str | None
    ativo: bool
    nutricionista_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
