"""
Testes: PedidoService — itens série, personalizado, preço, snapshots
Tasks: 5.1.3, 5.1.4, 5.1.5
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services.pedido_service import (
    PedidoService,
    PedidoNaoEncontradoError,
    PedidoNaoEditavelError,
    ClienteNaoEncontradoError,
    ProdutoNaoEncontradoError,
    IngredienteNaoEncontradoError,
    ComposicaoVaziaError,
    NomeObrigatorioError,
)
from app.infra.database.models.base import StatusPedido, TipoItem, TipoRefeicao
from app.infra.database.models.cliente import Cliente
from app.infra.database.models.ingrediente import Ingrediente
from app.infra.database.models.markup import Markup
from app.infra.database.models.produto import Produto
from app.infra.database.models.tenant import Tenant
from app.infra.repository.pedido_repository import PedidoRepository
from app.infra.repository.produto_repository import ProdutoRepository
from app.infra.repository.produto_composicao_repository import ProdutoComposicaoRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.markup_repository import MarkupRepository
from app.infra.repository.cliente_repository import ClienteRepository
from app.infra.repository.tenant_repository import TenantRepository


def _make_service(session: AsyncSession, tenant: Tenant) -> PedidoService:
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


# ── CRUD Pedido ──────────────────────────────────────────────────────────────

class TestPedidoCRUD:

    async def test_criar_pedido(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        assert pedido.id is not None
        assert pedido.numero.startswith("PED-")
        assert pedido.status == StatusPedido.RASCUNHO
        assert pedido.cliente_id == cliente.id
        assert pedido.valor_total == 0

    async def test_criar_pedido_cliente_inexistente(self, session, tenant):
        service = _make_service(session, tenant)
        with pytest.raises(ClienteNaoEncontradoError):
            await service.criar(cliente_id=uuid.uuid4())

    async def test_buscar_pedido_inexistente(self, session, tenant):
        service = _make_service(session, tenant)
        with pytest.raises(PedidoNaoEncontradoError):
            await service.buscar_por_id(uuid.uuid4())

    async def test_deletar_pedido_rascunho(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        await service.deletar(pedido.id)

        with pytest.raises(PedidoNaoEncontradoError):
            await service.buscar_por_id(pedido.id)

    async def test_criar_pedido_com_markup(self, session, tenant, cliente, markup):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id, markup_id=markup.id)

        assert pedido.markup_id == markup.id


# ── Item de série ────────────────────────────────────────────────────────────

class TestItemSerie:

    async def test_adicionar_item_serie(
        self, session, tenant, cliente, produto_com_composicao
    ):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.SERIE,
            produto_id=produto_com_composicao.id,
            quantidade=1,
        )

        assert len(pedido.itens) == 1
        item = pedido.itens[0]
        assert item.tipo == TipoItem.SERIE
        assert item.produto_id == produto_com_composicao.id
        assert item.nome_snapshot == "Escondidinho de Ragu"
        assert item.tipo_refeicao == TipoRefeicao.ALMOCO

    async def test_serie_clona_composicao_com_snapshots(
        self, session, tenant, cliente, produto_com_composicao, ingredientes
    ):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.SERIE,
            produto_id=produto_com_composicao.id,
            quantidade=1,
        )

        item = pedido.itens[0]
        assert len(item.composicao) == 4

        # Verifica snapshots do primeiro ingrediente (Purê de Batata Baroa)
        pure_snap = next(
            c for c in item.composicao if c.ingrediente_nome_snap == "Purê de Batata Baroa"
        )
        assert pure_snap.quantidade_g == 100
        assert pure_snap.custo_kg_snapshot == 25.0  # Snapshot do momento

    async def test_serie_calcula_preco_sem_markup(
        self, session, tenant, cliente, produto_com_composicao
    ):
        """Sem markup, preco_unitario = custo puro."""
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.SERIE,
            produto_id=produto_com_composicao.id,
            quantidade=2,
        )

        item = pedido.itens[0]
        # Custo: 100g×25/kg + 85g×45/kg + 10g×89.9/kg + 5g×120/kg
        # = 2.50 + 3.825 + 0.899 + 0.60 = 7.824
        custo_esperado = Decimal("7.824")
        assert abs(Decimal(str(item.preco_unitario)) - custo_esperado) < Decimal("0.01")
        assert item.quantidade == 2

    async def test_serie_calcula_preco_com_markup(
        self, session, tenant, cliente, markup, produto_com_composicao
    ):
        """Com markup fator 1.8182, preço = custo × 1.8182."""
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id, markup_id=markup.id)

        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.SERIE,
            produto_id=produto_com_composicao.id,
            quantidade=1,
        )

        item = pedido.itens[0]
        # Custo base ~7.824 × 1.8182 = ~14.226
        preco = Decimal(str(item.preco_unitario))
        assert preco > Decimal("14")
        assert preco < Decimal("15")

    async def test_serie_override_tipo_refeicao(
        self, session, tenant, cliente, produto_com_composicao
    ):
        """Tipo de refeição pode ser sobrescrito no momento do pedido."""
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.SERIE,
            produto_id=produto_com_composicao.id,
            tipo_refeicao=TipoRefeicao.JANTAR,  # Override
            quantidade=1,
        )

        item = pedido.itens[0]
        assert item.tipo_refeicao == TipoRefeicao.JANTAR  # Não ALMOCO do catálogo

    async def test_serie_produto_inexistente_erro(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        with pytest.raises(ProdutoNaoEncontradoError):
            await service.adicionar_item(
                pedido_id=pedido.id,
                tipo=TipoItem.SERIE,
                produto_id=uuid.uuid4(),
                quantidade=1,
            )


# ── Item personalizado ───────────────────────────────────────────────────────

class TestItemPersonalizado:

    async def test_adicionar_item_personalizado(self, session, tenant, cliente, ingredientes):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pure = ingredientes["Purê de Batata Baroa"]
        ragu = ingredientes["Ragu de Carne"]

        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.PERSONALIZADO,
            nome="Marmita Custom",
            tipo_refeicao=TipoRefeicao.ALMOCO,
            quantidade=1,
            composicao_manual=[
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("120")},
                {"ingrediente_id": ragu.id, "quantidade_g": Decimal("80")},
            ],
        )

        assert len(pedido.itens) == 1
        item = pedido.itens[0]
        assert item.tipo == TipoItem.PERSONALIZADO
        assert item.produto_id is None
        assert item.nome_snapshot == "Marmita Custom"
        assert len(item.composicao) == 2

    async def test_personalizado_snapshot_custo(self, session, tenant, cliente, ingredientes):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pure = ingredientes["Purê de Batata Baroa"]  # R$25/kg

        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.PERSONALIZADO,
            nome="Simples",
            quantidade=1,
            composicao_manual=[
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("200")},
            ],
        )

        item = pedido.itens[0]
        snap = item.composicao[0]
        assert snap.custo_kg_snapshot == 25.0
        assert snap.ingrediente_nome_snap == "Purê de Batata Baroa"
        # Preço: 200g × 25/kg = 5.00 (sem markup)
        assert abs(Decimal(str(item.preco_unitario)) - Decimal("5.00")) < Decimal("0.01")

    async def test_personalizado_sem_nome_erro(self, session, tenant, cliente, ingredientes):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pure = ingredientes["Purê de Batata Baroa"]

        with pytest.raises(NomeObrigatorioError):
            await service.adicionar_item(
                pedido_id=pedido.id,
                tipo=TipoItem.PERSONALIZADO,
                nome=None,
                composicao_manual=[
                    {"ingrediente_id": pure.id, "quantidade_g": Decimal("100")},
                ],
            )

    async def test_personalizado_sem_composicao_erro(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        with pytest.raises(ComposicaoVaziaError):
            await service.adicionar_item(
                pedido_id=pedido.id,
                tipo=TipoItem.PERSONALIZADO,
                nome="Vazia",
                composicao_manual=None,
            )

    async def test_personalizado_ingrediente_inexistente_erro(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        with pytest.raises(IngredienteNaoEncontradoError):
            await service.adicionar_item(
                pedido_id=pedido.id,
                tipo=TipoItem.PERSONALIZADO,
                nome="Ingrediente Fake",
                composicao_manual=[
                    {"ingrediente_id": uuid.uuid4(), "quantidade_g": Decimal("100")},
                ],
            )


# ── Recálculo de valor_total ─────────────────────────────────────────────────

class TestRecalculoValorTotal:

    async def test_valor_total_soma_itens(
        self, session, tenant, cliente, ingredientes
    ):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pure = ingredientes["Purê de Batata Baroa"]  # R$25/kg

        # Item 1: 100g × 25/kg = R$2.50 × 2un = R$5.00
        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.PERSONALIZADO,
            nome="Item 1",
            quantidade=2,
            composicao_manual=[
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("100")},
            ],
        )

        # Item 2: 200g × 25/kg = R$5.00 × 1un = R$5.00
        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.PERSONALIZADO,
            nome="Item 2",
            quantidade=1,
            composicao_manual=[
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("200")},
            ],
        )

        # Total esperado: 5.00 + 5.00 = 10.00
        assert abs(Decimal(str(pedido.valor_total)) - Decimal("10.00")) < Decimal("0.01")

    async def test_valor_total_recalcula_apos_remover_item(
        self, session, tenant, cliente, ingredientes
    ):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pure = ingredientes["Purê de Batata Baroa"]

        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.PERSONALIZADO,
            nome="Item A",
            quantidade=1,
            composicao_manual=[
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("100")},
            ],
        )
        pedido = await service.adicionar_item(
            pedido_id=pedido.id,
            tipo=TipoItem.PERSONALIZADO,
            nome="Item B",
            quantidade=1,
            composicao_manual=[
                {"ingrediente_id": pure.id, "quantidade_g": Decimal("100")},
            ],
        )

        # Remove Item A
        item_a = pedido.itens[0]
        pedido = await service.remover_item(pedido.id, item_a.id)

        # Só ficou Item B: 100g × 25/kg = R$2.50
        assert abs(Decimal(str(pedido.valor_total)) - Decimal("2.50")) < Decimal("0.01")
