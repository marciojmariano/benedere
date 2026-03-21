"""
Testes: Isolamento multi-tenant
Task: 5.1.7

Garante que Tenant A nunca vê dados de Tenant B.
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services.produto_service import ProdutoService, ProdutoNaoEncontradoError
from app.domain.services.pedido_service import PedidoService, PedidoNaoEncontradoError
from app.infra.database.models.base import UnidadeMedida, TipoItem
from app.infra.database.models.cliente import Cliente
from app.infra.database.models.ingrediente import Ingrediente
from app.infra.database.models.tenant import Tenant
from app.infra.repository.produto_repository import ProdutoRepository
from app.infra.repository.produto_composicao_repository import ProdutoComposicaoRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.pedido_repository import PedidoRepository
from app.infra.repository.markup_repository import MarkupRepository
from app.infra.repository.cliente_repository import ClienteRepository
from app.infra.repository.tenant_repository import TenantRepository


def _make_produto_service(session: AsyncSession, tenant: Tenant) -> ProdutoService:
    return ProdutoService(
        produto_repo=ProdutoRepository(session, tenant.id),
        composicao_repo=ProdutoComposicaoRepository(session),
        ingrediente_repo=IngredienteRepository(session, tenant.id),
        tenant_id=tenant.id,
    )


def _make_pedido_service(session: AsyncSession, tenant: Tenant) -> PedidoService:
    return PedidoService(
        pedido_repo=PedidoRepository(session, tenant.id),
        produto_repo=ProdutoRepository(session, tenant.id),
        composicao_repo=ProdutoComposicaoRepository(session),
        ingrediente_repo=IngredienteRepository(session, tenant.id),
        markup_repo=MarkupRepository(session, tenant.id),
        cliente_repo=ClienteRepository(session, tenant.id),
        tenant_repo=TenantRepository(session),
        tenant_id=tenant.id,
    )


class TestIsolamentoMultiTenant:

    async def test_produto_tenant_a_invisivel_para_b(self, session, tenant, tenant_b):
        """Produto criado no Tenant A não aparece na listagem do Tenant B."""
        service_a = _make_produto_service(session, tenant)
        service_b = _make_produto_service(session, tenant_b)

        await service_a.criar(nome="Produto do Tenant A")

        produtos_a = await service_a.listar()
        produtos_b = await service_b.listar()

        assert any(p.nome == "Produto do Tenant A" for p in produtos_a)
        assert not any(p.nome == "Produto do Tenant A" for p in produtos_b)

    async def test_produto_tenant_a_nao_acessivel_por_b(self, session, tenant, tenant_b):
        """Buscar por ID de produto do Tenant A pelo Tenant B retorna erro."""
        service_a = _make_produto_service(session, tenant)
        service_b = _make_produto_service(session, tenant_b)

        produto = await service_a.criar(nome="Secreto do A")

        with pytest.raises(ProdutoNaoEncontradoError):
            await service_b.buscar_por_id(produto.id)

    async def test_pedido_tenant_a_invisivel_para_b(self, session, tenant, tenant_b, cliente):
        """Pedido criado no Tenant A não aparece na listagem do Tenant B."""
        service_a = _make_pedido_service(session, tenant)
        service_b = _make_pedido_service(session, tenant_b)

        await service_a.criar(cliente_id=cliente.id)

        pedidos_a = await service_a.listar()
        pedidos_b = await service_b.listar()

        assert len(pedidos_a) >= 1
        assert len(pedidos_b) == 0

    async def test_pedido_tenant_a_nao_acessivel_por_b(self, session, tenant, tenant_b, cliente):
        """Buscar pedido do Tenant A pelo Tenant B retorna erro."""
        service_a = _make_pedido_service(session, tenant)
        service_b = _make_pedido_service(session, tenant_b)

        pedido = await service_a.criar(cliente_id=cliente.id)

        with pytest.raises(PedidoNaoEncontradoError):
            await service_b.buscar_por_id(pedido.id)

    async def test_ingrediente_tenant_a_invisivel_para_b(self, session, tenant, tenant_b, ingredientes):
        """Ingredientes do Tenant A não são visíveis pelo Tenant B."""
        repo_a = IngredienteRepository(session, tenant.id)
        repo_b = IngredienteRepository(session, tenant_b.id)

        ingredientes_a = await repo_a.list_all()
        ingredientes_b = await repo_b.list_all()

        assert len(ingredientes_a) >= 4  # Os 4 da fixture
        assert len(ingredientes_b) == 0
