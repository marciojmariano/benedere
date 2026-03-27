"""
Endpoints: Tenant
Responsabilidade: receber HTTP, chamar service, retornar resposta.
Não contém regras de negócio — apenas orquestra request → service → response.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.tenant import (
    LabelSettingsUpdateRequest,
    TenantCreateRequest,
    TenantDetailResponse,
    TenantResponse,
    TenantUpdateRequest,
)
from app.domain.services.tenant_service import (
    TenantNaoEncontradoError,
    TenantService,
    TenantSlugJaExisteError,
    TenantInativoError,
)
from app.core.auth0 import get_tenant_id
from app.infra.database.models.base import TenantPlano
from app.infra.database.session import get_session
from app.infra.repository.tenant_repository import TenantRepository

router = APIRouter(prefix="/tenants", tags=["Tenants"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_tenant_service(
    session: AsyncSession = Depends(get_session),
) -> TenantService:
    """Monta o service com suas dependências via injeção."""
    repo = TenantRepository(session)
    return TenantService(repo)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=TenantDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo tenant",
)
async def criar_tenant(
    body: TenantCreateRequest,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        tenant = await service.criar(
            nome=body.nome,
            slug=body.slug,
            email_dono=str(body.email_dono),
            plano=body.plano,
        )
        return tenant
    except TenantSlugJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/",
    response_model=list[TenantResponse],
    summary="Listar todos os tenants",
)
async def listar_tenants(
    apenas_ativos: bool = True,
    service: TenantService = Depends(get_tenant_service),
):
    return await service.listar(apenas_ativos=apenas_ativos)


@router.get(
    "/label-settings",
    response_model=TenantDetailResponse,
    summary="Obter configuração de etiqueta do tenant autenticado",
)
async def obter_label_settings(
    tenant_id: str = Depends(get_tenant_id),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return await service.buscar_por_id(uuid.UUID(tenant_id))
    except TenantNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/label-settings",
    response_model=TenantDetailResponse,
    summary="Atualizar template de etiqueta do tenant autenticado",
)
async def atualizar_label_settings(
    body: LabelSettingsUpdateRequest,
    tenant_id: str = Depends(get_tenant_id),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return await service.atualizar_etiqueta(
            tenant_id=uuid.UUID(tenant_id),
            template_delta=body.template_delta,
            html_output=body.html_output,
            largura_mm=body.dimensions.w if body.dimensions else None,
            altura_mm=body.dimensions.h if body.dimensions else None,
        )
    except TenantNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantInativoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{slug}",
    response_model=TenantDetailResponse,
    summary="Buscar tenant pelo slug",
)
async def buscar_tenant(
    slug: str,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return await service.buscar_por_slug(slug)
    except TenantNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{tenant_id}",
    response_model=TenantDetailResponse,
    summary="Atualizar dados do tenant",
)
async def atualizar_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdateRequest,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return await service.atualizar(
            tenant_id=tenant_id,
            nome=body.nome,
            email_dono=str(body.email_dono) if body.email_dono else None,
        )
    except TenantNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantInativoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{tenant_id}/ativar",
    response_model=TenantDetailResponse,
    summary="Ativar tenant",
)
async def ativar_tenant(
    tenant_id: uuid.UUID,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return await service.ativar(tenant_id)
    except TenantNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{tenant_id}/suspender",
    response_model=TenantDetailResponse,
    summary="Suspender tenant",
)
async def suspender_tenant(
    tenant_id: uuid.UUID,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return await service.suspender(tenant_id)
    except TenantNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{tenant_id}/plano",
    response_model=TenantDetailResponse,
    summary="Atualizar plano do tenant",
)
async def upgrade_plano(
    tenant_id: uuid.UUID,
    novo_plano: TenantPlano,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return await service.upgrade_plano(tenant_id, novo_plano)
    except TenantNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (TenantInativoError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar tenant (soft delete)",
)
async def desativar_tenant(
    tenant_id: uuid.UUID,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        await service.desativar(tenant_id)
    except TenantNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
