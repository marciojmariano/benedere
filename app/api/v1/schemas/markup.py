"""
Schemas Pydantic — IndiceMarkup e Markup
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


# ── IndiceMarkup Requests ─────────────────────────────────────────────────────

class IndiceMarkupCreateRequest(BaseModel):
    nome: str
    percentual: Decimal
    descricao: str | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        if len(v) > 100:
            raise ValueError("Nome deve ter no máximo 100 caracteres")
        return v

    @field_validator("percentual")
    @classmethod
    def validate_percentual(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Percentual deve ser maior que zero")
        if v >= 100:
            raise ValueError("Percentual deve ser menor que 100%")
        return round(v, 2)


class IndiceMarkupUpdateRequest(BaseModel):
    nome: str | None = None
    percentual: Decimal | None = None
    descricao: str | None = None

    @field_validator("percentual")
    @classmethod
    def validate_percentual(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("Percentual deve ser maior que zero")
        if v >= 100:
            raise ValueError("Percentual deve ser menor que 100%")
        return round(v, 2)


# ── IndiceMarkup Response ─────────────────────────────────────────────────────

class IndiceMarkupResponse(BaseModel):
    id: uuid.UUID
    nome: str
    percentual: Decimal
    descricao: str | None
    ativo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Markup Requests ───────────────────────────────────────────────────────────

class MarkupCreateRequest(BaseModel):
    nome: str
    descricao: str | None = None
    indices_ids: list[uuid.UUID]

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        if len(v) > 100:
            raise ValueError("Nome deve ter no máximo 100 caracteres")
        return v

    @field_validator("indices_ids")
    @classmethod
    def validate_indices(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        if not v:
            raise ValueError("Markup deve ter pelo menos um índice")
        if len(set(v)) != len(v):
            raise ValueError("Índices duplicados não são permitidos")
        return v


class MarkupUpdateRequest(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    indices_ids: list[uuid.UUID] | None = None

    @field_validator("indices_ids")
    @classmethod
    def validate_indices(cls, v: list[uuid.UUID] | None) -> list[uuid.UUID] | None:
        if v is None:
            return v
        if not v:
            raise ValueError("Markup deve ter pelo menos um índice")
        if len(set(v)) != len(v):
            raise ValueError("Índices duplicados não são permitidos")
        return v


# ── Markup Response ───────────────────────────────────────────────────────────

class MarkupIndiceResponse(BaseModel):
    """Representa o IndiceMarkup dentro da resposta do Markup."""
    id: uuid.UUID
    nome: str
    percentual: Decimal
    descricao: str | None
    ativo: bool

    model_config = {"from_attributes": True}


class MarkupResponse(BaseModel):
    id: uuid.UUID
    nome: str
    descricao: str | None
    fator: Decimal
    ativo: bool
    indices: list[MarkupIndiceResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_markup(cls, markup) -> "MarkupResponse":
        """Extrai os IndiceMarkup da tabela associativa MarkupIndice."""
        indices = [
            MarkupIndiceResponse(
                id=mi.indice.id,
                nome=mi.indice.nome,
                percentual=mi.indice.percentual,
                descricao=mi.indice.descricao,
                ativo=mi.indice.ativo,
            )
            for mi in markup.indices
        ]
        return cls(
            id=markup.id,
            nome=markup.nome,
            descricao=markup.descricao,
            fator=markup.fator,
            ativo=markup.ativo,
            indices=indices,
            created_at=markup.created_at,
            updated_at=markup.updated_at,
        )
