"""Remove tipo_refeicao de produtos — campo movido para PedidoItem (override no pedido)

Revision ID: 00000000005
Revises: 00000000004
Create Date: 2026-03-27

Altera:
- Remove coluna tipo_refeicao da tabela produtos
"""

from alembic import op
import sqlalchemy as sa


revision = "00000000005"
down_revision = "00000000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("produtos", "tipo_refeicao")


def downgrade() -> None:
    op.add_column(
        "produtos",
        sa.Column(
            "tipo_refeicao",
            sa.Enum(
                "CAFE_MANHA", "LANCHE_MANHA", "ALMOCO", "LANCHE_TARDE", "JANTAR",
                name="tiporefeicao",
            ),
            nullable=True,
        ),
    )
