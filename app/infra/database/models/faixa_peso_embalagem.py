"""Model: FaixaPesoEmbalagem — regras de embalagem por faixa de peso por tenant."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped

if TYPE_CHECKING:
    from app.infra.database.models.ingrediente import Ingrediente


class FaixaPesoEmbalagem(Base, TenantScoped):
    """
    Faixa de peso associada a um ingrediente do tipo EMBALAGEM.
    Quando o peso total dos ingredientes de um item cai nesta faixa,
    a embalagem correspondente é automaticamente vinculada ao item do pedido.

    Isolamento garantido via tenant_id (TenantScoped).
    """
    __tablename__ = "faixas_peso_embalagem"
    __table_args__ = (
        CheckConstraint("peso_min_g >= 0", name="ck_faixa_peso_min_nao_negativo"),
        CheckConstraint("peso_max_g > peso_min_g", name="ck_faixa_peso_max_maior_min"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    peso_min_g: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    peso_max_g: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    ingrediente_embalagem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relacionamentos ──────────────────────────────────────────────────────
    ingrediente_embalagem: Mapped["Ingrediente"] = relationship("Ingrediente")
