"""
Service: Pedido
Tasks: 3.1.4, 3.2.3-3.2.6, 3.3.2-3.3.3
"""
import uuid
from datetime import datetime
from decimal import Decimal

from app.infra.database.models.base import StatusPedido, TipoItem, TipoRefeicao
from app.infra.database.models.pedido import Pedido
from app.infra.database.models.pedido_item import PedidoItem
from app.infra.database.models.pedido_item_composicao import PedidoItemComposicao
from app.infra.repository.pedido_repository import PedidoRepository
from app.infra.repository.produto_repository import ProdutoRepository
from app.infra.repository.produto_composicao_repository import ProdutoComposicaoRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.markup_repository import MarkupRepository
from app.infra.repository.cliente_repository import ClienteRepository
from app.infra.repository.tenant_repository import TenantRepository
from app.infra.repository.faixa_peso_embalagem_repository import FaixaPesoEmbalagemRepository


# ── Exceções ──────────────────────────────────────────────────────────────────

class PedidoNaoEncontradoError(Exception):
    def __init__(self, pedido_id: uuid.UUID):
        super().__init__(f"Pedido não encontrado: {pedido_id}")


class PedidoNaoEditavelError(Exception):
    def __init__(self):
        super().__init__("Pedido só pode ser editado nos status RASCUNHO ou APROVADO")


class TransicaoStatusInvalidaError(Exception):
    def __init__(self, atual: str, destino: str):
        super().__init__(f"Transição inválida: {atual} → {destino}")


class ClienteNaoEncontradoError(Exception):
    def __init__(self, cliente_id: uuid.UUID):
        super().__init__(f"Cliente não encontrado: {cliente_id}")


class ProdutoNaoEncontradoError(Exception):
    def __init__(self, produto_id: uuid.UUID):
        super().__init__(f"Produto não encontrado: {produto_id}")


class IngredienteNaoEncontradoError(Exception):
    def __init__(self, ingrediente_id: uuid.UUID):
        super().__init__(f"Ingrediente não encontrado: {ingrediente_id}")


class ItemNaoEncontradoError(Exception):
    def __init__(self, item_id: uuid.UUID):
        super().__init__(f"Item do pedido não encontrado: {item_id}")


class ComposicaoVaziaError(Exception):
    def __init__(self):
        super().__init__("Item personalizado deve ter pelo menos 1 ingrediente")


class NomeObrigatorioError(Exception):
    def __init__(self):
        super().__init__("Nome é obrigatório para itens personalizados")


# ── Máquina de estados ───────────────────────────────────────────────────────

TRANSICOES_VALIDAS: dict[StatusPedido, list[StatusPedido]] = {
    StatusPedido.RASCUNHO: [StatusPedido.APROVADO, StatusPedido.CANCELADO],
    StatusPedido.APROVADO: [StatusPedido.EM_PRODUCAO, StatusPedido.CANCELADO, StatusPedido.RASCUNHO],
    StatusPedido.EM_PRODUCAO: [StatusPedido.ENTREGUE, StatusPedido.CANCELADO, StatusPedido.APROVADO],
    StatusPedido.ENTREGUE: [],
    StatusPedido.CANCELADO: [],
}


# ── Service ───────────────────────────────────────────────────────────────────

class PedidoService:

    def __init__(
        self,
        pedido_repo: PedidoRepository,
        produto_repo: ProdutoRepository,
        composicao_repo: ProdutoComposicaoRepository,
        ingrediente_repo: IngredienteRepository,
        markup_repo: MarkupRepository,
        cliente_repo: ClienteRepository,
        tenant_repo: TenantRepository,
        faixa_repo: FaixaPesoEmbalagemRepository,
        tenant_id: uuid.UUID,
    ) -> None:
        self._pedido_repo = pedido_repo
        self._produto_repo = produto_repo
        self._composicao_repo = composicao_repo
        self._ingrediente_repo = ingrediente_repo
        self._markup_repo = markup_repo
        self._cliente_repo = cliente_repo
        self._tenant_repo = tenant_repo
        self._faixa_repo = faixa_repo
        self._tenant_id = tenant_id

    # ── CRUD Pedido ──────────────────────────────────────────────────────────

    async def criar(
        self,
        cliente_id: uuid.UUID,
        markup_id: uuid.UUID | None = None,
        observacoes: str | None = None,
        data_entrega_prevista: datetime | None = None,
    ) -> Pedido:
        # Valida cliente
        cliente = await self._cliente_repo.get_by_id(cliente_id)
        if not cliente:
            raise ClienteNaoEncontradoError(cliente_id)

        # Resolve markup: parâmetro → cliente → tenant → null
        markup_id_resolvido = await self._resolver_markup(markup_id, cliente)

        numero = await self._pedido_repo.get_next_numero()

        pedido = Pedido(
            tenant_id=self._tenant_id,
            numero=numero,
            cliente_id=cliente_id,
            markup_id=markup_id_resolvido,
            status=StatusPedido.RASCUNHO,
            observacoes=observacoes,
            data_entrega_prevista=data_entrega_prevista,
        )
        return await self._pedido_repo.create(pedido)

    async def buscar_por_id(self, pedido_id: uuid.UUID) -> Pedido:
        pedido = await self._pedido_repo.get_by_id(pedido_id)
        if not pedido:
            raise PedidoNaoEncontradoError(pedido_id)
        return pedido

    async def listar(
        self,
        status: StatusPedido | None = None,
        cliente_id: uuid.UUID | None = None,
    ) -> list[Pedido]:
        return await self._pedido_repo.list_all(status=status, cliente_id=cliente_id)

    async def atualizar(
        self,
        pedido_id: uuid.UUID,
        observacoes: str | None = None,
        data_entrega_prevista: datetime | None = None,
    ) -> Pedido:
        pedido = await self.buscar_por_id(pedido_id)
        self._validar_editavel(pedido)

        if observacoes is not None:
            pedido.observacoes = observacoes
        if data_entrega_prevista is not None:
            pedido.data_entrega_prevista = data_entrega_prevista

        pedido.updated_at = datetime.utcnow()
        return await self._pedido_repo.update(pedido)

    async def deletar(self, pedido_id: uuid.UUID) -> None:
        pedido = await self.buscar_por_id(pedido_id)
        self._validar_editavel(pedido)
        await self._pedido_repo.delete(pedido)

    # ── Transição de status ──────────────────────────────────────────────────

    async def transicionar_status(
        self,
        pedido_id: uuid.UUID,
        novo_status: StatusPedido,
    ) -> Pedido:
        pedido = await self.buscar_por_id(pedido_id)

        if novo_status not in TRANSICOES_VALIDAS.get(pedido.status, []):
            raise TransicaoStatusInvalidaError(pedido.status.value, novo_status.value)

        pedido.status = novo_status

        # Registra data de entrega ao marcar como entregue
        if novo_status == StatusPedido.ENTREGUE:
            pedido.data_entrega_realizada = datetime.utcnow()

        pedido.updated_at = datetime.utcnow()
        return await self._pedido_repo.update(pedido)

    # ── Duplicar pedido ──────────────────────────────────────────────────────

    async def duplicar(self, pedido_id: uuid.UUID) -> Pedido:
        """Clona um pedido existente como novo RASCUNHO com os mesmos itens e snapshots."""
        original = await self.buscar_por_id(pedido_id)

        numero = await self._pedido_repo.get_next_numero()

        novo_pedido = Pedido(
            tenant_id=self._tenant_id,
            numero=numero,
            cliente_id=original.cliente_id,
            markup_id=original.markup_id,
            status=StatusPedido.RASCUNHO,
            observacoes=original.observacoes,
            data_entrega_prevista=original.data_entrega_prevista,
            valor_total=original.valor_total,
        )
        novo_pedido = await self._pedido_repo.create(novo_pedido)

        for item in original.itens:
            composicao_clone = [
                PedidoItemComposicao(
                    ingrediente_id=c.ingrediente_id,
                    ingrediente_nome_snap=c.ingrediente_nome_snap,
                    quantidade_g=c.quantidade_g,
                    custo_kg_snapshot=c.custo_kg_snapshot,
                    kcal_snapshot=c.kcal_snapshot,
                )
                for c in item.composicao
            ]
            novo_item = PedidoItem(
                pedido_id=novo_pedido.id,
                produto_id=item.produto_id,
                nome_snapshot=item.nome_snapshot,
                tipo_refeicao=item.tipo_refeicao,
                tipo=item.tipo,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                preco_total=item.preco_total,
                composicao=composicao_clone,
                embalagem_ingrediente_id=item.embalagem_ingrediente_id,
                embalagem_nome_snapshot=item.embalagem_nome_snapshot,
                embalagem_custo_snapshot=item.embalagem_custo_snapshot,
            )
            self._session_add(novo_item)

        await self._session_flush()
        return await self.buscar_por_id(novo_pedido.id)

    # ── Adicionar item ───────────────────────────────────────────────────────

    async def adicionar_item(
        self,
        pedido_id: uuid.UUID,
        tipo: TipoItem,
        produto_id: uuid.UUID | None = None,
        nome: str | None = None,
        tipo_refeicao: TipoRefeicao | None = None,
        quantidade: int = 1,
        composicao_manual: list[dict] | None = None,
    ) -> Pedido:
        pedido = await self.buscar_por_id(pedido_id)
        self._validar_editavel(pedido)

        if tipo == TipoItem.SERIE:
            item = await self._criar_item_serie(
                pedido, produto_id, tipo_refeicao, quantidade
            )
        else:
            item = await self._criar_item_personalizado(
                pedido, nome, tipo_refeicao, quantidade, composicao_manual
            )

        self._session_add(item)
        await self._recalcular_valor_total(pedido)
        return await self.buscar_por_id(pedido_id)

    async def atualizar_item(
        self,
        pedido_id: uuid.UUID,
        item_id: uuid.UUID,
        nome: str | None = None,
        tipo_refeicao: TipoRefeicao | None = None,
        quantidade: int | None = None,
        composicao_manual: list[dict] | None = None,
    ) -> Pedido:
        pedido = await self.buscar_por_id(pedido_id)
        self._validar_editavel(pedido)

        item = self._encontrar_item(pedido, item_id)

        if nome is not None:
            item.nome_snapshot = nome
        if tipo_refeicao is not None:
            item.tipo_refeicao = tipo_refeicao

        # Se composição nova veio, substitui
        if composicao_manual is not None:
            if not composicao_manual:
                raise ComposicaoVaziaError()
            # Remove composição antiga
            item.composicao.clear()
            await self._session_flush()
            # Cria nova
            markup_fator = await self._get_markup_fator(pedido.markup_id)
            composicao_items = await self._criar_composicao_manual(composicao_manual)
            custo_total = sum(
                Decimal(str(c.quantidade_g)) / Decimal("1000") * Decimal(str(c.custo_kg_snapshot))
                for c in composicao_items
            )
            item.preco_unitario = float(custo_total * markup_fator)
            item.composicao = composicao_items

            # Re-resolve embalagem pelo novo peso
            peso_total_g = sum(float(c.quantidade_g) for c in composicao_items)
            embalagem = await self._resolver_embalagem(peso_total_g)
            item.embalagem_ingrediente_id = embalagem[0] if embalagem else None
            item.embalagem_nome_snapshot = embalagem[1] if embalagem else None
            item.embalagem_custo_snapshot = embalagem[2] if embalagem else None

        if quantidade is not None:
            item.quantidade = quantidade

        item.preco_total = float(Decimal(str(item.preco_unitario)) * item.quantidade)
        await self._recalcular_valor_total(pedido)
        return await self.buscar_por_id(pedido_id)

    async def remover_item(
        self,
        pedido_id: uuid.UUID,
        item_id: uuid.UUID,
    ) -> Pedido:
        pedido = await self.buscar_por_id(pedido_id)
        self._validar_editavel(pedido)

        item = self._encontrar_item(pedido, item_id)
        pedido.itens.remove(item)
        await self._session_flush()
        await self._recalcular_valor_total(pedido)
        return await self.buscar_por_id(pedido_id)

    # ── Criação de itens (privados) ──────────────────────────────────────────

    async def _criar_item_serie(
        self,
        pedido: Pedido,
        produto_id: uuid.UUID | None,
        tipo_refeicao_override: TipoRefeicao | None,
        quantidade: int,
    ) -> PedidoItem:
        if not produto_id:
            raise ProdutoNaoEncontradoError(uuid.UUID(int=0))

        produto = await self._produto_repo.get_by_id(produto_id)
        if not produto:
            raise ProdutoNaoEncontradoError(produto_id)

        # Clona composição do catálogo com snapshots
        composicao_catalogo = await self._composicao_repo.list_by_produto(produto_id)
        markup_fator = await self._get_markup_fator(pedido.markup_id)

        composicao_snapshot = []
        custo_total = Decimal("0")
        for comp in composicao_catalogo:
            ing = comp.ingrediente
            custo_kg = Decimal(str(ing.custo_calculado)) if ing.custo_calculado is not None else Decimal(str(ing.custo_unitario))
            qtd_g = Decimal(str(comp.quantidade_g))
            custo_item = qtd_g / Decimal("1000") * custo_kg

            composicao_snapshot.append(
                PedidoItemComposicao(
                    ingrediente_id=ing.id,
                    ingrediente_nome_snap=ing.nome,
                    quantidade_g=float(qtd_g),
                    custo_kg_snapshot=float(custo_kg),
                    kcal_snapshot=0,  # TODO: calcular via JSONB
                )
            )
            custo_total += custo_item

        # tipo_refeicao: usa override se fornecido, senão herda do catálogo
        tipo_refeicao = tipo_refeicao_override or produto.tipo_refeicao

        # Resolve embalagem pelo peso total dos ingredientes
        peso_total_g = sum(float(c.quantidade_g) for c in composicao_snapshot)
        embalagem = await self._resolver_embalagem(peso_total_g)

        # Soma custo da embalagem antes de aplicar markup
        if embalagem:
            custo_total += Decimal(str(embalagem[2]))

        preco_unitario = custo_total * markup_fator
        preco_total = preco_unitario * quantidade

        item = PedidoItem(
            pedido_id=pedido.id,
            produto_id=produto.id,
            nome_snapshot=produto.nome,
            tipo_refeicao=tipo_refeicao,
            tipo=TipoItem.SERIE,
            quantidade=quantidade,
            preco_unitario=float(preco_unitario),
            preco_total=float(preco_total),
            composicao=composicao_snapshot,
            embalagem_ingrediente_id=embalagem[0] if embalagem else None,
            embalagem_nome_snapshot=embalagem[1] if embalagem else None,
            embalagem_custo_snapshot=embalagem[2] if embalagem else None,
        )
        return item

    async def _criar_item_personalizado(
        self,
        pedido: Pedido,
        nome: str | None,
        tipo_refeicao: TipoRefeicao | None,
        quantidade: int,
        composicao_manual: list[dict] | None,
    ) -> PedidoItem:
        if not nome:
            raise NomeObrigatorioError()
        if not composicao_manual:
            raise ComposicaoVaziaError()

        markup_fator = await self._get_markup_fator(pedido.markup_id)
        composicao_items = await self._criar_composicao_manual(composicao_manual)

        custo_total = sum(
            Decimal(str(c.quantidade_g)) / Decimal("1000") * Decimal(str(c.custo_kg_snapshot))
            for c in composicao_items
        )

        # Resolve embalagem pelo peso total dos ingredientes
        peso_total_g = sum(float(c.quantidade_g) for c in composicao_items)
        embalagem = await self._resolver_embalagem(peso_total_g)

        # Soma custo da embalagem antes de aplicar markup
        if embalagem:
            custo_total += Decimal(str(embalagem[2]))

        preco_unitario = custo_total * markup_fator
        preco_total = preco_unitario * quantidade

        item = PedidoItem(
            pedido_id=pedido.id,
            produto_id=None,
            nome_snapshot=nome,
            tipo_refeicao=tipo_refeicao,
            tipo=TipoItem.PERSONALIZADO,
            quantidade=quantidade,
            preco_unitario=float(preco_unitario),
            preco_total=float(preco_total),
            composicao=composicao_items,
            embalagem_ingrediente_id=embalagem[0] if embalagem else None,
            embalagem_nome_snapshot=embalagem[1] if embalagem else None,
            embalagem_custo_snapshot=embalagem[2] if embalagem else None,
        )
        return item

    async def _criar_composicao_manual(
        self,
        composicao: list[dict],
    ) -> list[PedidoItemComposicao]:
        """Cria snapshots de composição a partir da seleção manual do usuário."""
        items = []
        for comp in composicao:
            ingrediente_id = comp["ingrediente_id"]
            ingrediente = await self._ingrediente_repo.get_by_id(ingrediente_id)
            if not ingrediente:
                raise IngredienteNaoEncontradoError(ingrediente_id)

            custo_kg = ingrediente.custo_calculado if ingrediente.custo_calculado is not None else ingrediente.custo_unitario
            items.append(
                PedidoItemComposicao(
                    ingrediente_id=ingrediente.id,
                    ingrediente_nome_snap=ingrediente.nome,
                    quantidade_g=float(comp["quantidade_g"]),
                    custo_kg_snapshot=float(custo_kg),
                    kcal_snapshot=0,  # TODO: calcular via JSONB
                )
            )
        return items

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def _resolver_embalagem(
        self, peso_total_g: float
    ) -> tuple[uuid.UUID, str, float] | None:
        """Busca a faixa de peso correspondente e retorna (id, nome, custo) da embalagem."""
        faixa = await self._faixa_repo.buscar_por_peso(peso_total_g)
        if not faixa:
            return None
        ing = faixa.ingrediente_embalagem
        custo_embalagem = ing.custo_calculado if ing.custo_calculado is not None else ing.custo_unitario
        return (ing.id, ing.nome, float(custo_embalagem))

    async def _resolver_markup(self, markup_id: uuid.UUID | None, cliente) -> uuid.UUID | None:
        """Cadeia: parâmetro → cliente.markup_id_padrao → tenant.markup_id_padrao → null."""
        if markup_id:
            markup = await self._markup_repo.get_by_id(markup_id)
            if markup and markup.ativo:
                return markup.id

        if cliente.markup_id_padrao:
            markup = await self._markup_repo.get_by_id(cliente.markup_id_padrao)
            if markup and markup.ativo:
                return markup.id

        tenant = await self._tenant_repo.get_by_id(self._tenant_id)
        if tenant and tenant.markup_id_padrao:
            markup = await self._markup_repo.get_by_id(tenant.markup_id_padrao)
            if markup and markup.ativo:
                return markup.id

        return None

    async def _get_markup_fator(self, markup_id: uuid.UUID | None) -> Decimal:
        """Retorna o fator do markup ou 1.0 se não houver markup."""
        if not markup_id:
            return Decimal("1")
        markup = await self._markup_repo.get_by_id(markup_id)
        if not markup or not markup.ativo:
            return Decimal("1")
        return Decimal(str(markup.fator))

    async def _recalcular_valor_total(self, pedido: Pedido) -> None:
        """Recalcula valor_total pela soma dos preco_total de todos os itens."""
        # Flush garante que itens pendentes estão no DB antes da re-leitura
        await self._session_flush()
        # Expira a relação para forçar o selectinload a recarregar do DB
        self._pedido_repo._session.expire(pedido, ['itens'])
        pedido_atualizado = await self._pedido_repo.get_by_id(pedido.id)
        if pedido_atualizado:
            total = sum(
                Decimal(str(item.preco_total))
                for item in pedido_atualizado.itens
            )
            pedido_atualizado.valor_total = float(total)
            pedido_atualizado.updated_at = datetime.utcnow()
            await self._pedido_repo.update(pedido_atualizado)

    def _validar_editavel(self, pedido: Pedido) -> None:
        if pedido.status not in (StatusPedido.RASCUNHO, StatusPedido.APROVADO):
            raise PedidoNaoEditavelError()

    def _encontrar_item(self, pedido: Pedido, item_id: uuid.UUID) -> PedidoItem:
        for item in pedido.itens:
            if item.id == item_id:
                return item
        raise ItemNaoEncontradoError(item_id)

    def _session_add(self, obj):
        self._pedido_repo._session.add(obj)

    async def _session_flush(self):
        await self._pedido_repo._session.flush()
