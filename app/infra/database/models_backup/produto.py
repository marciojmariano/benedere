"""Model: Produto — catálogo de itens de série (Task 1.1.2)."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped, TipoRefeicao

if TYPE_CHECKING:
    from app.infra.database.models.produto_composicao import ProdutoComposicao


class Produto(Base, TenantScoped):
    """
    Produto do catálogo (ex: Escondidinho de Ragu, Granola Artesanal).
    Contém a receita padrão via ProdutoComposicao.
    Quando adicionado a um pedido de série, a composição é clonada como snapshot.
    """
    __tablename__ = "produtos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_refeicao: Mapped[TipoRefeicao | None] = mapped_column(
        Enum(TipoRefeicao), nullable=True
    )
    # Peso total calculado pela soma da composição (atualizado pelo service)
    peso_total_g: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relacionamentos ──────────────────────────────────────────────────────
    composicao: Mapped[list["ProdutoComposicao"]] = relationship(
        "ProdutoComposicao",
        back_populates="produto",
        cascade="all, delete-orphan",
        order_by="ProdutoComposicao.ordem",
    )
