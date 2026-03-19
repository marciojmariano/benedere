"""Model: Nutricionista."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped

if TYPE_CHECKING:
    from app.infra.database.models.cliente import Cliente


class Nutricionista(Base, TenantScoped):
    """
    Nutricionista que acompanha o cliente.
    Vínculo com cliente é opcional.
    """
    __tablename__ = "nutricionistas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    crn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    clientes: Mapped[list["Cliente"]] = relationship(
        "Cliente", back_populates="nutricionista"
    )
