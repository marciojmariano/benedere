"""Model: Pedido — pedido unificado (substitui fluxo Orçamento→Pedido) (Task 1.2.1)."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
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
    Substitui o fluxo antigo Orçamento → Pedido.

    Cadeia de markup: Pedido.markup_id → Cliente.markup_id_padrao → Tenant.markup_id_padrao
    O service resolve a cadeia na criação.
    """
    __tablename__ = "pedidos_v2"
    # Tabela com nome diferente pra coexistir durante migração de dados.
    # Após Épico 1 US 1.3 (migração) e Épico 4 (limpeza), renomear para "pedidos".

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    numero: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True  # Ex: PED-2026-0001
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Markup resolvido no momento da criação (snapshot da cadeia)
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
        DateTime, nullable=True
    )
    data_entrega_realizada: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # ── Relacionamentos ──────────────────────────────────────────────────────
    cliente: Mapped["Cliente"] = relationship("Cliente")
    markup: Mapped["Markup | None"] = relationship("Markup")
    itens: Mapped[list["PedidoItem"]] = relationship(
        "PedidoItem", back_populates="pedido", cascade="all, delete-orphan"
    )
