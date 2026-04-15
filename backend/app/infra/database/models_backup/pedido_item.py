"""Model: PedidoItem — item (marmita/produto) dentro de um pedido (Task 1.2.2)."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TipoRefeicao, TipoItem

if TYPE_CHECKING:
    from app.infra.database.models.pedido_v2 import Pedido
    from app.infra.database.models.produto import Produto
    from app.infra.database.models.pedido_item_composicao import PedidoItemComposicao


class PedidoItem(Base):
    """
    Item do pedido — pode ser:
      - SERIE:         produto_id preenchido, composição clonada do catálogo.
      - PERSONALIZADO: produto_id NULL, composição montada manualmente.

    O nome_snapshot congela o nome no ato da venda.
    tipo_refeicao é editável (vem como sugestão do catálogo mas pode ser alterado).
    NÃO herda TenantScoped — isolamento via Pedido (que é TenantScoped).
    """
    __tablename__ = "pedido_itens_v2"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pedidos_v2.id", ondelete="CASCADE"),
        nullable=False,
    )
    # NULL = personalizado; preenchido = série (vinculado ao catálogo)
    produto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Snapshot do nome do produto/marmita no momento da criação
    nome_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)

    tipo_refeicao: Mapped[TipoRefeicao | None] = mapped_column(
        Enum(TipoRefeicao), nullable=True
    )
    tipo: Mapped[TipoItem] = mapped_column(
        Enum(TipoItem), nullable=False
    )

    # Quantidade de unidades (o "2x" do protótipo)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Preço calculado: soma(custo_ingredientes) × fator_markup
    preco_unitario: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    # preco_total = preco_unitario × quantidade
    preco_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )

    # ── Relacionamentos ──────────────────────────────────────────────────────
    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="itens")
    produto: Mapped["Produto | None"] = relationship("Produto")
    composicao: Mapped[list["PedidoItemComposicao"]] = relationship(
        "PedidoItemComposicao",
        back_populates="pedido_item",
        cascade="all, delete-orphan",
    )
