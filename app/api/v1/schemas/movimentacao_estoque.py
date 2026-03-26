"""
Schemas Pydantic — MovimentacaoEstoque
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.infra.database.models.base import TipoMovimentacao


# ── Requests ──────────────────────────────────────────────────────────────────

class EntradaEstoqueCreateRequest(BaseModel):
    ingrediente_id: uuid.UUID
    quantidade: Decimal
    preco_unitario_custo: Decimal
    data_movimentacao: date
    observacoes: str | None = None

    @field_validator("quantidade")
    @classmethod
    def validate_quantidade(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return round(v, 4)

    @field_validator("preco_unitario_custo")
    @classmethod
    def validate_preco(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Preço unitário deve ser maior que zero")
        return round(v, 4)


# ── Importação Excel ──────────────────────────────────────────────────────────

class ImportacaoLinhaErro(BaseModel):
    linha: int
    ingrediente_nome: str
    mensagem: str


class ImportacaoEstoqueResponse(BaseModel):
    total_linhas: int
    importadas: int
    erros: list[ImportacaoLinhaErro]


# ── Responses ─────────────────────────────────────────────────────────────────

class MovimentacaoEstoqueResponse(BaseModel):
    id: uuid.UUID
    ingrediente_id: uuid.UUID
    ingrediente_nome: str
    tipo: TipoMovimentacao
    quantidade: Decimal
    preco_unitario_custo: Decimal
    data_movimentacao: date
    observacoes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_nome(cls, obj) -> "MovimentacaoEstoqueResponse":
        return cls(
            id=obj.id,
            ingrediente_id=obj.ingrediente_id,
            ingrediente_nome=obj.ingrediente.nome if obj.ingrediente else "",
            tipo=obj.tipo,
            quantidade=obj.quantidade,
            preco_unitario_custo=obj.preco_unitario_custo,
            data_movimentacao=obj.data_movimentacao,
            observacoes=obj.observacoes,
            created_at=obj.created_at,
        )
