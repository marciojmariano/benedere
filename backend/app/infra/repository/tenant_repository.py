"""
Repository: Tenant
Responsabilidade: acesso ao banco de dados.
Isola o SQLAlchemy do restante da aplicação.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database.models.tenant import Tenant


class TenantRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, tenant: Tenant) -> Tenant:
        self._session.add(tenant)
        await self._session.flush()  # Gera o ID sem commitar
        await self._session.refresh(tenant)
        return tenant

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        result = await self._session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_all(self, apenas_ativos: bool = True) -> list[Tenant]:
        query = select(Tenant)
        if apenas_ativos:
            query = query.where(Tenant.ativo == True)  # noqa: E712
        query = query.order_by(Tenant.nome)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, tenant: Tenant) -> Tenant:
        await self._session.flush()
        await self._session.refresh(tenant)
        return tenant

    async def delete(self, tenant: Tenant) -> None:
        """Soft delete — apenas marca como inativo."""
        tenant.ativo = False
        await self._session.flush()

    async def exists_by_slug(self, slug: str) -> bool:
        result = await self._session.execute(
            select(Tenant.id).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none() is not None
