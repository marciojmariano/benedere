"""
Repository: Cliente
Todo acesso filtrado por tenant_id.
"""
import uuid

from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infra.database.models.cliente import Cliente
from app.infra.database.models.pedido import Pedido
from app.infra.database.models.base import StatusPedido


class ClienteRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return select(Cliente).where(Cliente.tenant_id == self._tenant_id)

    async def create(self, cliente: Cliente) -> Cliente:
        self._session.add(cliente)
        await self._session.flush()
        await self._session.refresh(cliente)
        return cliente

    async def get_by_id(self, cliente_id: uuid.UUID) -> Cliente | None:
        result = await self._session.execute(
            self._base_query()
            .where(Cliente.id == cliente_id)
            .options(selectinload(Cliente.nutricionista))
        )
        return result.scalar_one_or_none()

    async def list_all(self, apenas_ativos: bool = True) -> list[Cliente]:
        query = self._base_query().options(selectinload(Cliente.nutricionista))
        if apenas_ativos:
            query = query.where(Cliente.ativo == True)  # noqa: E712
        query = query.order_by(Cliente.nome)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, cliente: Cliente) -> Cliente:
        await self._session.flush()
        await self._session.refresh(cliente)
        return cliente

    async def has_active_pedidos(self, cliente_id: uuid.UUID) -> bool:
        """Retorna True se o cliente possui pedidos não-cancelados."""
        result = await self._session.execute(
            select(exists().where(
                Pedido.cliente_id == cliente_id,
                Pedido.status != StatusPedido.CANCELADO,
            ))
        )
        return bool(result.scalar())

    async def delete(self, cliente: Cliente) -> None:
        """Soft delete."""
        cliente.ativo = False
        await self._session.flush()
