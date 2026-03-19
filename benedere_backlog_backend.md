# Benedere SaaS — Backlog Backend

> **Versão:** 1.0 • **Data:** Março 2026
> **Modelagem de referência:** `benedere_nova_modelagem_db.html` (v2)
>
> **Status:** ⬜ Pendente | 🔄 Em andamento | ✅ Concluído

---

## Épico 1 — Nova Modelagem de Banco de Dados

> Refatorar o schema do banco para suportar Produto (catálogo série), Pedido unificado (sem Orçamento separado) e snapshot de composição por item.

### US 1.1 — Criar enum e tabelas de catálogo

**Como** administrador do tenant, **quero** cadastrar produtos com receita padrão e tipo de refeição, **para que** eu possa reutilizá-los em pedidos de série.

| # | Task | SP | Status |
|---|------|----|--------|
| 1.1.1 | Criar enum PostgreSQL `tipo_refeicao` (cafe_manha, lanche_manha, almoco, lanche_tarde, jantar) | 1 | [ ] Pendente |
| 1.1.2 | Criar migration: tabela `produto` (id, tenant_id, nome, tipo_refeicao, peso_total_g, ativo) | 2 | ⬜ Pendente |
| 1.1.3 | Criar migration: tabela `produto_composicao` (id, produto_id, ingrediente_id, quantidade_g, ordem) | 2 | ⬜ Pendente |
| 1.1.4 | Remover tabelas legadas `orcamento` e `orcamento_item` (migration de drop com backup de dados) | 3 | ⬜ Pendente |
| | **Subtotal** | **8** | |

### US 1.2 — Criar tabelas de Pedido unificado

**Como** operador do sistema, **quero** que o pedido substitua o orçamento, **para que** o fluxo de venda tenha uma única entidade com status progressivo.

| # | Task | SP | Status |
|---|------|----|--------|
| 1.2.1 | Criar migration: tabela `pedido` (id, tenant_id, cliente_id, markup_id, status, valor_total, criado_em) | 2 | ⬜ Pendente |
| 1.2.2 | Criar migration: tabela `pedido_item` (id, pedido_id, produto_id nullable, nome_snapshot, tipo_refeicao, tipo, quantidade, preco_unitario, preco_total) | 3 | ⬜ Pendente |
| 1.2.3 | Criar migration: tabela `pedido_item_composicao` (id, pedido_item_id, ingrediente_id, ingrediente_nome_snap, quantidade_g, custo_kg_snapshot, kcal_snapshot) | 3 | ⬜ Pendente |
| 1.2.4 | Criar enum PostgreSQL `status_pedido` (rascunho, aprovado, em_producao, entregue, cancelado) | 1 | ⬜ Pendente |
| 1.2.5 | Criar enum PostgreSQL `tipo_item` (serie, personalizado) | 1 | ⬜ Pendente |
| | **Subtotal** | **10** | |

### US 1.3 — Migração de dados legados

**Como** devops, **quero** migrar os dados existentes de orçamento/pedido antigo para o novo schema, **para que** nenhum dado histórico seja perdido.

| # | Task | SP | Status |
|---|------|----|--------|
| 1.3.1 | Criar script de migração: orçamentos aprovados → pedidos (status=aprovado) | 5 | ⬜ Pendente |
| 1.3.2 | Criar script de migração: pedidos antigos → novo schema de pedido | 5 | ⬜ Pendente |
| 1.3.3 | Validar integridade pós-migração (contagem, valores totais, snapshots) | 3 | ⬜ Pendente |
| | **Subtotal** | **13** | |

---

## Épico 2 — Módulo Produto (Catálogo)

> CRUD completo de Produto com composição (receita padrão), seguindo o padrão Repository + Service + Endpoint.

### US 2.1 — CRUD de Produto

**Como** administrador do tenant, **quero** criar, listar, editar e desativar produtos do catálogo, **para que** eu tenha um portfólio de itens de série disponíveis.

| # | Task | SP | Status |
|---|------|----|--------|
| 2.1.1 | Criar model SQLAlchemy `Produto` com relacionamentos | 2 | ⬜ Pendente |
| 2.1.2 | Criar schemas Pydantic: `ProdutoCreate`, `ProdutoUpdate`, `ProdutoResponse`, `ProdutoListResponse` | 2 | ⬜ Pendente |
| 2.1.3 | Criar `ProdutoRepository` (list com paginação, get, create, update, soft_delete — todos filtrados por tenant_id) | 3 | ⬜ Pendente |
| 2.1.4 | Criar `ProdutoService` com validações de negócio | 2 | ⬜ Pendente |
| 2.1.5 | Criar endpoints REST: `GET /produtos`, `GET /produtos/{id}`, `POST /produtos`, `PUT /produtos/{id}`, `DELETE /produtos/{id}` | 3 | ⬜ Pendente |
| | **Subtotal** | **12** | |

### US 2.2 — Gestão de composição do produto (receita)

**Como** administrador do tenant, **quero** definir a receita de um produto (ingredientes + quantidades), **para que** o custo e peso sejam calculados automaticamente.

| # | Task | SP | Status |
|---|------|----|--------|
| 2.2.1 | Criar model SQLAlchemy `ProdutoComposicao` | 2 | ⬜ Pendente |
| 2.2.2 | Criar schemas Pydantic: `ProdutoComposicaoCreate`, `ProdutoComposicaoResponse` | 1 | ⬜ Pendente |
| 2.2.3 | Criar `ProdutoComposicaoRepository` | 2 | ⬜ Pendente |
| 2.2.4 | Implementar lógica no `ProdutoService`: criar produto com composição em batch, calcular peso_total_g automaticamente | 3 | ⬜ Pendente |
| 2.2.5 | Endpoint: `PUT /produtos/{id}/composicao` (substituição total da receita) | 2 | ⬜ Pendente |
| 2.2.6 | Endpoint: `GET /produtos/{id}/composicao` (lista ingredientes com custo calculado) | 2 | ⬜ Pendente |
| | **Subtotal** | **12** | |

---

## Épico 3 — Módulo Pedido (Unificado)

> Pedido com itens de série e personalizados, snapshot de composição, cálculo de preço via markup.

### US 3.1 — CRUD de Pedido

**Como** operador do sistema, **quero** criar e gerenciar pedidos com status progressivo, **para que** eu acompanhe o ciclo de vida da venda.

| # | Task | SP | Status |
|---|------|----|--------|
| 3.1.1 | Criar model SQLAlchemy `Pedido` com relacionamentos (cliente, markup, itens) | 2 | ⬜ Pendente |
| 3.1.2 | Criar schemas Pydantic: `PedidoCreate`, `PedidoUpdate`, `PedidoResponse`, `PedidoListResponse`, `PedidoResumo` | 3 | ⬜ Pendente |
| 3.1.3 | Criar `PedidoRepository` (list com paginação e filtros por status/cliente, get com eager load de itens) | 3 | ⬜ Pendente |
| 3.1.4 | Criar `PedidoService`: criação com resolução de markup (Pedido → Cliente → Tenant → null) | 3 | ⬜ Pendente |
| 3.1.5 | Endpoints REST: `GET /pedidos`, `GET /pedidos/{id}`, `POST /pedidos`, `PUT /pedidos/{id}`, `DELETE /pedidos/{id}` | 3 | ⬜ Pendente |
| 3.1.6 | Endpoint de transição de status: `PATCH /pedidos/{id}/status` com validação de máquina de estados | 3 | ⬜ Pendente |
| | **Subtotal** | **17** | |

### US 3.2 — Itens de série (explosão automática de composição)

**Como** operador, **quero** adicionar um produto de série ao pedido e ter a composição clonada automaticamente com snapshots de custo/kcal, **para que** o histórico financeiro fique protegido.

| # | Task | SP | Status |
|---|------|----|--------|
| 3.2.1 | Criar models `PedidoItem` e `PedidoItemComposicao` | 3 | ⬜ Pendente |
| 3.2.2 | Criar schemas: `PedidoItemCreate` (serie), `PedidoItemResponse`, `PedidoItemComposicaoResponse` | 2 | ⬜ Pendente |
| 3.2.3 | Implementar no `PedidoService`: ao adicionar item serie, clonar `produto_composicao` → `pedido_item_composicao` com snapshot de custo_por_kg e kcal do momento | 5 | ⬜ Pendente |
| 3.2.4 | Calcular `preco_unitario` = soma(custo_ingredientes) × fator_markup | 3 | ⬜ Pendente |
| 3.2.5 | Calcular `preco_total` = preco_unitario × quantidade | 1 | ⬜ Pendente |
| 3.2.6 | Recalcular `pedido.valor_total` a cada add/remove/update de item | 2 | ⬜ Pendente |
| | **Subtotal** | **16** | |

### US 3.3 — Itens personalizados (composição manual)

**Como** operador, **quero** montar uma marmita personalizada escolhendo ingredientes e quantidades, **para que** o cliente receba exatamente o que pediu.

| # | Task | SP | Status |
|---|------|----|--------|
| 3.3.1 | Criar schema `PedidoItemCreate` (personalizado): produto_id=null, nome livre, tipo_refeicao obrigatório, lista de composições | 2 | ⬜ Pendente |
| 3.3.2 | Implementar no `PedidoService`: validar que item personalizado tem pelo menos 1 ingrediente | 1 | ⬜ Pendente |
| 3.3.3 | Snapshot de custo/kcal no momento da criação (mesma lógica do série, mas sem clonar de catálogo) | 3 | ⬜ Pendente |
| 3.3.4 | Endpoint: `POST /pedidos/{id}/itens` (aceita tanto serie quanto personalizado via campo `tipo`) | 3 | ⬜ Pendente |
| 3.3.5 | Endpoint: `PUT /pedidos/{id}/itens/{item_id}` (editar composição enquanto status=rascunho) | 3 | ⬜ Pendente |
| 3.3.6 | Endpoint: `DELETE /pedidos/{id}/itens/{item_id}` (remover item e recalcular total) | 2 | ⬜ Pendente |
| | **Subtotal** | **14** | |

---

## Épico 4 — Limpeza Legada (Backend)

> Remover código de Orçamento e Pedido antigo do backend.

### US 4.1 — Remover módulo Orçamento

**Como** dev, **quero** eliminar todo o código de Orçamento do backend, **para que** não haja código morto no repositório.

| # | Task | SP | Status |
|---|------|----|--------|
| 4.1.1 | Remover model, schema, repository, service e endpoints de Orçamento | 2 | ⬜ Pendente |
| 4.1.2 | Remover model, schema, repository, service e endpoints de OrcamentoItem | 2 | ⬜ Pendente |
| 4.1.3 | Atualizar registros de rotas no `main.py` | 1 | ⬜ Pendente |
| 4.1.4 | Remover testes relacionados (se existirem) | 1 | ⬜ Pendente |
| | **Subtotal** | **6** | |

### US 4.2 — Remover módulo Pedido antigo

**Como** dev, **quero** remover o Pedido antigo (gerado a partir de orçamento), **para que** o novo módulo assuma completamente.

| # | Task | SP | Status |
|---|------|----|--------|
| 4.2.1 | Remover model, schema, repository, service e endpoints do Pedido antigo | 2 | ⬜ Pendente |
| 4.2.2 | Remover interfaces e tipos legados | 1 | ⬜ Pendente |
| | **Subtotal** | **3** | |

---

## Épico 5 — Testes Backend

> Cobertura de testes nos novos módulos para garantir integridade dos snapshots e cálculos.

### US 5.1 — Testes de Services

**Como** dev, **quero** testes automatizados nos services críticos, **para que** regressões sejam detectadas antes de irem pra produção.

| # | Task | SP | Status |
|---|------|----|--------|
| 5.1.1 | Setup de fixtures pytest: tenant, cliente, ingredientes, markup de teste | 3 | ⬜ Pendente |
| 5.1.2 | Testes `ProdutoService`: CRUD + composição + cálculo de peso | 3 | ⬜ Pendente |
| 5.1.3 | Testes `PedidoService`: criação com item serie (validar clonagem de composição e snapshots) | 5 | ⬜ Pendente |
| 5.1.4 | Testes `PedidoService`: criação com item personalizado (validar snapshots manuais) | 3 | ⬜ Pendente |
| 5.1.5 | Testes `PedidoService`: cálculo de preço (custo × markup), recálculo de valor_total | 3 | ⬜ Pendente |
| 5.1.6 | Testes `PedidoService`: máquina de estados de status (transições válidas e inválidas) | 3 | ⬜ Pendente |
| 5.1.7 | Teste de isolamento multi-tenant: tenant A não acessa dados de tenant B | 3 | ⬜ Pendente |
| | **Subtotal** | **23** | |

---

## Resumo Backend

| Épico | Descrição | US | Total SP |
|-------|-----------|:--:|---------:|
| 1 | Nova modelagem de banco | 3 | 31 |
| 2 | Módulo Produto (Catálogo) | 2 | 24 |
| 3 | Módulo Pedido (Unificado) | 3 | 47 |
| 4 | Limpeza legada | 2 | 9 |
| 5 | Testes | 1 | 23 |
| **Total** | | **11 US** | **134 SP** |

---

## Ordem de execução

```
Épico 1 (DB) → Épico 4 (Limpeza) → Épico 2 (Produto) → Épico 3 (Pedido) → Épico 5 (Testes)
```

> **Dependência crítica:** Épico 1 é pré-requisito de tudo. Épico 4 deve ser feito logo após pra evitar conflitos com código legado.
