"""
Testes: ProdutoService
Task: 5.1.2
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services.produto_service import (
    ProdutoService,
    ProdutoNaoEncontradoError,
    ProdutoInativoError,
    IngredienteNaoEncontradoError,
    ComposicaoVaziaError,
)
from app.infra.database.models.base import TipoRefeicao
from app.infra.database.models.ingrediente import Ingrediente
from app.infra.database.models.tenant import Tenant
from app.infra.repository.produto_repository import ProdutoRepository
from app.infra.repository.produto_composicao_repository import ProdutoComposicaoRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository


def _make_service(session: AsyncSession, tenant: Tenant) -> ProdutoService:
    return ProdutoService(
        produto_repo=ProdutoRepository(session, tenant.id),
        composicao_repo=ProdutoComposicaoRepository(session),
        ingrediente_repo=IngredienteRepository(session, tenant.id),
        tenant_id=tenant.id,
    )


# ── CRUD ─────────────────────────────────────────────────────────────────────

class TestProdutoCRUD:

    async def test_criar_produto_simples(self, session, tenant):
        service = _make_service(session, tenant)
        produto = await service.criar(nome="Granola Artesanal", tipo_refeicao=TipoRefeicao.CAFE_MANHA)

        assert produto.id is not None
        assert produto.nome == "Granola Artesanal"
        assert produto.tipo_refeicao == TipoRefeicao.CAFE_MANHA
        assert produto.peso_total_g == 0
        assert produto.ativo is True
        assert produto.tenant_id == tenant.id

    async def test_criar_produto_com_composicao(self, session, tenant, ingredientes):
        service = _make_service(session, tenant)
        pure = ingredientes["Purê de Batata Baroa"]
        ragu = ingredientes["Ragu de Carne"]

        produto = await service.criar(
            nome="Escondidinho Teste",
            composicao=[
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("100"), "ordem": 0},
                {"ingrediente_id": ragu.id, "quantidade_g": Decimal("85"), "ordem": 1},
            ],
        )

        assert produto.peso_total_g == 185  # 100 + 85

    async def test_listar_produtos(self, session, tenant):
        service = _make_service(session, tenant)
        await service.criar(nome="Produto A")
        await service.criar(nome="Produto B")

        produtos = await service.listar()
        assert len(produtos) >= 2

    async def test_buscar_por_id(self, session, tenant):
        service = _make_service(session, tenant)
        criado = await service.criar(nome="Busca Teste")

        encontrado = await service.buscar_por_id(criado.id)
        assert encontrado.nome == "Busca Teste"

    async def test_buscar_por_id_inexistente(self, session, tenant):
        service = _make_service(session, tenant)
        with pytest.raises(ProdutoNaoEncontradoError):
            await service.buscar_por_id(uuid.uuid4())

    async def test_atualizar_produto(self, session, tenant):
        service = _make_service(session, tenant)
        produto = await service.criar(nome="Original")

        atualizado = await service.atualizar(
            produto.id, nome="Atualizado", tipo_refeicao=TipoRefeicao.JANTAR
        )

        assert atualizado.nome == "Atualizado"
        assert atualizado.tipo_refeicao == TipoRefeicao.JANTAR

    async def test_desativar_e_reativar(self, session, tenant):
        service = _make_service(session, tenant)
        produto = await service.criar(nome="Desativar Teste")

        await service.desativar(produto.id)
        encontrado = await service.buscar_por_id(produto.id)
        assert encontrado.ativo is False

        reativado = await service.reativar(produto.id)
        assert reativado.ativo is True

    async def test_atualizar_produto_inativo_erro(self, session, tenant):
        service = _make_service(session, tenant)
        produto = await service.criar(nome="Inativo")
        await service.desativar(produto.id)

        with pytest.raises(ProdutoInativoError):
            await service.atualizar(produto.id, nome="Tentativa")


# ── Composição ───────────────────────────────────────────────────────────────

class TestProdutoComposicao:

    async def test_substituir_composicao(self, session, tenant, ingredientes):
        service = _make_service(session, tenant)
        produto = await service.criar(nome="Composicao Teste")

        pure = ingredientes["Purê de Batata Baroa"]
        ragu = ingredientes["Ragu de Carne"]

        atualizado = await service.substituir_composicao(
            produto.id,
            [
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("120"), "ordem": 0},
                {"ingrediente_id": ragu.id, "quantidade_g": Decimal("80"), "ordem": 1},
            ],
        )

        assert atualizado.peso_total_g == 200  # 120 + 80

    async def test_substituir_composicao_vazia_erro(self, session, tenant):
        service = _make_service(session, tenant)
        produto = await service.criar(nome="Vazia Teste")

        with pytest.raises(ComposicaoVaziaError):
            await service.substituir_composicao(produto.id, [])

    async def test_composicao_ingrediente_inexistente_erro(self, session, tenant):
        service = _make_service(session, tenant)
        produto = await service.criar(nome="Ingrediente Fake")

        with pytest.raises(IngredienteNaoEncontradoError):
            await service.substituir_composicao(
                produto.id,
                [{"ingrediente_id": uuid.uuid4(), "quantidade_g": Decimal("100"), "ordem": 0}],
            )

    async def test_listar_composicao_com_custos(self, session, tenant, ingredientes):
        service = _make_service(session, tenant)
        pure = ingredientes["Purê de Batata Baroa"]  # R$ 25/kg

        produto = await service.criar(
            nome="Custo Teste",
            composicao=[
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("100"), "ordem": 0},
            ],
        )

        composicao = await service.listar_composicao(produto.id)

        assert len(composicao) == 1
        # 100g de purê a R$25/kg = R$2.50
        assert composicao[0]["custo_item"] == Decimal("2.5000")
        assert composicao[0]["ingrediente_nome"] == "Purê de Batata Baroa"

    async def test_peso_total_recalculado_apos_substituicao(self, session, tenant, ingredientes):
        service = _make_service(session, tenant)
        pure = ingredientes["Purê de Batata Baroa"]
        ragu = ingredientes["Ragu de Carne"]

        produto = await service.criar(
            nome="Peso Teste",
            composicao=[
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("100"), "ordem": 0},
            ],
        )
        assert produto.peso_total_g == 100

        # Substitui com nova composição
        atualizado = await service.substituir_composicao(
            produto.id,
            [
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("150"), "ordem": 0},
                {"ingrediente_id": ragu.id, "quantidade_g": Decimal("50"), "ordem": 1},
            ],
        )
        assert atualizado.peso_total_g == 200  # 150 + 50
