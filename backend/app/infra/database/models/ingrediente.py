"""Model: Ingrediente."""
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, EstrategiaCusto, TenantScoped, TipoIngrediente, UnidadeMedida

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
        Enum(TipoIngrediente), nullable=False, default=TipoIngrediente.INSUMO, server_default="INSUMO"
    )
    unidade_medida: Mapped[UnidadeMedida] = mapped_column(
        Enum(UnidadeMedida), nullable=False
    )
    custo_unitario: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    saldo_atual: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, server_default="0", default=Decimal("0")
    )

    # ── Estratégia de custo ───────────────────────────────────────────────────
    estrategia_custo: Mapped[EstrategiaCusto | None] = mapped_column(
        Enum(EstrategiaCusto), nullable=True, default=None
    )
    periodo_dias_custo_medio: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    custo_calculado: Mapped[float | None] = mapped_column(
        Numeric(10, 4), nullable=True, default=None
    )

    # Markup específico do ingrediente (opcional)
    markup_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relacionamentos
    markup: Mapped["Markup | None"] = relationship("Markup")
