"""
Endpoints: Produto
Tasks: 2.1.5, 2.2.5, 2.2.6
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.produto import (
    ProdutoCreateRequest,
    ProdutoUpdateRequest,
    ProdutoResponse,
    ProdutoDetalheResponse,
    ProdutoComposicaoCreateRequest,
    ProdutoComposicaoResponse,
)
from app.core.auth0 import get_tenant_id
from app.domain.services.produto_service import (
    ProdutoService,
    ProdutoNaoEncontradoError,
    ProdutoInativoError,
    IngredienteNaoEncontradoError,
    ComposicaoVaziaError,
)
from app.infra.database.session import get_session
from app.infra.repository.produto_repository import ProdutoRepository
from app.infra.repository.produto_composicao_repository import ProdutoComposicaoRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository

router = APIRouter(prefix="/produtos", tags=["Produtos"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_produto_service(
    session: AsyncSession = Depends(get_session),
    tenant_id: str = Depends(get_tenant_id),
) -> ProdutoService:
    _tenant_id = uuid.UUID(tenant_id)
    return ProdutoService(
        produto_repo=ProdutoRepository(session, tenant_id=_tenant_id),
        composicao_repo=ProdutoComposicaoRepository(session),
        ingrediente_repo=IngredienteRepository(session, tenant_id=_tenant_id),
        tenant_id=_tenant_id,
    )


# ── CRUD Produto ─────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar produto no catálogo",
)
async def criar_produto(
    body: ProdutoCreateRequest,
    service: ProdutoService = Depends(get_produto_service),
):
    try:
        composicao = None
        if body.composicao:
            composicao = [item.model_dump() for item in body.composicao]

        return await service.criar(
            nome=body.nome,
            descricao=body.descricao,
            composicao=composicao,
        )
    except IngredienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/",
    response_model=list[ProdutoResponse],
    summary="Listar produtos do catálogo",
)
async def listar_produtos(
    apenas_ativos: bool = True,
    service: ProdutoService = Depends(get_produto_service),
):
    return await service.listar(apenas_ativos=apenas_ativos)


@router.get(
    "/{produto_id}",
    response_model=ProdutoDetalheResponse,
    summary="Buscar produto por ID (com composição detalhada)",
)
async def buscar_produto(
    produto_id: uuid.UUID,
    service: ProdutoService = Depends(get_produto_service),
):
    try:
        produto = await service.buscar_por_id(produto_id)
        composicao = await service.listar_composicao(produto_id)

        # Calcular totais
        custo_total = sum(item["custo_item"] for item in composicao)
        kcal_total = sum(item["kcal_item"] for item in composicao)

        return ProdutoDetalheResponse(
            id=produto.id,
            nome=produto.nome,
            peso_total_g=produto.peso_total_g,
            descricao=produto.descricao,
            ativo=produto.ativo,
            created_at=produto.created_at,
            updated_at=produto.updated_at,
            composicao=[ProdutoComposicaoResponse(**item) for item in composicao],
            custo_total=custo_total,
            kcal_total=kcal_total,
        )
    except ProdutoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{produto_id}",
    response_model=ProdutoResponse,
    summary="Atualizar produto",
)
async def atualizar_produto(
    produto_id: uuid.UUID,
    body: ProdutoUpdateRequest,
    service: ProdutoService = Depends(get_produto_service),
):
    try:
        return await service.atualizar(
            produto_id=produto_id,
            nome=body.nome,
            descricao=body.descricao,
        )
    except ProdutoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProdutoInativoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{produto_id}/reativar",
    response_model=ProdutoResponse,
    summary="Reativar produto",
)
async def reativar_produto(
    produto_id: uuid.UUID,
    service: ProdutoService = Depends(get_produto_service),
):
    try:
        return await service.reativar(produto_id)
    except ProdutoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{produto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar produto (soft delete)",
)
async def desativar_produto(
    produto_id: uuid.UUID,
    service: ProdutoService = Depends(get_produto_service),
):
    try:
        await service.desativar(produto_id)
    except ProdutoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Composição (Receita) ─────────────────────────────────────────────────────

@router.put(
    "/{produto_id}/composicao",
    response_model=ProdutoResponse,
    summary="Substituir composição do produto (receita completa)",
)
async def substituir_composicao(
    produto_id: uuid.UUID,
    body: list[ProdutoComposicaoCreateRequest],
    service: ProdutoService = Depends(get_produto_service),
):
    try:
        composicao = [item.model_dump() for item in body]
        return await service.substituir_composicao(produto_id, composicao)
    except ProdutoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProdutoInativoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IngredienteNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ComposicaoVaziaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{produto_id}/composicao",
    response_model=list[ProdutoComposicaoResponse],
    summary="Listar composição do produto (com custos calculados)",
)
async def listar_composicao(
    produto_id: uuid.UUID,
    service: ProdutoService = Depends(get_produto_service),
):
    try:
        itens = await service.listar_composicao(produto_id)
        return [ProdutoComposicaoResponse(**item) for item in itens]
    except ProdutoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
