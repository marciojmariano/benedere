"""
Endpoints: Pedido
"""
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.pedido import (
    PedidoCreateRequest,
    PedidoResponse,
    PedidoUpdateRequest,
)
from app.core.auth0 import get_tenant_id
from app.domain.services.pedido_service import (
    OrcamentoNaoAprovadoError,
    PedidoJaExisteError,
    PedidoNaoEncontradoError,
    PedidoService,
    TransicaoStatusInvalidaError,
)
from app.infra.database.models.base import StatusPedido
from app.infra.database.session import get_session
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.orcamento_repository import OrcamentoRepository
from app.infra.repository.pedido_repository import PedidoRepository

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_pedido_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id)
) -> PedidoService:
    _tenant_id = uuid.UUID(tenant_id)
    return PedidoService(
        pedido_repo=PedidoRepository(session, tenant_id=_tenant_id),
        orcamento_repo=OrcamentoRepository(session, tenant_id=_tenant_id),
        ingrediente_repo=IngredienteRepository(session, tenant_id=_tenant_id),
        tenant_id=_tenant_id,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=PedidoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar pedido a partir de orçamento aprovado",
)
async def criar_pedido(
    body: PedidoCreateRequest,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.criar_de_orcamento(
            orcamento_id=body.orcamento_id,
            data_entrega_prevista=body.data_entrega_prevista,
            observacoes=body.observacoes,
        )
    except OrcamentoNaoAprovadoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PedidoJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=list[PedidoResponse],
    summary="Listar pedidos",
)
async def listar_pedidos(
    cliente_id: uuid.UUID | None = None,
    status_pedido: StatusPedido | None = None,
    service: PedidoService = Depends(get_pedido_service),
):
    return await service.listar(cliente_id=cliente_id, status=status_pedido)


@router.get(
    "/{pedido_id}",
    response_model=PedidoResponse,
    summary="Buscar pedido por ID",
)
async def buscar_pedido(
    pedido_id: uuid.UUID,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.buscar_por_id(pedido_id)
    except PedidoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{pedido_id}",
    response_model=PedidoResponse,
    summary="Atualizar dados do pedido",
)
async def atualizar_pedido(
    pedido_id: uuid.UUID,
    body: PedidoUpdateRequest,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.atualizar(
            pedido_id=pedido_id,
            data_entrega_prevista=body.data_entrega_prevista,
            data_entrega_realizada=body.data_entrega_realizada,
            observacoes=body.observacoes,
        )
    except PedidoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{pedido_id}/status",
    response_model=PedidoResponse,
    summary="Mudar status do pedido",
)
async def mudar_status(
    pedido_id: uuid.UUID,
    novo_status: StatusPedido,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.mudar_status(pedido_id, novo_status)
    except PedidoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TransicaoStatusInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
