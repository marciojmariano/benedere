"""Impressão de etiquetas em lote — rastreamento por item e calibração de offset

Revision ID: 00000000007
Revises: 00000000006
Create Date: 2026-03-28

Altera:
- pedido_itens: adiciona etiqueta_impressa (Boolean, default False)
- tenants: adiciona etiqueta_offset_x_mm (Integer, default 0) e etiqueta_offset_y_mm (Integer, default 0)
"""

from alembic import op
import sqlalchemy as sa

revision = "00000000007"
down_revision = "00000000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pedido_itens",
        sa.Column("etiqueta_impressa", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "tenants",
        sa.Column("etiqueta_offset_x_mm", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tenants",
        sa.Column("etiqueta_offset_y_mm", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("tenants", "etiqueta_offset_y_mm")
    op.drop_column("tenants", "etiqueta_offset_x_mm")
    op.drop_column("pedido_itens", "etiqueta_impressa")
