"""Model: Cliente."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped

if TYPE_CHECKING:
    from app.infra.database.models.nutricionista import Nutricionista
    from app.infra.database.models.orcamento import Orcamento


class Cliente(Base, TenantScoped):
    """
    Cliente que solicita orçamento de marmitas.
    Nutricionista é opcional.
    """
    __tablename__ = "clientes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    endereco: Mapped[str | None] = mapped_column(Text, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Nutricionista opcional
    nutricionista_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nutricionistas.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relacionamentos
    nutricionista: Mapped["Nutricionista | None"] = relationship(
        "Nutricionista", back_populates="clientes"
    )
    orcamentos: Mapped[list["Orcamento"]] = relationship(
        "Orcamento", back_populates="cliente"
    )
