"""Adiciona campos de template de etiqueta ao tenant

Revision ID: 00000000006
Revises: 00000000005
Create Date: 2026-03-27

Altera:
- Adiciona colunas etiqueta_template_delta (JSONB), etiqueta_html_output (Text),
  etiqueta_largura_mm (Integer), etiqueta_altura_mm (Integer) à tabela tenants
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "00000000006"
down_revision = "00000000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("etiqueta_template_delta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("etiqueta_html_output", sa.Text(), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("etiqueta_largura_mm", sa.Integer(), nullable=True, server_default="100"),
    )
    op.add_column(
        "tenants",
        sa.Column("etiqueta_altura_mm", sa.Integer(), nullable=True, server_default="60"),
    )


def downgrade() -> None:
    op.drop_column("tenants", "etiqueta_altura_mm")
    op.drop_column("tenants", "etiqueta_largura_mm")
    op.drop_column("tenants", "etiqueta_html_output")
    op.drop_column("tenants", "etiqueta_template_delta")
