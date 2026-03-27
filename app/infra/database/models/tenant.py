"""Model: Tenant — raiz do multi-tenancy."""
import uuid
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.database.models.base import Base, EstrategiaCusto, TimestampMixin, TenantPlano, TenantStatus

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

    # ── Estratégia de custo padrão do tenant ─────────────────────────────────
    estrategia_custo_padrao: Mapped[EstrategiaCusto] = mapped_column(
        Enum(EstrategiaCusto), nullable=False, default=EstrategiaCusto.MANUAL,
        server_default="MANUAL"
    )
    periodo_dias_custo_medio_padrao: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=30
    )

    # ── Template de etiqueta por tenant ──────────────────────────────────────
    etiqueta_template_delta: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
    etiqueta_html_output: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    etiqueta_largura_mm: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=100
    )
    etiqueta_altura_mm: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=60
    )