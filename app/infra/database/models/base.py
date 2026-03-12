"""
Base, Mixins e Enums compartilhados por todos os models.
Este arquivo não deve importar nenhum model — apenas definir fundações.
"""
import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
import uuid


# ── Base ORM ──────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Mixins ────────────────────────────────────────────────────────────────────

class TimestampMixin:
    """Colunas de auditoria presentes em todas as tabelas."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class TenantScoped(TimestampMixin):
    """
    Mixin obrigatório para toda tabela multi-tenant.
    Garante que toda tabela de negócio tenha tenant_id.
    """
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


# ── Enums ─────────────────────────────────────────────────────────────────────

class TenantStatus(str, enum.Enum):
    ATIVO = "ativo"
    SUSPENSO = "suspenso"
    TRIAL = "trial"
    CANCELADO = "cancelado"


class TenantPlano(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class UnidadeMedida(str, enum.Enum):
    KG = "kg"
    G = "g"
    ML = "ml"
    L = "l"
    UNIDADE = "unidade"


class StatusOrcamento(str, enum.Enum):
    RASCUNHO = "rascunho"
    ENVIADO = "enviado"
    APROVADO = "aprovado"
    REPROVADO = "reprovado"
    CANCELADO = "cancelado"


class StatusPedido(str, enum.Enum):
    AGUARDANDO_PRODUCAO = "aguardando_producao"
    EM_PRODUCAO = "em_producao"
    PRONTO = "pronto"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"
