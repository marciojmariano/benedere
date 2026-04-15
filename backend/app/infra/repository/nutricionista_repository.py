"""
Repository: Nutricionista
Responsabilidade: acesso ao banco de dados.
Todo acesso é filtrado por tenant_id — isolamento multi-tenant.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database.models.nutricionista import Nutricionista


class NutricionistaRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        """Toda query parte daqui — garante isolamento por tenant."""
        return select(Nutricionista).where(
            Nutricionista.tenant_id == self._tenant_id
        )

    async def create(self, nutricionista: Nutricionista) -> Nutricionista:
        self._session.add(nutricionista)
        await self._session.flush()
        await self._session.refresh(nutricionista)
        return nutricionista

    async def get_by_id(self, nutricionista_id: uuid.UUID) -> Nutricionista | None:
        result = await self._session.execute(
            self._base_query().where(Nutricionista.id == nutricionista_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, apenas_ativos: bool = True) -> list[Nutricionista]:
        query = self._base_query()
        if apenas_ativos:
            query = query.where(Nutricionista.ativo == True)  # noqa: E712
        query = query.order_by(Nutricionista.nome)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, nutricionista: Nutricionista) -> Nutricionista:
        await self._session.flush()
        await self._session.refresh(nutricionista)
        return nutricionista

    async def delete(self, nutricionista: Nutricionista) -> None:
        """Soft delete."""
        nutricionista.ativo = False
        await self._session.flush()

    async def exists_by_crn(self, crn: str) -> bool:
        result = await self._session.execute(
            self._base_query().where(Nutricionista.crn == crn)
        )
        return result.scalar_one_or_none() is not None
