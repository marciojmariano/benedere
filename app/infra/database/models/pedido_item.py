"""Model: PedidoItem — item (marmita/produto) dentro de um pedido."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TipoRefeicao, TipoItem

if TYPE_CHECKING:
    from app.infra.database.models.pedido import Pedido
    from app.infra.database.models.produto import Produto
    from app.infra.database.models.ingrediente import Ingrediente
    from app.infra.database.models.pedido_item_composicao import PedidoItemComposicao


class PedidoItem(Base):
    """
    Item do pedido — pode ser:
      - SERIE:         produto_id preenchido, composição clonada do catálogo.
      - PERSONALIZADO: produto_id NULL, composição montada manualmente.

    Isolamento via Pedido (TenantScoped).
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
    produto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.id", ondelete="SET NULL"),
        nullable=True,
    )
    nome_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)

    tipo_refeicao: Mapped[TipoRefeicao | None] = mapped_column(
        Enum(TipoRefeicao), nullable=True
    )
    tipo: Mapped[TipoItem] = mapped_column(
        Enum(TipoItem), nullable=False
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    preco_unitario: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    preco_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )

    # ── Embalagem (auto-selecionada por faixa de peso) ────────────────────────
    embalagem_ingrediente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredientes.id", ondelete="SET NULL"),
        nullable=True,
    )
    embalagem_nome_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embalagem_custo_snapshot: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)

    # ── Relacionamentos ──────────────────────────────────────────────────────
    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="itens")
    produto: Mapped["Produto | None"] = relationship("Produto")
    embalagem_ingrediente: Mapped["Ingrediente | None"] = relationship(
        "Ingrediente", foreign_keys=[embalagem_ingrediente_id]
    )
    composicao: Mapped[list["PedidoItemComposicao"]] = relationship(
        "PedidoItemComposicao",
        back_populates="pedido_item",
        cascade="all, delete-orphan",
    )
