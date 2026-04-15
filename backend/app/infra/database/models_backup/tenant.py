"""Model: Tenant — raiz do multi-tenancy."""
import uuid
from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database.models.base import Base, TimestampMixin, TenantPlano, TenantStatus

class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    email_dono: Mapped[str] = mapped_column(String(255), nullable=False)
    plano: Mapped[TenantPlano] = mapped_column(
        Enum(TenantPlano), nullable=False, default=TenantPlano.FREE
    )
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus), nullable=False, default=TenantStatus.TRIAL
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    markup_id_padrao: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markups.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )