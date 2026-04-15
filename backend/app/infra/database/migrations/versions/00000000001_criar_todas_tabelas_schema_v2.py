"""criar todas as tabelas (schema v2 consolidado)

Revision ID: 00000000001
Revises:
Create Date: 2026-03-19

Schema limpo — sem tabelas legadas (orcamentos, orcamento_itens, pedidos/pedido_itens antigos).
Inclui: tenant, nutricionista, markup, ingrediente, cliente, produto, pedido unificado.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '00000000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── Tenants ──────────────────────────────────────────────────────────────
    op.create_table('tenants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('email_dono', sa.String(length=255), nullable=False),
        sa.Column('plano', sa.Enum('FREE', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE', name='tenantplano'), nullable=False),
        sa.Column('status', sa.Enum('ATIVO', 'SUSPENSO', 'TRIAL', 'CANCELADO', name='tenantstatus'), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)

    # ── Índices de Markup ────────────────────────────────────────────────────
    op.create_table('indices_markup',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('percentual', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_indices_markup_tenant_id'), 'indices_markup', ['tenant_id'])

    # ── Markups ──────────────────────────────────────────────────────────────
    op.create_table('markups',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('fator', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_markups_tenant_id'), 'markups', ['tenant_id'])

    # ── Adicionar markup_padrao no Tenant (FK circular) ──────────────────────
    op.add_column('tenants', sa.Column('markup_id_padrao', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_tenants_markup_padrao', 'tenants', 'markups', ['markup_id_padrao'], ['id'], ondelete='SET NULL')

    # ── Nutricionistas ───────────────────────────────────────────────────────
    op.create_table('nutricionistas',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('crn', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('telefone', sa.String(length=20), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_nutricionistas_tenant_id'), 'nutricionistas', ['tenant_id'])

    # ── Clientes ─────────────────────────────────────────────────────────────
    op.create_table('clientes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('telefone', sa.String(length=20), nullable=True),
        sa.Column('endereco', sa.Text(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('nutricionista_id', sa.UUID(), nullable=True),
        sa.Column('markup_id_padrao', sa.UUID(), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['nutricionista_id'], ['nutricionistas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['markup_id_padrao'], ['markups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_clientes_tenant_id'), 'clientes', ['tenant_id'])

    # ── Ingredientes ─────────────────────────────────────────────────────────
    op.create_table('ingredientes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('unidade_medida', sa.Enum('KG', 'G', 'ML', 'L', 'UNIDADE', name='unidademedida'), nullable=False),
        sa.Column('custo_unitario', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('markup_id', sa.UUID(), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['markup_id'], ['markups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ingredientes_tenant_id'), 'ingredientes', ['tenant_id'])

    # ── Markup ↔ Índice (N:N) ────────────────────────────────────────────────
    op.create_table('markup_indices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('markup_id', sa.UUID(), nullable=False),
        sa.Column('indice_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['indice_id'], ['indices_markup.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['markup_id'], ['markups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_markup_indices_tenant_id'), 'markup_indices', ['tenant_id'])

    # ── Produtos (catálogo de série) ─────────────────────────────────────────
    op.create_table('produtos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('tipo_refeicao', sa.Enum('CAFE_MANHA', 'LANCHE_MANHA', 'ALMOCO', 'LANCHE_TARDE', 'JANTAR', name='tiporefeicao'), nullable=True),
        sa.Column('peso_total_g', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_produtos_tenant_id'), 'produtos', ['tenant_id'])

    # ── Produto Composição (receita padrão) ──────────────────────────────────
    op.create_table('produto_composicoes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('produto_id', sa.UUID(), nullable=False),
        sa.Column('ingrediente_id', sa.UUID(), nullable=False),
        sa.Column('quantidade_g', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('ordem', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['produto_id'], ['produtos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingrediente_id'], ['ingredientes.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_produto_composicoes_produto_id', 'produto_composicoes', ['produto_id'])

    # ── Pedidos (unificado) ──────────────────────────────────────────────────
    op.create_table('pedidos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('numero', sa.String(length=20), nullable=False),
        sa.Column('cliente_id', sa.UUID(), nullable=False),
        sa.Column('markup_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.Enum('RASCUNHO', 'APROVADO', 'EM_PRODUCAO', 'ENTREGUE', 'CANCELADO', name='statuspedido'), nullable=False, server_default='RASCUNHO'),
        sa.Column('valor_total', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('data_entrega_prevista', sa.DateTime(), nullable=True),
        sa.Column('data_entrega_realizada', sa.DateTime(), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['markup_id'], ['markups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pedidos_numero'), 'pedidos', ['numero'])
    op.create_index(op.f('ix_pedidos_tenant_id'), 'pedidos', ['tenant_id'])

    # ── Pedido Itens (container série/personalizado) ─────────────────────────
    op.create_table('pedido_itens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('pedido_id', sa.UUID(), nullable=False),
        sa.Column('produto_id', sa.UUID(), nullable=True),
        sa.Column('nome_snapshot', sa.String(length=255), nullable=False),
        sa.Column('tipo_refeicao', sa.Enum('CAFE_MANHA', 'LANCHE_MANHA', 'ALMOCO', 'LANCHE_TARDE', 'JANTAR', name='tiporefeicao'), nullable=True),
        sa.Column('tipo', sa.Enum('SERIE', 'PERSONALIZADO', name='tipoitem'), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('preco_unitario', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('preco_total', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['produto_id'], ['produtos.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pedido_itens_pedido_id', 'pedido_itens', ['pedido_id'])

    # ── Pedido Item Composição (snapshot de ingredientes) ────────────────────
    op.create_table('pedido_item_composicoes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('pedido_item_id', sa.UUID(), nullable=False),
        sa.Column('ingrediente_id', sa.UUID(), nullable=False),
        sa.Column('ingrediente_nome_snap', sa.String(length=255), nullable=False),
        sa.Column('quantidade_g', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('custo_kg_snapshot', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('kcal_snapshot', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['pedido_item_id'], ['pedido_itens.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingrediente_id'], ['ingredientes.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pedido_item_composicoes_pedido_item_id', 'pedido_item_composicoes', ['pedido_item_id'])


def downgrade() -> None:
    op.drop_table('pedido_item_composicoes')
    op.drop_table('pedido_itens')
    op.drop_table('pedidos')
    op.drop_table('produto_composicoes')
    op.drop_table('produtos')
    op.drop_table('markup_indices')
    op.drop_table('ingredientes')
    op.drop_table('clientes')
    op.drop_table('nutricionistas')
    op.drop_constraint('fk_tenants_markup_padrao', 'tenants', type_='foreignkey')
    op.drop_column('tenants', 'markup_id_padrao')
    op.drop_table('markups')
    op.drop_table('indices_markup')
    op.drop_table('tenants')
