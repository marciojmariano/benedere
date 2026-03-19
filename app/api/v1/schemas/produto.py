"""
Schemas Pydantic — Produto e ProdutoComposicao
Tasks: 2.1.2, 2.2.2
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.infra.database.models.base import TipoRefeicao


# ── Composição (sub-schemas) ─────────────────────────────────────────────────

class ProdutoComposicaoCreateRequest(BaseModel):
    """Item da receita ao criar/atualizar composição."""
    ingrediente_id: uuid.UUID
    quantidade_g: Decimal
    ordem: int = 0

    @field_validator("quantidade_g")
    @classmethod
    def validate_quantidade(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return round(v, 2)


class ProdutoComposicaoResponse(BaseModel):
    """Retorno de um item da composição."""
    id: uuid.UUID
    ingrediente_id: uuid.UUID
    ingrediente_nome: str | None = None
    ingrediente_custo_unitario: Decimal | None = None
    quantidade_g: Decimal
    ordem: int
    # Campos calculados (preenchidos pelo service)
    custo_item: Decimal | None = None
    kcal_item: Decimal | None = None

    model_config = {"from_attributes": True}


# ── Produto — Requests ───────────────────────────────────────────────────────

class ProdutoCreateRequest(BaseModel):
    nome: str
    tipo_refeicao: TipoRefeicao | None = None
    descricao: str | None = None
    # Composição pode ser enviada junto na criação
    composicao: list[ProdutoComposicaoCreateRequest] | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        if len(v) > 255:
            raise ValueError("Nome deve ter no máximo 255 caracteres")
        return v


class ProdutoUpdateRequest(BaseModel):
    nome: str | None = None
    tipo_refeicao: TipoRefeicao | None = None
    descricao: str | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        return v


# ── Produto — Responses ──────────────────────────────────────────────────────

class ProdutoResponse(BaseModel):
    id: uuid.UUID
    nome: str
    tipo_refeicao: TipoRefeicao | None
    peso_total_g: Decimal
    descricao: str | None
    ativo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProdutoDetalheResponse(ProdutoResponse):
    """Produto com composição detalhada (usado no GET por ID)."""
    composicao: list[ProdutoComposicaoResponse] = []
    custo_total: Decimal | None = None
    kcal_total: Decimal | None = None
