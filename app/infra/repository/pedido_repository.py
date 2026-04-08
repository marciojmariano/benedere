"""
Repository: Pedido
Task: 3.1.3
"""
import uuid
from datetime import date
from typing import Literal

from sqlalchemy import func, null, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infra.database.models.base import StatusPedido
from app.infra.database.models.cliente import Cliente
from app.infra.database.models.ingrediente import Ingrediente
from app.infra.database.models.pedido import Pedido
from app.infra.database.models.pedido_item import PedidoItem
from app.infra.database.models.pedido_item_composicao import PedidoItemComposicao


class PedidoRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return select(Pedido).where(Pedido.tenant_id == self._tenant_id)

    def _eager_options(self):
        """Carrega itens e composição em cascade."""
        return [
            selectinload(Pedido.itens).selectinload(PedidoItem.composicao),
        ]

    async def create(self, pedido: Pedido) -> Pedido:
        self._session.add(pedido)
        await self._session.flush()
        await self._session.refresh(pedido)
        return pedido

    async def get_by_id(self, pedido_id: uuid.UUID) -> Pedido | None:
        result = await self._session.execute(
            self._base_query()
            .where(Pedido.id == pedido_id)
            .options(*self._eager_options())
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        status: StatusPedido | None = None,
        cliente_id: uuid.UUID | None = None,
    ) -> list[Pedido]:
        query = self._base_query().options(
            selectinload(Pedido.itens),
            selectinload(Pedido.cliente),
        )
        if status:
            query = query.where(Pedido.status == status)
        if cliente_id:
            query = query.where(Pedido.cliente_id == cliente_id)
        query = query.order_by(Pedido.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, pedido: Pedido) -> Pedido:
        await self._session.flush()
        await self._session.refresh(pedido)
        return pedido

    async def delete(self, pedido: Pedido) -> None:
        await self._session.delete(pedido)
        await self._session.flush()

    async def explosao_ingredientes(
        self,
        data_inicio: date,
        data_fim: date,
        status_list: list[StatusPedido] | None = None,
        filtro_data: Literal["entrega", "criacao"] = "entrega",
    ) -> list:
        """Agrega ingredientes de todos os pedidos do período (BOM explosion)."""
        if status_list is None:
            status_list = [StatusPedido.APROVADO, StatusPedido.EM_PRODUCAO]

        campo_data = Pedido.data_entrega_prevista if filtro_data == "entrega" else Pedido.created_at

        qtd_total = func.sum(
            PedidoItemComposicao.quantidade_g * PedidoItem.quantidade
        ).label("quantidade_total_g")
        custo_kg_medio = (
            func.sum(
                PedidoItemComposicao.quantidade_g
                * PedidoItem.quantidade
                * PedidoItemComposicao.custo_kg_snapshot
            )
            / func.nullif(
                func.sum(PedidoItemComposicao.quantidade_g * PedidoItem.quantidade),
                0,
            )
        ).label("custo_kg_medio")

        query = (
            select(
                PedidoItemComposicao.ingrediente_id,
                PedidoItemComposicao.ingrediente_nome_snap,
                Ingrediente.tipo,
                Ingrediente.unidade_medida,
                Ingrediente.saldo_atual,
                qtd_total,
                custo_kg_medio,
            )
            .join(PedidoItem, PedidoItem.id == PedidoItemComposicao.pedido_item_id)
            .join(Pedido, Pedido.id == PedidoItem.pedido_id)
            .outerjoin(Ingrediente, Ingrediente.id == PedidoItemComposicao.ingrediente_id)
            .where(Pedido.tenant_id == self._tenant_id)
            .where(Pedido.status.in_(status_list))
            .where(campo_data >= data_inicio)
            .where(campo_data <= data_fim)
            .group_by(
                PedidoItemComposicao.ingrediente_id,
                PedidoItemComposicao.ingrediente_nome_snap,
                Ingrediente.tipo,
                Ingrediente.unidade_medida,
                Ingrediente.saldo_atual,
            )
            .order_by(PedidoItemComposicao.ingrediente_nome_snap)
        )
        result = await self._session.execute(query)
        return result.all()

    async def listar_pedidos_periodo(
        self,
        data_inicio: date,
        data_fim: date,
        status_list: list[StatusPedido] | None = None,
        filtro_data: Literal["entrega", "criacao"] = "entrega",
    ) -> list:
        """Retorna pedidos do período com nome do cliente e contagem de itens."""
        if status_list is None:
            status_list = [StatusPedido.APROVADO, StatusPedido.EM_PRODUCAO]

        campo_data = Pedido.data_entrega_prevista if filtro_data == "entrega" else Pedido.created_at

        query = (
            select(
                Pedido.id,
                Pedido.numero,
                Cliente.nome.label("cliente_nome"),
                Pedido.data_entrega_prevista,
                func.count(PedidoItem.id).label("total_itens"),
            )
            .join(Cliente, Cliente.id == Pedido.cliente_id)
            .outerjoin(PedidoItem, PedidoItem.pedido_id == Pedido.id)
            .where(Pedido.tenant_id == self._tenant_id)
            .where(Pedido.status.in_(status_list))
            .where(campo_data >= data_inicio)
            .where(campo_data <= data_fim)
            .group_by(Pedido.id, Pedido.numero, Cliente.nome, Pedido.data_entrega_prevista)
            .order_by(Pedido.data_entrega_prevista.asc().nulls_last(), Pedido.numero)
        )
        result = await self._session.execute(query)
        return result.all()

    async def mapa_montagem(
        self,
        data_inicio: date,
        data_fim: date,
        status_list: list[StatusPedido] | None = None,
        filtro_data: Literal["entrega", "criacao"] = "entrega",
    ) -> list[Pedido]:
        """Retorna pedidos com cliente + itens + composição para o mapa de montagem."""
        if status_list is None:
            status_list = [StatusPedido.APROVADO, StatusPedido.EM_PRODUCAO]

        campo_data = Pedido.data_entrega_prevista if filtro_data == "entrega" else Pedido.created_at

        query = (
            self._base_query()
            .options(
                selectinload(Pedido.cliente),
                selectinload(Pedido.itens).selectinload(PedidoItem.composicao),
            )
            .where(Pedido.status.in_(status_list))
            .where(campo_data >= data_inicio)
            .where(campo_data <= data_fim)
            .order_by(Pedido.data_entrega_prevista.asc().nulls_last(), Pedido.numero)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_next_numero(self) -> str:
        """Gera o próximo número sequencial: PED-2026-0001."""
        from datetime import datetime
        ano = datetime.utcnow().year
        prefix = f"PED-{ano}-"
        result = await self._session.execute(
            select(func.count(Pedido.id))
            .where(Pedido.tenant_id == self._tenant_id)
            .where(Pedido.numero.like(f"{prefix}%"))
        )
        count = result.scalar_one() or 0
        return f"{prefix}{(count + 1):04d}"
