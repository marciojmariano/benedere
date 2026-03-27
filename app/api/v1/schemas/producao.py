"""
Schemas Pydantic — Producao (Ordem de Produção / Explosão BOM + Mapa de Montagem)
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.infra.database.models.base import TipoIngrediente, TipoItem, TipoRefeicao, UnidadeMedida


class ExplosaoIngredienteItem(BaseModel):
    ingrediente_id: uuid.UUID
    ingrediente_nome: str
    tipo: TipoIngrediente
    unidade_medida: UnidadeMedida
    quantidade_total_g: Decimal
    custo_kg_medio: Decimal | None
    custo_total_estimado: Decimal | None
    saldo_atual: Decimal | None
    deficit_g: Decimal | None


class ExplosaoPedidoDetalhe(BaseModel):
    pedido_id: uuid.UUID
    pedido_numero: str
    cliente_nome: str
    data_entrega_prevista: datetime | None
    total_itens: int


class ExplosaoProducaoResponse(BaseModel):
    periodo_inicio: date
    periodo_fim: date
    total_pedidos: int
    total_ingredientes: int
    custo_total_estimado: Decimal
    ingredientes: list[ExplosaoIngredienteItem]
    pedidos: list[ExplosaoPedidoDetalhe]


# ── Mapa de Montagem ──────────────────────────────────────────────────────────

class MapaComposicaoItem(BaseModel):
    ingrediente_nome: str
    quantidade_g: Decimal


class MapaItemDetalhe(BaseModel):
    nome_snapshot: str
    tipo_refeicao: TipoRefeicao | None
    tipo: TipoItem
    quantidade: int
    embalagem_nome: str | None
    composicao: list[MapaComposicaoItem]


class MapaPedidoDetalhe(BaseModel):
    pedido_id: uuid.UUID
    pedido_numero: str
    data_entrega_prevista: datetime | None
    observacoes: str | None
    itens: list[MapaItemDetalhe]


class MapaClienteGrupo(BaseModel):
    cliente_id: uuid.UUID
    cliente_nome: str
    cliente_endereco: str | None
    cliente_observacoes: str | None
    pedidos: list[MapaPedidoDetalhe]


class MapaMontagemResponse(BaseModel):
    periodo_inicio: date
    periodo_fim: date
    total_clientes: int
    total_pedidos: int
    total_itens: int
    clientes: list[MapaClienteGrupo]
