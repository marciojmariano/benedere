"""
Schemas Pydantic — Pedido e PedidoItem
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.infra.database.models.base import StatusPedido, UnidadeMedida


# ── Requests ──────────────────────────────────────────────────────────────────

class PedidoCreateRequest(BaseModel):
    """Pedido é criado a partir de um orçamento aprovado."""
    orcamento_id: uuid.UUID
    data_entrega_prevista: datetime | None = None
    observacoes: str | None = None


class PedidoUpdateRequest(BaseModel):
    """Apenas campos operacionais são editáveis após criação."""
    data_entrega_prevista: datetime | None = None
    data_entrega_realizada: datetime | None = None
    observacoes: str | None = None


# ── Responses ─────────────────────────────────────────────────────────────────

class PedidoItemResponse(BaseModel):
    id: uuid.UUID
    ingrediente_id: uuid.UUID
    nome_ingrediente_snapshot: str
    quantidade: Decimal
    unidade_medida: UnidadeMedida
    custo_unitario_snapshot: Decimal
    custo_total_item: Decimal

    model_config = {"from_attributes": True}


class PedidoResponse(BaseModel):
    id: uuid.UUID
    numero: str
    orcamento_id: uuid.UUID
    cliente_id: uuid.UUID
    status: StatusPedido
    valor_total: Decimal
    taxa_entrega: Decimal
    custo_embalagem: Decimal
    data_entrega_prevista: datetime | None
    data_entrega_realizada: datetime | None
    observacoes: str | None
    itens: list[PedidoItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
