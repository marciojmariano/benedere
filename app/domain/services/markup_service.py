"""
Service: IndiceMarkup e Markup
"""
import uuid
from decimal import Decimal
from datetime import datetime

from app.infra.database.models.markup import IndiceMarkup, Markup
from app.infra.repository.markup_repository import IndiceMarkupRepository, MarkupRepository


# ── Exceções ──────────────────────────────────────────────────────────────────

class IndiceMarkupNaoEncontradoError(Exception):
    def __init__(self, indice_id: uuid.UUID):
        super().__init__(f"Índice de markup não encontrado: {indice_id}")


class MarkupNaoEncontradoError(Exception):
    def __init__(self, markup_id: uuid.UUID):
        super().__init__(f"Markup não encontrado: {markup_id}")


class MarkupSomaPecentualInvalidaError(Exception):
    def __init__(self, soma: Decimal):
        super().__init__(
            f"A soma dos percentuais ({soma}%) deve ser menor que 100%"
        )


class IndiceEmUsoError(Exception):
    def __init__(self):
        super().__init__("Índice está em uso por um ou mais markups e não pode ser desativado")


# ── Helpers ───────────────────────────────────────────────────────────────────

def calcular_fator_markup(percentuais: list[Decimal]) -> Decimal:
    """
    Fórmula: Markup = 100 / (100 - soma_percentuais)
    Ex: impostos 15% + despesas 10% + lucro 20% = 45%
    Fator = 100 / (100 - 45) = 1.8182
    """
    soma = sum(percentuais)
    return round(Decimal(100) / (Decimal(100) - soma), 4)


# ── IndiceMarkup Service ──────────────────────────────────────────────────────

class IndiceMarkupService:

    def __init__(self, repo: IndiceMarkupRepository, tenant_id: uuid.UUID) -> None:
        self._repo = repo
        self._tenant_id = tenant_id

    async def criar(
        self,
        nome: str,
        percentual: Decimal,
        descricao: str | None = None,
    ) -> IndiceMarkup:
        indice = IndiceMarkup(
            tenant_id=self._tenant_id,
            nome=nome,
            percentual=percentual,
            descricao=descricao,
            ativo=True,
        )
        return await self._repo.create(indice)

    async def buscar_por_id(self, indice_id: uuid.UUID) -> IndiceMarkup:
        indice = await self._repo.get_by_id(indice_id)
        if not indice:
            raise IndiceMarkupNaoEncontradoError(indice_id)
        return indice

    async def listar(self, apenas_ativos: bool = True) -> list[IndiceMarkup]:
        return await self._repo.list_all(apenas_ativos=apenas_ativos)

    async def atualizar(
        self,
        indice_id: uuid.UUID,
        nome: str | None = None,
        percentual: Decimal | None = None,
        descricao: str | None = None,
    ) -> IndiceMarkup:
        indice = await self.buscar_por_id(indice_id)

        if nome is not None:
            indice.nome = nome
        if percentual is not None:
            indice.percentual = percentual
        if descricao is not None:
            indice.descricao = descricao

        indice.updated_at = datetime.utcnow()
        return await self._repo.update(indice)

    async def desativar(self, indice_id: uuid.UUID) -> None:
        indice = await self.buscar_por_id(indice_id)
        await self._repo.delete(indice)


# ── Markup Service ────────────────────────────────────────────────────────────

class MarkupService:

    def __init__(
        self,
        markup_repo: MarkupRepository,
        indice_repo: IndiceMarkupRepository,
        tenant_id: uuid.UUID,
    ) -> None:
        self._markup_repo = markup_repo
        self._indice_repo = indice_repo
        self._tenant_id = tenant_id

    async def _validar_e_buscar_indices(
        self, indices_ids: list[uuid.UUID]
    ) -> list[IndiceMarkup]:
        indices = await self._indice_repo.get_many_by_ids(indices_ids)

        # Verifica se todos foram encontrados
        encontrados_ids = {i.id for i in indices}
        for indice_id in indices_ids:
            if indice_id not in encontrados_ids:
                raise IndiceMarkupNaoEncontradoError(indice_id)

        # Verifica se todos estão ativos
        for indice in indices:
            if not indice.ativo:
                raise IndiceMarkupNaoEncontradoError(indice.id)

        # Valida soma dos percentuais
        soma = sum(i.percentual for i in indices)
        if soma >= 100:
            raise MarkupSomaPecentualInvalidaError(soma)

        return indices

    async def criar(
        self,
        nome: str,
        indices_ids: list[uuid.UUID],
        descricao: str | None = None,
    ) -> Markup:
        indices = await self._validar_e_buscar_indices(indices_ids)
        fator = calcular_fator_markup([i.percentual for i in indices])

        markup = Markup(
            tenant_id=self._tenant_id,
            nome=nome,
            descricao=descricao,
            fator=fator,
            ativo=True,
        )
        return await self._markup_repo.create(markup, indices)

    async def buscar_por_id(self, markup_id: uuid.UUID) -> Markup:
        markup = await self._markup_repo.get_by_id(markup_id)
        if not markup:
            raise MarkupNaoEncontradoError(markup_id)
        return markup

    async def listar(self, apenas_ativos: bool = True) -> list[Markup]:
        return await self._markup_repo.list_all(apenas_ativos=apenas_ativos)

    async def atualizar(
        self,
        markup_id: uuid.UUID,
        nome: str | None = None,
        descricao: str | None = None,
        indices_ids: list[uuid.UUID] | None = None,
    ) -> Markup:
        markup = await self.buscar_por_id(markup_id)

        if nome is not None:
            markup.nome = nome
        if descricao is not None:
            markup.descricao = descricao

        if indices_ids is not None:
            indices = await self._validar_e_buscar_indices(indices_ids)
            fator = calcular_fator_markup([i.percentual for i in indices])
            markup.fator = fator
            await self._markup_repo.replace_indices(markup, indices)

        markup.updated_at = datetime.utcnow()
        return await self._markup_repo.update(markup)

    async def desativar(self, markup_id: uuid.UUID) -> None:
        markup = await self.buscar_por_id(markup_id)
        await self._markup_repo.delete(markup)
