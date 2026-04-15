"""
Service: FaixaPesoEmbalagem
Gerencia as regras de seleção automática de embalagem por faixa de peso por tenant.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from app.infra.database.models.base import TipoIngrediente
from app.infra.database.models.faixa_peso_embalagem import FaixaPesoEmbalagem
from app.infra.repository.faixa_peso_embalagem_repository import FaixaPesoEmbalagemRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository


# ── Exceções ──────────────────────────────────────────────────────────────────

class FaixaNaoEncontradaError(Exception):
    def __init__(self, faixa_id: uuid.UUID):
        super().__init__(f"Faixa de peso não encontrada: {faixa_id}")


class FaixaSobrepostaError(Exception):
    def __init__(self, peso_min: float, peso_max: float):
        super().__init__(
            f"A faixa {peso_min}g–{peso_max}g se sobrepõe a uma faixa já cadastrada"
        )


class IngredienteNaoEmbalagemError(Exception):
    def __init__(self, ingrediente_id: uuid.UUID):
        super().__init__(
            f"Ingrediente {ingrediente_id} não é do tipo EMBALAGEM"
        )


class IngredienteNaoEncontradoError(Exception):
    def __init__(self, ingrediente_id: uuid.UUID):
        super().__init__(f"Ingrediente não encontrado: {ingrediente_id}")


# ── Service ───────────────────────────────────────────────────────────────────

class FaixaPesoEmbalagemService:

    def __init__(
        self,
        faixa_repo: FaixaPesoEmbalagemRepository,
        ingrediente_repo: IngredienteRepository,
        tenant_id: uuid.UUID,
    ) -> None:
        self._faixa_repo = faixa_repo
        self._ingrediente_repo = ingrediente_repo
        self._tenant_id = tenant_id

    async def criar(
        self,
        peso_min_g: Decimal,
        peso_max_g: Decimal,
        ingrediente_embalagem_id: uuid.UUID,
    ) -> FaixaPesoEmbalagem:
        await self._validar_ingrediente_embalagem(ingrediente_embalagem_id)
        await self._validar_sem_sobreposicao(float(peso_min_g), float(peso_max_g))

        faixa = FaixaPesoEmbalagem(
            tenant_id=self._tenant_id,
            peso_min_g=float(peso_min_g),
            peso_max_g=float(peso_max_g),
            ingrediente_embalagem_id=ingrediente_embalagem_id,
            ativo=True,
        )
        return await self._faixa_repo.create(faixa)

    async def buscar_por_id(self, faixa_id: uuid.UUID) -> FaixaPesoEmbalagem:
        faixa = await self._faixa_repo.get_by_id(faixa_id)
        if not faixa:
            raise FaixaNaoEncontradaError(faixa_id)
        return faixa

    async def listar(self, apenas_ativas: bool = True) -> list[FaixaPesoEmbalagem]:
        return await self._faixa_repo.list_all(apenas_ativas=apenas_ativas)

    async def atualizar(
        self,
        faixa_id: uuid.UUID,
        peso_min_g: Decimal | None = None,
        peso_max_g: Decimal | None = None,
        ingrediente_embalagem_id: uuid.UUID | None = None,
    ) -> FaixaPesoEmbalagem:
        faixa = await self.buscar_por_id(faixa_id)

        novo_min = float(peso_min_g) if peso_min_g is not None else float(faixa.peso_min_g)
        novo_max = float(peso_max_g) if peso_max_g is not None else float(faixa.peso_max_g)
        novo_ingrediente_id = ingrediente_embalagem_id or faixa.ingrediente_embalagem_id

        if ingrediente_embalagem_id is not None:
            await self._validar_ingrediente_embalagem(ingrediente_embalagem_id)

        await self._validar_sem_sobreposicao(novo_min, novo_max, excluir_id=faixa_id)

        faixa.peso_min_g = novo_min
        faixa.peso_max_g = novo_max
        faixa.ingrediente_embalagem_id = novo_ingrediente_id
        faixa.updated_at = datetime.utcnow()

        return await self._faixa_repo.update(faixa)

    async def desativar(self, faixa_id: uuid.UUID) -> None:
        faixa = await self.buscar_por_id(faixa_id)
        await self._faixa_repo.delete(faixa)

    async def resolver_embalagem(
        self, peso_g: float
    ) -> tuple[uuid.UUID, str, float] | None:
        """Retorna (ingrediente_id, nome, custo_unitario) para o peso dado, ou None."""
        faixa = await self._faixa_repo.buscar_por_peso(peso_g)
        if not faixa:
            return None
        ing = faixa.ingrediente_embalagem
        return (ing.id, ing.nome, float(ing.custo_unitario))

    # ── Validações privadas ──────────────────────────────────────────────────

    async def _validar_ingrediente_embalagem(self, ingrediente_id: uuid.UUID) -> None:
        ingrediente = await self._ingrediente_repo.get_by_id(ingrediente_id)
        if not ingrediente:
            raise IngredienteNaoEncontradoError(ingrediente_id)
        if ingrediente.tipo != TipoIngrediente.EMBALAGEM:
            raise IngredienteNaoEmbalagemError(ingrediente_id)

    async def _validar_sem_sobreposicao(
        self,
        peso_min: float,
        peso_max: float,
        excluir_id: uuid.UUID | None = None,
    ) -> None:
        faixas = await self._faixa_repo.list_all(apenas_ativas=True)
        for faixa in faixas:
            if excluir_id and faixa.id == excluir_id:
                continue
            fmin = float(faixa.peso_min_g)
            fmax = float(faixa.peso_max_g)
            # Sobreposição: [a, b] e [c, d] se sobrepõem quando a <= d e c <= b
            if peso_min <= fmax and fmin <= peso_max:
                raise FaixaSobrepostaError(peso_min, peso_max)
