"""
Models SQLAlchemy — Benedere Alimentação Saudável
Todas as tabelas de negócio herdam TenantScoped (tenant_id obrigatório).
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ── Base e Mixins ─────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


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
    Garante isolamento por tenant em todas as queries.
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


# ── Tenant ────────────────────────────────────────────────────────────────────

class Tenant(Base, TimestampMixin):
    """
    Tabela raiz do multi-tenancy.
    Cada empresa cliente do SaaS é um Tenant.
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    email_dono: Mapped[str] = mapped_column(String(255), nullable=False)
    plano: Mapped[TenantPlano] = mapped_column(
        Enum(TenantPlano), nullable=False, default=TenantPlano.FREE
    )
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus), nullable=False, default=TenantStatus.TRIAL
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ── Clientes ──────────────────────────────────────────────────────────────────

class Cliente(Base, TenantScoped):
    """
    Cliente que solicita orçamento de marmitas.
    Nutricionista é opcional — nem todo cliente tem acompanhamento.
    """
    __tablename__ = "clientes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    endereco: Mapped[str | None] = mapped_column(Text, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Nutricionista é opcional
    nutricionista_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nutricionistas.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relacionamentos
    nutricionista: Mapped["Nutricionista | None"] = relationship(
        "Nutricionista", back_populates="clientes"
    )
    orcamentos: Mapped[list["Orcamento"]] = relationship(
        "Orcamento", back_populates="cliente"
    )


# ── Nutricionistas ────────────────────────────────────────────────────────────

class Nutricionista(Base, TenantScoped):
    """
    Nutricionista que acompanha o cliente.
    Opcional — o orçamento pode ser feito sem vínculo com nutricionista.
    """
    __tablename__ = "nutricionistas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    crn: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Registro profissional
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    clientes: Mapped[list["Cliente"]] = relationship(
        "Cliente", back_populates="nutricionista"
    )


# ── Índices de Markup ─────────────────────────────────────────────────────────

class IndiceMarkup(Base, TenantScoped):
    """
    Índices que compõem o cálculo do Markup.
    Ex: Impostos (15%), Despesas fixas (10%), Lucro desejado (20%).
    """
    __tablename__ = "indices_markup"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    percentual: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False  # Ex: 15.00 = 15%
    )
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    markups: Mapped[list["MarkupIndice"]] = relationship(
        "MarkupIndice", back_populates="indice"
    )


# ── Markup ────────────────────────────────────────────────────────────────────

class Markup(Base, TenantScoped):
    """
    Markup é um conjunto de índices que define o fator de precificação.
    Fórmula: Markup = 100 / (100 - soma_dos_percentuais)
    """
    __tablename__ = "markups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    fator: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False  # Calculado: ex: 2.8571
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    indices: Mapped[list["MarkupIndice"]] = relationship(
        "MarkupIndice", back_populates="markup"
    )


class MarkupIndice(Base, TenantScoped):
    """
    Tabela associativa: quais índices compõem cada Markup.
    """
    __tablename__ = "markup_indices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    markup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markups.id", ondelete="CASCADE"),
        nullable=False,
    )
    indice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indices_markup.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Relacionamentos
    markup: Mapped["Markup"] = relationship("Markup", back_populates="indices")
    indice: Mapped["IndiceMarkup"] = relationship("IndiceMarkup", back_populates="markups")


# ── Ingredientes ──────────────────────────────────────────────────────────────

class Ingrediente(Base, TenantScoped):
    """
    Ingrediente cadastrado com custo por unidade de medida.
    Cada ingrediente pode ter seu próprio markup (markup por ingrediente).
    """
    __tablename__ = "ingredientes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade_medida: Mapped[UnidadeMedida] = mapped_column(
        Enum(UnidadeMedida), nullable=False
    )
    custo_unitario: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False  # Custo por unidade de medida
    )
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Markup específico do ingrediente (opcional)
    markup_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relacionamentos
    markup: Mapped["Markup | None"] = relationship("Markup")


# ── Orçamentos ────────────────────────────────────────────────────────────────

class Orcamento(Base, TenantScoped):
    """
    Orçamento de marmitas personalizado.
    Composto de ingredientes, embalagem e taxa de entrega.
    Quando aprovado, gera um novo registro de Pedido.
    """
    __tablename__ = "orcamentos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    numero: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True  # Ex: ORC-2025-0001
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[StatusOrcamento] = mapped_column(
        Enum(StatusOrcamento), nullable=False, default=StatusOrcamento.RASCUNHO
    )

    # Markup aplicado no total do orçamento
    markup_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Custos
    custo_ingredientes: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    custo_embalagem: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    taxa_entrega: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    custo_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0  # Soma dos custos
    )
    preco_final: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0  # Após aplicação do markup total
    )

    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    validade_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=7)

    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="orcamentos")
    markup: Mapped["Markup | None"] = relationship("Markup")
    itens: Mapped[list["OrcamentoItem"]] = relationship(
        "OrcamentoItem", back_populates="orcamento", cascade="all, delete-orphan"
    )
    pedido: Mapped["Pedido | None"] = relationship(
        "Pedido", back_populates="orcamento", uselist=False
    )


class OrcamentoItem(Base, TenantScoped):
    """
    Item de ingrediente dentro de um orçamento.
    Registra o custo no momento do orçamento (snapshot de preço).
    """
    __tablename__ = "orcamento_itens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    orcamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orcamentos.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingrediente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredientes.id", ondelete="RESTRICT"),
        nullable=False,
    )

    quantidade: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unidade_medida: Mapped[UnidadeMedida] = mapped_column(
        Enum(UnidadeMedida), nullable=False
    )

    # Snapshot de preços no momento do orçamento
    custo_unitario_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    markup_fator_snapshot: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), nullable=True  # Markup do ingrediente no momento
    )
    custo_total_item: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False  # quantidade * custo_unitario
    )
    preco_item_com_markup: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False  # custo_total_item * markup_fator
    )

    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    orcamento: Mapped["Orcamento"] = relationship("Orcamento", back_populates="itens")
    ingrediente: Mapped["Ingrediente"] = relationship("Ingrediente")


# ── Pedidos ───────────────────────────────────────────────────────────────────

class Pedido(Base, TenantScoped):
    """
    Pedido gerado a partir de um orçamento aprovado.
    É um novo registro — preserva o histórico do orçamento original.
    """
    __tablename__ = "pedidos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    numero: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True  # Ex: PED-2025-0001
    )
    orcamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orcamentos.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,  # 1 orçamento → 1 pedido
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[StatusPedido] = mapped_column(
        Enum(StatusPedido),
        nullable=False,
        default=StatusPedido.AGUARDANDO_PRODUCAO,
    )

    # Valores copiados do orçamento no momento da aprovação (snapshot)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    taxa_entrega: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    custo_embalagem: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )

    data_entrega_prevista: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    data_entrega_realizada: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    orcamento: Mapped["Orcamento"] = relationship("Orcamento", back_populates="pedido")
    cliente: Mapped["Cliente"] = relationship("Cliente")
    itens: Mapped[list["PedidoItem"]] = relationship(
        "PedidoItem", back_populates="pedido", cascade="all, delete-orphan"
    )


class PedidoItem(Base, TenantScoped):
    """
    Itens do pedido — cópia dos itens do orçamento no momento da aprovação.
    Garante rastreabilidade mesmo se o ingrediente mudar de preço depois.
    """
    __tablename__ = "pedido_itens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pedidos.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingrediente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nome_ingrediente_snapshot: Mapped[str] = mapped_column(
        String(255), nullable=False  # Nome no momento do pedido
    )
    quantidade: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unidade_medida: Mapped[UnidadeMedida] = mapped_column(
        Enum(UnidadeMedida), nullable=False
    )
    custo_unitario_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    custo_total_item: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relacionamentos
    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="itens")
    ingrediente: Mapped["Ingrediente"] = relationship("Ingrediente")
