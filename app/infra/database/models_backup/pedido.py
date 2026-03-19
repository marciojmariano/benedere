"""Models: Pedido, PedidoItem."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped, StatusPedido, UnidadeMedida

if TYPE_CHECKING:
    from app.infra.database.models.cliente import Cliente
    from app.infra.database.models.orcamento import Orcamento
    from app.infra.database.models.ingrediente import Ingrediente


class Pedido(Base, TenantScoped):
    """
    Pedido gerado a partir de um orçamento aprovado.
    Novo registro — preserva histórico do orçamento original.
    """
    __tablename__ = "pedidos"
    __table_args__ = (
        UniqueConstraint("orcamento_id", name="uq_pedido_orcamento"),
    )

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

    # Valores copiados do orçamento (snapshot)
    valor_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    taxa_entrega: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    custo_embalagem: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    data_entrega_prevista: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_entrega_realizada: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    orcamento: Mapped["Orcamento"] = relationship("Orcamento", back_populates="pedido")
    cliente: Mapped["Cliente"] = relationship("Cliente")
    itens: Mapped[list["PedidoItem"]] = relationship(
        "PedidoItem", back_populates="pedido", cascade="all, delete-orphan"
    )


class PedidoItem(Base, TenantScoped):
    """
    Itens do pedido — cópia dos itens do orçamento.
    Garante rastreabilidade mesmo se o ingrediente mudar de preço.
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
    nome_ingrediente_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    unidade_medida: Mapped[UnidadeMedida] = mapped_column(
        Enum(UnidadeMedida), nullable=False
    )
    custo_unitario_snapshot: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    custo_total_item: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Relacionamentos
    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="itens")
    ingrediente: Mapped["Ingrediente"] = relationship("Ingrediente")
