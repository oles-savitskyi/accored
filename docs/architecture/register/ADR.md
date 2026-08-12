## ADR-RA-001

Register Types

Accepted

AcCore core architecture defines
two register types:

- Information Register
- Accumulation Register

Other register types may be introduced
in future versions as specialized extensions
of the core register model.

## ADR-RA-002

Information Register Identity

Accepted

Every Information Register record
has a globally unique ULID.

Business uniqueness is defined by
period and dimensions.

Technical identity and business identity
are separate concepts.

## ADR-RA-003

Information Register Record Versioning

Accepted

Information Register records are versionable.

Record modifications create a new version
while preserving previous versions.

The platform may expose only the current
version to users.

Historical versions remain available for
auditing, dependency tracking, and future
recalculation mechanisms.

## ADR-RA-004

Information Register Record Origin

Accepted
Decision

Every Information Register record shall have traceable origin information.

Record Origin Fields
source_type

source_id
Supported Source Types
MANUAL

DOCUMENT

PROCESSING

IMPORT

SYSTEM

Список может расширяться в будущем.

Purpose

Origin information provides:

Traceability

Auditing

Dependency Tracking

Recalculation Support

Data Provenance
Architectural Principle
Every register fact should be traceable
to its origin.

## ADR-RA-005

Accumulation Movement Model

Accepted

Accumulation Movements use
a dedicated movement_type field.

Movement resources are always positive.

Movement direction is determined exclusively
by movement_type.

Supported movement types:

- INCOME
- EXPENSE

## ADR-RA-006
Balances are primary aggregates.

Turnovers are derived aggregates.

The Totals Engine must maintain
balance totals.

The platform may optionally maintain
materialized turnover totals
as a performance optimization.

## ADR-RA-007

Totals Engine Strategy

Hybrid

Incremental Maintenance
+
Periodic Rebuild

## ADR-RA-008

Balance Storage Model

Accepted

Totals are stored as aggregated
period deltas grouped by dimensions.

Current balances are derived
from totals buckets.

## ADR-RA-009

Adaptive Totals Management

Hybrid Strategy

Register metadata defines
preferred totals granularity.

Totals Engine may adapt granularity
based on workload and data volume.

## ADR-RA-010

Register Query Model

Accepted
Query Types
Movement Query

Balance Query

Turnover Query
Query Independence
Queries are independent
from storage implementation.

Queries access register services,
not totals storage.
Temporal Model
Balances and register state
are queried as of a specified moment.
Aggregation Model
Queries aggregate resources
grouped by dimensions.

## ADR-RA-011

Я бы сформулировал примерно так.

Register Events

Accepted
Event Categories
Movement Events

Totals Events

Register Events
Core Events
MovementCreated

MovementDeleted

MovementChanged

TotalsUpdated

TotalsRebuilt

RegisterChanged
Architectural Principle
Register Events describe
changes in register facts
and infrastructure state.

Register Events do not
contain business logic.
Dependency Integration
Register Events may be consumed
by the Dependency Graph
to identify affected objects
and trigger recalculation.

## ADR-RA-012

Я бы зафиксировал примерно так.

Register Dependency Integration

Accepted
Dependency Unit
Register State

is the primary dependency node.

Movements are not dependency nodes.

Change Propagation
RegisterChanged
        ↓
Dependency Graph
        ↓
Dirty Objects
        ↓
Recalculation
Architectural Principle
Registers publish changes.

Dependency Graph manages propagation.

Registers do not trigger recalculation directly.
Reposting Integration
Reposting participates in the same
dependency mechanism as normal posting.

## ADR-RA-013

Я бы зафиксировал:

Register Lifecycle

Accepted
Lifecycle Stages
Metadata Definition

Compilation

Registration

Initialization

Operational State

Maintenance

Shutdown
Operational Principle
Registers are runtime-managed components.

Register lifecycle is managed
by Register Manager.
Maintenance Principle
Maintenance operations are
a normal part of the register lifecycle.