"""
Repository: Pedido e PedidoItem
"""
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infra.database.models.pedido import Pedido, PedidoItem


class PedidoRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return (
            select(Pedido)
            .where(Pedido.tenant_id == self._tenant_id)
            .options(selectinload(Pedido.itens))
        )

    async def create(self, pedido: Pedido) -> Pedido:
        self._session.add(pedido)
        await self._session.flush()
        result = await self._session.execute(
            self._base_query().where(Pedido.id == pedido.id)
        )
        return result.scalar_one()

    async def get_by_id(self, pedido_id: uuid.UUID) -> Pedido | None:
        result = await self._session.execute(
            self._base_query().where(Pedido.id == pedido_id)
        )
        return result.scalar_one_or_none()

    async def get_by_orcamento_id(self, orcamento_id: uuid.UUID) -> Pedido | None:
        result = await self._session.execute(
            self._base_query().where(Pedido.orcamento_id == orcamento_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        cliente_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[Pedido]:
        query = self._base_query().order_by(Pedido.created_at.desc())
        if cliente_id:
            query = query.where(Pedido.cliente_id == cliente_id)
        if status:
            query = query.where(Pedido.status == status)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, pedido: Pedido) -> Pedido:
        await self._session.flush()
        result = await self._session.execute(
            self._base_query().where(Pedido.id == pedido.id)
        )
        return result.scalar_one()

    async def proximo_numero(self) -> str:
        """Gera número sequencial no formato PED-YYYY-NNNN."""
        from datetime import datetime
        ano = datetime.utcnow().year
        result = await self._session.execute(
            select(func.count(Pedido.id)).where(
                Pedido.tenant_id == self._tenant_id,
                Pedido.numero.like(f"PED-{ano}-%"),
            )
        )
        count = result.scalar_one()
        return f"PED-{ano}-{str(count + 1).zfill(4)}"
