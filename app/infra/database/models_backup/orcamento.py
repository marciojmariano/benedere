"""Models: Orcamento, OrcamentoItem."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped, StatusOrcamento, UnidadeMedida

if TYPE_CHECKING:
    from app.infra.database.models.cliente import Cliente
    from app.infra.database.models.markup import Markup
    from app.infra.database.models.ingrediente import Ingrediente
    from app.infra.database.models.pedido import Pedido


class Orcamento(Base, TenantScoped):
    """
    Orçamento de marmitas personalizado.
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

    # Markup aplicado no total do orçamento (opcional)
    markup_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Custos
    custo_ingredientes: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    custo_embalagem: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    taxa_entrega: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    custo_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    preco_final: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

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
    Guarda snapshot de preço no momento do orçamento.
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
    quantidade: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    unidade_medida: Mapped[UnidadeMedida] = mapped_column(
        Enum(UnidadeMedida), nullable=False
    )

    # Snapshots de preço no momento do orçamento
    custo_unitario_snapshot: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    markup_fator_snapshot: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    custo_total_item: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    preco_item_com_markup: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    orcamento: Mapped["Orcamento"] = relationship("Orcamento", back_populates="itens")
    ingrediente: Mapped["Ingrediente"] = relationship("Ingrediente")
