"""
Schemas Pydantic — Pedido, PedidoItem, PedidoItemComposicao
Tasks: 3.1.2, 3.2.2, 3.3.1
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.infra.database.models.base import StatusPedido, TipoRefeicao, TipoItem


# ── PedidoItemComposicao ─────────────────────────────────────────────────────

class PedidoItemComposicaoCreateRequest(BaseModel):
    """Ingrediente na composição manual (item personalizado)."""
    ingrediente_id: uuid.UUID
    quantidade_g: Decimal

    @field_validator("quantidade_g")
    @classmethod
    def validate_quantidade(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return round(v, 2)


class PedidoItemComposicaoResponse(BaseModel):
    id: uuid.UUID
    ingrediente_id: uuid.UUID
    ingrediente_nome_snap: str
    quantidade_g: Decimal
    custo_kg_snapshot: Decimal
    kcal_snapshot: Decimal

    model_config = {"from_attributes": True}


# ── PedidoItem ───────────────────────────────────────────────────────────────

class PedidoItemCreateRequest(BaseModel):
    """
    Criação de item no pedido.
    - tipo=serie:         produto_id obrigatório, composição clonada automaticamente.
    - tipo=personalizado: produto_id null, nome e composição obrigatórios.
    """
    tipo: TipoItem
    produto_id: uuid.UUID | None = None
    nome: str | None = None
    tipo_refeicao: TipoRefeicao | None = None
    quantidade: int = 1
    # Composição manual — só pra personalizado
    composicao: list[PedidoItemComposicaoCreateRequest] | None = None

    @field_validator("quantidade")
    @classmethod
    def validate_quantidade(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantidade deve ser pelo menos 1")
        return v


class PedidoItemUpdateRequest(BaseModel):
    """Atualização de item (só quando pedido em rascunho)."""
    nome: str | None = None
    tipo_refeicao: TipoRefeicao | None = None
    quantidade: int | None = None
    composicao: list[PedidoItemComposicaoCreateRequest] | None = None

    @field_validator("quantidade")
    @classmethod
    def validate_quantidade(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("Quantidade deve ser pelo menos 1")
        return v


class PedidoItemResponse(BaseModel):
    id: uuid.UUID
    produto_id: uuid.UUID | None
    nome_snapshot: str
    tipo_refeicao: TipoRefeicao | None
    tipo: TipoItem
    quantidade: int
    preco_unitario: Decimal
    preco_total: Decimal
    etiqueta_impressa: bool = False
    composicao: list[PedidoItemComposicaoResponse] = []
    embalagem_ingrediente_id: uuid.UUID | None = None
    embalagem_nome_snapshot: str | None = None
    embalagem_custo_snapshot: Decimal | None = None

    model_config = {"from_attributes": True}


# ── Pedido ───────────────────────────────────────────────────────────────────

class PedidoCreateRequest(BaseModel):
    cliente_id: uuid.UUID
    markup_id: uuid.UUID | None = None
    observacoes: str | None = None
    data_entrega_prevista: datetime | None = None


class PedidoUpdateRequest(BaseModel):
    observacoes: str | None = None
    data_entrega_prevista: datetime | None = None


class StatusUpdateRequest(BaseModel):
    status: StatusPedido


class PedidoResponse(BaseModel):
    id: uuid.UUID
    numero: str
    cliente_id: uuid.UUID
    markup_id: uuid.UUID | None
    status: StatusPedido
    valor_total: Decimal
    observacoes: str | None
    data_entrega_prevista: datetime | None
    data_entrega_realizada: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PedidoDetalheResponse(PedidoResponse):
    """Pedido com itens e composição detalhada."""
    itens: list[PedidoItemResponse] = []


class PedidoResumo(BaseModel):
    """Resumo compacto pra listagem."""
    id: uuid.UUID
    numero: str
    cliente_id: uuid.UUID
    cliente_nome: str
    status: StatusPedido
    valor_total: Decimal
    total_itens: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Impressão de etiquetas em lote ───────────────────────────────────────────

class IngredienteEtiquetaSchema(BaseModel):
    nome: str
    peso_g: float


class BulkLabelItemResponse(BaseModel):
    """Dados de uma etiqueta pronta para impressão (um por PedidoItem)."""
    item_id: uuid.UUID
    pedido_numero: str
    cliente_nome: str
    tipo_refeicao: str | None
    data_fabricacao: str
    data_validade: str
    empresa_nome: str
    empresa_cnpj: str
    ingredientes: list[IngredienteEtiquetaSchema]
    ingredientes_html: str = ""
    etiqueta_impressa: bool
    copia: int = 1
    total_copias: int = 1


class BulkLabelDataRequest(BaseModel):
    pedido_ids: list[uuid.UUID]


class MarcarImpressasRequest(BaseModel):
    item_ids: list[uuid.UUID]
