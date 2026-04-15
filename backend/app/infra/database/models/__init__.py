"""
Exporta todos os models para que o Alembic os enxergue automaticamente.

⚠️ IMPORTANTE: Todo novo model criado DEVE ser importado aqui.
Sem isso, o Alembic não detecta a tabela e não gera a migration.
"""

from app.infra.database.models.base import (  # noqa: F401
    Base,
    TimestampMixin,
    TenantScoped,
    TenantStatus,
    TenantPlano,
    UnidadeMedida,
    TipoRefeicao,
    StatusPedido,
    TipoItem,
)

from app.infra.database.models.tenant import Tenant  # noqa: F401
from app.infra.database.models.nutricionista import Nutricionista  # noqa: F401
from app.infra.database.models.cliente import Cliente  # noqa: F401
from app.infra.database.models.markup import IndiceMarkup, Markup, MarkupIndice  # noqa: F401
from app.infra.database.models.ingrediente import Ingrediente  # noqa: F401
from app.infra.database.models.produto import Produto  # noqa: F401
from app.infra.database.models.produto_composicao import ProdutoComposicao  # noqa: F401
from app.infra.database.models.pedido import Pedido  # noqa: F401
from app.infra.database.models.pedido_item import PedidoItem  # noqa: F401
from app.infra.database.models.pedido_item_composicao import PedidoItemComposicao  # noqa: F401
