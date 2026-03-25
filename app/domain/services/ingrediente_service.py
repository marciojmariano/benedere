"""
Service: Ingrediente
"""
import uuid
from datetime import datetime
from decimal import Decimal

from app.infra.database.models.base import TipoIngrediente, UnidadeMedida
from app.infra.database.models.ingrediente import Ingrediente
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.markup_repository import MarkupRepository


# ── Exceções ──────────────────────────────────────────────────────────────────

class IngredienteNaoEncontradoError(Exception):
    def __init__(self, ingrediente_id: uuid.UUID):
        super().__init__(f"Ingrediente não encontrado: {ingrediente_id}")


class IngredienteInativoError(Exception):
    def __init__(self):
        super().__init__("Ingrediente está inativo e não pode ser modificado")


class MarkupNaoEncontradoError(Exception):
    def __init__(self, markup_id: uuid.UUID):
        super().__init__(f"Markup não encontrado: {markup_id}")


# ── Service ───────────────────────────────────────────────────────────────────

class IngredienteService:

    def __init__(
        self,
        ingrediente_repo: IngredienteRepository,
        markup_repo: MarkupRepository,
        tenant_id: uuid.UUID,
    ) -> None:
        self._ingrediente_repo = ingrediente_repo
        self._markup_repo = markup_repo
        self._tenant_id = tenant_id

    async def criar(
        self,
        nome: str,
        unidade_medida: UnidadeMedida,
        custo_unitario: Decimal,
        tipo: TipoIngrediente = TipoIngrediente.INSUMO,
        descricao: str | None = None,
        markup_id: uuid.UUID | None = None,
    ) -> Ingrediente:
        # Valida markup se informado
        if markup_id:
            markup = await self._markup_repo.get_by_id(markup_id)
            if not markup or not markup.ativo:
                raise MarkupNaoEncontradoError(markup_id)

        ingrediente = Ingrediente(
            tenant_id=self._tenant_id,
            nome=nome,
            tipo=tipo,
            unidade_medida=unidade_medida,
            custo_unitario=custo_unitario,
            descricao=descricao,
            markup_id=markup_id,
            ativo=True,
        )
        return await self._ingrediente_repo.create(ingrediente)

    async def buscar_por_id(self, ingrediente_id: uuid.UUID) -> Ingrediente:
        ingrediente = await self._ingrediente_repo.get_by_id(ingrediente_id)
        if not ingrediente:
            raise IngredienteNaoEncontradoError(ingrediente_id)
        return ingrediente

    async def listar(self, apenas_ativos: bool = True) -> list[Ingrediente]:
        return await self._ingrediente_repo.list_all(apenas_ativos=apenas_ativos)

    async def atualizar(
        self,
        ingrediente_id: uuid.UUID,
        nome: str | None = None,
        tipo: TipoIngrediente | None = None,
        unidade_medida: UnidadeMedida | None = None,
        custo_unitario: Decimal | None = None,
        descricao: str | None = None,
        markup_id: uuid.UUID | None = None,
    ) -> Ingrediente:
        ingrediente = await self.buscar_por_id(ingrediente_id)

        if not ingrediente.ativo:
            raise IngredienteInativoError()

        # Valida markup se informado
        if markup_id:
            markup = await self._markup_repo.get_by_id(markup_id)
            if not markup or not markup.ativo:
                raise MarkupNaoEncontradoError(markup_id)

        if nome is not None:
            ingrediente.nome = nome
        if tipo is not None:
            ingrediente.tipo = tipo
        if unidade_medida is not None:
            ingrediente.unidade_medida = unidade_medida
        if custo_unitario is not None:
            ingrediente.custo_unitario = custo_unitario
        if descricao is not None:
            ingrediente.descricao = descricao
        if markup_id is not None:
            ingrediente.markup_id = markup_id

        ingrediente.updated_at = datetime.utcnow()
        return await self._ingrediente_repo.update(ingrediente)

    async def desativar(self, ingrediente_id: uuid.UUID) -> None:
        ingrediente = await self.buscar_por_id(ingrediente_id)
        await self._ingrediente_repo.delete(ingrediente)

    async def reativar(self, ingrediente_id: uuid.UUID) -> Ingrediente:
        ingrediente = await self._ingrediente_repo.get_by_id(ingrediente_id)
        if not ingrediente:
            raise IngredienteNaoEncontradoError(ingrediente_id)
        ingrediente.ativo = True
        ingrediente.updated_at = datetime.utcnow()
        return await self._ingrediente_repo.update(ingrediente)
