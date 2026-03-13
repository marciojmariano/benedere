"""
Repository: Orcamento e OrcamentoItem
"""
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infra.database.models.orcamento import Orcamento, OrcamentoItem


class OrcamentoRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return (
            select(Orcamento)
            .where(Orcamento.tenant_id == self._tenant_id)
            .options(selectinload(Orcamento.itens))
        )

    async def create(self, orcamento: Orcamento) -> Orcamento:
        self._session.add(orcamento)
        await self._session.flush()
        await self._session.refresh(orcamento)
        # Recarrega com itens
        result = await self._session.execute(
            self._base_query().where(Orcamento.id == orcamento.id)
        )
        return result.scalar_one()

    async def get_by_id(self, orcamento_id: uuid.UUID) -> Orcamento | None:
        result = await self._session.execute(
            self._base_query().where(Orcamento.id == orcamento_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        cliente_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[Orcamento]:
        query = self._base_query().order_by(Orcamento.created_at.desc())
        if cliente_id:
            query = query.where(Orcamento.cliente_id == cliente_id)
        if status:
            query = query.where(Orcamento.status == status)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, orcamento: Orcamento) -> Orcamento:
        await self._session.flush()
        result = await self._session.execute(
            self._base_query().where(Orcamento.id == orcamento.id)
        )
        return result.scalar_one()

    async def proximo_numero(self) -> str:
        """Gera número sequencial no formato ORC-YYYY-NNNN."""
        from datetime import datetime
        ano = datetime.utcnow().year
        result = await self._session.execute(
            select(func.count(Orcamento.id)).where(
                Orcamento.tenant_id == self._tenant_id,
                Orcamento.numero.like(f"ORC-{ano}-%"),
            )
        )
        count = result.scalar_one()
        return f"ORC-{ano}-{str(count + 1).zfill(4)}"
