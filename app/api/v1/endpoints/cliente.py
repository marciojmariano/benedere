"""
Endpoints: Cliente
"""
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.cliente import (
    ClienteCreateRequest,
    ClienteResponse,
    ClienteUpdateRequest,
)
from app.core.auth0 import get_tenant_id
from app.domain.services.cliente_service import (
    ClienteInativoError,
    ClienteNaoEncontradoError,
    ClienteService,
    NutricionistaNaoEncontradoError,
)
from app.infra.database.session import get_session
from app.infra.repository.cliente_repository import ClienteRepository
from app.infra.repository.nutricionista_repository import NutricionistaRepository

router = APIRouter(prefix="/clientes", tags=["Clientes"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_cliente_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id),
) -> ClienteService:
    _tenant_id = uuid.UUID(tenant_id)
    cliente_repo = ClienteRepository(session, tenant_id=_tenant_id)
    nutricionista_repo = NutricionistaRepository(session, tenant_id=_tenant_id)
    return ClienteService(cliente_repo, nutricionista_repo, tenant_id=_tenant_id)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar cliente",
)
async def criar_cliente(
    body: ClienteCreateRequest,
    service: ClienteService = Depends(get_cliente_service),
):
    try:
        return await service.criar(
            nome=body.nome,
            email=str(body.email) if body.email else None,
            telefone=body.telefone,
            endereco=body.endereco,
            observacoes=body.observacoes,
            nutricionista_id=body.nutricionista_id,
            markup_id_padrao=body.markup_id_padrao,
        )
    except NutricionistaNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/",
    response_model=list[ClienteResponse],
    summary="Listar clientes",
)
async def listar_clientes(
    apenas_ativos: bool = True,
    service: ClienteService = Depends(get_cliente_service),
):
    return await service.listar(apenas_ativos=apenas_ativos)


@router.get(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Buscar cliente por ID",
)
async def buscar_cliente(
    cliente_id: uuid.UUID,
    service: ClienteService = Depends(get_cliente_service),
):
    try:
        return await service.buscar_por_id(cliente_id)
    except ClienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Atualizar cliente",
)
async def atualizar_cliente(
    cliente_id: uuid.UUID,
    body: ClienteUpdateRequest,
    service: ClienteService = Depends(get_cliente_service),
):
    try:
        return await service.atualizar(
            cliente_id=cliente_id,
            nome=body.nome,
            email=str(body.email) if body.email else None,
            telefone=body.telefone,
            endereco=body.endereco,
            observacoes=body.observacoes,
            nutricionista_id=body.nutricionista_id,
            markup_id_padrao=body.markup_id_padrao,
        )
    except ClienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NutricionistaNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ClienteInativoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{cliente_id}/reativar",
    response_model=ClienteResponse,
    summary="Reativar cliente",
)
async def reativar_cliente(
    cliente_id: uuid.UUID,
    service: ClienteService = Depends(get_cliente_service),
):
    try:
        return await service.reativar(cliente_id)
    except ClienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar cliente (soft delete)",
)
async def desativar_cliente(
    cliente_id: uuid.UUID,
    service: ClienteService = Depends(get_cliente_service),
):
    try:
        await service.desativar(cliente_id)
    except ClienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
