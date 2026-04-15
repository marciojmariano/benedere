"""
Repository: Ingrediente
"""
import uuid

from sqlalchemy import func, select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database.models.ingrediente import Ingrediente
from app.infra.database.models.produto_composicao import ProdutoComposicao
from app.infra.database.models.faixa_peso_embalagem import FaixaPesoEmbalagem


class IngredienteRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return select(Ingrediente).where(Ingrediente.tenant_id == self._tenant_id)

    async def create(self, ingrediente: Ingrediente) -> Ingrediente:
        self._session.add(ingrediente)
        await self._session.flush()
        await self._session.refresh(ingrediente)
        return ingrediente

    async def get_by_id(self, ingrediente_id: uuid.UUID) -> Ingrediente | None:
        result = await self._session.execute(
            self._base_query().where(Ingrediente.id == ingrediente_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, apenas_ativos: bool = True) -> list[Ingrediente]:
        query = self._base_query()
        if apenas_ativos:
            query = query.where(Ingrediente.ativo == True)  # noqa: E712
        query = query.order_by(Ingrediente.nome)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_nome(self, nome: str) -> Ingrediente | None:
        result = await self._session.execute(
            self._base_query()
            .where(func.lower(Ingrediente.nome) == nome.lower().strip())
            .where(Ingrediente.ativo == True)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def update(self, ingrediente: Ingrediente) -> Ingrediente:
        await self._session.flush()
        await self._session.refresh(ingrediente)
        return ingrediente

    async def is_used(self, ingrediente_id: uuid.UUID) -> bool:
        """Retorna True se o ingrediente está em uso em composições de produto ou faixas de embalagem ativas."""
        em_composicao = await self._session.execute(
            select(exists().where(ProdutoComposicao.ingrediente_id == ingrediente_id))
        )
        if em_composicao.scalar():
            return True
        em_faixa = await self._session.execute(
            select(exists().where(
                FaixaPesoEmbalagem.ingrediente_embalagem_id == ingrediente_id,
                FaixaPesoEmbalagem.ativo == True,  # noqa: E712
            ))
        )
        return bool(em_faixa.scalar())

    async def delete(self, ingrediente: Ingrediente) -> None:
        ingrediente.ativo = False
        await self._session.flush()
