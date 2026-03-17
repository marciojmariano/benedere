"""
Service: Cliente
Responsabilidade: regras de negócio e casos de uso.
"""
import uuid
from datetime import datetime

from app.infra.database.models.cliente import Cliente
from app.infra.repository.cliente_repository import ClienteRepository
from app.infra.repository.nutricionista_repository import NutricionistaRepository


# ── Exceções de domínio ───────────────────────────────────────────────────────

class ClienteNaoEncontradoError(Exception):
    def __init__(self, cliente_id: uuid.UUID):
        super().__init__(f"Cliente não encontrado: {cliente_id}")


class ClienteInativoError(Exception):
    def __init__(self):
        super().__init__("Cliente está inativo e não pode ser modificado")


class NutricionistaNaoEncontradoError(Exception):
    def __init__(self, nutricionista_id: uuid.UUID):
        super().__init__(f"Nutricionista não encontrado: {nutricionista_id}")


# ── Service ───────────────────────────────────────────────────────────────────

class ClienteService:

    def __init__(
        self,
        cliente_repo: ClienteRepository,
        nutricionista_repo: NutricionistaRepository,
        tenant_id: uuid.UUID,
    ) -> None:
        self._cliente_repo = cliente_repo
        self._nutricionista_repo = nutricionista_repo
        self._tenant_id = tenant_id

    async def criar(
        self,
        nome: str,
        email: str | None = None,
        telefone: str | None = None,
        endereco: str | None = None,
        observacoes: str | None = None,
        nutricionista_id: uuid.UUID | None = None,
        markup_id_padrao: uuid.UUID | None = None,
    ) -> Cliente:
        # Valida nutricionista se informado
        if nutricionista_id:
            nutricionista = await self._nutricionista_repo.get_by_id(nutricionista_id)
            if not nutricionista or not nutricionista.ativo:
                raise NutricionistaNaoEncontradoError(nutricionista_id)

        cliente = Cliente(
            tenant_id=self._tenant_id,
            nome=nome,
            email=email,
            telefone=telefone,
            endereco=endereco,
            observacoes=observacoes,
            nutricionista_id=nutricionista_id,
            markup_id_padrao=markup_id_padrao,
            ativo=True,
        )
        return await self._cliente_repo.create(cliente)

    async def buscar_por_id(self, cliente_id: uuid.UUID) -> Cliente:
        cliente = await self._cliente_repo.get_by_id(cliente_id)
        if not cliente:
            raise ClienteNaoEncontradoError(cliente_id)
        return cliente

    async def listar(self, apenas_ativos: bool = True) -> list[Cliente]:
        return await self._cliente_repo.list_all(apenas_ativos=apenas_ativos)

    async def atualizar(
        self,
        cliente_id: uuid.UUID,
        nome: str | None = None,
        email: str | None = None,
        telefone: str | None = None,
        endereco: str | None = None,
        observacoes: str | None = None,
        nutricionista_id: uuid.UUID | None = None,
        markup_id_padrao: uuid.UUID | None = None,
    ) -> Cliente:
        cliente = await self.buscar_por_id(cliente_id)

        if not cliente.ativo:
            raise ClienteInativoError()

        # Valida nutricionista se informado
        if nutricionista_id:
            nutricionista = await self._nutricionista_repo.get_by_id(nutricionista_id)
            if not nutricionista or not nutricionista.ativo:
                raise NutricionistaNaoEncontradoError(nutricionista_id)

        if nome is not None:
            cliente.nome = nome
        if email is not None:
            cliente.email = email
        if telefone is not None:
            cliente.telefone = telefone
        if endereco is not None:
            cliente.endereco = endereco
        if observacoes is not None:
            cliente.observacoes = observacoes
        if nutricionista_id is not None:
            cliente.nutricionista_id = nutricionista_id


        if markup_id_padrao is not None:
            cliente.markup_id_padrao = markup_id_padrao

        cliente.updated_at = datetime.utcnow()
        return await self._cliente_repo.update(cliente)

    async def desativar(self, cliente_id: uuid.UUID) -> None:
        cliente = await self.buscar_por_id(cliente_id)
        await self._cliente_repo.delete(cliente)

    async def reativar(self, cliente_id: uuid.UUID) -> Cliente:
        cliente = await self._cliente_repo.get_by_id(cliente_id)
        if not cliente:
            raise ClienteNaoEncontradoError(cliente_id)
        cliente.ativo = True
        cliente.updated_at = datetime.utcnow()
        return await self._cliente_repo.update(cliente)
