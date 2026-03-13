"""
Endpoints: IndiceMarkup e Markup
"""
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.markup import (
    IndiceMarkupCreateRequest,
    IndiceMarkupResponse,
    IndiceMarkupUpdateRequest,
    MarkupCreateRequest,
    MarkupResponse,
    MarkupUpdateRequest,
)
from app.domain.services.markup_service import (
    IndiceMarkupNaoEncontradoError,
    IndiceMarkupService,
    MarkupNaoEncontradoError,
    MarkupService,
    MarkupSomaPecentualInvalidaError,
)
from app.infra.database.session import get_session
from app.infra.repository.markup_repository import IndiceMarkupRepository, MarkupRepository

indice_router = APIRouter(prefix="/indices-markup", tags=["Índices de Markup"])
markup_router = APIRouter(prefix="/markups", tags=["Markups"])


# ── Dependencies ──────────────────────────────────────────────────────────────

def get_indice_service(
    session: AsyncSession = Depends(get_session),
    x_tenant_id: uuid.UUID = Header(..., description="ID do tenant"),
) -> IndiceMarkupService:
    repo = IndiceMarkupRepository(session, tenant_id=x_tenant_id)
    return IndiceMarkupService(repo, tenant_id=x_tenant_id)


def get_markup_service(
    session: AsyncSession = Depends(get_session),
    x_tenant_id: uuid.UUID = Header(..., description="ID do tenant"),
) -> MarkupService:
    indice_repo = IndiceMarkupRepository(session, tenant_id=x_tenant_id)
    markup_repo = MarkupRepository(session, tenant_id=x_tenant_id)
    return MarkupService(markup_repo, indice_repo, tenant_id=x_tenant_id)


# ── Endpoints: IndiceMarkup ───────────────────────────────────────────────────

@indice_router.post(
    "/",
    response_model=IndiceMarkupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar índice de markup",
)
async def criar_indice(
    body: IndiceMarkupCreateRequest,
    service: IndiceMarkupService = Depends(get_indice_service),
):
    return await service.criar(
        nome=body.nome,
        percentual=body.percentual,
        descricao=body.descricao,
    )


@indice_router.get(
    "/",
    response_model=list[IndiceMarkupResponse],
    summary="Listar índices de markup",
)
async def listar_indices(
    apenas_ativos: bool = True,
    service: IndiceMarkupService = Depends(get_indice_service),
):
    return await service.listar(apenas_ativos=apenas_ativos)


@indice_router.get(
    "/{indice_id}",
    response_model=IndiceMarkupResponse,
    summary="Buscar índice por ID",
)
async def buscar_indice(
    indice_id: uuid.UUID,
    service: IndiceMarkupService = Depends(get_indice_service),
):
    try:
        return await service.buscar_por_id(indice_id)
    except IndiceMarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@indice_router.patch(
    "/{indice_id}",
    response_model=IndiceMarkupResponse,
    summary="Atualizar índice de markup",
)
async def atualizar_indice(
    indice_id: uuid.UUID,
    body: IndiceMarkupUpdateRequest,
    service: IndiceMarkupService = Depends(get_indice_service),
):
    try:
        return await service.atualizar(
            indice_id=indice_id,
            nome=body.nome,
            percentual=body.percentual,
            descricao=body.descricao,
        )
    except IndiceMarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@indice_router.delete(
    "/{indice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar índice de markup",
)
async def desativar_indice(
    indice_id: uuid.UUID,
    service: IndiceMarkupService = Depends(get_indice_service),
):
    try:
        await service.desativar(indice_id)
    except IndiceMarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Endpoints: Markup ─────────────────────────────────────────────────────────

@markup_router.post(
    "/",
    response_model=MarkupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar markup",
)
async def criar_markup(
    body: MarkupCreateRequest,
    service: MarkupService = Depends(get_markup_service),
):
    try:
        markup = await service.criar(
            nome=body.nome,
            indices_ids=body.indices_ids,
            descricao=body.descricao,
        )
        return MarkupResponse.from_markup(markup)
    except IndiceMarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except MarkupSomaPecentualInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@markup_router.get(
    "/",
    response_model=list[MarkupResponse],
    summary="Listar markups",
)
async def listar_markups(
    apenas_ativos: bool = True,
    service: MarkupService = Depends(get_markup_service),
):
    markups = await service.listar(apenas_ativos=apenas_ativos)
    return [MarkupResponse.from_markup(m) for m in markups]


@markup_router.get(
    "/{markup_id}",
    response_model=MarkupResponse,
    summary="Buscar markup por ID",
)
async def buscar_markup(
    markup_id: uuid.UUID,
    service: MarkupService = Depends(get_markup_service),
):
    try:
        markup = await service.buscar_por_id(markup_id)
        return MarkupResponse.from_markup(markup)
    except MarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@markup_router.patch(
    "/{markup_id}",
    response_model=MarkupResponse,
    summary="Atualizar markup",
)
async def atualizar_markup(
    markup_id: uuid.UUID,
    body: MarkupUpdateRequest,
    service: MarkupService = Depends(get_markup_service),
):
    try:
        markup = await service.atualizar(
            markup_id=markup_id,
            nome=body.nome,
            descricao=body.descricao,
            indices_ids=body.indices_ids,
        )
        return MarkupResponse.from_markup(markup)
    except MarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IndiceMarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except MarkupSomaPecentualInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@markup_router.delete(
    "/{markup_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar markup",
)
async def desativar_markup(
    markup_id: uuid.UUID,
    service: MarkupService = Depends(get_markup_service),
):
    try:
        await service.desativar(markup_id)
    except MarkupNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
