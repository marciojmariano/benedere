"""
Endpoints: FaixaPesoEmbalagem
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.faixa_peso_embalagem import (
    FaixaPesoEmbalagemCreateRequest,
    FaixaPesoEmbalagemUpdateRequest,
    FaixaPesoEmbalagemResponse,
)
from app.core.auth0 import get_tenant_id
from app.domain.services.faixa_peso_embalagem_service import (
    FaixaPesoEmbalagemService,
    FaixaNaoEncontradaError,
    FaixaSobrepostaError,
    IngredienteNaoEmbalagemError,
    IngredienteNaoEncontradoError,
)
from app.infra.database.session import get_session
from app.infra.repository.faixa_peso_embalagem_repository import FaixaPesoEmbalagemRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository

router = APIRouter(prefix="/faixas-peso-embalagem", tags=["Faixas de Peso Embalagem"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_faixa_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id),
) -> FaixaPesoEmbalagemService:
    _tenant_id = uuid.UUID(tenant_id)
    return FaixaPesoEmbalagemService(
        faixa_repo=FaixaPesoEmbalagemRepository(session, tenant_id=_tenant_id),
        ingrediente_repo=IngredienteRepository(session, tenant_id=_tenant_id),
        tenant_id=_tenant_id,
    )


def _to_response(faixa) -> FaixaPesoEmbalagemResponse:
    ing = faixa.ingrediente_embalagem
    return FaixaPesoEmbalagemResponse(
        id=faixa.id,
        peso_min_g=faixa.peso_min_g,
        peso_max_g=faixa.peso_max_g,
        ingrediente_embalagem_id=faixa.ingrediente_embalagem_id,
        ingrediente_embalagem_nome=ing.nome,
        ingrediente_embalagem_custo=ing.custo_unitario,
        ativo=faixa.ativo,
        created_at=faixa.created_at,
        updated_at=faixa.updated_at,
    )


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=FaixaPesoEmbalagemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar faixa de peso de embalagem",
)
async def criar_faixa(
    body: FaixaPesoEmbalagemCreateRequest,
    service: FaixaPesoEmbalagemService = Depends(get_faixa_service),
):
    try:
        faixa = await service.criar(
            peso_min_g=body.peso_min_g,
            peso_max_g=body.peso_max_g,
            ingrediente_embalagem_id=body.ingrediente_embalagem_id,
        )
        return _to_response(faixa)
    except (IngredienteNaoEncontradoError, FaixaNaoEncontradaError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (FaixaSobrepostaError, IngredienteNaoEmbalagemError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=list[FaixaPesoEmbalagemResponse],
    summary="Listar faixas de peso (ordenadas por peso_min_g)",
)
async def listar_faixas(
    service: FaixaPesoEmbalagemService = Depends(get_faixa_service),
):
    faixas = await service.listar()
    return [_to_response(f) for f in faixas]


@router.get(
    "/{faixa_id}",
    response_model=FaixaPesoEmbalagemResponse,
    summary="Buscar faixa por ID",
)
async def buscar_faixa(
    faixa_id: uuid.UUID,
    service: FaixaPesoEmbalagemService = Depends(get_faixa_service),
):
    try:
        faixa = await service.buscar_por_id(faixa_id)
        return _to_response(faixa)
    except FaixaNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{faixa_id}",
    response_model=FaixaPesoEmbalagemResponse,
    summary="Atualizar faixa de peso",
)
async def atualizar_faixa(
    faixa_id: uuid.UUID,
    body: FaixaPesoEmbalagemUpdateRequest,
    service: FaixaPesoEmbalagemService = Depends(get_faixa_service),
):
    try:
        faixa = await service.atualizar(
            faixa_id=faixa_id,
            peso_min_g=body.peso_min_g,
            peso_max_g=body.peso_max_g,
            ingrediente_embalagem_id=body.ingrediente_embalagem_id,
        )
        return _to_response(faixa)
    except FaixaNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (FaixaSobrepostaError, IngredienteNaoEmbalagemError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IngredienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{faixa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar faixa de peso (soft delete)",
)
async def desativar_faixa(
    faixa_id: uuid.UUID,
    service: FaixaPesoEmbalagemService = Depends(get_faixa_service),
):
    try:
        await service.desativar(faixa_id)
    except FaixaNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
