"""
Repository: FaixaPesoEmbalagem
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infra.database.models.faixa_peso_embalagem import FaixaPesoEmbalagem


class FaixaPesoEmbalagemRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return select(FaixaPesoEmbalagem).where(
            FaixaPesoEmbalagem.tenant_id == self._tenant_id
        )

    async def create(self, faixa: FaixaPesoEmbalagem) -> FaixaPesoEmbalagem:
        self._session.add(faixa)
        await self._session.flush()
        await self._session.refresh(faixa)
        return faixa

    async def get_by_id(self, faixa_id: uuid.UUID) -> FaixaPesoEmbalagem | None:
        result = await self._session.execute(
            self._base_query()
            .where(FaixaPesoEmbalagem.id == faixa_id)
            .options(selectinload(FaixaPesoEmbalagem.ingrediente_embalagem))
        )
        return result.scalar_one_or_none()

    async def list_all(self, apenas_ativas: bool = True) -> list[FaixaPesoEmbalagem]:
        query = self._base_query().options(
            selectinload(FaixaPesoEmbalagem.ingrediente_embalagem)
        )
        if apenas_ativas:
            query = query.where(FaixaPesoEmbalagem.ativo == True)  # noqa: E712
        query = query.order_by(FaixaPesoEmbalagem.peso_min_g)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, faixa: FaixaPesoEmbalagem) -> FaixaPesoEmbalagem:
        await self._session.flush()
        await self._session.refresh(faixa)
        return faixa

    async def delete(self, faixa: FaixaPesoEmbalagem) -> None:
        faixa.ativo = False
        await self._session.flush()

    async def buscar_por_peso(self, peso_g: float) -> FaixaPesoEmbalagem | None:
        """Retorna a faixa ativa cujo intervalo contém o peso informado."""
        result = await self._session.execute(
            self._base_query()
            .where(FaixaPesoEmbalagem.ativo == True)  # noqa: E712
            .where(FaixaPesoEmbalagem.peso_min_g <= peso_g)
            .where(FaixaPesoEmbalagem.peso_max_g >= peso_g)
            .options(selectinload(FaixaPesoEmbalagem.ingrediente_embalagem))
            .limit(1)
        )
        return result.scalar_one_or_none()
