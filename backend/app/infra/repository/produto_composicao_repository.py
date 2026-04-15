"""
Repository: ProdutoComposicao
Task: 2.2.3
"""
import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.infra.database.models.produto_composicao import ProdutoComposicao


class ProdutoComposicaoRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_batch(self, itens: list[ProdutoComposicao]) -> list[ProdutoComposicao]:
        """Insere múltiplos itens de composição de uma vez."""
        self._session.add_all(itens)
        await self._session.flush()
        for item in itens:
            await self._session.refresh(item)
        return itens

    async def list_by_produto(self, produto_id: uuid.UUID) -> list[ProdutoComposicao]:
        """Lista composição com dados do ingrediente (join)."""
        result = await self._session.execute(
            select(ProdutoComposicao)
            .where(ProdutoComposicao.produto_id == produto_id)
            .options(joinedload(ProdutoComposicao.ingrediente))
            .order_by(ProdutoComposicao.ordem)
        )
        return list(result.scalars().all())

    async def delete_by_produto(self, produto_id: uuid.UUID) -> None:
        """Remove toda a composição de um produto (pra substituição total)."""
        await self._session.execute(
            delete(ProdutoComposicao)
            .where(ProdutoComposicao.produto_id == produto_id)
        )
        await self._session.flush()
