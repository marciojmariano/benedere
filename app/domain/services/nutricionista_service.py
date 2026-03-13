"""
Service: Nutricionista
Responsabilidade: regras de negócio e casos de uso.
"""
import uuid
from datetime import datetime

from app.infra.database.models.nutricionista import Nutricionista
from app.infra.repository.nutricionista_repository import NutricionistaRepository


# ── Exceções de domínio ───────────────────────────────────────────────────────

class NutricionistaNaoEncontradoError(Exception):
    def __init__(self, nutricionista_id: uuid.UUID):
        super().__init__(f"Nutricionista não encontrado: {nutricionista_id}")


class NutricionistaCRNJaExisteError(Exception):
    def __init__(self, crn: str):
        super().__init__(f"Já existe um nutricionista com o CRN '{crn}'")


class NutricionistaInativoError(Exception):
    def __init__(self):
        super().__init__("Nutricionista está inativo e não pode ser modificado")


# ── Service ───────────────────────────────────────────────────────────────────

class NutricionistaService:

    def __init__(self, repository: NutricionistaRepository, tenant_id: uuid.UUID) -> None:
        self._repo = repository
        self._tenant_id = tenant_id

    async def criar(
        self,
        nome: str,
        crn: str | None = None,
        email: str | None = None,
        telefone: str | None = None,
    ) -> Nutricionista:
        """Cadastra novo nutricionista. CRN deve ser único por tenant."""
        if crn and await self._repo.exists_by_crn(crn):
            raise NutricionistaCRNJaExisteError(crn)

        nutricionista = Nutricionista(
            tenant_id=self._tenant_id,
            nome=nome,
            crn=crn,
            email=email,
            telefone=telefone,
            ativo=True,
        )
        return await self._repo.create(nutricionista)

    async def buscar_por_id(self, nutricionista_id: uuid.UUID) -> Nutricionista:
        nutricionista = await self._repo.get_by_id(nutricionista_id)
        if not nutricionista:
            raise NutricionistaNaoEncontradoError(nutricionista_id)
        return nutricionista

    async def listar(self, apenas_ativos: bool = True) -> list[Nutricionista]:
        return await self._repo.list_all(apenas_ativos=apenas_ativos)

    async def atualizar(
        self,
        nutricionista_id: uuid.UUID,
        nome: str | None = None,
        crn: str | None = None,
        email: str | None = None,
        telefone: str | None = None,
    ) -> Nutricionista:
        nutricionista = await self.buscar_por_id(nutricionista_id)

        if not nutricionista.ativo:
            raise NutricionistaInativoError()

        if crn and crn != nutricionista.crn:
            if await self._repo.exists_by_crn(crn):
                raise NutricionistaCRNJaExisteError(crn)
            nutricionista.crn = crn

        if nome is not None:
            nutricionista.nome = nome
        if email is not None:
            nutricionista.email = email
        if telefone is not None:
            nutricionista.telefone = telefone

        nutricionista.updated_at = datetime.utcnow()
        return await self._repo.update(nutricionista)

    async def desativar(self, nutricionista_id: uuid.UUID) -> None:
        nutricionista = await self.buscar_por_id(nutricionista_id)
        await self._repo.delete(nutricionista)

    async def reativar(self, nutricionista_id: uuid.UUID) -> Nutricionista:
        nutricionista = await self._repo.get_by_id(nutricionista_id)
        if not nutricionista:
            raise NutricionistaNaoEncontradoError(nutricionista_id)
        nutricionista.ativo = True
        nutricionista.updated_at = datetime.utcnow()
        return await self._repo.update(nutricionista)
