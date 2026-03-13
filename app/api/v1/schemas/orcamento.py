"""
Schemas Pydantic — Orcamento e OrcamentoItem
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.infra.database.models.base import StatusOrcamento, UnidadeMedida


# ── OrcamentoItem Requests ────────────────────────────────────────────────────

class OrcamentoItemCreateRequest(BaseModel):
    ingrediente_id: uuid.UUID
    quantidade: Decimal
    unidade_medida: UnidadeMedida
    observacoes: str | None = None

    @field_validator("quantidade")
    @classmethod
    def validate_quantidade(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return round(v, 3)


# ── Orcamento Requests ────────────────────────────────────────────────────────

class OrcamentoCreateRequest(BaseModel):
    cliente_id: uuid.UUID
    markup_id: uuid.UUID | None = None
    custo_embalagem: Decimal = Decimal("0")
    taxa_entrega: Decimal = Decimal("0")
    validade_dias: int = 7
    observacoes: str | None = None
    itens: list[OrcamentoItemCreateRequest]

    @field_validator("itens")
    @classmethod
    def validate_itens(cls, v: list) -> list:
        if not v:
            raise ValueError("Orçamento deve ter pelo menos um item")
        return v

    @field_validator("custo_embalagem", "taxa_entrega")
    @classmethod
    def validate_custos(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Valor não pode ser negativo")
        return round(v, 2)

    @field_validator("validade_dias")
    @classmethod
    def validate_validade(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Validade deve ser de pelo menos 1 dia")
        if v > 365:
            raise ValueError("Validade não pode exceder 365 dias")
        return v


class OrcamentoUpdateRequest(BaseModel):
    """Apenas campos editáveis — somente quando status=RASCUNHO."""
    markup_id: uuid.UUID | None = None
    custo_embalagem: Decimal | None = None
    taxa_entrega: Decimal | None = None
    validade_dias: int | None = None
    observacoes: str | None = None


# ── Responses ─────────────────────────────────────────────────────────────────

class OrcamentoItemResponse(BaseModel):
    id: uuid.UUID
    ingrediente_id: uuid.UUID
    quantidade: Decimal
    unidade_medida: UnidadeMedida
    custo_unitario_snapshot: Decimal
    markup_fator_snapshot: Decimal | None
    custo_total_item: Decimal
    preco_item_com_markup: Decimal
    observacoes: str | None

    model_config = {"from_attributes": True}


class OrcamentoResponse(BaseModel):
    id: uuid.UUID
    numero: str
    cliente_id: uuid.UUID
    status: StatusOrcamento
    markup_id: uuid.UUID | None
    custo_ingredientes: Decimal
    custo_embalagem: Decimal
    taxa_entrega: Decimal
    custo_total: Decimal
    preco_final: Decimal
    validade_dias: int
    observacoes: str | None
    itens: list[OrcamentoItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
