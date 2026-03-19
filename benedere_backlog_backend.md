# Benedere SaaS — Backlog Backend

> **Versão:** 1.3 • **Data:** Março 2026
> **Modelagem de referência:** `benedere_nova_modelagem_db.html` (v2)
>
> **Status:** ⬜ Pendente | 🔄 Em andamento | ✅ Concluído | 🚫 Eliminada

---

## Épico 1 — Nova Modelagem de Banco de Dados ✅

> Banco recriado do zero. Migration única consolidada.

### US 1.1 — Criar enum e tabelas de catálogo ✅

| # | Task | SP | Status |
|---|------|----|--------|
| 1.1.1 | Criar enum PostgreSQL `tipo_refeicao` | 1 | ✅ Concluído |
| 1.1.2 | Criar migration: tabela `produto` | 2 | ✅ Concluído |
| 1.1.3 | Criar migration: tabela `produto_composicao` | 2 | ✅ Concluído |
| 1.1.4 | Remover tabelas legadas `orcamento` e `orcamento_item` | 3 | ✅ Concluído |
| | **Subtotal** | **8** | |

### US 1.2 — Criar tabelas de Pedido unificado ✅

| # | Task | SP | Status |
|---|------|----|--------|
| 1.2.1 | Criar migration: tabela `pedido` | 2 | ✅ Concluído |
| 1.2.2 | Criar migration: tabela `pedido_item` | 3 | ✅ Concluído |
| 1.2.3 | Criar migration: tabela `pedido_item_composicao` | 3 | ✅ Concluído |
| 1.2.4 | Criar enum PostgreSQL `status_pedido` | 1 | ✅ Concluído |
| 1.2.5 | Criar enum PostgreSQL `tipo_item` | 1 | ✅ Concluído |
| | **Subtotal** | **10** | |

### US 1.3 — Migração de dados legados 🚫

| # | Task | SP | Status |
|---|------|----|--------|
| 1.3.1 | ~~Migração orçamentos → pedidos~~ | 5 | 🚫 Eliminada |
| 1.3.2 | ~~Migração pedidos antigos~~ | 5 | 🚫 Eliminada |
| 1.3.3 | ~~Validar integridade~~ | 3 | 🚫 Eliminada |
| | **Subtotal** | **0** | |

---

## Épico 2 — Módulo Produto (Catálogo) ✅

### US 2.1 — CRUD de Produto ✅

| # | Task | SP | Status |
|---|------|----|--------|
| 2.1.1 | Model SQLAlchemy `Produto` | 2 | ✅ Concluído |
| 2.1.2 | Schemas Pydantic Produto | 2 | ✅ Concluído |
| 2.1.3 | `ProdutoRepository` | 3 | ✅ Concluído |
| 2.1.4 | `ProdutoService` | 2 | ✅ Concluído |
| 2.1.5 | Endpoints REST Produto | 3 | ✅ Concluído |
| | **Subtotal** | **12** | |

### US 2.2 — Gestão de composição do produto (receita) ✅

| # | Task | SP | Status |
|---|------|----|--------|
| 2.2.1 | Model SQLAlchemy `ProdutoComposicao` | 2 | ✅ Concluído |
| 2.2.2 | Schemas Pydantic ProdutoComposicao | 1 | ✅ Concluído |
| 2.2.3 | `ProdutoComposicaoRepository` | 2 | ✅ Concluído |
| 2.2.4 | Lógica de composição em batch + cálculo peso_total_g | 3 | ✅ Concluído |
| 2.2.5 | Endpoint `PUT /produtos/{id}/composicao` | 2 | ✅ Concluído |
| 2.2.6 | Endpoint `GET /produtos/{id}/composicao` | 2 | ✅ Concluído |
| | **Subtotal** | **12** | |

---

## Épico 3 — Módulo Pedido (Unificado) ✅

### US 3.1 — CRUD de Pedido ✅

| # | Task | SP | Status |
|---|------|----|--------|
| 3.1.1 | Model SQLAlchemy `Pedido` | 2 | ✅ Concluído |
| 3.1.2 | Schemas Pydantic Pedido | 3 | ✅ Concluído |
| 3.1.3 | `PedidoRepository` com eager load e filtros | 3 | ✅ Concluído |
| 3.1.4 | `PedidoService` com resolução de markup | 3 | ✅ Concluído |
| 3.1.5 | Endpoints REST Pedido | 3 | ✅ Concluído |
| 3.1.6 | Transição de status com máquina de estados | 3 | ✅ Concluído |
| | **Subtotal** | **17** | |

### US 3.2 — Itens de série (explosão automática) ✅

| # | Task | SP | Status |
|---|------|----|--------|
| 3.2.1 | Models `PedidoItem` e `PedidoItemComposicao` | 3 | ✅ Concluído |
| 3.2.2 | Schemas PedidoItem serie | 2 | ✅ Concluído |
| 3.2.3 | Clonagem composição catálogo → snapshot | 5 | ✅ Concluído |
| 3.2.4 | Cálculo `preco_unitario` = custo × markup | 3 | ✅ Concluído |
| 3.2.5 | Cálculo `preco_total` = unitário × quantidade | 1 | ✅ Concluído |
| 3.2.6 | Recálculo `pedido.valor_total` | 2 | ✅ Concluído |
| | **Subtotal** | **16** | |

### US 3.3 — Itens personalizados (composição manual) ✅

| # | Task | SP | Status |
|---|------|----|--------|
| 3.3.1 | Schema PedidoItem personalizado | 2 | ✅ Concluído |
| 3.3.2 | Validação mínimo 1 ingrediente | 1 | ✅ Concluído |
| 3.3.3 | Snapshot custo/kcal manual | 3 | ✅ Concluído |
| 3.3.4 | Endpoint `POST /pedidos/{id}/itens` | 3 | ✅ Concluído |
| 3.3.5 | Endpoint `PUT /pedidos/{id}/itens/{item_id}` | 3 | ✅ Concluído |
| 3.3.6 | Endpoint `DELETE /pedidos/{id}/itens/{item_id}` | 2 | ✅ Concluído |
| | **Subtotal** | **14** | |

---

## Épico 4 — Limpeza Legada (Backend) ✅

### US 4.1 — Remover módulo Orçamento ✅

| # | Task | SP | Status |
|---|------|----|--------|
| 4.1.1 | Remover model, schema, repository, service e endpoints de Orçamento | 2 | ✅ Concluído |
| 4.1.2 | Remover model, schema, repository, service e endpoints de OrcamentoItem | 2 | ✅ Concluído |
| 4.1.3 | Atualizar registros de rotas no `main.py` | 1 | ✅ Concluído |
| 4.1.4 | Remover testes relacionados | 1 | ✅ Concluído |
| | **Subtotal** | **6** | |

### US 4.2 — Remover módulo Pedido antigo ✅

| # | Task | SP | Status |
|---|------|----|--------|
| 4.2.1 | Remover model, schema, repository, service e endpoints do Pedido antigo | 2 | ✅ Concluído |
| 4.2.2 | Remover interfaces e tipos legados | 1 | ✅ Concluído |
| | **Subtotal** | **3** | |

---

## Épico 5 — Testes Backend

> Cobertura de testes nos novos módulos.

### US 5.1 — Testes de Services

| # | Task | SP | Status |
|---|------|----|--------|
| 5.1.1 | Setup de fixtures pytest | 3 | ⬜ Pendente |
| 5.1.2 | Testes `ProdutoService`: CRUD + composição + peso | 3 | ⬜ Pendente |
| 5.1.3 | Testes `PedidoService`: item serie (clonagem + snapshots) | 5 | ⬜ Pendente |
| 5.1.4 | Testes `PedidoService`: item personalizado (snapshots manuais) | 3 | ⬜ Pendente |
| 5.1.5 | Testes `PedidoService`: cálculo preço + recálculo valor_total | 3 | ⬜ Pendente |
| 5.1.6 | Testes `PedidoService`: máquina de estados | 3 | ⬜ Pendente |
| 5.1.7 | Teste isolamento multi-tenant | 3 | ⬜ Pendente |
| | **Subtotal** | **23** | |

---

## Resumo Backend

| Épico | Descrição | US | SP Total | SP Concluído | Progresso |
|-------|-----------|:--:|--------:|------------:|----------:|
| 1 | Nova modelagem de banco | 3 | 18 | 18 | 100% |
| 2 | Módulo Produto (Catálogo) | 2 | 24 | 24 | 100% |
| 3 | Módulo Pedido (Unificado) | 3 | 47 | 47 | 100% |
| 4 | Limpeza legada | 2 | 9 | 9 | 100% |
| 5 | Testes | 1 | 23 | 0 | 0% |
| **Total** | | **11 US** | **121 SP** | **98 SP** | **81%** |

---

## Apontamento de horas

> **18/03/2026: 23:30 - 23:59 (00:30)**
> **19/03/2026  00:00 - 02:40 (02:40)**
> **19/03/2026: 12:40 - 13:40 (01:00)**
---
> **Total de horas trabalhadas: 04:10**

---

## Ordem de execução

```
✅ Épico 1 (DB) → ✅ Épico 4 (Limpeza) → ✅ Épico 2 (Produto) → ✅ Épico 3 (Pedido) → Épico 5 (Testes)
```

> **Próximo:** Épico 5 — Testes, ou iniciar o Frontend.
