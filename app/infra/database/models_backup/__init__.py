"""
Exporta todos os models para que o Alembic os enxergue automaticamente.

⚠️ IMPORTANTE: Todo novo model criado DEVE ser importado aqui.
Sem isso, o Alembic não detecta a tabela e não gera a migration.

No env.py do Alembic, basta importar este __init__:
    from app.infra.database.models import Base  # noqa: F401
"""

from app.infra.database.models.base import (  # noqa: F401
    Base,
    TimestampMixin,
    TenantScoped,
    # Enums existentes
    TenantStatus,
    TenantPlano,
    UnidadeMedida,
    StatusOrcamento,      # LEGADO — manter até Épico 1 US 1.3
    # Enums novos (Refatoração v2)
    TipoRefeicao,
    StatusPedido,
    TipoItem,
)

# ── Models existentes ────────────────────────────────────────────────────────
from app.infra.database.models.tenant import Tenant  # noqa: F401
from app.infra.database.models.nutricionista import Nutricionista  # noqa: F401
from app.infra.database.models.cliente import Cliente  # noqa: F401
from app.infra.database.models.markup import IndiceMarkup, Markup, MarkupIndice  # noqa: F401
from app.infra.database.models.ingrediente import Ingrediente  # noqa: F401

# ── Models LEGADOS (manter até migração de dados — Épico 1 US 1.3) ──────────
from app.infra.database.models.orcamento import Orcamento, OrcamentoItem  # noqa: F401
from app.infra.database.models.pedido import Pedido as PedidoLegado, PedidoItem as PedidoItemLegado  # noqa: F401

# ── Models NOVOS (Refatoração v2) ────────────────────────────────────────────
from app.infra.database.models.produto import Produto  # noqa: F401
from app.infra.database.models.produto_composicao import ProdutoComposicao  # noqa: F401
from app.infra.database.models.pedido_v2 import Pedido  # noqa: F401
from app.infra.database.models.pedido_item import PedidoItem  # noqa: F401
from app.infra.database.models.pedido_item_composicao import PedidoItemComposicao  # noqa: F401
