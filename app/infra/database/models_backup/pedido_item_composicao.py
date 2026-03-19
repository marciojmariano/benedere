"""Model: PedidoItemComposicao — snapshot dos ingredientes no ato da venda (Task 1.2.3)."""
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
    Registra custo/kg e kcal NO ATO DA CRIAÇÃO — protege o histórico financeiro
    contra alterações futuras no cadastro de ingredientes.

    NÃO herda TenantScoped — isolamento via PedidoItem → Pedido (TenantScoped).
    """
    __tablename__ = "pedido_item_composicoes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pedido_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pedido_itens_v2.id", ondelete="CASCADE"),
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
    # Custo por kg do ingrediente no momento da venda
    custo_kg_snapshot: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    # Kcal calculado: (quantidade_g / 1000) × kcal_por_kg do ingrediente
    kcal_snapshot: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )

    # ── Relacionamentos ──────────────────────────────────────────────────────
    pedido_item: Mapped["PedidoItem"] = relationship(
        "PedidoItem", back_populates="composicao"
    )
    ingrediente: Mapped["Ingrediente"] = relationship("Ingrediente")
