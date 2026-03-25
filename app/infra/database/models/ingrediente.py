"""Model: Ingrediente."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped, TipoIngrediente, UnidadeMedida

if TYPE_CHECKING:
    from app.infra.database.models.markup import Markup


class Ingrediente(Base, TenantScoped):
    """
    Ingrediente com custo por unidade de medida.
    Pode ter markup próprio (markup por ingrediente).
    """
    __tablename__ = "ingredientes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoIngrediente] = mapped_column(
        Enum(TipoIngrediente), nullable=False, default=TipoIngrediente.INSUMO, server_default="insumo"
    )
    unidade_medida: Mapped[UnidadeMedida] = mapped_column(
        Enum(UnidadeMedida), nullable=False
    )
    custo_unitario: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Markup específico do ingrediente (opcional)
    markup_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relacionamentos
    markup: Mapped["Markup | None"] = relationship("Markup")
