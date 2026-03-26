"""
Serviço de cálculo de custo efetivo do ingrediente.

Implementa o Strategy Pattern para as quatro estratégias:
  MANUAL               → retorna custo_unitario (valor fixo)
  ULTIMA_COMPRA        → preço da entrada de compra mais recente
  MEDIA_PONDERADA_TOTAL  → média ponderada de todas as compras
  MEDIA_PONDERADA_PERIODO → média ponderada das compras nos últimos N dias

Fallback: se a estratégia requer histórico mas não há entradas, retorna custo_unitario.
"""
import uuid
from decimal import Decimal

from app.infra.database.models.base import EstrategiaCusto
from app.infra.database.models.ingrediente import Ingrediente
from app.infra.database.models.tenant import Tenant
from app.infra.repository.movimentacao_estoque_repository import MovimentacaoEstoqueRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository


class CustoIngredienteService:

    def __init__(
        self,
        mov_repo: MovimentacaoEstoqueRepository,
        ing_repo: IngredienteRepository,
        tenant: Tenant,
    ) -> None:
        self._mov_repo = mov_repo
        self._ing_repo = ing_repo
        self._tenant = tenant

    def _resolver_estrategia(self, ingrediente: Ingrediente) -> EstrategiaCusto:
        """Resolve a estratégia efetiva: ingrediente-level ou default do tenant."""
        return ingrediente.estrategia_custo or self._tenant.estrategia_custo_padrao

    def _resolver_periodo_dias(self, ingrediente: Ingrediente) -> int:
        """Resolve o período em dias: ingrediente-level ou default do tenant."""
        if ingrediente.periodo_dias_custo_medio is not None:
            return ingrediente.periodo_dias_custo_medio
        return self._tenant.periodo_dias_custo_medio_padrao or 30

    async def calcular_custo(self, ingrediente: Ingrediente) -> Decimal:
        """
        Calcula o custo efetivo conforme a estratégia, com fallback para custo_unitario.
        Não persiste nada — apenas retorna o valor calculado.
        """
        estrategia = self._resolver_estrategia(ingrediente)

        if estrategia == EstrategiaCusto.MANUAL:
            return self._calcular_manual(ingrediente)

        if estrategia == EstrategiaCusto.ULTIMA_COMPRA:
            resultado = await self._calcular_ultima_compra(ingrediente.id)
        elif estrategia == EstrategiaCusto.MEDIA_PONDERADA_TOTAL:
            resultado = await self._calcular_media_total(ingrediente.id)
        elif estrategia == EstrategiaCusto.MEDIA_PONDERADA_PERIODO:
            dias = self._resolver_periodo_dias(ingrediente)
            resultado = await self._calcular_media_periodo(ingrediente.id, dias)
        else:
            resultado = None

        return resultado if resultado is not None else self._calcular_manual(ingrediente)

    async def recalcular_e_persistir(self, ingrediente: Ingrediente) -> Ingrediente:
        """
        Calcula o custo e grava em ingrediente.custo_calculado.
        Deve ser chamado dentro de uma sessão aberta (sem commit próprio).
        """
        novo_custo = await self.calcular_custo(ingrediente)
        ingrediente.custo_calculado = float(novo_custo)
        return ingrediente

    def obter_custo_efetivo(self, ingrediente: Ingrediente) -> Decimal:
        """
        Retorna o custo efetivo cacheado (custo_calculado) ou custo_unitario como fallback.
        Uso: leitura rápida, sem queries adicionais.
        """
        if ingrediente.custo_calculado is not None:
            return Decimal(str(ingrediente.custo_calculado))
        return Decimal(str(ingrediente.custo_unitario))

    # ── Estratégias privadas ──────────────────────────────────────────────────

    def _calcular_manual(self, ingrediente: Ingrediente) -> Decimal:
        return Decimal(str(ingrediente.custo_unitario))

    async def _calcular_ultima_compra(self, ingrediente_id: uuid.UUID) -> Decimal | None:
        return await self._mov_repo.get_ultima_compra(ingrediente_id)

    async def _calcular_media_total(self, ingrediente_id: uuid.UUID) -> Decimal | None:
        return await self._mov_repo.calcular_media_ponderada_total(ingrediente_id)

    async def _calcular_media_periodo(
        self, ingrediente_id: uuid.UUID, dias: int
    ) -> Decimal | None:
        return await self._mov_repo.calcular_media_ponderada_periodo(ingrediente_id, dias)
