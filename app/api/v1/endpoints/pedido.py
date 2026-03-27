"""
Endpoints: Pedido
Tasks: 3.1.5, 3.1.6, 3.3.4, 3.3.5, 3.3.6
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.pedido import (
    PedidoCreateRequest,
    PedidoUpdateRequest,
    PedidoDetalheResponse,
    PedidoResumo,
    PedidoResponse,
    PedidoItemCreateRequest,
    PedidoItemUpdateRequest,
    PedidoItemResponse,
    StatusUpdateRequest,
)
from app.core.auth0 import get_tenant_id
from app.domain.services.pedido_service import (
    PedidoService,
    PedidoNaoEncontradoError,
    PedidoNaoEditavelError,
    TransicaoStatusInvalidaError,
    ClienteNaoEncontradoError,
    ProdutoNaoEncontradoError,
    IngredienteNaoEncontradoError,
    ItemNaoEncontradoError,
    ComposicaoVaziaError,
    NomeObrigatorioError,
)
from app.infra.database.models.base import StatusPedido
from app.infra.database.session import get_session
from app.infra.repository.pedido_repository import PedidoRepository
from app.infra.repository.produto_repository import ProdutoRepository
from app.infra.repository.produto_composicao_repository import ProdutoComposicaoRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.markup_repository import MarkupRepository
from app.infra.repository.cliente_repository import ClienteRepository
from app.infra.repository.tenant_repository import TenantRepository
from app.infra.repository.faixa_peso_embalagem_repository import FaixaPesoEmbalagemRepository

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_pedido_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id),
) -> PedidoService:
    _tenant_id = uuid.UUID(tenant_id)
    return PedidoService(
        pedido_repo=PedidoRepository(session, tenant_id=_tenant_id),
        produto_repo=ProdutoRepository(session, tenant_id=_tenant_id),
        composicao_repo=ProdutoComposicaoRepository(session),
        ingrediente_repo=IngredienteRepository(session, tenant_id=_tenant_id),
        markup_repo=MarkupRepository(session, tenant_id=_tenant_id),
        cliente_repo=ClienteRepository(session, tenant_id=_tenant_id),
        tenant_repo=TenantRepository(session),
        faixa_repo=FaixaPesoEmbalagemRepository(session, tenant_id=_tenant_id),
        tenant_id=_tenant_id,
    )


# ── Helpers de erro ──────────────────────────────────────────────────────────

def _handle_not_found(e: Exception):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

def _handle_bad_request(e: Exception):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

def _handle_conflict(e: Exception):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ── CRUD Pedido ──────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=PedidoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar pedido (status=rascunho)",
)
async def criar_pedido(
    body: PedidoCreateRequest,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.criar(
            cliente_id=body.cliente_id,
            markup_id=body.markup_id,
            observacoes=body.observacoes,
            data_entrega_prevista=body.data_entrega_prevista,
        )
    except ClienteNaoEncontradoError as e:
        _handle_not_found(e)


@router.get(
    "/",
    response_model=list[PedidoResumo],
    summary="Listar pedidos (com filtros opcionais)",
)
async def listar_pedidos(
    status_filter: StatusPedido | None = Query(None, alias="status"),
    cliente_id: uuid.UUID | None = None,
    service: PedidoService = Depends(get_pedido_service),
):
    pedidos = await service.listar(status=status_filter, cliente_id=cliente_id)
    return [
        PedidoResumo(
            id=p.id,
            numero=p.numero,
            cliente_id=p.cliente_id,
            status=p.status,
            valor_total=p.valor_total,
            total_itens=len(p.itens),
            created_at=p.created_at,
        )
        for p in pedidos
    ]


@router.get(
    "/{pedido_id}",
    response_model=PedidoDetalheResponse,
    summary="Buscar pedido por ID (com itens e composição)",
)
async def buscar_pedido(
    pedido_id: uuid.UUID,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.buscar_por_id(pedido_id)
    except PedidoNaoEncontradoError as e:
        _handle_not_found(e)


@router.patch(
    "/{pedido_id}",
    response_model=PedidoResponse,
    summary="Atualizar pedido (só em rascunho)",
)
async def atualizar_pedido(
    pedido_id: uuid.UUID,
    body: PedidoUpdateRequest,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.atualizar(
            pedido_id=pedido_id,
            observacoes=body.observacoes,
            data_entrega_prevista=body.data_entrega_prevista,
        )
    except PedidoNaoEncontradoError as e:
        _handle_not_found(e)
    except PedidoNaoEditavelError as e:
        _handle_bad_request(e)


@router.delete(
    "/{pedido_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar pedido (só em rascunho)",
)
async def deletar_pedido(
    pedido_id: uuid.UUID,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        await service.deletar(pedido_id)
    except PedidoNaoEncontradoError as e:
        _handle_not_found(e)
    except PedidoNaoEditavelError as e:
        _handle_bad_request(e)


# ── Transição de status ──────────────────────────────────────────────────────

@router.patch(
    "/{pedido_id}/status",
    response_model=PedidoResponse,
    summary="Avançar status do pedido (máquina de estados)",
)
async def transicionar_status(
    pedido_id: uuid.UUID,
    body: StatusUpdateRequest,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.transicionar_status(pedido_id, body.status)
    except PedidoNaoEncontradoError as e:
        _handle_not_found(e)
    except TransicaoStatusInvalidaError as e:
        _handle_conflict(e)


# ── Duplicar pedido ──────────────────────────────────────────────────────────

@router.post(
    "/{pedido_id}/duplicar",
    response_model=PedidoDetalheResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicar pedido como novo rascunho",
)
async def duplicar_pedido(
    pedido_id: uuid.UUID,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.duplicar(pedido_id)
    except PedidoNaoEncontradoError as e:
        _handle_not_found(e)


# ── Itens do pedido ──────────────────────────────────────────────────────────

@router.post(
    "/{pedido_id}/itens",
    response_model=PedidoDetalheResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar item ao pedido (série ou personalizado)",
)
async def adicionar_item(
    pedido_id: uuid.UUID,
    body: PedidoItemCreateRequest,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        composicao = None
        if body.composicao:
            composicao = [item.model_dump() for item in body.composicao]

        return await service.adicionar_item(
            pedido_id=pedido_id,
            tipo=body.tipo,
            produto_id=body.produto_id,
            nome=body.nome,
            tipo_refeicao=body.tipo_refeicao,
            quantidade=body.quantidade,
            composicao_manual=composicao,
        )
    except PedidoNaoEncontradoError as e:
        _handle_not_found(e)
    except PedidoNaoEditavelError as e:
        _handle_bad_request(e)
    except (ProdutoNaoEncontradoError, IngredienteNaoEncontradoError) as e:
        _handle_not_found(e)
    except (ComposicaoVaziaError, NomeObrigatorioError) as e:
        _handle_bad_request(e)


@router.put(
    "/{pedido_id}/itens/{item_id}",
    response_model=PedidoDetalheResponse,
    summary="Atualizar item do pedido (só em rascunho)",
)
async def atualizar_item(
    pedido_id: uuid.UUID,
    item_id: uuid.UUID,
    body: PedidoItemUpdateRequest,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        composicao = None
        if body.composicao:
            composicao = [item.model_dump() for item in body.composicao]

        return await service.atualizar_item(
            pedido_id=pedido_id,
            item_id=item_id,
            nome=body.nome,
            tipo_refeicao=body.tipo_refeicao,
            quantidade=body.quantidade,
            composicao_manual=composicao,
        )
    except PedidoNaoEncontradoError as e:
        _handle_not_found(e)
    except PedidoNaoEditavelError as e:
        _handle_bad_request(e)
    except ItemNaoEncontradoError as e:
        _handle_not_found(e)
    except (IngredienteNaoEncontradoError, ComposicaoVaziaError) as e:
        _handle_bad_request(e)


@router.delete(
    "/{pedido_id}/itens/{item_id}",
    response_model=PedidoDetalheResponse,
    summary="Remover item do pedido (só em rascunho)",
)
async def remover_item(
    pedido_id: uuid.UUID,
    item_id: uuid.UUID,
    service: PedidoService = Depends(get_pedido_service),
):
    try:
        return await service.remover_item(pedido_id, item_id)
    except PedidoNaoEncontradoError as e:
        _handle_not_found(e)
    except PedidoNaoEditavelError as e:
        _handle_bad_request(e)
    except ItemNaoEncontradoError as e:
        _handle_not_found(e)
