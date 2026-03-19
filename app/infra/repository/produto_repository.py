"""
Repository: Produto
Task: 2.1.3
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infra.database.models.produto import Produto


class ProdutoRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return select(Produto).where(Produto.tenant_id == self._tenant_id)

    async def create(self, produto: Produto) -> Produto:
        self._session.add(produto)
        await self._session.flush()
        await self._session.refresh(produto)
        return produto

    async def get_by_id(self, produto_id: uuid.UUID) -> Produto | None:
        result = await self._session.execute(
            self._base_query()
            .where(Produto.id == produto_id)
            .options(selectinload(Produto.composicao))
        )
        return result.scalar_one_or_none()

    async def list_all(self, apenas_ativos: bool = True) -> list[Produto]:
        query = self._base_query()
        if apenas_ativos:
            query = query.where(Produto.ativo == True)  # noqa: E712
        query = query.order_by(Produto.nome)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, produto: Produto) -> Produto:
        await self._session.flush()
        await self._session.refresh(produto)
        return produto

    async def delete(self, produto: Produto) -> None:
        produto.ativo = False
        await self._session.flush()
