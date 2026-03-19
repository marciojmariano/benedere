"""
Service: Produto
Tasks: 2.1.4, 2.2.4
"""
import uuid
from datetime import datetime
from decimal import Decimal

from app.infra.database.models.base import TipoRefeicao
from app.infra.database.models.produto import Produto
from app.infra.database.models.produto_composicao import ProdutoComposicao
from app.infra.repository.produto_repository import ProdutoRepository
from app.infra.repository.produto_composicao_repository import ProdutoComposicaoRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository


# ── Exceções ──────────────────────────────────────────────────────────────────

class ProdutoNaoEncontradoError(Exception):
    def __init__(self, produto_id: uuid.UUID):
        super().__init__(f"Produto não encontrado: {produto_id}")


class ProdutoInativoError(Exception):
    def __init__(self):
        super().__init__("Produto está inativo e não pode ser modificado")


class IngredienteNaoEncontradoError(Exception):
    def __init__(self, ingrediente_id: uuid.UUID):
        super().__init__(f"Ingrediente não encontrado: {ingrediente_id}")


class ComposicaoVaziaError(Exception):
    def __init__(self):
        super().__init__("Composição deve ter pelo menos 1 ingrediente")


# ── Service ───────────────────────────────────────────────────────────────────

class ProdutoService:

    def __init__(
        self,
        produto_repo: ProdutoRepository,
        composicao_repo: ProdutoComposicaoRepository,
        ingrediente_repo: IngredienteRepository,
        tenant_id: uuid.UUID,
    ) -> None:
        self._produto_repo = produto_repo
        self._composicao_repo = composicao_repo
        self._ingrediente_repo = ingrediente_repo
        self._tenant_id = tenant_id

    # ── CRUD ─────────────────────────────────────────────────────────────────

    async def criar(
        self,
        nome: str,
        tipo_refeicao: TipoRefeicao | None = None,
        descricao: str | None = None,
        composicao: list[dict] | None = None,
    ) -> Produto:
        produto = Produto(
            tenant_id=self._tenant_id,
            nome=nome,
            tipo_refeicao=tipo_refeicao,
            descricao=descricao,
            ativo=True,
        )
        produto = await self._produto_repo.create(produto)

        # Se composição veio junto, salva e calcula peso
        if composicao:
            await self._salvar_composicao(produto.id, composicao)
            produto = await self._recalcular_peso(produto)

        return produto

    async def buscar_por_id(self, produto_id: uuid.UUID) -> Produto:
        produto = await self._produto_repo.get_by_id(produto_id)
        if not produto:
            raise ProdutoNaoEncontradoError(produto_id)
        return produto

    async def listar(self, apenas_ativos: bool = True) -> list[Produto]:
        return await self._produto_repo.list_all(apenas_ativos=apenas_ativos)

    async def atualizar(
        self,
        produto_id: uuid.UUID,
        nome: str | None = None,
        tipo_refeicao: TipoRefeicao | None = None,
        descricao: str | None = None,
    ) -> Produto:
        produto = await self.buscar_por_id(produto_id)

        if not produto.ativo:
            raise ProdutoInativoError()

        if nome is not None:
            produto.nome = nome
        if tipo_refeicao is not None:
            produto.tipo_refeicao = tipo_refeicao
        if descricao is not None:
            produto.descricao = descricao

        produto.updated_at = datetime.utcnow()
        return await self._produto_repo.update(produto)

    async def desativar(self, produto_id: uuid.UUID) -> None:
        produto = await self.buscar_por_id(produto_id)
        await self._produto_repo.delete(produto)

    async def reativar(self, produto_id: uuid.UUID) -> Produto:
        produto = await self._produto_repo.get_by_id(produto_id)
        if not produto:
            raise ProdutoNaoEncontradoError(produto_id)
        produto.ativo = True
        produto.updated_at = datetime.utcnow()
        return await self._produto_repo.update(produto)

    # ── Composição ───────────────────────────────────────────────────────────

    async def substituir_composicao(
        self,
        produto_id: uuid.UUID,
        composicao: list[dict],
    ) -> Produto:
        """Substituição total da receita (delete + insert)."""
        produto = await self.buscar_por_id(produto_id)

        if not produto.ativo:
            raise ProdutoInativoError()

        if not composicao:
            raise ComposicaoVaziaError()

        # Remove composição antiga e insere nova
        await self._composicao_repo.delete_by_produto(produto_id)
        await self._salvar_composicao(produto_id, composicao)
        produto = await self._recalcular_peso(produto)

        return produto

    async def listar_composicao(self, produto_id: uuid.UUID) -> list[dict]:
        """Lista composição com dados calculados (custo e kcal por item)."""
        await self.buscar_por_id(produto_id)  # valida existência
        itens = await self._composicao_repo.list_by_produto(produto_id)

        resultado = []
        for item in itens:
            ing = item.ingrediente
            custo_item = Decimal(str(item.quantidade_g)) / Decimal("1000") * Decimal(str(ing.custo_unitario))

            resultado.append({
                "id": item.id,
                "ingrediente_id": ing.id,
                "ingrediente_nome": ing.nome,
                "ingrediente_custo_unitario": Decimal(str(ing.custo_unitario)),
                "quantidade_g": Decimal(str(item.quantidade_g)),
                "ordem": item.ordem,
                "custo_item": round(custo_item, 4),
                "kcal_item": Decimal("0"),  # TODO: calcular via atributos JSONB quando disponível
            })

        return resultado

    # ── Helpers privados ─────────────────────────────────────────────────────

    async def _salvar_composicao(
        self,
        produto_id: uuid.UUID,
        composicao: list[dict],
    ) -> None:
        """Valida ingredientes e insere composição em batch."""
        itens_model = []
        for idx, item in enumerate(composicao):
            ingrediente_id = item["ingrediente_id"]
            ingrediente = await self._ingrediente_repo.get_by_id(ingrediente_id)
            if not ingrediente:
                raise IngredienteNaoEncontradoError(ingrediente_id)

            itens_model.append(
                ProdutoComposicao(
                    produto_id=produto_id,
                    ingrediente_id=ingrediente_id,
                    quantidade_g=item["quantidade_g"],
                    ordem=item.get("ordem", idx),
                )
            )

        await self._composicao_repo.create_batch(itens_model)

    async def _recalcular_peso(self, produto: Produto) -> Produto:
        """Recalcula peso_total_g pela soma da composição."""
        itens = await self._composicao_repo.list_by_produto(produto.id)
        peso_total = sum(Decimal(str(item.quantidade_g)) for item in itens)
        produto.peso_total_g = float(peso_total)
        produto.updated_at = datetime.utcnow()
        return await self._produto_repo.update(produto)
