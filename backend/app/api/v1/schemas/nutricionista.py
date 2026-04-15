"""
Schemas Pydantic — Nutricionista
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────

class NutricionistaCreateRequest(BaseModel):
    nome: str
    crn: str | None = None
    email: EmailStr | None = None
    telefone: str | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        if len(v) > 255:
            raise ValueError("Nome deve ter no máximo 255 caracteres")
        return v

    @field_validator("crn")
    @classmethod
    def validate_crn(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().upper()
        if len(v) < 3:
            raise ValueError("CRN inválido")
        return v

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Remove caracteres não numéricos para validação
        digits = "".join(filter(str.isdigit, v))
        if len(digits) < 10 or len(digits) > 11:
            raise ValueError("Telefone deve ter 10 ou 11 dígitos")
        return v.strip()


class NutricionistaUpdateRequest(BaseModel):
    nome: str | None = None
    crn: str | None = None
    email: EmailStr | None = None
    telefone: str | None = None

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

class NutricionistaResponse(BaseModel):
    id: uuid.UUID
    nome: str
    crn: str | None
    email: str | None
    telefone: str | None
    ativo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
