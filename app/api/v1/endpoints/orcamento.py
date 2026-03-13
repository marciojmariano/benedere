"""
Endpoints: Orcamento
"""
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.orcamento import (
    OrcamentoCreateRequest,
    OrcamentoResponse,
    OrcamentoUpdateRequest,
)
from app.core.auth0 import get_tenant_id
from app.domain.services.orcamento_service import (
    ClienteNaoEncontradoError,
    IngredienteNaoEncontradoError,
    OrcamentoNaoEditavelError,
    OrcamentoNaoEncontradoError,
    OrcamentoService,
    TransicaoStatusInvalidaError,
)
from app.infra.database.models.base import StatusOrcamento
from app.infra.database.session import get_session
from app.infra.repository.cliente_repository import ClienteRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.markup_repository import MarkupRepository
from app.infra.repository.orcamento_repository import OrcamentoRepository

router = APIRouter(prefix="/orcamentos", tags=["Orçamentos"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_orcamento_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id)
) -> OrcamentoService:
    _tenant_id = uuid.UUID(tenant_id)
    return OrcamentoService(       
        orcamento_repo=OrcamentoRepository(session, tenant_id=_tenant_id),
        cliente_repo=ClienteRepository(session, tenant_id=_tenant_id),
        ingrediente_repo=IngredienteRepository(session, tenant_id=_tenant_id),
        markup_repo=MarkupRepository(session, tenant_id=_tenant_id),
        tenant_id=_tenant_id,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=OrcamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar orçamento",
)
async def criar_orcamento(
    body: OrcamentoCreateRequest,
    service: OrcamentoService = Depends(get_orcamento_service),
):
    try:
        itens_data = [
            {
                "ingrediente_id": item.ingrediente_id,
                "quantidade": item.quantidade,
                "unidade_medida": item.unidade_medida,
                "observacoes": item.observacoes,
            }
            for item in body.itens
        ]
        return await service.criar(
            cliente_id=body.cliente_id,
            itens_data=itens_data,
            markup_id=body.markup_id,
            custo_embalagem=body.custo_embalagem,
            taxa_entrega=body.taxa_entrega,
            validade_dias=body.validade_dias,
            observacoes=body.observacoes,
        )
    except ClienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IngredienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=list[OrcamentoResponse],
    summary="Listar orçamentos",
)
async def listar_orcamentos(
    cliente_id: uuid.UUID | None = None,
    status_orcamento: StatusOrcamento | None = None,
    service: OrcamentoService = Depends(get_orcamento_service),
):
    return await service.listar(cliente_id=cliente_id, status=status_orcamento)


@router.get(
    "/{orcamento_id}",
    response_model=OrcamentoResponse,
    summary="Buscar orçamento por ID",
)
async def buscar_orcamento(
    orcamento_id: uuid.UUID,
    service: OrcamentoService = Depends(get_orcamento_service),
):
    try:
        return await service.buscar_por_id(orcamento_id)
    except OrcamentoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{orcamento_id}",
    response_model=OrcamentoResponse,
    summary="Atualizar orçamento (apenas RASCUNHO)",
)
async def atualizar_orcamento(
    orcamento_id: uuid.UUID,
    body: OrcamentoUpdateRequest,
    service: OrcamentoService = Depends(get_orcamento_service),
):
    try:
        return await service.atualizar(
            orcamento_id=orcamento_id,
            markup_id=body.markup_id,
            custo_embalagem=body.custo_embalagem,
            taxa_entrega=body.taxa_entrega,
            validade_dias=body.validade_dias,
            observacoes=body.observacoes,
        )
    except OrcamentoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrcamentoNaoEditavelError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{orcamento_id}/status",
    response_model=OrcamentoResponse,
    summary="Mudar status do orçamento",
)
async def mudar_status(
    orcamento_id: uuid.UUID,
    novo_status: StatusOrcamento,
    service: OrcamentoService = Depends(get_orcamento_service),
):
    try:
        return await service.mudar_status(orcamento_id, novo_status)
    except OrcamentoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TransicaoStatusInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
