"""Model: MovimentacaoEstoque."""
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped, TipoMovimentacao

if TYPE_CHECKING:
    from app.infra.database.models.ingrediente import Ingrediente


class MovimentacaoEstoque(Base, TenantScoped):
    """
    Registro de movimentação de estoque de um ingrediente.
    Toda entrada (COMPRA) atualiza o saldo_atual do ingrediente.
    """
    __tablename__ = "movimentacoes_estoque"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ingrediente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredientes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoMovimentacao] = mapped_column(
        Enum(TipoMovimentacao), nullable=False
    )
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    preco_unitario_custo: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    data_movimentacao: Mapped[date] = mapped_column(Date, nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    ingrediente: Mapped["Ingrediente"] = relationship("Ingrediente")
