
---

# 📖 Guia de Desenvolvimento: Arquitetura Hexagonal SaaS (Benedere)

## 1. Visão Geral da Arquitetura
Este projeto utiliza a **Hexagonal SaaS Architecture** (Ports and Adapters). O objetivo central é o **Isolamento de Domínio** e a **Blindagem de Tenants**.



### As 3 Camadas de Ouro:
1. **Domain (Coração):** Regras de negócio puras (Python puro). Não conhece banco de dados nem API.
2. **Infra (Detalhes):** Implementações técnicas (SQLAlchemy, PDF, Auth0).
3. **API (Interface):** Entrada de dados (FastAPI, Pydantic Schemas).

---

## 2. Estrutura de Pastas (The Blueprint)

```text
app/
├── api/             # Schemas (Pydantic) e Endpoints (FastAPI)
├── domain/          # Entities (Regras), Services (Fluxos), Exceptions
├── infra/           # Repository (SQL), Database (Models), Services (PDF/Email)
├── core/            # Configurações globais e Segurança (Auth0)
└── worker/          # Tarefas em background (Celery)
```

---

## 3. Regras de Ouro (The CTO Commandments)

### 🛡️ I. Blindagem de Tenant (Multi-tenancy)
* **Proibido:** Fazer queries no Repository sem o filtro de `tenant_id`.
* **Obrigatório:** Todo Repository deve receber `tenant_id` no construtor.
* **Fluxo de Contexto:** O `tenant_id` é extraído do JWT na camada de **API/Dependencies** e repassado para o Service, que o entrega ao Repository.

### 🧩 II. Independência de Domínio
* **Proibido:** Importar `sqlalchemy` ou `fastapi` dentro da pasta `app/domain/`.
* **Portas (Interfaces):** Defina o que o banco deve fazer em `app/domain/repositories/` usando classes abstratas (`ABC`).
* **Adaptadores (Implementação):** Escreva o SQL real em `app/infra/repository/`.

### 📦 III. Snapshots e Imutabilidade
* **Regra:** Pedidos e Orçamentos devem salvar cópias (snapshots) de preços, nomes e markups no momento da criação.
* **Por que?** Se o preço do ingrediente mudar no cadastro, o valor do pedido histórico não pode ser alterado.

---

## 4. Fluxo de uma Nova Feature
Para criar uma funcionalidade (ex: "Criar Pedido"), siga esta ordem:

1. **Domain/Entity:** Crie a classe `Pedido` com suas regras de cálculo e validação de status.
2. **Domain/Repository (Porta):** Defina o método `save(pedido)` na interface.
3. **Infra/Repository (Adaptador):** Implemente o `save` usando SQLAlchemy com filtro de `tenant_id`.
4. **Domain/Service:** Crie o `PedidoService` para orquestrar: `repo.get_cliente` -> `pedido.validar()` -> `repo.save()`.
5. **API/Schema:** Crie os Pydantic Models de Entrada e Saída.
6. **API/Endpoint:** Crie a rota FastAPI que recebe o Schema e chama o Service.



---

## 5. Checklist de Qualidade (Go-Live)
- [ ] O código passa no `make lint`?
- [ ] Existe teste de integração garantindo que o **Tenant A** não acessa dados do **Tenant B**?
- [ ] As exceções de negócio estão em `domain/exceptions`?
- [ ] O Service possui mais de 7 repositórios injetados? (Se sim, considere refatorar).

---

## 6. Comandos Úteis (Makefile)
* `make test`: Roda a pirâmide de testes.
* `make migrate`: Atualiza o esquema do banco de dados via Alembic.
* `make run`: Sobe o ambiente completo via Docker Compose.

---

### 🧠 Importante
> *"Trate o seu domínio como uma biblioteca privada. Ela deve funcionar perfeitamente mesmo que a internet (API) ou o HD (Banco) não existissem. Se você conseguir testar o cálculo de um pedido em um script simples de 5 linhas, sua arquitetura está correta."*

---