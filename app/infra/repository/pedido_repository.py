"""
Repository: Pedido
Task: 3.1.3
"""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infra.database.models.base import StatusPedido
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
        query = self._base_query().options(selectinload(Pedido.itens))
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
