"""
Repository: IndiceMarkup e Markup
"""
import uuid

from sqlalchemy import select, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.infra.database.models.markup import IndiceMarkup, Markup, MarkupIndice


class IndiceMarkupRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return select(IndiceMarkup).where(IndiceMarkup.tenant_id == self._tenant_id)

    async def create(self, indice: IndiceMarkup) -> IndiceMarkup:
        self._session.add(indice)
        await self._session.flush()
        await self._session.refresh(indice)
        return indice

    async def get_by_id(self, indice_id: uuid.UUID) -> IndiceMarkup | None:
        result = await self._session.execute(
            self._base_query().where(IndiceMarkup.id == indice_id)
        )
        return result.scalar_one_or_none()

    async def get_many_by_ids(self, ids: list[uuid.UUID]) -> list[IndiceMarkup]:
        result = await self._session.execute(
            self._base_query().where(IndiceMarkup.id.in_(ids))
        )
        return list(result.scalars().all())

    async def list_all(self, apenas_ativos: bool = True) -> list[IndiceMarkup]:
        query = self._base_query()
        if apenas_ativos:
            query = query.where(IndiceMarkup.ativo == True)  # noqa: E712
        query = query.order_by(IndiceMarkup.nome)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, indice: IndiceMarkup) -> IndiceMarkup:
        await self._session.flush()
        await self._session.refresh(indice)
        return indice

    async def is_used_by_active_markups(self, indice_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(exists().where(
                MarkupIndice.indice_id == indice_id,
                MarkupIndice.markup_id == Markup.id,
                Markup.ativo == True,  # noqa: E712
            ))
        )
        return bool(result.scalar())

    async def delete(self, indice: IndiceMarkup) -> None:
        indice.ativo = False
        await self._session.flush()


class MarkupRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return select(Markup).where(Markup.tenant_id == self._tenant_id)

    async def create(self, markup: Markup, indices: list[IndiceMarkup]) -> Markup:
        self._session.add(markup)
        await self._session.flush()

        for indice in indices:
            associacao = MarkupIndice(
                tenant_id=self._tenant_id,
                markup_id=markup.id,
             indice_id=indice.id,
            )
            self._session.add(associacao)

        await self._session.flush()

        # Busca novamente com relacionamentos carregados
        result = await self._session.execute(
            select(Markup)
            .where(Markup.id == markup.id)
            .options(selectinload(Markup.indices).selectinload(MarkupIndice.indice))
        )
        return result.scalar_one()

    async def get_by_id(self, markup_id: uuid.UUID) -> Markup | None:
        result = await self._session.execute(
            self._base_query()
            .where(Markup.id == markup_id)
            .options(selectinload(Markup.indices).selectinload(MarkupIndice.indice))
        )
        return result.scalar_one_or_none()

    async def list_all(self, apenas_ativos: bool = True) -> list[Markup]:
        query = (
            self._base_query()
            .options(selectinload(Markup.indices).selectinload(MarkupIndice.indice))
        )
        if apenas_ativos:
            query = query.where(Markup.ativo == True)  # noqa: E712
        query = query.order_by(Markup.nome)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, markup: Markup) -> Markup:
        await self._session.flush()
        await self._session.refresh(markup)
        return markup

    async def replace_indices(self, markup: Markup, indices: list[IndiceMarkup]) -> None:
        """Remove todos os índices atuais e adiciona os novos."""
        await self._session.execute(
            delete(MarkupIndice).where(MarkupIndice.markup_id == markup.id)
        )
        for indice in indices:
            associacao = MarkupIndice(
                tenant_id=self._tenant_id,
                markup_id=markup.id,
                indice_id=indice.id,
            )
            self._session.add(associacao)
        await self._session.flush()

    async def delete(self, markup: Markup) -> None:
        markup.ativo = False
        await self._session.flush()
