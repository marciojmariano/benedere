"""Inteligência de Custo de Insumos: estratégia de cálculo por ingrediente

Revision ID: 00000000004
Revises: 00000000003
Create Date: 2026-03-26

Adiciona:
- Enum estrategiacusto (MANUAL, ULTIMA_COMPRA, MEDIA_PONDERADA_TOTAL, MEDIA_PONDERADA_PERIODO)
- Colunas em ingredientes: estrategia_custo, periodo_dias_custo_medio, custo_calculado
- Colunas em tenants: estrategia_custo_padrao, periodo_dias_custo_medio_padrao
- Index em movimentacoes_estoque(ingrediente_id, data_movimentacao DESC) para queries de agregação
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '00000000004'
down_revision: Union[str, None] = '00000000003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── 1. Enum EstrategiaCusto ───────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE estrategiacusto AS ENUM (
                'MANUAL', 'ULTIMA_COMPRA', 'MEDIA_PONDERADA_TOTAL', 'MEDIA_PONDERADA_PERIODO'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── 2. Colunas em ingredientes ────────────────────────────────────────────
    op.add_column(
        'ingredientes',
        sa.Column('estrategia_custo', sa.Enum('MANUAL', 'ULTIMA_COMPRA', 'MEDIA_PONDERADA_TOTAL', 'MEDIA_PONDERADA_PERIODO', name='estrategiacusto'), nullable=True)
    )
    op.add_column(
        'ingredientes',
        sa.Column('periodo_dias_custo_medio', sa.Integer(), nullable=True)
    )
    op.add_column(
        'ingredientes',
        sa.Column('custo_calculado', sa.Numeric(precision=10, scale=4), nullable=True)
    )

    # ── 3. Backfill: custo_calculado = custo_unitario para ingredientes existentes
    op.execute("UPDATE ingredientes SET custo_calculado = custo_unitario")

    # ── 4. Colunas em tenants ─────────────────────────────────────────────────
    op.add_column(
        'tenants',
        sa.Column(
            'estrategia_custo_padrao',
            sa.Enum('MANUAL', 'ULTIMA_COMPRA', 'MEDIA_PONDERADA_TOTAL', 'MEDIA_PONDERADA_PERIODO', name='estrategiacusto'),
            nullable=False,
            server_default='MANUAL'
        )
    )
    op.add_column(
        'tenants',
        sa.Column('periodo_dias_custo_medio_padrao', sa.Integer(), nullable=True)
    )

    # ── 5. Index para queries de agregação de custo ───────────────────────────
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_movest_ingrediente_data
        ON movimentacoes_estoque (ingrediente_id, data_movimentacao DESC)
    """)


def downgrade() -> None:

    # ── 5. Remover index ──────────────────────────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_movest_ingrediente_data")

    # ── 4. Remover colunas de tenants ─────────────────────────────────────────
    op.drop_column('tenants', 'periodo_dias_custo_medio_padrao')
    op.drop_column('tenants', 'estrategia_custo_padrao')

    # ── 2. Remover colunas de ingredientes ────────────────────────────────────
    op.drop_column('ingredientes', 'custo_calculado')
    op.drop_column('ingredientes', 'periodo_dias_custo_medio')
    op.drop_column('ingredientes', 'estrategia_custo')

    # ── 1. Remover enum ───────────────────────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS estrategiacusto")
