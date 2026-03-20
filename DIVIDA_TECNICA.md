# Benedere SaaS — Dívida Técnica

> Registro de débitos técnicos identificados durante o desenvolvimento.
> Priorizar refatoração antes de ir pra produção.

---

## Auditoria de Services — Clean Architecture

> Revisão realizada em Março/2026. Critérios: separação de responsabilidades,
> acoplamento com infraestrutura, regras de domínio no lugar correto.

### Resultado por Service

| Service | Veredito | Problemas |
|---------|----------|-----------|
| `TenantService` | ✅ Limpo | CRUD + validações simples. Respeita camadas. |
| `NutricionistaService` | ✅ Limpo | CRUD + validação de CRN único. Sem lógica de domínio complexa. |
| `ClienteService` | ✅ Limpo | CRUD + validação de nutricionista. Sem acoplamento indevido. |
| `IngredienteService` | ✅ Limpo | CRUD + validação de markup. Sem regras complexas. |
| `MarkupService` | ⚠️ Leve | `calcular_fator_markup()` é regra de domínio pura, mas já está extraída como função isolada no mesmo arquivo. Aceitável. |
| `ProdutoService` | ⚠️ Médio | Cálculo de custo por item e instanciação de `ProdutoComposicao` (model SQLAlchemy) dentro do service. |
| `PedidoService` | 🔴 Gordo | Acesso direto à sessão, cálculo de preço, markup chain, máquina de estados, instanciação de models. |

---

## DT-001 — PedidoService "Fat Service"

**Severidade:** Alta
**Impacto:** Manutenibilidade, testabilidade unitária, Clean Architecture

### Problemas identificados

1. **Acesso direto à sessão** — `_session_add()` e `_session_flush()` furam a camada do repository
2. **Regras de domínio no service** — cálculo de preço (custo × markup), resolução da cadeia de markup, máquina de estados
3. **Instanciação de models** — cria `PedidoItem` e `PedidoItemComposicao` diretamente, acoplando com SQLAlchemy

### Refatoração proposta

**Domain Layer** (regras puras, sem infra):
- `PrecificacaoService` — calcula custo × markup, arredondamento. Recebe dados, retorna números.
- `StatusMachine` — valida transições de status. Classe ou dict com lógica encapsulada.
- `MarkupResolver` — resolve cadeia markup (pedido → cliente → tenant). Recebe objetos, retorna markup_id.

**Application Layer** (orquestração):
- `PedidoService` — apenas orquestra: chama repos, delega cálculos pro domain, persiste.

**Infra Layer**:
- Criar `PedidoItemRepository` — service não deve instanciar models nem acessar sessão diretamente.

### Arquivos afetados
- `app/domain/services/pedido_service.py` → quebrar em 4+ arquivos
- `app/infra/repository/` → novo `pedido_item_repository.py`
- `app/domain/` → novos domain services puros

### Estimativa: 8-13 SP

---

## DT-002 — ProdutoService — Lógica de domínio leve no service

**Severidade:** Média
**Impacto:** Testabilidade unitária

### Problemas identificados

1. **Cálculo de custo por item** — `listar_composicao()` faz `quantidade_g / 1000 × custo_unitario` inline. É regra de domínio.
2. **Instanciação de model** — `_salvar_composicao()` cria `ProdutoComposicao` diretamente.
3. **Cálculo de peso** — `_recalcular_peso()` soma quantidade_g da composição. Regra de domínio simples.

### Refatoração proposta

- Extrair cálculos pra um `ComposicaoDomainService` ou métodos na entidade.
- Mover instanciação de `ProdutoComposicao` pra `ProdutoComposicaoRepository`.

### Estimativa: 3-5 SP

---

## DT-003 — PDF endpoint desabilitado

**Severidade:** Baixa (feature não crítica)
**Impacto:** Funcionalidade de geração de PDF inoperante

### Problema
O endpoint de PDF (`app/api/v1/endpoints/pdf.py`) foi desabilitado no `main.py` porque dependia dos models legados (Orçamento + Pedido antigo).

### Refatoração proposta
Reescrever `pdf.py` e `pdf_generator.py` pra usar o novo schema de Pedido unificado.

### Estimativa: 5 SP

---

## DT-004 — kcal_snapshot sempre 0

**Severidade:** Baixa
**Impacto:** Campo de kcal não calculado nos snapshots

### Problema
O campo `kcal_snapshot` em `PedidoItemComposicao` e o cálculo de kcal em `ProdutoService.listar_composicao` sempre retornam 0. O modelo prevê armazenamento via JSONB (`Ingrediente.atributos`), mas não há lógica implementada.

### Refatoração proposta
Definir schema JSONB padrão pra atributos nutricionais e implementar cálculo: `(quantidade_g / 1000) × kcal_por_kg`.

### Estimativa: 3 SP

---

## DT-005 — Exceções de domínio duplicadas

**Severidade:** Baixa
**Impacto:** Manutenibilidade

### Problema
Exceções como `IngredienteNaoEncontradoError` e `MarkupNaoEncontradoError` estão definidas em múltiplos services (`IngredienteService`, `ProdutoService`, `PedidoService`). Se a mensagem mudar, precisa alterar em vários lugares.

### Refatoração proposta
Centralizar exceções de domínio em `app/domain/exceptions.py`.

### Estimativa: 2 SP

---

## Resumo

| ID | Descrição | Severidade | SP |
|----|-----------|-----------|---:|
| DT-001 | PedidoService Fat Service | Alta | 8-13 |
| DT-002 | ProdutoService lógica de domínio | Média | 3-5 |
| DT-003 | PDF endpoint desabilitado | Baixa | 5 |
| DT-004 | kcal_snapshot sempre 0 | Baixa | 3 |
| DT-005 | Exceções duplicadas | Baixa | 2 |
| **Total estimado** | | | **21-28 SP** |

> **Nota:** TenantService, NutricionistaService, ClienteService e IngredienteService estão limpos — CRUD simples sem violações de Clean Architecture. MarkupService tem `calcular_fator_markup()` como função isolada no mesmo arquivo, o que é aceitável.
