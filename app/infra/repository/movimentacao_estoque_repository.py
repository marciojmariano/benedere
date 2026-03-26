"""
Repository: MovimentacaoEstoque
Todo acesso filtrado por tenant_id.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infra.database.models.base import TipoMovimentacao
from app.infra.database.models.movimentacao_estoque import MovimentacaoEstoque


class MovimentacaoEstoqueRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_query(self):
        return select(MovimentacaoEstoque).where(
            MovimentacaoEstoque.tenant_id == self._tenant_id
        )

    async def create(self, mov: MovimentacaoEstoque) -> MovimentacaoEstoque:
        self._session.add(mov)
        await self._session.flush()
        await self._session.refresh(mov, ['ingrediente'])
        return mov

    async def get_by_id(self, mov_id: uuid.UUID) -> MovimentacaoEstoque | None:
        result = await self._session.execute(
            self._base_query()
            .where(MovimentacaoEstoque.id == mov_id)
            .options(selectinload(MovimentacaoEstoque.ingrediente))
        )
        return result.scalar_one_or_none()

    async def list_by_ingrediente(
        self,
        ingrediente_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MovimentacaoEstoque]:
        result = await self._session.execute(
            self._base_query()
            .where(MovimentacaoEstoque.ingrediente_id == ingrediente_id)
            .options(selectinload(MovimentacaoEstoque.ingrediente))
            .order_by(MovimentacaoEstoque.data_movimentacao.desc(), MovimentacaoEstoque.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[MovimentacaoEstoque]:
        result = await self._session.execute(
            self._base_query()
            .options(selectinload(MovimentacaoEstoque.ingrediente))
            .order_by(MovimentacaoEstoque.data_movimentacao.desc(), MovimentacaoEstoque.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    # ── Queries de agregação para cálculo de custo ────────────────────────────

    async def get_ultima_compra(self, ingrediente_id: uuid.UUID) -> Decimal | None:
        """Retorna o preço unitário da entrada de compra mais recente."""
        result = await self._session.execute(
            select(MovimentacaoEstoque.preco_unitario_custo)
            .where(
                MovimentacaoEstoque.tenant_id == self._tenant_id,
                MovimentacaoEstoque.ingrediente_id == ingrediente_id,
                MovimentacaoEstoque.tipo == TipoMovimentacao.COMPRA,
            )
            .order_by(
                MovimentacaoEstoque.data_movimentacao.desc(),
                MovimentacaoEstoque.created_at.desc(),
            )
            .limit(1)
        )
        valor = result.scalar_one_or_none()
        return Decimal(str(valor)) if valor is not None else None

    async def calcular_media_ponderada_total(self, ingrediente_id: uuid.UUID) -> Decimal | None:
        """Média ponderada por quantidade de todas as entradas de compra."""
        result = await self._session.execute(
            select(
                func.sum(
                    MovimentacaoEstoque.quantidade * MovimentacaoEstoque.preco_unitario_custo
                ) / func.sum(MovimentacaoEstoque.quantidade)
            )
            .where(
                MovimentacaoEstoque.tenant_id == self._tenant_id,
                MovimentacaoEstoque.ingrediente_id == ingrediente_id,
                MovimentacaoEstoque.tipo == TipoMovimentacao.COMPRA,
            )
        )
        valor = result.scalar_one_or_none()
        return Decimal(str(valor)).quantize(Decimal("0.0001")) if valor is not None else None

    async def calcular_media_ponderada_periodo(
        self, ingrediente_id: uuid.UUID, dias: int
    ) -> Decimal | None:
        """Média ponderada por quantidade das entradas de compra nos últimos N dias."""
        data_limite = date.today() - timedelta(days=dias)
        result = await self._session.execute(
            select(
                func.sum(
                    MovimentacaoEstoque.quantidade * MovimentacaoEstoque.preco_unitario_custo
                ) / func.sum(MovimentacaoEstoque.quantidade)
            )
            .where(
                MovimentacaoEstoque.tenant_id == self._tenant_id,
                MovimentacaoEstoque.ingrediente_id == ingrediente_id,
                MovimentacaoEstoque.tipo == TipoMovimentacao.COMPRA,
                MovimentacaoEstoque.data_movimentacao >= data_limite,
            )
        )
        valor = result.scalar_one_or_none()
        return Decimal(str(valor)).quantize(Decimal("0.0001")) if valor is not None else None
