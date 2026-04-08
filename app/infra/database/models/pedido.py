"""Model: Pedido — pedido unificado."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped, StatusPedido

if TYPE_CHECKING:
    from app.infra.database.models.cliente import Cliente
    from app.infra.database.models.markup import Markup
    from app.infra.database.models.pedido_item import PedidoItem


class Pedido(Base, TenantScoped):
    """
    Pedido unificado — nasce como rascunho, evolui via máquina de estados.
    Cadeia de markup: Pedido.markup_id → Cliente.markup_id_padrao → Tenant.markup_id_padrao
    """
    __tablename__ = "pedidos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    numero: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    markup_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markups.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[StatusPedido] = mapped_column(
        Enum(StatusPedido), nullable=False, default=StatusPedido.RASCUNHO
    )
    valor_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    data_entrega_prevista: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    data_entrega_realizada: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relacionamentos ──────────────────────────────────────────────────────
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="pedidos")
    markup: Mapped["Markup | None"] = relationship("Markup")
    itens: Mapped[list["PedidoItem"]] = relationship(
        "PedidoItem", back_populates="pedido", cascade="all, delete-orphan"
    )
