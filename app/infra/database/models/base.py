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


# ── Enums: Tenant ────────────────────────────────────────────────────────────

class TenantStatus(str, enum.Enum):
    ATIVO = "ATIVO"
    SUSPENSO = "SUSPENSO"
    TRIAL = "TRIAL"
    CANCELADO = "CANCELADO"


class TenantPlano(str, enum.Enum):
    FREE = "FREE"
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


# ── Enums: Ingrediente ───────────────────────────────────────────────────────

class TipoIngrediente(str, enum.Enum):
    INSUMO = "INSUMO"
    EMBALAGEM = "EMBALAGEM"


class UnidadeMedida(str, enum.Enum):
    KG = "KG"
    G = "G"
    ML = "ML"
    L = "L"
    UNIDADE = "UNIDADE"


# ── Enums: Produto / Refeição ────────────────────────────────────────────────

class TipoRefeicao(str, enum.Enum):
    """Tipo de refeição — enum fixo no banco."""
    CAFE_MANHA = "CAFE_MANHA"
    LANCHE_MANHA = "LANCHE_MANHA"
    ALMOCO = "ALMOCO"
    LANCHE_TARDE = "LANCHE_TARDE"
    JANTAR = "JANTAR"


# ── Enums: Pedido ────────────────────────────────────────────────────────────

class StatusPedido(str, enum.Enum):
    """Status do pedido unificado com máquina de estados."""
    RASCUNHO = "RASCUNHO"
    APROVADO = "APROVADO"
    EM_PRODUCAO = "EM_PRODUCAO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"


class TipoItem(str, enum.Enum):
    """Tipo do item no pedido: série (catálogo) ou personalizado."""
    SERIE = "SERIE"
    PERSONALIZADO = "PERSONALIZADO"


# ── Enums: Estoque ────────────────────────────────────────────────────────────

class TipoMovimentacao(str, enum.Enum):
    """Tipo de movimentação de estoque."""
    COMPRA = "COMPRA"
    ENTRADA_PRODUCAO = "ENTRADA_PRODUCAO"   # reservado para futuro
    AJUSTE_ENTRADA = "AJUSTE_ENTRADA"       # reservado para futuro
    VENDA_DEVOLUCAO = "VENDA_DEVOLUCAO"     # reservado para futuro
    VENDA = "VENDA"                         # reservado para futuro
    SAIDA_PRODUCAO = "SAIDA_PRODUCAO"       # reservado para futuro
    AJUSTE_SAIDA = "AJUSTE_SAIDA"           # reservado para futuro
    COMPRA_DEVOLUCAO = "COMPRA_DEVOLUCAO"   # reservado para futuro
