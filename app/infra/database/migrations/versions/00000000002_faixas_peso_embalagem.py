"""faixas de peso para seleção automática de embalagem

Revision ID: 00000000002
Revises: 00000000001
Create Date: 2026-03-25

Adiciona:
- Enum tipoingrediente (insumo, embalagem)
- Coluna tipo em ingredientes (default: insumo)
- Tabela faixas_peso_embalagem (faixas de peso por tenant)
- Colunas de embalagem em pedido_itens (snapshot auto-selecionado)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '00000000002'
down_revision: Union[str, None] = '00000000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── 1. Enum TipoIngrediente ───────────────────────────────────────────────
    tipoingrediente = sa.Enum('insumo', 'embalagem', name='tipoingrediente')
    tipoingrediente.create(op.get_bind(), checkfirst=True)

    # ── 2. Coluna tipo em ingredientes ───────────────────────────────────────
    op.add_column(
        'ingredientes',
        sa.Column(
            'tipo',
            sa.Enum('insumo', 'embalagem', name='tipoingrediente'),
            nullable=False,
            server_default='insumo',
        )
    )

    # ── 3. Tabela faixas_peso_embalagem ──────────────────────────────────────
    op.create_table(
        'faixas_peso_embalagem',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('peso_min_g', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('peso_max_g', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('ingrediente_embalagem_id', sa.UUID(), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('peso_min_g >= 0', name='ck_faixa_peso_min_nao_negativo'),
        sa.CheckConstraint('peso_max_g > peso_min_g', name='ck_faixa_peso_max_maior_min'),
        sa.ForeignKeyConstraint(
            ['tenant_id'], ['tenants.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['ingrediente_embalagem_id'], ['ingredientes.id'], ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_faixas_peso_embalagem_tenant_id'),
        'faixas_peso_embalagem',
        ['tenant_id'],
    )

    # ── 4. Colunas de embalagem em pedido_itens ──────────────────────────────
    op.add_column(
        'pedido_itens',
        sa.Column('embalagem_ingrediente_id', sa.UUID(), nullable=True)
    )
    op.add_column(
        'pedido_itens',
        sa.Column('embalagem_nome_snapshot', sa.String(length=255), nullable=True)
    )
    op.add_column(
        'pedido_itens',
        sa.Column('embalagem_custo_snapshot', sa.Numeric(precision=10, scale=4), nullable=True)
    )
    op.create_foreign_key(
        'fk_pedido_itens_embalagem_ingrediente',
        'pedido_itens',
        'ingredientes',
        ['embalagem_ingrediente_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:

    # ── 4. Remover colunas de embalagem de pedido_itens ──────────────────────
    op.drop_constraint(
        'fk_pedido_itens_embalagem_ingrediente', 'pedido_itens', type_='foreignkey'
    )
    op.drop_column('pedido_itens', 'embalagem_custo_snapshot')
    op.drop_column('pedido_itens', 'embalagem_nome_snapshot')
    op.drop_column('pedido_itens', 'embalagem_ingrediente_id')

    # ── 3. Remover tabela faixas_peso_embalagem ──────────────────────────────
    op.drop_index(
        op.f('ix_faixas_peso_embalagem_tenant_id'), table_name='faixas_peso_embalagem'
    )
    op.drop_table('faixas_peso_embalagem')

    # ── 2. Remover coluna tipo de ingredientes ───────────────────────────────
    op.drop_column('ingredientes', 'tipo')

    # ── 1. Remover enum TipoIngrediente ──────────────────────────────────────
    sa.Enum(name='tipoingrediente').drop(op.get_bind(), checkfirst=True)
