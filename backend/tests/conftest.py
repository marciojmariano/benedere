"""
Fixtures compartilhadas — banco de teste, session, tenant, dados base.
Task: 5.1.1

Usa o banco de dev existente (tabelas já criadas via Alembic).
Cada teste roda dentro de uma transação com SAVEPOINT + rollback.
"""
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.infra.database.models.base import (
    Base,
    TenantPlano,
    TenantStatus,
    UnidadeMedida,
    TipoRefeicao,
)
from app.infra.database.models.tenant import Tenant
from app.infra.database.models.cliente import Cliente
from app.infra.database.models.ingrediente import Ingrediente
from app.infra.database.models.markup import Markup
from app.infra.database.models.produto import Produto
from app.infra.database.models.produto_composicao import ProdutoComposicao


# ── Engine de teste ──────────────────────────────────────────────────────────

engine = create_async_engine(settings.DATABASE_URL, echo=False)


# ── Fixtures de infraestrutura ───────────────────────────────────────────────

@pytest_asyncio.fixture
async def session():
    """
    Escopo de função: Cada teste ganha uma sessão limpa.
    Implementa o padrão de transação aninhada para isolamento total.
    Session com SAVEPOINT — cada teste roda isolado.
    Usa begin_nested() (SAVEPOINT) pra rollback sem afetar o banco.
    As tabelas já existem via Alembic — não precisa de create_all.
    """
    # 1. Abrimos uma conexão dedicada para este teste
    async with engine.connect() as conn:
        trans = await conn.begin()
        
        # Criamos a sessão com autoflush=False
        async_session = AsyncSession(
            bind=conn, 
            expire_on_commit=False,
            autoflush=False  # CRÍTICO: Impede que queries disparem flushes concorrentes
        )

        try:
            yield async_session
        finally:
            await async_session.close()
            await trans.rollback()


# ── Fixtures de dados ────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def tenant(session: AsyncSession) -> Tenant:
    t = Tenant(
        id=uuid.uuid4(), # ID já definido aqui, não depende do DB
        nome="Tenant Teste",
        slug=f"teste-{uuid.uuid4().hex[:8]}",
        email_dono="teste@benedere.local",
        plano=TenantPlano.FREE,
        status=TenantStatus.ATIVO,
        ativo=True,
    )
    session.add(t)
    # Não precisamos de flush aqui se o service apenas associar o ID.
    return t


@pytest_asyncio.fixture
async def tenant_b(session: AsyncSession) -> Tenant:
    t = Tenant(
        id=uuid.uuid4(),
        nome="Tenant B",
        slug=f"tenant-b-{uuid.uuid4().hex[:8]}",
        email_dono="b@benedere.local",
        plano=TenantPlano.FREE,
        status=TenantStatus.ATIVO,
        ativo=True,
    )
    session.add(t)
    await session.flush()
    return t


@pytest_asyncio.fixture
async def cliente(session: AsyncSession, tenant: Tenant) -> Cliente:
    c = Cliente(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        nome="Cliente Teste",
        email="cliente@teste.com",
        ativo=True,
    )
    session.add(c)
    await session.flush()
    return c


@pytest_asyncio.fixture
async def ingredientes(session: AsyncSession, tenant: Tenant) -> dict[str, Ingrediente]:
    dados = [
        ("Purê de Batata Baroa", Decimal("25.0000")),
        ("Ragu de Carne", Decimal("45.0000")),
        ("Mussarela de Búfala", Decimal("89.9000")),
        ("Queijo Parmesão Ralado", Decimal("120.0000")),
    ]
    result = {}
    for nome, custo in dados:
        ing = Ingrediente(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            nome=nome,
            unidade_medida=UnidadeMedida.KG,
            custo_unitario=custo,
            ativo=True,
        )
        session.add(ing)
        result[nome] = ing

    # O flush aqui é opcional. Se remover, os testes ficam mais estáveis.
    return result


@pytest_asyncio.fixture
async def markup(session: AsyncSession, tenant: Tenant) -> Markup:
    m = Markup(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        nome="Markup Teste",
        fator=Decimal("1.8182"),
        ativo=True,
    )
    session.add(m)
    await session.flush()
    return m


@pytest_asyncio.fixture
async def produto_com_composicao(
    session: AsyncSession,
    tenant: Tenant,
    ingredientes: dict[str, Ingrediente],
) -> Produto:
    produto = Produto(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        nome="Escondidinho de Ragu",
        tipo_refeicao=TipoRefeicao.ALMOCO,
        peso_total_g=200,
        ativo=True,
    )
    session.add(produto)
    await session.flush()

    composicao = [
        ("Purê de Batata Baroa", 100),
        ("Ragu de Carne", 85),
        ("Mussarela de Búfala", 10),
        ("Queijo Parmesão Ralado", 5),
    ]
    for ordem, (nome, qtd) in enumerate(composicao):
        comp = ProdutoComposicao(
            id=uuid.uuid4(),
            produto_id=produto.id,
            ingrediente_id=ingredientes[nome].id,
            quantidade_g=qtd,
            ordem=ordem,
        )
        session.add(comp)

    await session.flush()
    return produto
