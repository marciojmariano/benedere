"""
Testes: PedidoService — máquina de estados
Task: 5.1.6
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services.pedido_service import (
    PedidoService,
    PedidoNaoEditavelError,
    TransicaoStatusInvalidaError,
)
from app.infra.database.models.base import StatusPedido, TipoItem
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


class TestMaquinaDeEstados:

    # ── Transições válidas ───────────────────────────────────────────────────

    async def test_rascunho_para_aprovado(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pedido = await service.transicionar_status(pedido.id, StatusPedido.APROVADO)
        assert pedido.status == StatusPedido.APROVADO

    async def test_aprovado_para_em_producao(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)
        pedido = await service.transicionar_status(pedido.id, StatusPedido.APROVADO)

        pedido = await service.transicionar_status(pedido.id, StatusPedido.EM_PRODUCAO)
        assert pedido.status == StatusPedido.EM_PRODUCAO

    async def test_em_producao_para_entregue(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)
        await service.transicionar_status(pedido.id, StatusPedido.APROVADO)
        await service.transicionar_status(pedido.id, StatusPedido.EM_PRODUCAO)

        pedido = await service.transicionar_status(pedido.id, StatusPedido.ENTREGUE)
        assert pedido.status == StatusPedido.ENTREGUE
        assert pedido.data_entrega_realizada is not None

    async def test_rascunho_para_cancelado(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        pedido = await service.transicionar_status(pedido.id, StatusPedido.CANCELADO)
        assert pedido.status == StatusPedido.CANCELADO

    async def test_aprovado_para_cancelado(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)
        await service.transicionar_status(pedido.id, StatusPedido.APROVADO)

        pedido = await service.transicionar_status(pedido.id, StatusPedido.CANCELADO)
        assert pedido.status == StatusPedido.CANCELADO

    async def test_em_producao_para_cancelado(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)
        await service.transicionar_status(pedido.id, StatusPedido.APROVADO)
        await service.transicionar_status(pedido.id, StatusPedido.EM_PRODUCAO)

        pedido = await service.transicionar_status(pedido.id, StatusPedido.CANCELADO)
        assert pedido.status == StatusPedido.CANCELADO

    # ── Transições inválidas ─────────────────────────────────────────────────

    async def test_rascunho_para_em_producao_erro(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        with pytest.raises(TransicaoStatusInvalidaError):
            await service.transicionar_status(pedido.id, StatusPedido.EM_PRODUCAO)

    async def test_rascunho_para_entregue_erro(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)

        with pytest.raises(TransicaoStatusInvalidaError):
            await service.transicionar_status(pedido.id, StatusPedido.ENTREGUE)

    async def test_aprovado_para_rascunho_erro(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)
        await service.transicionar_status(pedido.id, StatusPedido.APROVADO)

        with pytest.raises(TransicaoStatusInvalidaError):
            await service.transicionar_status(pedido.id, StatusPedido.RASCUNHO)

    async def test_entregue_para_qualquer_status_erro(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)
        await service.transicionar_status(pedido.id, StatusPedido.APROVADO)
        await service.transicionar_status(pedido.id, StatusPedido.EM_PRODUCAO)
        await service.transicionar_status(pedido.id, StatusPedido.ENTREGUE)

        for status in [StatusPedido.RASCUNHO, StatusPedido.APROVADO, StatusPedido.EM_PRODUCAO, StatusPedido.CANCELADO]:
            with pytest.raises(TransicaoStatusInvalidaError):
                await service.transicionar_status(pedido.id, status)

    async def test_cancelado_para_qualquer_status_erro(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)
        await service.transicionar_status(pedido.id, StatusPedido.CANCELADO)

        for status in [StatusPedido.RASCUNHO, StatusPedido.APROVADO, StatusPedido.EM_PRODUCAO, StatusPedido.ENTREGUE]:
            with pytest.raises(TransicaoStatusInvalidaError):
                await service.transicionar_status(pedido.id, status)

    # ── Bloqueio de edição fora de rascunho ──────────────────────────────────

    async def test_nao_edita_pedido_aprovado(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)
        await service.transicionar_status(pedido.id, StatusPedido.APROVADO)

        with pytest.raises(PedidoNaoEditavelError):
            await service.atualizar(pedido.id, observacoes="Tentativa")

    async def test_nao_deleta_pedido_aprovado(self, session, tenant, cliente):
        service = _make_service(session, tenant)
        pedido = await service.criar(cliente_id=cliente.id)
        await service.transicionar_status(pedido.id, StatusPedido.APROVADO)

        with pytest.raises(PedidoNaoEditavelError):
            await service.deletar(pedido.id)
