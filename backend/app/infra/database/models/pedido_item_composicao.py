"""Model: PedidoItemComposicao — snapshot dos ingredientes no ato da venda."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base

if TYPE_CHECKING:
    from app.infra.database.models.pedido_item import PedidoItem
    from app.infra.database.models.ingrediente import Ingrediente


class PedidoItemComposicao(Base):
    """
    Snapshot de cada ingrediente dentro de um PedidoItem.
    Registra custo/kg e kcal no ato da criação — protege o histórico financeiro.
    Isolamento via PedidoItem → Pedido (TenantScoped).
    """
    __tablename__ = "pedido_item_composicoes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pedido_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pedido_itens.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingrediente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredientes.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # ── Snapshots (imutáveis após criação) ───────────────────────────────────
    ingrediente_nome_snap: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    quantidade_g: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    custo_kg_snapshot: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    kcal_snapshot: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )

    # ── Relacionamentos ──────────────────────────────────────────────────────
    pedido_item: Mapped["PedidoItem"] = relationship(
        "PedidoItem", back_populates="composicao"
    )
    ingrediente: Mapped["Ingrediente"] = relationship("Ingrediente")
