"""
Endpoints: Estoque (Movimentações)
"""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.movimentacao_estoque import (
    EntradaEstoqueCreateRequest,
    ImportacaoEstoqueResponse,
    MovimentacaoEstoqueResponse,
)
from app.core.auth0 import get_tenant_id
from app.domain.services.custo_ingrediente_service import CustoIngredienteService
from app.domain.services.movimentacao_estoque_service import (
    IngredienteNaoEncontradoParaEstoqueError,
    MovimentacaoEstoqueService,
    MovimentacaoNaoEncontradaError,
)
from app.infra.database.session import get_session
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.movimentacao_estoque_repository import MovimentacaoEstoqueRepository
from app.infra.repository.tenant_repository import TenantRepository

router = APIRouter(prefix="/estoque", tags=["Estoque"])


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_movimentacao_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id),
) -> MovimentacaoEstoqueService:
    _tenant_id = uuid.UUID(tenant_id)
    mov_repo = MovimentacaoEstoqueRepository(session, tenant_id=_tenant_id)
    ingrediente_repo = IngredienteRepository(session, tenant_id=_tenant_id)
    tenant_repo = TenantRepository(session)
    tenant = await tenant_repo.get_by_id(_tenant_id)
    custo_service = CustoIngredienteService(mov_repo, ingrediente_repo, tenant) if tenant else None
    return MovimentacaoEstoqueService(mov_repo, ingrediente_repo, tenant_id=_tenant_id, custo_service=custo_service)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/entradas",
    response_model=MovimentacaoEstoqueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar entrada de estoque",
)
async def registrar_entrada(
    body: EntradaEstoqueCreateRequest,
    service: MovimentacaoEstoqueService = Depends(get_movimentacao_service),
):
    try:
        mov = await service.registrar_entrada(
            ingrediente_id=body.ingrediente_id,
            quantidade=body.quantidade,
            preco_unitario_custo=body.preco_unitario_custo,
            data_movimentacao=body.data_movimentacao,
            observacoes=body.observacoes,
        )
        return MovimentacaoEstoqueResponse.from_orm_with_nome(mov)
    except IngredienteNaoEncontradoParaEstoqueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/movimentacoes",
    response_model=list[MovimentacaoEstoqueResponse],
    summary="Listar todas as movimentações",
)
async def listar_movimentacoes(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: MovimentacaoEstoqueService = Depends(get_movimentacao_service),
):
    movs = await service.listar_todas(limit=limit, offset=offset)
    return [MovimentacaoEstoqueResponse.from_orm_with_nome(m) for m in movs]


@router.get(
    "/movimentacoes/{mov_id}",
    response_model=MovimentacaoEstoqueResponse,
    summary="Buscar movimentação por ID",
)
async def buscar_movimentacao(
    mov_id: uuid.UUID,
    service: MovimentacaoEstoqueService = Depends(get_movimentacao_service),
):
    try:
        mov = await service.buscar_por_id(mov_id)
        return MovimentacaoEstoqueResponse.from_orm_with_nome(mov)
    except MovimentacaoNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/ingredientes/{ingrediente_id}/movimentacoes",
    response_model=list[MovimentacaoEstoqueResponse],
    summary="Histórico de movimentações por ingrediente",
)
async def listar_por_ingrediente(
    ingrediente_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: MovimentacaoEstoqueService = Depends(get_movimentacao_service),
):
    movs = await service.listar_por_ingrediente(
        ingrediente_id=ingrediente_id, limit=limit, offset=offset
    )
    return [MovimentacaoEstoqueResponse.from_orm_with_nome(m) for m in movs]


@router.post(
    "/entradas/importar",
    response_model=ImportacaoEstoqueResponse,
    summary="Importar entradas de estoque via Excel (.xlsx)",
)
async def importar_entradas_excel(
    arquivo: UploadFile = File(...),
    service: MovimentacaoEstoqueService = Depends(get_movimentacao_service),
):
    if arquivo.filename and not arquivo.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos .xlsx são aceitos",
        )
    conteudo = await arquivo.read()
    return await service.importar_excel(conteudo)
