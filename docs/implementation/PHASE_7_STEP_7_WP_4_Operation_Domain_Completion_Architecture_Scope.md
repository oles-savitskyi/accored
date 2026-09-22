# Phase 7 — Step 7 — WP-4 Operation Domain Completion

## Architecture Scope

### 1. Scope Purpose

WP-4 завершает Register Operation Domain как единственную Register-scoped serialization boundary для consistency-sensitive операций Register domain.

Цель WP-4 — привести текущую реализацию в соответствие с утверждённой архитектурой:

* один логический `RegisterOperationDomain` на каждый Register;
* единая serialization boundary для mutation, rebuild и recovery;
* отсутствие конкурирующей per-Register serialization boundary внутри `TotalsMaintenanceCoordinator`;
* сохранение `TotalsMaintenanceCoordinator` как единственного владельца semantic maintenance state;
* сохранение изоляции операций разных Registers;
* отсутствие изменения утверждённых семантик Totals, persistence, mutation и recovery.

WP-4 является завершением operation-domain модели, а не пересмотром общей архитектуры Registers или Totals.

---

## 2. In Scope

### 2.1. Register Operation Domain

В WP-4 входит завершение `RegisterOperationDomain` как единственной точки Register-scoped serialization.

Domain должен:

* сериализовать consistency-sensitive операции одного Register;
* обеспечивать mutual exclusion между competing operations;
* применяться одинаково к mutation, rebuild и recovery;
* не создавать отдельного semantic state;
* не определять lifecycle или consistency state Register;
* не становиться владельцем Totals maintenance semantics.

Operation Domain отвечает только за вопрос:

> **какая consistency-sensitive операция данного Register может исполняться сейчас?**

---

### 2.2. Register Operation Domain Registry

В WP-4 входит завершение `RegisterOperationDomainRegistry` как structural composition boundary.

Registry должен обеспечивать:

* стабильное соответствие `Register identity → logical Operation Domain`;
* получение одного и того же logical domain для одного Register;
* получение независимых domains для разных Registers;
* использование одного Registry всеми соответствующими platform components.

Registry не должен рассматриваться только как технический cache locks.

Архитектурное требование:

> Компоненты, участвующие в Register-scoped consistency-sensitive operations, должны входить в существующий Operation Domain через общий `RegisterOperationDomainRegistry`.

Создание независимого per-component lock для того же Register не считается эквивалентной реализацией этой архитектуры.

---

### 2.3. Removal of Competing Coordinator Serialization

В WP-4 входит устранение собственной Register-scoped serialization boundary из `TotalsMaintenanceCoordinator`.

В частности, из Coordinator должна быть удалена ответственность за:

* хранение per-Register operation locks;
* создание per-Register lock map;
* самостоятельную сериализацию `apply`, `remove`, `rebuild` или других consistency-sensitive operations.

После WP-4 Coordinator может сохранять внутреннюю синхронизацию, необходимую исключительно для защиты собственного semantic state, если такая синхронизация не становится второй Register operation boundary.

Ключевое различие:

```text
RegisterOperationDomain
    → serialization of Register operations

TotalsMaintenanceCoordinator
    → semantic maintenance state
```

Наличие технической внутренней synchronization primitive само по себе не нарушает Scope, если она не является альтернативной Register-scoped operation boundary.

---

### 2.4. Mutation Integration

В WP-4 входит приведение mutation flow к единой Register Operation Domain boundary.

Для consistency-sensitive mutation:

```text
pre-validation
      │
      ▼
RegisterOperationDomain
      │
      ├── authoritative Movement Facts mutation
      │
      └── corresponding Totals maintenance mutation
```

В Scope входит:

* получение domain для Register через shared Registry;
* выполнение state-changing части mutation внутри этого domain;
* выполнение соответствующего Totals maintenance внутри того же domain;
* сохранение существующего mutation orchestration API;
* сохранение существующей validation semantics.

Предварительная validation, не изменяющая state, может оставаться за пределами domain.

Не входит в Scope перенос всей validation infrastructure внутрь Operation Domain без архитектурной необходимости.

---

### 2.5. Rebuild Integration

В WP-4 входит использование того же Register Operation Domain для rebuild.

Rebuild должен:

* получать domain через shared Registry;
* выполняться внутри domain;
* быть взаимоисключающим с mutation;
* быть взаимоисключающим с другим rebuild;
* быть взаимоисключающим с recovery.

В Scope не входит изменение semantic meaning rebuild.

Rebuild остаётся операцией восстановления/пересчёта derived Totals из authoritative Movement Facts согласно уже утверждённым контрактам.

---

### 2.6. Recovery Integration

В WP-4 входит использование того же Register Operation Domain для recovery.

Recovery должен:

* получать domain через shared Registry;
* выполняться внутри domain;
* быть взаимоисключающим с mutation;
* быть взаимоисключающим с rebuild;
* быть взаимоисключающим с другим recovery.

Recovery остаётся отдельной semantic operation.

WP-4 не меняет существующую модель failure/recovery semantics, определённую предыдущими этапами.

---

### 2.7. Semantic State Ownership

В Scope входит явное сохранение `TotalsMaintenanceCoordinator` как единственного semantic owner.

В его ответственности остаются:

* `TotalsMaintenanceState`;
* lifecycle state;
* consistency state;
* applied/maintenance bookkeeping;
* semantic maintenance outcomes;
* admission semantics;
* rebuild semantics;
* recovery semantics.

`RegisterOperationDomain` не получает:

* копию lifecycle state;
* копию consistency state;
* собственный recovery state;
* собственный applied state;
* альтернативную модель failure state.

---

### 2.8. Register Isolation

В Scope входит проверка и, при необходимости, исправление Register isolation.

Операции разных Registers должны иметь независимые operation domains:

```text
Register A → Domain A
Register B → Domain B
```

При этом:

```text
Domain A ≠ Domain B
```

и выполнение операции для Register A не должно требовать ожидания завершения consistency-sensitive операции Register B только из-за operation-domain serialization.

WP-4 не вводит global Register lock.

---

### 2.9. Operation-Domain Integration Points

В WP-4 подлежат проверке и при необходимости корректировке следующие integration points:

* `RegisterOperationDomain`;
* `RegisterOperationDomainRegistry`;
* `RegisterMutationOrchestrator`;
* `TotalsMaintenanceCoordinator`;
* mutation flow;
* rebuild flow;
* recovery flow;
* соответствующие public exports;
* unit/integration tests, проверяющие serialization и isolation.

Другие platform components затрагиваются только в том случае, если они непосредственно участвуют в Register-scoped consistency-sensitive operation flow.

---

## 3. Out of Scope

Следующие изменения не входят в WP-4.

### 3.1. Totals Semantic Redesign

Не изменяются:

* `TotalsDefinition`;
* `TotalsKey`;
* `TotalsEngine`;
* sign semantics;
* Decimal-only arithmetic;
* current total semantics;
* Balance query semantics;
* Balance result semantics.

WP-4 изменяет только способ сериализации операций вокруг уже существующей semantic model.

---

### 3.2. Persistence Architecture Redesign

Не изменяются:

* `RegisterFactPersistence` contract;
* authoritative Movement Facts model;
* persistence representation;
* persistence storage architecture;
* persistence recovery model.

Persistence остаётся authoritative source для Movement Facts.

---

### 3.3. Mutation API Redesign

Не входит:

* изменение public API `RegisterMutationOrchestrator`;
* изменение `establish` / `remove` semantics;
* изменение validation contract;
* введение нового mutation protocol;
* введение transaction abstraction.

Изменяется только operation-domain integration, необходимая для выполнения утверждённого Contract.

---

### 3.4. Failure-State Redesign

Не входит:

* новая failure state machine;
* новый recovery state model;
* изменение существующих `TotalsMaintenanceState` semantics;
* изменение WP-3 failure outcomes;
* введение второго failure authority в Operation Domain.

WP-4 должен сохранить существующую failure semantics.

---

### 3.5. Global Concurrency Infrastructure

Не входит:

* global Register lock;
* global maintenance lock;
* application-wide transaction coordinator;
* новый concurrency framework;
* scheduler;
* queue;
* worker pool;
* fairness policy;
* priority policy.

WP-4 гарантирует mutual exclusion для одного Register и isolation между разными Registers, но не определяет scheduling policy.

---

### 3.6. Persistence Transactions

WP-4 не вводит:

* database transactions;
* distributed transactions;
* two-phase commit;
* rollback protocol;
* generic transactional abstraction.

Operation Domain является serialization boundary, а не transaction boundary.

---

### 3.7. Inventory Integration

Не входит изменение Inventory-specific behavior.

Inventory остаётся downstream consumer Register movement semantics и не получает специальной serialization model в рамках WP-4.

---

### 3.8. Public Domain Model Expansion

Не входит добавление новых business/domain concepts только ради WP-4.

В частности, не вводятся:

* новый Register lifecycle entity;
* новый consistency entity;
* новый recovery entity;
* новый transaction entity.

---

## 4. Required Structural Changes

WP-4 считается архитектурно выполненным только при наличии следующих structural properties.

### 4.1. Single Register Serialization Boundary

Для каждого Register существует одна logical operation serialization boundary.

```text
Register
   │
   ▼
RegisterOperationDomain
   │
   ├── mutation
   ├── rebuild
   └── recovery
```

---

### 4.2. No Competing Coordinator Lock

`TotalsMaintenanceCoordinator` не содержит отдельной Register-scoped operation lock model, конкурирующей с Operation Domain.

Недопустимая структура:

```text
Operation Domain lock
        │
        ▼
Maintenance Coordinator lock
```

Целевая структура:

```text
Operation Domain
        │
        ▼
TotalsMaintenanceCoordinator
```

При этом Coordinator сохраняет только необходимую для собственного semantic state внутреннюю synchronization logic, если она не создаёт вторую operation boundary.

---

### 4.3. Shared Registry Composition

Mutation, rebuild и recovery должны использовать один architectural composition boundary:

```text
RegisterOperationDomainRegistry
          │
     ┌────┼────┐
     ▼    ▼    ▼
 mutation rebuild recovery
     │    │    │
     └────┴────┘
          │
      same domain
```

---

### 4.4. Complete Mutation Boundary

State-changing части mutation не должны быть разделены между разными serialization contexts.

Недопустимо:

```text
Domain
  │
  └── Totals mutation

outside Domain
  │
  └── Movement Facts mutation
```

Требуется:

```text
Domain
  ├── Movement Facts mutation
  └── Totals mutation
```

---

## 5. Behavioral Verification Scope

WP-4 должен проверять следующие операции одного Register:

| Operation A | Operation B | Required behavior  |
| ----------- | ----------- | ------------------ |
| mutation    | mutation    | mutually exclusive |
| mutation    | rebuild     | mutually exclusive |
| mutation    | recovery    | mutually exclusive |
| rebuild     | rebuild     | mutually exclusive |
| rebuild     | recovery    | mutually exclusive |
| recovery    | recovery    | mutually exclusive |

Для разных Registers:

| Register A | Register B | Required behavior |
| ---------- | ---------- | ----------------- |
| mutation   | mutation   | independent       |
| mutation   | rebuild    | independent       |
| mutation   | recovery   | independent       |
| rebuild    | rebuild    | independent       |
| rebuild    | recovery   | independent       |
| recovery   | recovery   | independent       |

Проверка должна подтверждать не только отсутствие race conditions, но и наличие **одной общей serialization boundary** для операций одного Register.

---

## 6. Structural Verification Scope

Помимо behavioral tests, WP-4 должен проверить архитектурные structural properties.

Проверяются:

1. `RegisterOperationDomainRegistry` возвращает стабильный domain для одного Register.
2. Разные Registers получают независимые domains.
3. `TotalsMaintenanceCoordinator` не содержит competing Register-scoped lock model.
4. Mutation использует shared Registry.
5. Rebuild использует shared Registry.
6. Recovery использует shared Registry.
7. Operation Domain не хранит semantic lifecycle/consistency state.
8. `TotalsMaintenanceCoordinator` остаётся semantic state owner.
9. Existing WP-3 failure semantics сохраняются.
10. State-changing mutation actions находятся внутри единой Register Operation Domain boundary.

---

## 7. Compatibility Scope

WP-4 должен сохранять совместимость с уже утверждёнными Phase 7 semantics.

В частности, не должны измениться:

* Movement Facts semantics;
* Totals semantics;
* Balance semantics;
* maintenance lifecycle semantics;
* maintenance failure semantics;
* rebuild semantics;
* recovery semantics;
* public mutation semantics;
* Register identity semantics.

Если для выполнения WP-4 потребуется изменить существующую semantic contract, это должно рассматриваться как отдельное архитектурное решение, а не как скрытая часть WP-4 implementation.

---

## 8. Implementation Boundary

WP-4 implementation должна быть ограничена следующими типами изменений:

* изменение ownership of Register-scoped serialization;
* удаление competing serialization из Coordinator;
* интеграция mutation/rebuild/recovery с shared Operation Domain;
* корректировка component composition;
* добавление/изменение соответствующих tests;
* минимальные public exports, если они необходимы для утверждённой архитектуры.

Не допускается расширение WP-4 за счёт unrelated cleanup или speculative refactoring.

---

## 9. Acceptance Scope

WP-4 считается завершённым, если одновременно выполнены следующие условия:

### Architecture

* существует одна logical Register-scoped serialization boundary;
* Operation Domain является этой boundary;
* shared Registry является structural composition boundary;
* Coordinator остаётся единственным semantic state owner;
* different Registers сохраняют isolation.

### Implementation

* mutation использует Operation Domain;
* rebuild использует Operation Domain;
* recovery использует Operation Domain;
* competing Register-scoped lock в Coordinator устранён;
* state-changing mutation actions выполняются внутри единого domain.

### Verification

* все шесть same-Register operation combinations проверены;
* Register isolation проверена;
* shared domain identity проверена;
* отсутствие competing Coordinator serialization проверено;
* semantic state ownership проверено;
* WP-3 failure semantics regression-tested.

### Scope Discipline

* Totals semantics не изменены;
* persistence architecture не изменена;
* mutation public contract не изменён без необходимости;
* transaction infrastructure не добавлена;
* global lock не введён;
* Inventory-specific behavior не изменён.

---

## 10. WP-4 Deliverables

WP-4 должен привести к следующим результатам:

1. завершённый `RegisterOperationDomain` integration model;
2. shared `RegisterOperationDomainRegistry` composition;
3. единая serialization boundary для mutation/rebuild/recovery;
4. устранённая competing Register-scoped serialization в `TotalsMaintenanceCoordinator`;
5. сохранённое semantic state ownership Coordinator;
6. подтверждённая Register isolation;
7. tests для behavioral и structural guarantees;
8. обновлённая документация Step 7, если implementation выявит необходимость уточнения уже утверждённых architectural statements.

---

## 11. Explicit Non-Goals

Для предотвращения scope creep WP-4 явно не решает:

* fairness;
* operation priority;
* scheduling;
* transactionality;
* persistence rollback;
* distributed coordination;
* cross-Register consistency;
* Totals algorithm redesign;
* Balance redesign;
* Inventory behavior redesign;
* generic concurrency abstraction.

Эти вопросы могут быть предметом отдельных архитектурных решений, но не являются частью Operation Domain Completion.

---

## 12. Scope Completion Criterion

WP-4 завершён архитектурно тогда, когда Register-scoped serialization перестаёт быть распределённой ответственностью между несколькими компонентами и становится единой responsibility `RegisterOperationDomain`, при этом semantic maintenance state остаётся полностью принадлежащим `TotalsMaintenanceCoordinator`.

Итоговая модель:

```text
                 RegisterOperationDomainRegistry
                              │
                 ┌────────────┴────────────┐
                 │                         │
             Register A                Register B
                 │                         │
              Domain A                  Domain B
                 │                         │
        ┌────────┼────────┐        ┌───────┼────────┐
        │        │        │        │       │        │
    mutation  rebuild  recovery  mutation rebuild recovery
        │        │        │        │       │        │
        └────────┼────────┘        └───────┼────────┘
                 │                         │
                 ▼                         ▼
      TotalsMaintenanceCoordinator A   Coordinator B
                 │                         │
          semantic state              semantic state
```

Ключевой architectural result:

> **One Register → one Operation Domain → one serialization boundary.**
>
> **One Coordinator → one semantic maintenance state owner.**
>
> **Different Registers → independent operation domains.**

## 13. Coordinator Synchronization Boundary

TotalsMaintenanceCoordinator may retain internal synchronization required to protect atomic access or transitions of its own semantic maintenance state. Such synchronization is strictly an implementation mechanism for state protection and MUST NOT constitute, reproduce, or compete with the Register-scoped Operation Domain.

The Coordinator MUST NOT use its internal synchronization as the admission, ordering, or mutual-exclusion boundary for complete Register-scoped operations. Mutation, rebuild, and recovery MUST be serialized exclusively by RegisterOperationDomain.

The existence of a synchronization primitive inside the Coordinator is not itself an architectural violation; its role as a competing Register-scoped operation boundary is.


---

# WP-9 Documentation Reconciliation Note

This document has been reconciled against the implemented Phase 7 Step 7 state through WP-8. Normative architecture and API semantics are preserved; historical planning statements are retained only where they describe the design sequence. Current implementation status is authoritative for completion claims.

Final cross-work-package invariants: `RegisterOperationDomain` owns Register-scoped serialization; `TotalsMaintenanceCoordinator` owns maintenance semantics and lifecycle/consistency state; authoritative Movement Facts come from `RegisterFactPersistence`; derived Totals come from `TotalsEngine`; Movement Query and Balance Query remain read-side capabilities; the public API boundary is `accore.platform.registers`; WP-8 integration tests verify composition of these capabilities.
