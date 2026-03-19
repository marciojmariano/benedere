"""Models: IndiceMarkup, Markup, MarkupIndice."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.models.base import Base, TenantScoped


class IndiceMarkup(Base, TenantScoped):
    """
    Índices que compõem o cálculo do Markup.
    Ex: Impostos (15%), Despesas fixas (10%), Lucro desejado (20%).
    """
    __tablename__ = "indices_markup"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    percentual: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False  # Ex: 15.00 = 15%
    )
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    markups: Mapped[list["MarkupIndice"]] = relationship(
        "MarkupIndice", back_populates="indice"
    )


class Markup(Base, TenantScoped):
    """
    Conjunto de índices que define o fator de precificação.
    Fórmula: Markup = 100 / (100 - soma_dos_percentuais)
    """
    __tablename__ = "markups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    fator: Mapped[float] = mapped_column(
        Numeric(8, 4), nullable=False  # Ex: 2.8571
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    indices: Mapped[list["MarkupIndice"]] = relationship(
        "MarkupIndice", back_populates="markup"
    )


class MarkupIndice(Base, TenantScoped):
    """Tabela associativa: quais índices compõem cada Markup."""
    __tablename__ = "markup_indices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    markup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markups.id", ondelete="CASCADE"),
        nullable=False,
    )
    indice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("indices_markup.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Relacionamentos
    markup: Mapped["Markup"] = relationship("Markup", back_populates="indices")
    indice: Mapped["IndiceMarkup"] = relationship("IndiceMarkup", back_populates="markups")
