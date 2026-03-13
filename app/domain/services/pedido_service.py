"""
Service: Pedido
Regras de negócio:
- Pedido só pode ser criado a partir de orçamento APROVADO
- Copia itens do orçamento como snapshot
- Controla transição de status
"""
import uuid
from datetime import datetime

from app.infra.database.models.base import StatusOrcamento, StatusPedido
from app.infra.database.models.pedido import Pedido, PedidoItem
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.orcamento_repository import OrcamentoRepository
from app.infra.repository.pedido_repository import PedidoRepository


# ── Exceções ──────────────────────────────────────────────────────────────────

class PedidoNaoEncontradoError(Exception):
    def __init__(self, pedido_id: uuid.UUID):
        super().__init__(f"Pedido não encontrado: {pedido_id}")


class OrcamentoNaoAprovadoError(Exception):
    def __init__(self, status: str):
        super().__init__(
            f"Orçamento deve estar APROVADO para gerar pedido. Status atual: '{status}'"
        )


class PedidoJaExisteError(Exception):
    def __init__(self, orcamento_id: uuid.UUID):
        super().__init__(f"Já existe um pedido para o orçamento: {orcamento_id}")


class TransicaoStatusInvalidaError(Exception):
    def __init__(self, atual: str, novo: str):
        super().__init__(f"Não é possível mudar status de '{atual}' para '{novo}'")


# ── Transições de status permitidas ──────────────────────────────────────────

TRANSICOES_VALIDAS = {
    StatusPedido.AGUARDANDO_PRODUCAO: [StatusPedido.EM_PRODUCAO, StatusPedido.CANCELADO],
    StatusPedido.EM_PRODUCAO: [StatusPedido.PRONTO, StatusPedido.CANCELADO],
    StatusPedido.PRONTO: [StatusPedido.ENTREGUE],
    StatusPedido.ENTREGUE: [],
    StatusPedido.CANCELADO: [],
}


# ── Service ───────────────────────────────────────────────────────────────────

class PedidoService:

    def __init__(
        self,
        pedido_repo: PedidoRepository,
        orcamento_repo: OrcamentoRepository,
        ingrediente_repo: IngredienteRepository,
        tenant_id: uuid.UUID,
    ) -> None:
        self._pedido_repo = pedido_repo
        self._orcamento_repo = orcamento_repo
        self._ingrediente_repo = ingrediente_repo
        self._tenant_id = tenant_id

    async def criar_de_orcamento(
        self,
        orcamento_id: uuid.UUID,
        data_entrega_prevista: datetime | None = None,
        observacoes: str | None = None,
    ) -> Pedido:
        # Busca e valida orçamento
        orcamento = await self._orcamento_repo.get_by_id(orcamento_id)
        if not orcamento:
            raise Exception(f"Orçamento não encontrado: {orcamento_id}")

        if orcamento.status != StatusOrcamento.APROVADO:
            raise OrcamentoNaoAprovadoError(orcamento.status)

        # Verifica se já existe pedido para este orçamento
        pedido_existente = await self._pedido_repo.get_by_orcamento_id(orcamento_id)
        if pedido_existente:
            raise PedidoJaExisteError(orcamento_id)

        # Gera número do pedido
        numero = await self._pedido_repo.proximo_numero()

        # Cria o pedido com snapshot dos valores do orçamento
        pedido = Pedido(
            tenant_id=self._tenant_id,
            numero=numero,
            orcamento_id=orcamento_id,
            cliente_id=orcamento.cliente_id,
            status=StatusPedido.AGUARDANDO_PRODUCAO,
            valor_total=orcamento.preco_final,
            taxa_entrega=orcamento.taxa_entrega,
            custo_embalagem=orcamento.custo_embalagem,
            data_entrega_prevista=data_entrega_prevista,
            observacoes=observacoes,
        )
        self._pedido_repo._session.add(pedido)
        await self._pedido_repo._session.flush()

        # Copia itens do orçamento como snapshot
        for item_orc in orcamento.itens:
            ingrediente = await self._ingrediente_repo.get_by_id(item_orc.ingrediente_id)
            nome_snapshot = ingrediente.nome if ingrediente else "Ingrediente removido"

            item_pedido = PedidoItem(
                tenant_id=self._tenant_id,
                pedido_id=pedido.id,
                ingrediente_id=item_orc.ingrediente_id,
                nome_ingrediente_snapshot=nome_snapshot,
                quantidade=item_orc.quantidade,
                unidade_medida=item_orc.unidade_medida,
                custo_unitario_snapshot=item_orc.custo_unitario_snapshot,
                custo_total_item=item_orc.custo_total_item,
            )
            self._pedido_repo._session.add(item_pedido)

        return await self._pedido_repo.create(pedido)

    async def buscar_por_id(self, pedido_id: uuid.UUID) -> Pedido:
        pedido = await self._pedido_repo.get_by_id(pedido_id)
        if not pedido:
            raise PedidoNaoEncontradoError(pedido_id)
        return pedido

    async def listar(
        self,
        cliente_id: uuid.UUID | None = None,
        status: StatusPedido | None = None,
    ) -> list[Pedido]:
        return await self._pedido_repo.list_all(cliente_id=cliente_id, status=status)

    async def atualizar(
        self,
        pedido_id: uuid.UUID,
        data_entrega_prevista: datetime | None = None,
        data_entrega_realizada: datetime | None = None,
        observacoes: str | None = None,
    ) -> Pedido:
        pedido = await self.buscar_por_id(pedido_id)

        if pedido.status in [StatusPedido.ENTREGUE, StatusPedido.CANCELADO]:
            raise Exception(f"Pedido com status '{pedido.status}' não pode ser editado")

        if data_entrega_prevista is not None:
            pedido.data_entrega_prevista = data_entrega_prevista
        if data_entrega_realizada is not None:
            pedido.data_entrega_realizada = data_entrega_realizada
        if observacoes is not None:
            pedido.observacoes = observacoes

        pedido.updated_at = datetime.utcnow()
        return await self._pedido_repo.update(pedido)

    async def mudar_status(
        self, pedido_id: uuid.UUID, novo_status: StatusPedido
    ) -> Pedido:
        pedido = await self.buscar_por_id(pedido_id)

        transicoes = TRANSICOES_VALIDAS.get(pedido.status, [])
        if novo_status not in transicoes:
            raise TransicaoStatusInvalidaError(pedido.status, novo_status)

        # Se entregue, registra data de entrega realizada automaticamente
        if novo_status == StatusPedido.ENTREGUE:
            pedido.data_entrega_realizada = datetime.utcnow()

        pedido.status = novo_status
        pedido.updated_at = datetime.utcnow()
        return await self._pedido_repo.update(pedido)
