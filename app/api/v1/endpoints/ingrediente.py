"""
Endpoints: Ingrediente
"""
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.ingrediente import (
    IngredienteCreateRequest,
    IngredienteResponse,
    IngredienteUpdateRequest,
)
from app.domain.services.ingrediente_service import (
    IngredienteInativoError,
    IngredienteNaoEncontradoError,
    IngredienteService,
    MarkupNaoEncontradoError,
)
from app.infra.database.session import get_session
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.markup_repository import MarkupRepository

router = APIRouter(prefix="/ingredientes", tags=["Ingredientes"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_ingrediente_service(
    session: AsyncSession = Depends(get_session),
    x_tenant_id: uuid.UUID = Header(..., description="ID do tenant"),
) -> IngredienteService:
    ingrediente_repo = IngredienteRepository(session, tenant_id=x_tenant_id)
    markup_repo = MarkupRepository(session, tenant_id=x_tenant_id)
    return IngredienteService(ingrediente_repo, markup_repo, tenant_id=x_tenant_id)


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
            unidade_medida=body.unidade_medida,
            custo_unitario=body.custo_unitario,
            descricao=body.descricao,
            markup_id=body.markup_id,
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
            unidade_medida=body.unidade_medida,
            custo_unitario=body.custo_unitario,
            descricao=body.descricao,
            markup_id=body.markup_id,
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
