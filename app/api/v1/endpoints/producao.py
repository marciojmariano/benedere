"""
Endpoints: Producao — Ordem de Produção / Explosão BOM
"""
import uuid
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.producao import ExplosaoProducaoResponse, MapaMontagemResponse
from app.core.auth0 import get_tenant_id
from app.domain.services.producao_service import ProducaoService
from app.infra.database.models.base import StatusPedido
from app.infra.database.session import get_session
from app.infra.repository.pedido_repository import PedidoRepository

router = APIRouter(prefix="/producao", tags=["Producao"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_producao_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id),
) -> ProducaoService:
    _tenant_id = uuid.UUID(tenant_id)
    return ProducaoService(
        pedido_repo=PedidoRepository(session, tenant_id=_tenant_id),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/explosao",
    response_model=ExplosaoProducaoResponse,
    summary="Gerar Ordem de Produção — Explosão de Insumos (BOM)",
)
async def explosao_producao(
    data_inicio: date = Query(..., description="Data inicial do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data final do período (YYYY-MM-DD)"),
    status: Annotated[list[StatusPedido], Query()] = [StatusPedido.APROVADO, StatusPedido.EM_PRODUCAO],
    filtro_data: Literal["entrega", "criacao"] = Query(
        default="entrega",
        description="Campo de data usado no filtro: 'entrega' (data_entrega_prevista) ou 'criacao' (created_at)",
    ),
    service: ProducaoService = Depends(get_producao_service),
):
    return await service.gerar_explosao(
        data_inicio=data_inicio,
        data_fim=data_fim,
        status_list=status,
        filtro_data=filtro_data,
    )


@router.get(
    "/mapa-montagem",
    response_model=MapaMontagemResponse,
    summary="Mapa de Montagem — detalhamento por cliente/pedido/marmita",
)
async def mapa_montagem(
    data_inicio: date = Query(..., description="Data inicial do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data final do período (YYYY-MM-DD)"),
    status: Annotated[list[StatusPedido], Query()] = [StatusPedido.APROVADO, StatusPedido.EM_PRODUCAO],
    filtro_data: Literal["entrega", "criacao"] = Query(
        default="entrega",
        description="Campo de data usado no filtro: 'entrega' (data_entrega_prevista) ou 'criacao' (created_at)",
    ),
    service: ProducaoService = Depends(get_producao_service),
):
    return await service.gerar_mapa_montagem(
        data_inicio=data_inicio,
        data_fim=data_fim,
        status_list=status,
        filtro_data=filtro_data,
    )
