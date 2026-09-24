# Phase 7 Step 8 — Inventory Register Completion — Concrete API Design

## 1. Purpose

This document defines the concrete public and internal API required to complete the Inventory Register as a Standard Register Configuration over the existing generic Register Platform.

The design translates the approved Phase 7 Step 8 architecture into concrete Python interfaces, data structures, composition boundaries, and integration behavior.

The implementation must not introduce an Inventory-specific register engine, persistence layer, totals engine, maintenance coordinator, recovery service, or balance engine.

Inventory remains a Standard Configuration of the generic Register Platform.

---

# 2. Design Principles

The implementation shall preserve the following principles:

1. **Generic Register Platform owns register mechanics.**
2. **Inventory owns only Inventory-specific semantics and configuration.**
3. **Movement Facts are authoritative.**
4. **Totals and Balance are derived state.**
5. **Posting creates generic `Movement` objects.**
6. **Register mutation is performed through the generic mutation API.**
7. **Totals maintenance is performed through the generic maintenance API.**
8. **Persistence is performed through the generic fact persistence API.**
9. **Queries use the generic movement and balance query services.**
10. **Rebuild and recovery remain generic platform capabilities.**
11. **Inventory configuration remains declarative.**
12. **No Inventory-specific branches are added to generic Register Platform code.**

---

# 3. Concrete Module Structure

The Inventory-specific register configuration shall be introduced under:

```text
src/standard/registers/
    __init__.py
    inventory.py
```

The existing Goods Receipt posting implementation remains under:

```text
src/standard/posting/
    goods_receipt.py
    inventory.py
```

The generic Register Platform remains under:

```text
src/accore/platform/registers/
```

The generic posting integration remains under:

```text
src/accore/platform/posting/
```

The intended dependency direction is:

```text
standard.registers.inventory
        ↓
accore.platform.registers
        ↓
generic Register Platform

standard.posting.goods_receipt
        ↓
standard.registers.inventory
        ↓
generic Movement
```

Standard Configuration may depend on generic platform contracts.

Generic platform code must not depend on `standard.registers.inventory`.

---

# 4. Inventory Register Identity

The Inventory register identity shall be defined once in the Inventory register configuration module.

```python
INVENTORY_REGISTER_ID = Identifier.from_str(
    "01ARZ3NDEKTSV4RRFFQ69G5FAT"
)
```

This constant becomes the authoritative Inventory register identity.

The existing definition in:

```text
src/standard/posting/goods_receipt.py
```

shall be removed.

Goods Receipt shall import the authoritative constant from the Inventory register configuration.

---

# 5. Inventory Dimension Names

The Inventory register shall define the following dimension names:

```python
INVENTORY_PRODUCT_DIMENSION = "product"
INVENTORY_WAREHOUSE_DIMENSION = "warehouse"
```

These names are part of Inventory register semantics.

They shall not be duplicated independently across posting and register modules.

Goods Receipt shall import these constants when constructing movements.

---

# 6. Inventory Resource Name

The Inventory quantity resource shall be defined as:

```python
INVENTORY_QUANTITY_RESOURCE = "quantity"
```

The resource represents a Decimal quantity.

No Inventory-specific quantity value object shall be introduced in Step 8.

The existing generic `MovementResources` abstraction remains responsible for representing movement resources.

---

# 7. Inventory Quantity Type

Inventory quantity shall use:

```python
Decimal
```

as its resource type.

The Inventory register shall not use:

```python
float
```

for quantity.

The Totals Definition shall explicitly declare `Decimal` as the supported resource type.

The existing generic Totals Engine remains responsible for arithmetic and accumulation.

---

# 8. Inventory Movement Semantics

The Inventory register supports two movement types:

```text
MovementType.INCOME  → +Quantity
MovementType.EXPENSE → -Quantity
```

Therefore the Inventory totals definition shall contain:

```python
{
    MovementType.INCOME: Decimal("1"),
    MovementType.EXPENSE: Decimal("-1"),
}
```

or the equivalent existing `TotalsDefinition` representation.

This is a register-level semantic definition.

It is independent of the specific document posting operation.

---

# 9. Goods Receipt Movement Semantics

Goods Receipt currently represents an inventory increase.

Therefore:

```python
GOODS_RECEIPT_MOVEMENT_TYPE = MovementType.INCOME
```

shall remain the Goods Receipt-specific mapping.

The distinction is intentional:

```text
InventoryRegisterPostingContract
    supports:
        INCOME
        EXPENSE

GoodsReceiptPostingHandler
    produces:
        INCOME
```

This allows future Inventory decrease operations to use the same Inventory register without changing the register contract.

---

# 10. Inventory Totals Definition

The Inventory register shall expose a factory function:

```python
def inventory_totals_definition() -> TotalsDefinition:
    ...
```

The returned definition shall specify:

```python
TotalsDefinition(
    register_identity=INVENTORY_REGISTER_ID,
    dimensions=(
        INVENTORY_PRODUCT_DIMENSION,
        INVENTORY_WAREHOUSE_DIMENSION,
    ),
    resource_name=INVENTORY_QUANTITY_RESOURCE,
    movement_type_signs={
        MovementType.INCOME: Decimal("1"),
        MovementType.EXPENSE: Decimal("-1"),
    },
    resource_type=Decimal,
)
```

The exact constructor syntax shall follow the existing `TotalsDefinition` API.

The Inventory module shall not implement totals calculation itself.

---

# 11. Inventory Totals Responsibility Boundary

The Inventory configuration defines:

* register identity;
* dimensions;
* resource;
* supported movement types;
* movement signs;
* resource type.

The generic platform performs:

* totals key construction;
* contribution calculation;
* accumulation;
* removal;
* rebuild;
* balance retrieval;
* lifecycle maintenance.

Therefore no Inventory-specific totals class shall be introduced.

---

# 12. Inventory Register Posting Contract

The Inventory register shall provide:

```python
class InventoryRegisterPostingContract:
    def validate(self, movement: Movement) -> None:
        ...
```

The contract validates Inventory-specific register semantics.

It shall validate:

1. register identity;
2. supported movement type;
3. product dimension;
4. warehouse dimension;
5. quantity resource;
6. quantity type;
7. quantity magnitude.

---

# 13. Inventory Supported Movement Types

The Inventory posting contract shall accept:

```python
MovementType.INCOME
MovementType.EXPENSE
```

It shall reject unsupported movement types.

The contract must therefore not depend on:

```python
GOODS_RECEIPT_MOVEMENT_TYPE
```

because that constant belongs to the Goods Receipt operation rather than the Inventory register itself.

Conceptually:

```python
allowed_movement_types = {
    MovementType.INCOME,
    MovementType.EXPENSE,
}
```

The exact implementation may use an immutable representation where appropriate.

---

# 14. Inventory Register Contract Validation

The contract shall validate register identity:

```python
if movement.register_identity != INVENTORY_REGISTER_ID:
    raise ValueError(...)
```

It shall validate movement type:

```python
if movement.movement_type not in allowed_movement_types:
    raise ValueError(...)
```

It shall retrieve:

```python
product = movement.dimensions.get(INVENTORY_PRODUCT_DIMENSION)
warehouse = movement.dimensions.get(INVENTORY_WAREHOUSE_DIMENSION)
quantity = movement.resources.get(INVENTORY_QUANTITY_RESOURCE)
```

The product and warehouse values must be non-empty strings.

The quantity must be:

```python
Decimal
```

and must represent a positive magnitude.

The movement type determines the sign of the contribution.

---

# 15. Quantity Sign Convention

Movement quantities shall be represented as positive magnitudes.

The sign is not encoded in the movement resource itself.

For example:

```text
INCOME   quantity = 10
EXPENSE  quantity = 10
```

The Totals Definition determines:

```text
INCOME   → +10
EXPENSE  → -10
```

This preserves a clean distinction between:

* movement magnitude;
* movement semantic type;
* aggregated contribution.

---

# 16. Inventory Register Configuration

The Inventory register shall expose a declarative configuration object.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class InventoryRegisterConfiguration:
    register_identity: Identifier
    totals_definition: TotalsDefinition
    posting_contract: RegisterPostingContract
```

A concrete factory or constant may construct the standard configuration.

The configuration contains only declarative register semantics.

---

# 17. Configuration Purity

`InventoryRegisterConfiguration` must not contain mutable runtime infrastructure or operational dependencies.

It must not contain:

```text
TotalsEngine
RegisterFactPersistence
TotalsMaintenanceCoordinator
RegisterMutationOrchestrator
MovementQueryService
BalanceQueryService
PostingEngine
```

Those objects belong to runtime composition.

This preserves the distinction between:

```text
Configuration
    ↓
Runtime infrastructure
```

rather than embedding infrastructure inside configuration.

---

# 18. Posting Contract Resolution

The generic platform already defines:

```python
class RegisterPostingContract(Protocol):
    def validate(self, movement: Movement) -> None:
        ...


class RegisterPostingContractResolver(Protocol):
    def resolve(
        self,
        register_identity: Identifier,
    ) -> RegisterPostingContract:
        ...
```

Inventory shall integrate through this generic contract.

The Standard composition root shall register:

```text
INVENTORY_REGISTER_ID
        ↓
InventoryRegisterPostingContract
```

The implementation must not introduce:

```python
InventoryRegisterContractResolver
```

as a production Inventory-specific resolver.

The test-local resolver currently used by Phase 6 tests remains test infrastructure unless the generic composition implementation makes it obsolete.

---

# 19. Generic Contract Mapping

The preferred production composition is a generic mapping-based resolver or equivalent existing generic registry.

Conceptually:

```python
{
    INVENTORY_REGISTER_ID: inventory_configuration.posting_contract,
}
```

The resolver remains generic.

Adding another Standard register later should require adding configuration, not modifying generic Register Platform code.

---

# 20. Goods Receipt Posting Handler

The existing:

```python
GoodsReceiptPostingHandler
```

remains responsible for converting Goods Receipt document data into generic movements.

It shall continue to:

1. read Goods Receipt document state;
2. validate document-level line data;
3. validate product;
4. validate warehouse;
5. validate positive Decimal quantity;
6. create generic `Movement`;
7. assign Inventory register identity;
8. assign `MovementType.INCOME`;
9. assign product and warehouse dimensions;
10. assign quantity resource;
11. assign posting accounting time;
12. return `MovementSet`.

The handler shall not directly invoke:

* persistence;
* totals;
* maintenance;
* balance;
* Inventory register storage;
* Inventory-specific mutation services.

---

# 21. Goods Receipt Constants

The following Goods Receipt constant remains operation-specific:

```python
GOODS_RECEIPT_MOVEMENT_TYPE = MovementType.INCOME
```

The following constants shall instead be imported from:

```text
standard.registers.inventory
```

```python
INVENTORY_REGISTER_ID
INVENTORY_PRODUCT_DIMENSION
INVENTORY_WAREHOUSE_DIMENSION
INVENTORY_QUANTITY_RESOURCE
```

This prevents semantic duplication.

---

# 22. Register Mutation Integration

The existing generic:

```python
RegisterMutationOrchestrator
```

remains the only register mutation API.

Inventory must not receive an Inventory-specific mutation orchestrator.

The establish path is:

```text
GoodsReceiptPostingHandler
        ↓
MovementSet
        ↓
PostingEngine
        ↓
PostingResultCoordinator
        ↓
RegisterMutationOrchestrator.establish(...)
```

The mutation orchestrator continues to perform:

```text
validation
    ↓
operation-domain admission
    ↓
persistence
    ↓
totals maintenance
```

---

# 23. Posting Result Coordinator

The existing Posting API defines:

```python
class PostingResultCoordinator(Protocol):
    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> None:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> None:
        ...
```

Step 8 requires a production generic implementation connecting posting results to register mutation.

The implementation shall conceptually be:

```python
class RegisterPostingResultCoordinator:
    ...
```

This is a generic platform integration component.

It must not contain Inventory-specific behavior.

---

# 24. Coordinator Establish

The coordinator's `establish()` operation shall delegate the movement set to the generic mutation orchestrator.

Conceptually:

```python
def establish(
    self,
    document: ObjectInstance,
    movement_set: MovementSet,
) -> None:
    self._mutation.establish(movement_set.movements)
```

The document argument is retained because it is part of the Posting API contract.

The coordinator must not independently:

* persist facts;
* update totals;
* calculate balances;
* validate Inventory semantics.

Those responsibilities remain below the coordinator.

---

# 25. Coordinator Remove

The Posting API provides only:

```python
remove(document)
```

whereas the generic mutation API requires movements to remove.

Therefore the coordinator must resolve the authoritative movements belonging to the source document.

The generic flow shall be:

```text
PostingResultCoordinator.remove(document)
        ↓
RegisterFactPersistence.find_by_source_document(
    document.identity
)
        ↓
authoritative Movement Facts
        ↓
RegisterMutationOrchestrator.remove(movements)
```

This lookup is generic and must not be implemented by Inventory.

---

# 26. Authoritative Source for Unposting

Unposting shall operate on persisted Movement Facts.

The coordinator must not reconstruct movements from:

* current document state;
* posting handler output;
* current Inventory configuration;
* totals;
* balance.

The persisted Movement Facts are authoritative.

This prevents derived or reconstructed state from being used as the source of mutation reversal.

---

# 27. Unposting Flow

The concrete generic flow is:

```text
PostingEngine.unpost(document)
        ↓
RegisterPostingResultCoordinator.remove(document)
        ↓
RegisterFactPersistence.find_by_source_document(
    document.identity
)
        ↓
RegisterMutationOrchestrator.remove(movements)
        ↓
persistence.remove(...)
        ↓
TotalsMaintenanceCoordinator.remove(...)
        ↓
derived Inventory totals updated
```

The Inventory register remains unaware of the orchestration.

---

# 28. Reposting Semantics

Reposting shall mean:

```text
remove previous posting effect
+
establish new posting effect
```

It shall not mean simply establishing another movement set.

The current `PostingEngine.repost()` implementation must therefore be reconciled with this semantic requirement.

The generic repost path shall explicitly perform:

```text
coordinator.remove(document)
        ↓
handler.post(...)
        ↓
movement validation
        ↓
coordinator.establish(document, movement_set)
        ↓
DocumentReposted
```

The exact ordering must preserve the existing Posting lifecycle and failure semantics.

---

# 29. Repost Must Not Accumulate Movements

The following behavior is forbidden:

```text
old movements
+
new movements
```

after a repost.

A successful repost must leave the register state equivalent to:

```text
new posting effect only
```

The old persisted movements must first be removed through the generic mutation path.

No new `replace()` API shall be introduced unless implementation reveals a concrete generic requirement that cannot be expressed through the existing `remove()` + `establish()` lifecycle.

---

# 30. Posting Event Semantics

The existing event semantics remain unchanged.

`DocumentPosted` shall be emitted only after successful logical establishment.

`DocumentUnposted` shall be emitted only after successful logical removal.

`DocumentReposted` shall be emitted only after successful logical replacement of the previous register effect.

The Inventory register must not publish or control posting lifecycle events.

---

# 31. Persistence Integration

Inventory uses the existing:

```python
RegisterFactPersistence
```

interface.

No Inventory-specific persistence implementation shall be created.

Persistence stores generic Movement Facts.

Inventory-specific semantics are represented through:

```text
register_identity
movement_type
dimensions
resources
source document identity
accounting time
```

---

# 32. Totals Maintenance Integration

Inventory uses the existing:

```python
TotalsMaintenanceCoordinator
```

and:

```python
TotalsEngine
```

The Inventory configuration supplies:

```python
inventory_totals_definition()
```

to the generic totals engine.

No Inventory-specific maintenance coordinator shall be introduced.

---

# 33. Lifecycle Integration

Inventory participates in the existing generic lifecycle model.

The following states remain generic:

```text
TotalsConsistencyState
TotalsLifecycleState
TotalsMaintenanceState
```

Inventory configuration does not implement lifecycle transitions.

The generic maintenance coordinator remains responsible for:

* apply;
* remove;
* recovery admission;
* consistency state;
* lifecycle state;
* maintenance outcomes.

---

# 34. Rebuild Integration

Inventory rebuild shall use the generic rebuild mechanism.

The rebuild source is authoritative persisted Movement Facts.

Conceptually:

```text
Inventory Movement Facts
        ↓
generic rebuild
        ↓
Inventory TotalsDefinition
        ↓
generic TotalsEngine
        ↓
rebuilt totals
```

No Inventory-specific rebuild implementation shall be introduced.

---

# 35. Recovery Integration

Inventory recovery remains a generic Register Platform concern.

Recovery must operate through the generic persistence, totals, maintenance, and lifecycle abstractions.

Inventory configuration supplies semantics only.

There shall be no:

```text
InventoryRecoveryService
InventoryRecoveryCoordinator
Inventory-specific recovery branch
```

---

# 36. Movement Query Integration

Inventory movement history shall use:

```python
MovementQueryService
```

No Inventory-specific movement query implementation shall be introduced.

Queries shall filter by:

```text
register_identity = INVENTORY_REGISTER_ID
```

and may additionally filter by:

```text
product
warehouse
movement_type
source document
accounting time
```

according to the existing generic query API.

---

# 37. Balance Query Integration

Inventory balance shall use:

```python
BalanceQueryService
```

The balance query shall use the Inventory `TotalsDefinition` and generic `TotalsEngine` state.

A typical Inventory balance query identifies:

```text
register = Inventory
product = P
warehouse = W
resource = quantity
```

and returns the generic balance result.

No Inventory-specific balance engine shall be introduced.

---

# 38. Balance Semantics

For a product/warehouse pair:

```text
balance =
    Σ(INCOME quantity)
    -
    Σ(EXPENSE quantity)
```

The balance is derived from movement facts through the generic totals mechanism.

Movement Facts remain authoritative.

---

# 39. Standard Configuration Composition

The existing Standard configuration bootstrap currently initializes Standard metadata/runtime configuration.

Step 8 shall extend Standard composition only where required to make the Inventory register operational.

The composition boundary should assemble:

```text
Inventory configuration
        +
generic persistence
        +
generic totals engine
        +
generic maintenance coordinator
        +
generic mutation orchestrator
        +
generic query services
        +
generic posting coordinator
```

The composition root owns dependency wiring.

The implementation exposes that wiring through the existing Standard bootstrap as a
composition operation:

```python
StandardConfigurationBootstrap().compose_inventory_register_platform(
    persistence
)
```

The operation accepts the generic `RegisterFactPersistence` boundary and constructs
the Inventory configuration together with the generic totals, maintenance, mutation,
validation, posting-bridge, movement-query, and balance-query components. Before the
composition is returned, the generic maintenance coordinator rebuilds Inventory Totals
from authoritative persisted Movement Facts. This establishes the required
`ACTIVE / VALID` mutation-admission state and makes both an empty register and a
pre-populated register immediately operational. If authoritative reconstruction fails,
composition fails rather than exposing a non-admissible runtime. The returned composition
holder is an internal implementation detail and is not exported as an Inventory public
API.

---

# 40. No Mandatory `StandardRegisterRuntime`

The implementation shall not introduce a mandatory public abstraction such as:

```python
StandardRegisterRuntime
```

merely for Step 8.

There is currently no established repository-wide abstraction requiring such a type.

If a composition helper is useful, it may remain an internal composition detail.

A new public runtime abstraction should only be introduced if a broader reusable requirement is demonstrated by the repository.

---

# 41. Runtime Dependency Graph

The intended runtime graph is:

```text
                    Standard Configuration
                            │
             ┌──────────────┴──────────────┐
             │                             │
     InventoryRegisterConfiguration    GoodsReceiptPostingHandler
             │                             │
             ↓                             ↓
     TotalsDefinition                 MovementSet
             │                             │
             └──────────────┬──────────────┘
                            ↓
                    PostingResultCoordinator
                            ↓
                  RegisterMutationOrchestrator
                       ┌────┼────┐
                       │    │    │
                       ↓    ↓    ↓
                 Persistence │ Maintenance
                            │       │
                            └──┬────┘
                               ↓
                         TotalsEngine
```

Queries use the same generic register infrastructure:

```text
Movement Facts → MovementQueryService
Totals         → BalanceQueryService
```

---

# 42. Dependency Direction

The dependency direction must remain:

```text
Standard Inventory Configuration
        ↓
Generic Register Contracts
        ↓
Generic Register Infrastructure
```

Never:

```text
Generic Register Infrastructure
        ↓
Standard Inventory
```

Generic platform modules must not import:

```python
accore.standard
```

or any equivalent Standard Inventory module.

---

# 43. Public API Surface

The Inventory register public API should be limited to concrete semantic configuration.

Expected public symbols include:

```python
INVENTORY_REGISTER_ID
INVENTORY_PRODUCT_DIMENSION
INVENTORY_WAREHOUSE_DIMENSION
INVENTORY_QUANTITY_RESOURCE
InventoryRegisterPostingContract
InventoryRegisterConfiguration
inventory_totals_definition
```

Only symbols that are genuinely required externally should be exported from:

```text
standard.registers.inventory
```

The implementation must avoid exporting internal composition helpers.

---

# 44. Goods Receipt Public API

The existing Goods Receipt API remains responsible for the operation:

```python
GoodsReceiptPostingHandler
```

and its operation-specific constants.

Inventory register constants are imported from the Inventory register configuration rather than duplicated.

---

# 45. Generic Platform APIs Used by Inventory

The implementation shall reuse the existing APIs:

```text
Movement
MovementType
MovementDimensions
MovementResources

RegisterPostingContract
RegisterPostingContractResolver
MovementValidator

TotalsDefinition
TotalsKey
TotalsEngine
DefaultTotalsEngine

RegisterFactPersistence

TotalsMaintenanceCoordinator

RegisterMutationOrchestrator
RegisterOperationDomainRegistry

MovementQueryService
BalanceQueryService

PostingEngine
PostingResultCoordinator
```

No equivalent Inventory-specific replacements shall be created.

---

# 46. API Responsibility Matrix

| Responsibility                    | Owner                                |
| --------------------------------- | ------------------------------------ |
| Inventory register identity       | Standard Inventory Configuration     |
| Inventory dimensions              | Standard Inventory Configuration     |
| Inventory resource                | Standard Inventory Configuration     |
| Inventory movement types          | Standard Inventory Configuration     |
| Inventory movement signs          | Standard Inventory Configuration     |
| Inventory posting validation      | Standard Inventory Configuration     |
| Goods Receipt → INCOME mapping    | Goods Receipt Posting Handler        |
| Movement representation           | Generic Register Platform            |
| Movement validation orchestration | Generic Register Platform            |
| Persistence                       | Generic Register Platform            |
| Mutation                          | Generic Register Platform            |
| Totals                            | Generic Register Platform            |
| Maintenance                       | Generic Register Platform            |
| Rebuild                           | Generic Register Platform            |
| Recovery                          | Generic Register Platform            |
| Movement query                    | Generic Register Platform            |
| Balance query                     | Generic Register Platform            |
| Posting → register bridge         | Generic Posting/Register integration |
| Standard dependency composition   | Standard composition root            |

---

# 47. Error Handling

Inventory contract validation shall reject invalid Inventory movements through the existing validation/error mechanism.

The implementation shall not introduce an Inventory-specific error hierarchy unless an existing generic error contract cannot represent the required failure.

Generic mutation and maintenance failures remain governed by the existing Register Platform error model.

Unexpected failures must preserve the existing lifecycle and recovery semantics.

---

# 48. Atomicity and Failure Boundaries

Inventory implementation must preserve the generic mutation contract.

The following sequence must not be reimplemented independently for Inventory:

```text
persist
+
apply totals
+
recover on maintenance failure
```

The existing:

```python
RegisterMutationOrchestrator
```

remains responsible for these semantics.

The Inventory configuration only supplies the register-specific definitions required by that machinery.

---

# 49. Duplicate Prevention

Movement identity remains the generic duplicate-prevention mechanism.

Inventory must not introduce a separate duplicate detector.

Repeated establishment of the same movement identity must follow the existing generic mutation/persistence semantics.

---

# 50. Source Document Association

Every Inventory movement created from Goods Receipt shall retain the source document identity through the generic Movement model.

This identity is required for:

```text
unposting
reposting
auditability
movement queries
```

The Inventory register itself does not manage source-document relationships independently.

---

# 51. Accounting Time

Goods Receipt movements shall continue to receive accounting time from the existing posting clock.

Inventory does not own clock or time-generation logic.

The generic Movement representation remains responsible for carrying accounting time.

---

# 52. No Direct Inventory Persistence

The following design is explicitly prohibited:

```python
class InventoryRepository:
    ...
```

or any equivalent Inventory-specific persistence abstraction.

Inventory facts are generic Register Facts.

---

# 53. No Direct Inventory Totals Storage

The following design is explicitly prohibited:

```python
class InventoryBalanceStore:
    ...
```

or any equivalent Inventory-specific totals storage.

Inventory balances are derived through the generic Totals Engine.

---

# 54. No Inventory Mutation Service

The following design is explicitly prohibited:

```python
class InventoryMutationService:
    ...
```

Register mutation remains the responsibility of:

```python
RegisterMutationOrchestrator
```

---

# 55. No Inventory Maintenance Service

The following design is explicitly prohibited:

```python
class InventoryMaintenanceService:
    ...
```

Maintenance remains generic.

---

# 56. No Inventory Rebuild Service

The following design is explicitly prohibited:

```python
class InventoryRebuildService:
    ...
```

Rebuild remains generic.

---

# 57. No Inventory Balance Engine

The following design is explicitly prohibited:

```python
class InventoryBalanceEngine:
    ...
```

Balance remains a generic query over maintained totals.

---

# 58. Expected End-to-End Goods Receipt Flow

The completed runtime path shall be:

```text
Goods Receipt Document
        ↓
GoodsReceiptPostingHandler
        ↓
MovementSet
        ↓
MovementValidator
        ↓
InventoryRegisterPostingContract
        ↓
PostingResultCoordinator
        ↓
RegisterMutationOrchestrator.establish()
        ↓
RegisterFactPersistence.append()
        ↓
TotalsMaintenanceCoordinator.apply()
        ↓
TotalsEngine
        ↓
Inventory Current Total
        ↓
BalanceQueryService
        ↓
Inventory Balance
```

---

# 59. Expected End-to-End Unpost Flow

```text
PostingEngine.unpost()
        ↓
RegisterPostingResultCoordinator.remove()
        ↓
RegisterFactPersistence.find_by_source_document()
        ↓
RegisterMutationOrchestrator.remove()
        ↓
RegisterFactPersistence.remove()
        ↓
TotalsMaintenanceCoordinator.remove()
        ↓
TotalsEngine
        ↓
Inventory Current Total
```

---

# 60. Expected End-to-End Repost Flow

```text
PostingEngine.repost()
        ↓
RegisterPostingResultCoordinator.remove()
        ↓
authoritative persisted movements
        ↓
RegisterMutationOrchestrator.remove()
        ↓
GoodsReceiptPostingHandler.post()
        ↓
new MovementSet
        ↓
MovementValidator
        ↓
RegisterPostingResultCoordinator.establish()
        ↓
RegisterMutationOrchestrator.establish()
        ↓
new authoritative Movement Facts
        ↓
new Inventory Totals
```

A successful repost must not retain the previous movement set.

---

# 61. Test-Oriented API Expectations

The concrete API must permit isolated tests for:

### Inventory configuration

```text
register identity
dimensions
resource
totals definition
```

### Inventory contract

```text
valid INCOME
valid EXPENSE
invalid register
invalid movement type
invalid product
invalid warehouse
invalid quantity
```

### Goods Receipt

```text
document → INCOME movement
```

### Generic integration

```text
posting → mutation
mutation → persistence
mutation → maintenance
totals → balance
```

### Unpost

```text
document → persisted movements → removal
```

### Repost

```text
old movements removed
new movements established
```

---

# 62. Test Boundary

Tests shall preserve the same architectural boundary as production.

Inventory tests may instantiate:

```python
InventoryRegisterPostingContract
InventoryRegisterConfiguration
inventory_totals_definition
GoodsReceiptPostingHandler
```

Generic Register Platform tests remain responsible for generic mechanics.

Integration tests shall verify that Inventory configuration is correctly wired into those generic mechanisms.

---

# 63. Required Step 8 Implementation Changes

Implementation after approval is expected to cover the following concrete changes:

1. Create `src/standard/registers/inventory.py`.
2. Centralize Inventory register identity there.
3. Centralize Inventory dimension constants there.
4. Centralize Inventory quantity resource name there.
5. Add `inventory_totals_definition()`.
6. Update `InventoryRegisterPostingContract` to accept both `INCOME` and `EXPENSE`.
7. Update Goods Receipt to import Inventory constants.
8. Preserve Goods Receipt → `INCOME` mapping.
9. Add the generic production `PostingResultCoordinator` implementation if not already present.
10. Implement authoritative movement lookup for unposting.
11. Correct generic repost lifecycle to remove old effects before establishing new effects.
12. Wire Inventory configuration into Standard composition.
13. Remove obsolete duplicated constants.
14. Add and update unit/integration/vertical tests.
15. Reconcile public exports.

No Inventory-specific runtime infrastructure shall be added.

---

# 64. Implementation Constraints

Implementation must not:

* duplicate generic register mechanics;
* create Inventory-specific persistence;
* create Inventory-specific totals;
* create Inventory-specific maintenance;
* create Inventory-specific rebuild;
* create Inventory-specific recovery;
* create Inventory-specific balance engine;
* create an Inventory-specific contract resolver;
* create `StandardRegisterRuntime` as a mandatory public abstraction;
* introduce `replace()` without a demonstrated generic requirement;
* encode Inventory semantics inside generic Register Platform branches.

---

# 65. Concrete API Acceptance Criteria

The Concrete API Design is considered complete when:

1. Every Inventory-specific public symbol is identified.
2. Every generic dependency is identified.
3. Inventory configuration boundaries are explicit.
4. Inventory totals semantics are explicit.
5. Inventory posting validation semantics are explicit.
6. INCOME/EXPENSE support is explicit.
7. Goods Receipt → INCOME mapping is explicit.
8. Posting → register integration is explicit.
9. Unpost semantics are explicit.
10. Repost semantics are explicit.
11. Persistence authority is explicit.
12. Maintenance ownership is explicit.
13. Rebuild ownership is explicit.
14. Recovery ownership is explicit.
15. Query ownership is explicit.
16. Composition responsibility is explicit.
17. No unnecessary public runtime abstraction is required.
18. No Inventory-specific generic-platform duplication remains.

---

# 66. Implementation Acceptance Criteria

After implementation, the following must be demonstrated:

1. Inventory configuration is loadable.
2. Inventory totals definition is correctly constructed.
3. Inventory contract accepts valid INCOME movements.
4. Inventory contract accepts valid EXPENSE movements.
5. Inventory contract rejects invalid movements.
6. Goods Receipt creates INCOME Inventory movements.
7. Goods Receipt movements pass generic movement validation.
8. Posting establishes persisted Inventory movement facts.
9. Totals are maintained through the generic maintenance path.
10. Inventory balance queries return the expected derived quantity.
11. Unposting finds authoritative movements by source document.
12. Unposting removes persisted facts through the generic mutation path.
13. Unposting removes corresponding totals.
14. Reposting removes the old register effect.
15. Reposting establishes the new register effect.
16. Reposting does not accumulate old and new movements.
17. Rebuild reconstructs Inventory totals from Movement Facts.
18. Existing generic Register Platform tests remain valid.
19. Existing Posting tests remain valid or are correctly amended for the clarified repost semantics.
20. No Inventory-specific persistence/mutation/totals/maintenance/recovery/balance infrastructure is introduced.

---

# 67. Quality Gate

Before implementation is considered complete:

```text
pytest
ruff check
black --check
mypy
```

must pass according to the repository's existing quality standards.

Relevant focused tests shall also be executed independently.

The final implementation must leave the repository architecture consistent with this document.

---

# 68. Final Architectural Boundary

The final architecture is:

```text
                    ┌───────────────────────────┐
                    │   Standard Inventory      │
                    │       Configuration       │
                    │                           │
                    │ register identity         │
                    │ dimensions                │
                    │ quantity resource         │
                    │ movement semantics        │
                    │ posting contract          │
                    └─────────────┬─────────────┘
                                  │
                                  ↓
                    ┌───────────────────────────┐
                    │    Generic Register       │
                    │        Platform           │
                    │                           │
                    │ Movement                  │
                    │ Validation                │
                    │ Persistence               │
                    │ Mutation                  │
                    │ Totals                    │
                    │ Maintenance               │
                    │ Rebuild                   │
                    │ Recovery                  │
                    │ Movement Query            │
                    │ Balance Query             │
                    └─────────────┬─────────────┘
                                  │
                                  ↓
                    ┌───────────────────────────┐
                    │     Generic Posting       │
                    │       Integration        │
                    │                           │
                    │ PostingEngine             │
                    │ Result Coordinator        │
                    └───────────────────────────┘
```

The key architectural property is that Inventory defines **what the register means**, while the generic Register Platform defines **how a register operates**.

---

# 69. Final API Definition

The essential Inventory-specific API is therefore:

```python
INVENTORY_REGISTER_ID: Identifier

INVENTORY_PRODUCT_DIMENSION: str
INVENTORY_WAREHOUSE_DIMENSION: str
INVENTORY_QUANTITY_RESOURCE: str


def inventory_totals_definition() -> TotalsDefinition:
    ...


class InventoryRegisterPostingContract:
    def validate(self, movement: Movement) -> None:
        ...


@dataclass(frozen=True, slots=True)
class InventoryRegisterConfiguration:
    register_identity: Identifier
    totals_definition: TotalsDefinition
    posting_contract: RegisterPostingContract
```

The essential generic integration API is:

```python
class RegisterPostingResultCoordinator:
    def establish(
        self,
        document: ObjectInstance,
        movement_set: MovementSet,
    ) -> None:
        ...

    def remove(
        self,
        document: ObjectInstance,
    ) -> None:
        ...
```

with the implementation delegating to:

```python
RegisterMutationOrchestrator
RegisterFactPersistence
```

rather than implementing Inventory-specific behavior.

---

# 70. Final Decision

Phase 7 Step 8 shall implement Inventory as a complete Standard Register Configuration over the existing generic Register Platform.

The implementation shall:

```text
define Inventory semantics
        ↓
wire them into generic Register Platform
        ↓
connect Posting to generic register mutation
        ↓
support authoritative unpost
        ↓
support remove + establish repost
        ↓
expose Inventory movement and balance queries
```

No new Inventory-specific register infrastructure is required.

The only new generic infrastructure justified by this design is the missing production bridge between Posting results and the existing generic Register Mutation API, together with the generic authoritative movement lookup required by unposting and the corresponding correction of repost lifecycle semantics.

Architecture and Concrete API Design are complete at this point. Implementation begins only after approval of this final document.
