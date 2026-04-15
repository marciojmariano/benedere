"""Model: ProdutoComposicao — receita padrão de um produto de série (Task 1.1.3)."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base

if TYPE_CHECKING:
    from app.infra.database.models.produto import Produto
    from app.infra.database.models.ingrediente import Ingrediente


class ProdutoComposicao(Base):
    """
    Ingrediente dentro da receita padrão de um Produto.
    NÃO herda TenantScoped — o isolamento é garantido via Produto (que é TenantScoped).
    O tenant_id não precisa existir aqui: acesso sempre via join com produto.
    """
    __tablename__ = "produto_composicoes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    produto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produtos.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingrediente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Quantidade em gramas deste ingrediente na receita
    quantidade_g: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    # Ordem de exibição na receita (drag-and-drop no frontend)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Relacionamentos ──────────────────────────────────────────────────────
    produto: Mapped["Produto"] = relationship("Produto", back_populates="composicao")
    ingrediente: Mapped["Ingrediente"] = relationship("Ingrediente")
