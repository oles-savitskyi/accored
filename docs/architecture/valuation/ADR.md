# VAL-001 — Quantity First, Cost Later

Valuation subsystem shall never require
cost information to accept quantity facts.

Quantity accounting must remain operational
even when cost information is incomplete,
missing, or arrives later.

# VAL-002 — Layer Before Method

Valuation layers represent economic reality.

Valuation methods define how layers are consumed.

Valuation methods shall not define
the structure of valuation layers.

# VAL-003 — Cost Facts Are Explicit

The price should not change "on its own."

Any change in price must have a clear source.

# VAL-004 — All Cost Corrections Are Adjustments
Any change in layer valuation
shall be represented as a valuation adjustment.

Missing costs, late costs,
price corrections, revaluations,
and error corrections
are processed through the same adjustment mechanism.

# VAL-005 — Valuation Is A Deterministic Processing Pipeline
Valuation shall be implemented
as a deterministic processing pipeline.

Each stage consumes valuation facts
and produces new valuation facts.

# VAL-006

Every quantity-carrying register state shall have a corresponding valuation state.

# ADR-001
Valuation Is Independent From Quantity Accounting

Status: Accepted

Context

Accumulation Registers are responsible for tracking quantitative business facts.

Cost information may arrive later than the corresponding quantity movements.

Examples:

Transportation costs;
Customs expenses;
Additional supplier invoices;
Discounts;
Retroactive corrections;
Production overhead allocation.

As a result, quantity accounting and cost accounting may evolve independently over time.

Decision

Quantity accounting and valuation are separated architectural responsibilities.

Accumulation Registers store quantity facts.

Valuation Architecture calculates cost facts.

Cost is not a primary register resource.

Cost is a derived result produced by the Valuation Engine.

Consequences

Registers remain stable even when cost information changes.

Late-arriving cost information does not require redesign of register models.

Valuation may be recalculated independently from quantity accounting.

The platform supports historical cost reconstruction.

# ADR-002
Cost Facts May Arrive After Quantity Facts

Status: Accepted

Context

Business reality frequently produces delayed cost information.

Example:

Day 1

Purchase:
100 units × 1 = 100

Sale:
20 units

Initial cost of sale:
20
Day 2

Transportation Invoice:
10

Actual inventory cost becomes:

100 + 10 = 110

Actual unit cost becomes:

1.10

Actual cost of sold items becomes:

22

Previously calculated values become outdated.

Decision

The platform must assume that cost-related facts may arrive after quantity-related facts.

Late cost facts are considered normal business events.

The architecture must support retrospective valuation recalculation.

Consequences

Revaluation becomes a normal platform operation.

Historical valuation results may be recomputed.

Valuation dependencies must support dirty propagation.

Cost calculations cannot be permanently embedded into posting logic.

# ADR-003
Cost Is Produced By Valuation Engine

Status: Accepted

Context

Traditional accounting systems often calculate cost directly during posting.

This approach tightly couples posting, inventory logic, and valuation rules.

It becomes difficult to support:

Late cost facts;
Cost corrections;
Alternative valuation methods;
Historical recalculation.
Decision

Posting Architecture generates quantity movements only.

Accumulation Registers store quantity facts only.

All cost calculations are performed by the Valuation Engine.

Even when cost can be calculated immediately, valuation must still pass through the Valuation Engine.

Consequences

Posting remains deterministic.

Registers remain valuation-independent.

Valuation rules may evolve independently.

Future support for:

Average Cost;
FIFO;
LIFO (if required);
Standard Cost;
Weighted Cost;
Custom valuation models;

can be implemented without changing Posting Architecture or Register Architecture.

# ADR-004 — Valuation Layer Is The Primary Cost Carrier

Decision
Cost information shall be stored and tracked
through valuation layers.

Valuation layers are the primary carriers
of cost information within the valuation subsystem.
Consequences
- FIFO becomes natural.

- Average Cost can be implemented
  on top of layers.

- Late cost facts can be applied safely.

- Revaluation becomes deterministic.

- Cost balances become derived data.

- Cost movements become derived data.

# ADR-005 — Valuation Layers Are Immutable

## Status

Accepted

---

## Context

Valuation Architecture supports delayed cost facts.

Cost information may arrive after quantity movements have already been posted and partially consumed.

Examples include:

* transportation expenses;
* customs duties;
* supplier corrections;
* additional production costs;
* inventory revaluation adjustments.

A valuation layer may therefore require cost corrections after its creation.

The architecture must preserve:

* full auditability;
* deterministic recalculation;
* historical traceability;
* support for late-arriving cost facts.

---

## Decision

Valuation layers shall be immutable after creation.

Cost corrections shall not modify existing valuation layers.

Instead, every cost correction shall be represented as a separate valuation adjustment linked to the affected layer.

Conceptually:

```text
Valuation Layer
        +
Valuation Adjustments
        ↓
Effective Layer Cost
```

The effective cost of a layer is derived from:

```text
Layer Cost
+
All Applied Adjustments
```

A valuation adjustment is a first-class valuation object.

---

## Consequences

### Positive

* Complete audit trail is preserved.
* Original cost facts remain unchanged.
* Late cost facts can be applied safely.
* Revaluation becomes deterministic.
* Historical valuation states can be reconstructed.
* FIFO and future valuation methods remain compatible.
* Valuation recalculation becomes easier to reason about.

### Negative

* Additional storage is required for adjustments.
* Effective layer cost becomes a derived value.
* Valuation queries become slightly more complex.

### Neutral

Consumers of valuation results should not access layer cost directly.

Consumers should always use effective valuation results produced by the Valuation Engine.

---

## Example

Initial receipt:

```text
Layer L1

Quantity = 100
Cost = 100
```

Sale:

```text
Issue = 20
```

Consumed:

```text
20%
```

Remaining:

```text
80%
```

Later transportation expense:

```text
Adjustment A1

Layer = L1
Cost Change = +10
```

Effective layer cost becomes:

```text
100 + 10 = 110
```

Valuation Engine distributes the adjustment proportionally:

```text
Consumed Part  = +2
Remaining Part = +8
```

without modifying the original layer.

# ADR-006 — Cost Corrections Are Explicit Valuation Facts

## Status

Accepted

---

## Context

Valuation layers are immutable.

Cost information may arrive after quantity movements.

The valuation subsystem must preserve the economic origin of every cost change and maintain a complete audit trail.

Representing adjustments as anonymous cost deltas would make valuation difficult to audit and explain.

---

## Decision

Every cost correction shall be represented as an explicit valuation fact.

Valuation adjustments shall contain a business reason describing the origin of the cost change.

Cost changes shall never exist without an associated valuation fact.

---

## Consequences

### Positive

* Full traceability of cost formation.
* Improved auditability.
* Deterministic valuation history.
* Easier diagnostics and debugging.
* Future support for regulatory and accounting requirements.

### Negative

* Additional valuation objects must be stored.
* Valuation processing becomes more complex.

---

## Rule

Every effective layer cost must be explainable as:

```text
Original Layer Cost
+
Valuation Facts
=
Effective Cost
```

# ADR-007 — Cost Adjustments Are Allocated Proportionally Across Layer Consumption History

## Status

Accepted

---

## Context

Valuation layers are immutable.

Cost adjustments may arrive after a layer has been partially or fully consumed.

The valuation subsystem must distribute late-arriving cost information between:

* quantities already consumed;
* quantities still remaining in inventory.

The allocation mechanism must be deterministic, auditable, and independent from valuation methods.

---

## Decision

Cost adjustments shall be allocated proportionally based on the historical consumption state of the affected valuation layer.

The allocation ratio shall be calculated using:

```text
Consumed Ratio  = Consumed Quantity / Total Quantity
Remaining Ratio = Remaining Quantity / Total Quantity
```

Adjustment value shall be distributed according to these ratios.

---

## Example

Layer:

```text
Quantity Total = 100
Cost Total = 100
```

Consumption:

```text
Issued = 20
Remaining = 80
```

Adjustment:

```text
+10
```

Allocation:

```text
Consumed Share  = 2
Remaining Share = 8
```

Effective layer cost:

```text
110
```

---

## Consequences

### Positive

* Deterministic behavior.
* Simple implementation.
* Fully auditable calculations.
* Compatible with FIFO.
* Compatible with future valuation methods.
* Supports delayed cost facts naturally.

### Negative

* Historical valuation results may require recalculation.
* Cost adjustments may generate secondary valuation corrections.

### Neutral

Allocation is based on layer history and not on current inventory balances.

# ADR-008 — Valuation Allocations Are Explicit Valuation Facts

## Status

Accepted

---

## Context

Cost adjustments may affect both:

* consumed quantities;
* remaining quantities.

The valuation subsystem requires a deterministic and auditable mechanism for distributing adjustment values.

Recalculating allocation results dynamically would increase query complexity and make valuation history harder to audit.

---

## Decision

Allocation results shall be materialized as explicit valuation facts.

Each valuation allocation shall represent a portion of a valuation adjustment distributed to a specific valuation target.

Allocations shall be created by the Valuation Engine and stored as independent valuation records.

---

## Consequences

### Positive

* Full auditability.
* Deterministic valuation history.
* Fast valuation queries.
* Simplified diagnostics.
* Simplified recalculation logic.
* Consistent with the architecture of Posting and Registers.

### Negative

* Additional storage requirements.
* Additional processing during valuation.

### Neutral

Allocations are internal valuation artifacts and are produced exclusively by the Valuation Engine.

# ADR-009 — Layer Consumption Is An Explicit Valuation Fact

## Status

Accepted

---

## Context

Valuation methods consume quantities from valuation layers.

A single inventory issue may consume quantities from multiple layers.

Late cost adjustments require the valuation subsystem to identify which economic events have consumed a layer.

Without explicit consumption records, allocation of delayed cost facts becomes ambiguous and difficult to audit.

---

## Decision

Consumption of valuation layers shall be recorded as explicit valuation facts.

Each consumption record shall represent the consumption of a specific quantity from a specific valuation layer by a specific economic event.

Valuation Engine shall use consumption records as the basis for:

* cost calculation;
* cost allocation;
* revaluation;
* audit reconstruction.

---

## Consequences

### Positive

* Full traceability of layer usage.
* Deterministic FIFO processing.
* Support for delayed cost facts.
* Simplified revaluation.
* Complete audit chain.

### Negative

* Additional storage requirements.
* Additional valuation processing.

### Neutral

Consumption records are internal valuation artifacts and are created exclusively by the Valuation Engine.

# ADR-010 — Valuation Methods Produce Consumption Facts

## Status

Accepted

---

## Context

Valuation Architecture must support multiple valuation methods.

Examples include:

* FIFO;
* Average Cost;
* Specific Identification;
* Standard Cost;
* Future custom valuation methods.

The architecture must remain independent from any specific valuation method.

Valuation layers, adjustments, allocations, and consumptions represent valuation facts and shall remain stable regardless of valuation method.

---

## Decision

Valuation methods shall be implemented as consumption generation strategies.

A valuation method shall determine:

* which valuation layers are selected;
* how quantities are consumed from those layers.

The result of valuation processing shall always be explicit valuation consumption facts.

Valuation methods shall not define valuation storage structures.

Valuation methods shall not modify valuation data models.

---

## Consequences

### Positive

* Valuation Architecture remains method-independent.
* FIFO becomes a replaceable strategy.
* New valuation methods can be introduced without changing the valuation model.
* Simplified testing.
* Improved extensibility.

### Negative

* Additional abstraction layer inside Valuation Engine.

### Neutral

Consumption facts become the stable contract between valuation methods and the rest of the valuation subsystem.

# ADR-011 — Cost Movements Are Materialized Valuation Facts

## Status

Accepted

---

## Context

Valuation consumptions represent internal valuation processing.

External consumers require explicit cost facts representing the monetary impact of economic events.

Calculating cost effects dynamically from layers, consumptions, adjustments, and allocations would increase query complexity and reduce system performance.

---

## Decision

The valuation subsystem shall materialize cost movements as explicit valuation facts.

Cost movements shall represent the final cost impact of valuation processing for a specific economic event.

Cost movements shall be produced exclusively by the Valuation Engine.

---

## Consequences

### Positive

* Fast valuation queries.
* Simplified reporting.
* Simplified accounting integration.
* Stable external contract.
* Improved auditability.

### Negative

* Additional storage requirements.
* Additional valuation processing.

### Neutral

Cost movements are derived valuation facts and shall not be edited directly.

# ADR-012 — Cost Balances Are Materialized Valuation Facts

## Status

Accepted

---

## Context

Cost movements represent valuation changes over time.

Frequent calculation of inventory cost balances from historical valuation data would be expensive and inefficient.

The valuation subsystem requires fast access to inventory cost positions.

---

## Decision

The valuation subsystem shall maintain materialized cost balances.

Cost balances shall be derived from cost movements and maintained by the Valuation Engine.

Cost balances shall represent the effective inventory value for a valuation key at a specific moment.

---

## Consequences

### Positive

* Fast balance queries.
* Simplified reporting.
* Consistency with Register Totals Architecture.
* Reduced recalculation costs.

### Negative

* Additional storage requirements.
* Balance maintenance logic required.

### Neutral

Cost balances are derived valuation facts and shall not be edited directly.

# ADR-013 — Valuation Is Triggered By Posting

## Status

Accepted

---

## Context

Posting produces quantity facts that become inputs for valuation processing.

The platform requires valuation results to remain consistent with register state.

Delayed cost facts are supported and may trigger additional valuation cycles.

---

## Decision

Successful posting shall trigger valuation processing.

Valuation Engine shall process all valuation-relevant facts produced by posting.

Valuation processing shall be part of the normal document lifecycle.

Additional valuation cycles may be triggered later when new cost facts become available.

---

## Consequences

### Positive

* Quantity and cost states remain synchronized.
* Immediate availability of valuation results.
* Consistent user experience.
* Simplified reporting.

### Negative

* Posting processing becomes heavier.
* Valuation errors may affect posting completion if not handled properly.

### Neutral

Delayed cost facts may initiate additional valuation runs without requiring document reposting.


# ADR-014 — All Cost Corrections Are Adjustments

## Status

Accepted

---

## Context

Valuation layers may be created with:

* complete cost information;
* incomplete cost information;
* provisional cost information;
* incorrect cost information.

Cost information may change after layer creation due to:

* late-arriving expenses;
* supplier corrections;
* production cost allocations;
* revaluations;
* error corrections.

The valuation subsystem must support all such scenarios without introducing special valuation states or specialized processing paths.

---

## Decision

Any change affecting the valuation of a layer shall be represented as a valuation adjustment.

The valuation subsystem shall use a single adjustment mechanism for:

* missing costs;
* delayed costs;
* cost corrections;
* revaluations;
* error corrections.

Valuation layers shall not require special states such as:

* Incomplete;
* Pending Cost;
* Estimated Cost;
* Unvalued Layer.

The effective cost of a layer shall always be determined by:

```text
Effective Cost =
Base Cost +
Σ Valuation Adjustments
```

---

## Consequences

### Positive

* Single valuation model.
* No special valuation states.
* Uniform processing logic.
* Simplified valuation engine.
* Simplified auditing.
* Simplified recalculation logic.
* Natural support for delayed cost facts.

### Negative

* Effective cost becomes a derived value.
* Adjustment history may grow over time.

### Neutral

A layer with zero base cost is a valid valuation object.

The valuation subsystem does not distinguish between:

* missing cost;
* incorrect cost;
* corrected cost.

All such situations are represented through valuation adjustments.

# ADR-015 — Valuation Uses Pipeline Processing

## Status

Accepted

---

## Context

Valuation processing consists of multiple dependent stages.

Each stage consumes valuation facts produced by previous stages.

Valuation processing must remain deterministic, auditable, and extensible.

---

## Decision

Valuation processing shall be implemented as a pipeline of valuation stages.

Each stage shall:

* consume valuation facts;
* perform deterministic processing;
* produce new valuation facts.

Stages shall not bypass previous stages.

Valuation processing shall follow the lifecycle defined in VALUATION_LIFECYCLE.md.

---

## Consequences

### Positive

* Clear processing flow.
* Deterministic behavior.
* Easy diagnostics.
* Easy auditing.
* Extensible architecture.

### Negative

* Additional orchestration required.
* Multiple processing stages must be maintained.

### Neutral

Pipeline stages remain internal implementation details of the valuation subsystem.

# ADR-016 — Valuation Methods Are Pluggable Strategies

## Status

Accepted

---

## Context

Different installations may require different valuation methods.

Examples include:

* FIFO;
* Average Cost;
* Specific Identification;
* Standard Cost;
* Custom valuation methods.

Valuation Architecture must remain independent from any specific valuation method.

---

## Decision

Valuation methods shall be implemented as pluggable valuation strategies.

Valuation methods shall determine:

* layer selection;
* quantity allocation across layers.

Valuation methods shall not define valuation storage structures.

Valuation methods shall not create valuation balances directly.

The output of every valuation method shall be valuation consumption facts.

---

## Consequences

### Positive

* Method-independent architecture.
* Extensible valuation subsystem.
* Custom valuation methods supported.
* Simplified testing.

### Negative

* Additional abstraction layer.

### Neutral

Valuation methods are internal components of the Valuation Engine.

# ADR-017 — Valuation Method Is Defined By Asset Type

## Status

Accepted

---

## Context

Different categories of assets may require different valuation methods.

Valuation Architecture must support multiple valuation methods while maintaining consistent processing rules.

A global valuation method would be too restrictive.

Per-location valuation methods would introduce unnecessary complexity.

---

## Decision

Valuation method shall be defined by asset type metadata.

Each asset type shall specify the valuation method used for consumption processing.

Examples:

* FIFO;
* Average Cost;
* Specific Identification;
* Custom valuation methods.

Valuation Engine shall resolve the valuation method from asset metadata during consumption processing.

---

## Consequences

### Positive

* Flexible valuation configuration.
* Consistent behavior within an asset category.
* Metadata-driven architecture.
* Simplified extensibility.

### Negative

* Asset metadata becomes part of valuation configuration.

### Neutral

Different asset types may use different valuation methods within the same system.

# ADR-018 — Valuation Methods Are Metadata-Registered Extensions

## Status

Accepted

---

## Context

Valuation Architecture must support multiple valuation methods.

The platform must remain independent from specific costing algorithms.

Different configurations may require industry-specific valuation behavior.

---

## Decision

Valuation methods shall be implemented as metadata-registered extensions.

The platform shall provide a valuation method contract.

Valuation methods shall be registered through metadata and resolved by the Valuation Engine at runtime.

The platform shall not require a fixed set of valuation methods.

Built-in valuation methods, if provided, shall use the same extension mechanism as custom methods.

---

## Consequences

### Positive

* Open valuation architecture.
* Industry-specific methods supported.
* No platform dependency on specific costing algorithms.
* Consistent extensibility model.

### Negative

* Method registration infrastructure required.
* Additional validation required.

### Neutral

FIFO, Average Cost, and Specific Identification become ordinary implementations of the valuation method contract.

# ADR-019 — Cost Balances Are Maintained By Cost Totals Engine

## Status

Accepted

---

## Context

Valuation Engine produces materialized cost movements.

Cost balances represent aggregated valuation state.

Register Architecture already separates movement generation from totals maintenance.

The same principle should be applied to valuation processing.

---

## Decision

Cost balances shall be maintained by a dedicated Cost Totals Engine.

Valuation Engine shall produce cost movements only.

Cost Totals Engine shall consume cost movements and maintain cost balances.

---

## Consequences

### Positive

* Consistent with Register Architecture.
* Clear separation of responsibilities.
* Simplified maintenance and rebuilding.
* Independent balance recalculation.
* Improved architectural symmetry.

### Negative

* Additional subsystem required.

### Neutral

Cost balances become valuation totals maintained from cost movements.

# ADR-020 — Operational Queries Use Materialized Results

## Status

Accepted

---

## Context

Valuation Architecture maintains both valuation facts and materialized valuation results.

Operational queries require fast access to current valuation state.

Audit queries require complete valuation traceability.

Using valuation facts for all query types would significantly increase query complexity and execution cost.

---

## Decision

Operational queries shall use materialized valuation results.

Audit queries shall use valuation facts.

Materialized valuation results shall be optimized for reporting and operational access.

Valuation facts shall remain the source of truth for audit and reconstruction.

---

## Consequences

### Positive

* Fast operational queries.
* Clear separation between operational and audit workloads.
* Simplified reporting.
* Improved scalability.

### Negative

* Additional materialized structures required.

### Neutral

Operational and audit queries use different storage layers.
