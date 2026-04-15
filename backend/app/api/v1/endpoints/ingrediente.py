"""
Endpoints: Ingrediente
"""
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.ingrediente import (
    HistoricoCustoItem,
    IngredienteCreateRequest,
    IngredienteResponse,
    IngredienteUpdateRequest,
    RecalculoCustosResponse,
)
from app.core.auth0 import get_tenant_id
from app.domain.services.ingrediente_service import (
    IngredienteEmUsoError,
    IngredienteInativoError,
    IngredienteNaoEncontradoError,
    IngredienteService,
    MarkupNaoEncontradoError,
)
from app.domain.services.custo_ingrediente_service import CustoIngredienteService
from app.infra.database.session import get_session
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.markup_repository import MarkupRepository
from app.infra.repository.movimentacao_estoque_repository import MovimentacaoEstoqueRepository
from app.infra.repository.tenant_repository import TenantRepository

router = APIRouter(prefix="/ingredientes", tags=["Ingredientes"])


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_ingrediente_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id)
) -> IngredienteService:
    _tenant_id = uuid.UUID(tenant_id)
    ingrediente_repo = IngredienteRepository(session, tenant_id=_tenant_id)
    markup_repo = MarkupRepository(session, tenant_id=_tenant_id)
    mov_repo = MovimentacaoEstoqueRepository(session, tenant_id=_tenant_id)
    tenant_repo = TenantRepository(session)
    tenant = await tenant_repo.get_by_id(_tenant_id)
    custo_service = CustoIngredienteService(mov_repo, ingrediente_repo, tenant) if tenant else None
    return IngredienteService(ingrediente_repo, markup_repo, tenant_id=_tenant_id, custo_service=custo_service)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=IngredienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar ingrediente",
)
async def criar_ingrediente(
    body: IngredienteCreateRequest,
    service: IngredienteService = Depends(get_ingrediente_service),
):
    try:
        return await service.criar(
            nome=body.nome,
            tipo=body.tipo,
            unidade_medida=body.unidade_medida,
            custo_unitario=body.custo_unitario,
            descricao=body.descricao,
            markup_id=body.markup_id,
            estrategia_custo=body.estrategia_custo,
            periodo_dias_custo_medio=body.periodo_dias_custo_medio,
        )
    except MarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/",
    response_model=list[IngredienteResponse],
    summary="Listar ingredientes",
)
async def listar_ingredientes(
    apenas_ativos: bool = True,
    service: IngredienteService = Depends(get_ingrediente_service),
):
    return await service.listar(apenas_ativos=apenas_ativos)


@router.get(
    "/{ingrediente_id}",
    response_model=IngredienteResponse,
    summary="Buscar ingrediente por ID",
)
async def buscar_ingrediente(
    ingrediente_id: uuid.UUID,
    service: IngredienteService = Depends(get_ingrediente_service),
):
    try:
        return await service.buscar_por_id(ingrediente_id)
    except IngredienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{ingrediente_id}",
    response_model=IngredienteResponse,
    summary="Atualizar ingrediente",
)
async def atualizar_ingrediente(
    ingrediente_id: uuid.UUID,
    body: IngredienteUpdateRequest,
    service: IngredienteService = Depends(get_ingrediente_service),
):
    try:
        return await service.atualizar(
            ingrediente_id=ingrediente_id,
            nome=body.nome,
            tipo=body.tipo,
            unidade_medida=body.unidade_medida,
            custo_unitario=body.custo_unitario,
            descricao=body.descricao,
            markup_id=body.markup_id,
            estrategia_custo=body.estrategia_custo,
            periodo_dias_custo_medio=body.periodo_dias_custo_medio,
        )
    except IngredienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IngredienteInativoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except MarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{ingrediente_id}/reativar",
    response_model=IngredienteResponse,
    summary="Reativar ingrediente",
)
async def reativar_ingrediente(
    ingrediente_id: uuid.UUID,
    service: IngredienteService = Depends(get_ingrediente_service),
):
    try:
        return await service.reativar(ingrediente_id)
    except IngredienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{ingrediente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar ingrediente (soft delete)",
)
async def desativar_ingrediente(
    ingrediente_id: uuid.UUID,
    service: IngredienteService = Depends(get_ingrediente_service),
):
    try:
        await service.desativar(ingrediente_id)
    except IngredienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IngredienteEmUsoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{ingrediente_id}/historico-custo",
    response_model=list[HistoricoCustoItem],
    summary="Histórico de custo do ingrediente",
)
async def historico_custo_ingrediente(
    ingrediente_id: uuid.UUID,
    limit: int = 30,
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id),
):
    """Retorna as últimas N entradas de compra com custo médio ponderado acumulado."""
    from decimal import Decimal as D
    _tenant_id = uuid.UUID(tenant_id)
    mov_repo = MovimentacaoEstoqueRepository(session, tenant_id=_tenant_id)
    movs = await mov_repo.list_by_ingrediente(ingrediente_id, limit=limit, offset=0)

    resultado = []
    soma_qty = D("0")
    soma_custo_qty = D("0")
    for mov in reversed(movs):  # ordem cronológica para calcular média acumulada
        qty = D(str(mov.quantidade))
        preco = D(str(mov.preco_unitario_custo))
        soma_qty += qty
        soma_custo_qty += qty * preco
        media_acum = (soma_custo_qty / soma_qty).quantize(D("0.0001")) if soma_qty else preco
        resultado.append(HistoricoCustoItem(
            data_movimentacao=str(mov.data_movimentacao),
            preco_unitario_custo=preco,
            quantidade=qty,
            custo_medio_acumulado=media_acum,
        ))

    resultado.reverse()  # mais recente primeiro na resposta
    return resultado


@router.post(
    "/recalcular-custos",
    response_model=RecalculoCustosResponse,
    summary="Recalcular custo efetivo de todos os ingredientes ativos",
)
async def recalcular_custos(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id),
):
    """
    Recalcula custo_calculado de todos os ingredientes ativos do tenant,
    conforme a estratégia configurada em cada um.
    Útil para estratégias de período (janela deslizante diária).
    """
    _tenant_id = uuid.UUID(tenant_id)
    ingrediente_repo = IngredienteRepository(session, tenant_id=_tenant_id)
    mov_repo = MovimentacaoEstoqueRepository(session, tenant_id=_tenant_id)
    tenant_repo = TenantRepository(session)
    tenant = await tenant_repo.get_by_id(_tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant não encontrado")

    custo_service = CustoIngredienteService(mov_repo, ingrediente_repo, tenant)
    ingredientes = await ingrediente_repo.list_all(apenas_ativos=True)

    for ing in ingredientes:
        await custo_service.recalcular_e_persistir(ing)

    return RecalculoCustosResponse(recalculados=len(ingredientes))
