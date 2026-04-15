"""Módulo de gestão de estoque: entradas de insumos

Revision ID: 00000000003
Revises: 00000000002
Create Date: 2026-03-26

Adiciona:
- Enum tipomovimentacao (COMPRA, ENTRADA_PRODUCAO, AJUSTE_ENTRADA, VENDA_DEVOLUCAO,
  VENDA, SAIDA_PRODUCAO, AJUSTE_SAIDA, COMPRA_DEVOLUCAO)
- Coluna saldo_atual em ingredientes (default: 0)
- Tabela movimentacoes_estoque
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '00000000003'
down_revision: Union[str, None] = '00000000002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── 1. Enum TipoMovimentacao (SQL puro para evitar criação dupla via asyncpg) ──
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tipomovimentacao AS ENUM (
                'COMPRA', 'ENTRADA_PRODUCAO', 'AJUSTE_ENTRADA', 'VENDA_DEVOLUCAO',
                'VENDA', 'SAIDA_PRODUCAO', 'AJUSTE_SAIDA', 'COMPRA_DEVOLUCAO'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── 2. Coluna saldo_atual em ingredientes ─────────────────────────────────
    op.add_column(
        'ingredientes',
        sa.Column(
            'saldo_atual',
            sa.Numeric(precision=12, scale=4),
            nullable=False,
            server_default='0',
        )
    )

    # ── 3. Tabela movimentacoes_estoque (SQL puro para evitar recriação do enum) ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
            id          UUID                NOT NULL PRIMARY KEY,
            ingrediente_id UUID             NOT NULL REFERENCES ingredientes(id) ON DELETE RESTRICT,
            tipo        tipomovimentacao    NOT NULL,
            quantidade  NUMERIC(12, 4)      NOT NULL,
            preco_unitario_custo NUMERIC(10, 4) NOT NULL,
            data_movimentacao DATE           NOT NULL,
            observacoes TEXT,
            tenant_id   UUID                NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            created_at  TIMESTAMP           NOT NULL,
            updated_at  TIMESTAMP           NOT NULL,
            CONSTRAINT ck_movimentacao_quantidade_positiva CHECK (quantidade > 0),
            CONSTRAINT ck_movimentacao_preco_positivo CHECK (preco_unitario_custo > 0)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_movimentacoes_estoque_tenant_id
        ON movimentacoes_estoque (tenant_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_movimentacoes_estoque_ingrediente_id
        ON movimentacoes_estoque (ingrediente_id)
    """)


def downgrade() -> None:

    # ── 3. Remover tabela movimentacoes_estoque ───────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_movimentacoes_estoque_ingrediente_id")
    op.execute("DROP INDEX IF EXISTS ix_movimentacoes_estoque_tenant_id")
    op.execute("DROP TABLE IF EXISTS movimentacoes_estoque")

    # ── 2. Remover coluna saldo_atual de ingredientes ─────────────────────────
    op.drop_column('ingredientes', 'saldo_atual')

    # ── 1. Remover enum tipomovimentacao ──────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS tipomovimentacao")
