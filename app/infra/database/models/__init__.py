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
    TenantStatus,
    TenantPlano,
    UnidadeMedida,
    StatusOrcamento,
    StatusPedido,
)

from app.infra.database.models.tenant import Tenant  # noqa: F401
from app.infra.database.models.nutricionista import Nutricionista  # noqa: F401
from app.infra.database.models.cliente import Cliente  # noqa: F401
from app.infra.database.models.markup import IndiceMarkup, Markup, MarkupIndice  # noqa: F401
from app.infra.database.models.ingrediente import Ingrediente  # noqa: F401
from app.infra.database.models.orcamento import Orcamento, OrcamentoItem  # noqa: F401
from app.infra.database.models.pedido import Pedido, PedidoItem  # noqa: F401
