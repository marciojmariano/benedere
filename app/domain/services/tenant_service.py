"""
Service: Tenant
Responsabilidade: regras de negócio e casos de uso.
Não conhece HTTP, não conhece SQLAlchemy — apenas orquestra.
"""
import uuid
from datetime import datetime

from app.infra.database.models.base import TenantPlano, TenantStatus
from app.infra.database.models.tenant import Tenant
from app.infra.repository.tenant_repository import TenantRepository


# ── Exceções de domínio ───────────────────────────────────────────────────────

class TenantNaoEncontradoError(Exception):
    def __init__(self, identificador: str):
        super().__init__(f"Tenant não encontrado: {identificador}")


class TenantSlugJaExisteError(Exception):
    def __init__(self, slug: str):
        super().__init__(f"Já existe um tenant com o slug '{slug}'")


class TenantInativoError(Exception):
    def __init__(self):
        super().__init__("Tenant está inativo e não pode ser modificado")


# ── Service ───────────────────────────────────────────────────────────────────

class TenantService:

    def __init__(self, repository: TenantRepository) -> None:
        self._repo = repository

    async def criar(
        self,
        nome: str,
        slug: str,
        email_dono: str,
        plano: TenantPlano = TenantPlano.FREE,
    ) -> Tenant:
        """Cadastra um novo tenant. Slug deve ser único."""
        if await self._repo.exists_by_slug(slug):
            raise TenantSlugJaExisteError(slug)

        tenant = Tenant(
            nome=nome,
            slug=slug,
            email_dono=email_dono,
            plano=plano,
            status=TenantStatus.TRIAL,
            ativo=True,
        )
        return await self._repo.create(tenant)

    async def buscar_por_id(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = await self._repo.get_by_id(tenant_id)
        if not tenant:
            raise TenantNaoEncontradoError(str(tenant_id))
        return tenant

    async def buscar_por_slug(self, slug: str) -> Tenant:
        tenant = await self._repo.get_by_slug(slug)
        if not tenant:
            raise TenantNaoEncontradoError(slug)
        return tenant

    async def listar(self, apenas_ativos: bool = True) -> list[Tenant]:
        return await self._repo.list_all(apenas_ativos=apenas_ativos)

    async def atualizar(
        self,
        tenant_id: uuid.UUID,
        nome: str | None = None,
        email_dono: str | None = None,
    ) -> Tenant:
        """Atualiza apenas campos permitidos. Slug não pode ser alterado."""
        tenant = await self.buscar_por_id(tenant_id)

        if not tenant.ativo:
            raise TenantInativoError()

        if nome is not None:
            tenant.nome = nome
        if email_dono is not None:
            tenant.email_dono = email_dono

        tenant.updated_at = datetime.utcnow()
        return await self._repo.update(tenant)

    async def ativar(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = await self.buscar_por_id(tenant_id)
        if tenant.status == TenantStatus.CANCELADO:
            raise ValueError("Tenant cancelado não pode ser reativado")
        tenant.status = TenantStatus.ATIVO
        tenant.ativo = True
        tenant.updated_at = datetime.utcnow()
        return await self._repo.update(tenant)

    async def suspender(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = await self.buscar_por_id(tenant_id)
        if tenant.status == TenantStatus.CANCELADO:
            raise ValueError("Tenant já está cancelado")
        tenant.status = TenantStatus.SUSPENSO
        tenant.updated_at = datetime.utcnow()
        return await self._repo.update(tenant)

    async def upgrade_plano(
        self, tenant_id: uuid.UUID, novo_plano: TenantPlano
    ) -> Tenant:
        tenant = await self.buscar_por_id(tenant_id)
        if not tenant.ativo:
            raise TenantInativoError()
        if tenant.plano == novo_plano:
            raise ValueError(f"Tenant já está no plano {novo_plano}")
        tenant.plano = novo_plano
        tenant.updated_at = datetime.utcnow()
        return await self._repo.update(tenant)

    async def desativar(self, tenant_id: uuid.UUID) -> None:
        """Soft delete — preserva histórico."""
        tenant = await self.buscar_por_id(tenant_id)
        await self._repo.delete(tenant)
