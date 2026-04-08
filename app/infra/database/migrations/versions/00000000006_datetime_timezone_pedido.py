"""Adiciona timezone às colunas de data de entrega do pedido

Revision ID: 00000000006
Revises: 00000000005
Create Date: 2026-04-08

Altera:
- data_entrega_prevista: DateTime → DateTime(timezone=True)
- data_entrega_realizada: DateTime → DateTime(timezone=True)
"""

from alembic import op
import sqlalchemy as sa


revision = "00000000006"
down_revision = "00000000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "pedidos",
        "data_entrega_prevista",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True,
    )
    op.alter_column(
        "pedidos",
        "data_entrega_realizada",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "pedidos",
        "data_entrega_prevista",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "pedidos",
        "data_entrega_realizada",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
