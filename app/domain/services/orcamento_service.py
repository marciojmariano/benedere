"""
Service: Orcamento
Regras de negócio:
- Calcula custos automaticamente (snapshot de preços)
- Aplica markup por ingrediente e markup total
- Controla transição de status
"""
import uuid
from datetime import datetime
from decimal import Decimal

from app.infra.database.models.base import StatusOrcamento
from app.infra.database.models.orcamento import Orcamento, OrcamentoItem
from app.infra.repository.cliente_repository import ClienteRepository
from app.infra.repository.ingrediente_repository import IngredienteRepository
from app.infra.repository.markup_repository import MarkupRepository
from app.infra.repository.orcamento_repository import OrcamentoRepository
from app.infra.repository.tenant_repository import TenantRepository


# ── Exceções ──────────────────────────────────────────────────────────────────

class OrcamentoNaoEncontradoError(Exception):
    def __init__(self, orcamento_id: uuid.UUID):
        super().__init__(f"Orçamento não encontrado: {orcamento_id}")


class OrcamentoNaoEditavelError(Exception):
    def __init__(self, status: str):
        super().__init__(f"Orçamento com status '{status}' não pode ser editado")


class ClienteNaoEncontradoError(Exception):
    def __init__(self, cliente_id: uuid.UUID):
        super().__init__(f"Cliente não encontrado: {cliente_id}")


class IngredienteNaoEncontradoError(Exception):
    def __init__(self, ingrediente_id: uuid.UUID):
        super().__init__(f"Ingrediente não encontrado: {ingrediente_id}")


class TransicaoStatusInvalidaError(Exception):
    def __init__(self, atual: str, novo: str):
        super().__init__(f"Não é possível mudar status de '{atual}' para '{novo}'")


# ── Transições de status permitidas ──────────────────────────────────────────

TRANSICOES_VALIDAS = {
    StatusOrcamento.RASCUNHO: [StatusOrcamento.ENVIADO, StatusOrcamento.CANCELADO],
    StatusOrcamento.ENVIADO: [StatusOrcamento.APROVADO, StatusOrcamento.REPROVADO, StatusOrcamento.CANCELADO],
    StatusOrcamento.APROVADO: [],
    StatusOrcamento.REPROVADO: [StatusOrcamento.RASCUNHO],
    StatusOrcamento.CANCELADO: [],
}


# ── Service ───────────────────────────────────────────────────────────────────

class OrcamentoService:

    def __init__(
        self,
        orcamento_repo: OrcamentoRepository,
        cliente_repo: ClienteRepository,
        ingrediente_repo: IngredienteRepository,
        markup_repo: MarkupRepository,
        tenant_repo: TenantRepository,
        tenant_id: uuid.UUID,
    ) -> None:
        self._orcamento_repo = orcamento_repo
        self._cliente_repo = cliente_repo
        self._ingrediente_repo = ingrediente_repo
        self._markup_repo = markup_repo
        self._tenant_repo = tenant_repo
        self._tenant_id = tenant_id

    async def criar(
        self,
        cliente_id: uuid.UUID,
        itens_data: list[dict],
        markup_id: uuid.UUID | None = None,
        custo_embalagem: Decimal = Decimal("0"),
        taxa_entrega: Decimal = Decimal("0"),
        validade_dias: int = 7,
        observacoes: str | None = None,
    ) -> Orcamento:
        # Valida cliente
        cliente = await self._cliente_repo.get_by_id(cliente_id)
        if not cliente or not cliente.ativo:
            raise ClienteNaoEncontradoError(cliente_id)

        # Resolve markup: prioridade → informado > cliente > tenant
        if not markup_id:
            if cliente.markup_id_padrao:
                markup_id = cliente.markup_id_padrao
            else:
                # Busca markup padrão do tenant
                tenant = await self._tenant_repo.get_by_id(self._tenant_id)
                if tenant and tenant.markup_id_padrao:
                    markup_id = tenant.markup_id_padrao

        # Valida markup total se informado
        markup_fator_total = Decimal("1")  # ← deve vir DEPOIS da resolução do markup_id
        if markup_id:
            markup = await self._markup_repo.get_by_id(markup_id)
            if not markup or not markup.ativo:
                raise Exception(f"Markup não encontrado: {markup_id}")
            markup_fator_total = markup.fator

        # Gera número do orçamento
        numero = await self._orcamento_repo.proximo_numero()

        # Cria o orçamento
        orcamento = Orcamento(
            tenant_id=self._tenant_id,
            numero=numero,
            cliente_id=cliente_id,
            markup_id=markup_id,
            custo_embalagem=custo_embalagem,
            taxa_entrega=taxa_entrega,
            validade_dias=validade_dias,
            observacoes=observacoes,
            status=StatusOrcamento.RASCUNHO,
            custo_ingredientes=Decimal("0"),
            custo_total=Decimal("0"),
            preco_final=Decimal("0"),
        )
        self._orcamento_repo._session.add(orcamento)
        await self._orcamento_repo._session.flush()

        # Processa itens
        custo_ingredientes = Decimal("0")

        for item_data in itens_data:
            ingrediente = await self._ingrediente_repo.get_by_id(item_data["ingrediente_id"])
            if not ingrediente or not ingrediente.ativo:
                raise IngredienteNaoEncontradoError(item_data["ingrediente_id"])

            # Snapshot de preço no momento do orçamento
            custo_unitario = Decimal(str(ingrediente.custo_unitario))
            quantidade = item_data["quantidade"]
            custo_total_item = round(custo_unitario * quantidade, 2)

            # Markup por ingrediente (se tiver)
            markup_fator_ingrediente = None
            if ingrediente.markup_id:
                markup_ing = await self._markup_repo.get_by_id(ingrediente.markup_id)
                if markup_ing and markup_ing.ativo:
                    markup_fator_ingrediente = Decimal(str(markup_ing.fator))

            fator_aplicado = markup_fator_ingrediente or Decimal("1")
            preco_item_com_markup = round(custo_total_item * fator_aplicado, 2)

            item = OrcamentoItem(
                tenant_id=self._tenant_id,
                orcamento_id=orcamento.id,
                ingrediente_id=ingrediente.id,
                quantidade=quantidade,
                unidade_medida=item_data["unidade_medida"],
                custo_unitario_snapshot=custo_unitario,
                markup_fator_snapshot=markup_fator_ingrediente,
                custo_total_item=custo_total_item,
                preco_item_com_markup=preco_item_com_markup,
                observacoes=item_data.get("observacoes"),
            )
            self._orcamento_repo._session.add(item)
            custo_ingredientes += preco_item_com_markup

        # Calcula totais
        custo_total = round(custo_ingredientes + custo_embalagem + taxa_entrega, 2)
        preco_final = round(custo_total * markup_fator_total, 2)

        orcamento.custo_ingredientes = custo_ingredientes
        orcamento.custo_total = custo_total
        orcamento.preco_final = preco_final

        return await self._orcamento_repo.create(orcamento)

    async def buscar_por_id(self, orcamento_id: uuid.UUID) -> Orcamento:
        orcamento = await self._orcamento_repo.get_by_id(orcamento_id)
        if not orcamento:
            raise OrcamentoNaoEncontradoError(orcamento_id)
        return orcamento

    async def listar(
        self,
        cliente_id: uuid.UUID | None = None,
        status: StatusOrcamento | None = None,
    ) -> list[Orcamento]:
        return await self._orcamento_repo.list_all(
            cliente_id=cliente_id,
            status=status,
        )

    async def atualizar(
        self,
        orcamento_id: uuid.UUID,
        markup_id: uuid.UUID | None = None,
        custo_embalagem: Decimal | None = None,
        taxa_entrega: Decimal | None = None,
        validade_dias: int | None = None,
        observacoes: str | None = None,
    ) -> Orcamento:
        orcamento = await self.buscar_por_id(orcamento_id)

        if orcamento.status != StatusOrcamento.RASCUNHO:
            raise OrcamentoNaoEditavelError(orcamento.status)

        if markup_id is not None:
            orcamento.markup_id = markup_id
        if custo_embalagem is not None:
            orcamento.custo_embalagem = custo_embalagem
        if taxa_entrega is not None:
            orcamento.taxa_entrega = taxa_entrega
        if validade_dias is not None:
            orcamento.validade_dias = validade_dias
        if observacoes is not None:
            orcamento.observacoes = observacoes

        orcamento.updated_at = datetime.utcnow()
        return await self._orcamento_repo.update(orcamento)

    async def mudar_status(
        self, orcamento_id: uuid.UUID, novo_status: StatusOrcamento
    ) -> Orcamento:
        orcamento = await self.buscar_por_id(orcamento_id)

        transicoes = TRANSICOES_VALIDAS.get(orcamento.status, [])
        if novo_status not in transicoes:
            raise TransicaoStatusInvalidaError(orcamento.status, novo_status)

        orcamento.status = novo_status
        orcamento.updated_at = datetime.utcnow()
        return await self._orcamento_repo.update(orcamento)
