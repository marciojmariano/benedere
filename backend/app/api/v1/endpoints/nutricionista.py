"""
Endpoints: Nutricionista
O tenant_id é extraído do header X-Tenant-ID (provisório até Auth0 estar configurado).
"""
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.nutricionista import (
    NutricionistaCreateRequest,
    NutricionistaResponse,
    NutricionistaUpdateRequest,
)
from app.core.auth0 import get_tenant_id
from app.domain.services.nutricionista_service import (
    NutricionistaCRNJaExisteError,
    NutricionistaNaoEncontradoError,
    NutricionistaInativoError,
    NutricionistaService,
)
from app.infra.database.session import get_session
from app.infra.repository.nutricionista_repository import NutricionistaRepository

router = APIRouter(prefix="/nutricionistas", tags=["Nutricionistas"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_nutricionista_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id)
) -> NutricionistaService:
    _tenant_id = uuid.UUID(tenant_id)

    """
    Provisório: tenant_id via header X-Tenant-ID.
    Será substituído pela extração do JWT Auth0 futuramente.
    """
    repo = NutricionistaRepository(session, tenant_id=_tenant_id)
    return NutricionistaService(repo, tenant_id=_tenant_id)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=NutricionistaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar nutricionista",
)
async def criar_nutricionista(
    body: NutricionistaCreateRequest,
    service: NutricionistaService = Depends(get_nutricionista_service),
):
    try:
        return await service.criar(
            nome=body.nome,
            crn=body.crn,
            email=str(body.email) if body.email else None,
            telefone=body.telefone,
        )
    except NutricionistaCRNJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/",
    response_model=list[NutricionistaResponse],
    summary="Listar nutricionistas",
)
async def listar_nutricionistas(
    apenas_ativos: bool = True,
    service: NutricionistaService = Depends(get_nutricionista_service),
):
    return await service.listar(apenas_ativos=apenas_ativos)


@router.get(
    "/{nutricionista_id}",
    response_model=NutricionistaResponse,
    summary="Buscar nutricionista por ID",
)
async def buscar_nutricionista(
    nutricionista_id: uuid.UUID,
    service: NutricionistaService = Depends(get_nutricionista_service),
):
    try:
        return await service.buscar_por_id(nutricionista_id)
    except NutricionistaNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{nutricionista_id}",
    response_model=NutricionistaResponse,
    summary="Atualizar nutricionista",
)
async def atualizar_nutricionista(
    nutricionista_id: uuid.UUID,
    body: NutricionistaUpdateRequest,
    service: NutricionistaService = Depends(get_nutricionista_service),
):
    try:
        return await service.atualizar(
            nutricionista_id=nutricionista_id,
            nome=body.nome,
            crn=body.crn,
            email=str(body.email) if body.email else None,
            telefone=body.telefone,
        )
    except NutricionistaNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NutricionistaCRNJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NutricionistaInativoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{nutricionista_id}/reativar",
    response_model=NutricionistaResponse,
    summary="Reativar nutricionista",
)
async def reativar_nutricionista(
    nutricionista_id: uuid.UUID,
    service: NutricionistaService = Depends(get_nutricionista_service),
):
    try:
        return await service.reativar(nutricionista_id)
    except NutricionistaNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{nutricionista_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar nutricionista (soft delete)",
)
async def desativar_nutricionista(
    nutricionista_id: uuid.UUID,
    service: NutricionistaService = Depends(get_nutricionista_service),
):
    try:
        await service.desativar(nutricionista_id)
    except NutricionistaNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
