# ADR-001: Report Produces Dataset

Decision

A report execution produces a platform-neutral analytical dataset. Presentation, visualization, export, and UI rendering are separate concerns and are not part of report execution.

Consequences

Reports remain UI-independent.
The same dataset can be rendered as table, pivot, chart, dashboard, PDF, Excel, or API response.
Reporting Architecture remains compatible with desktop, web, and mobile runtimes.
Report execution becomes deterministic and testable.

# ADR-002: Report Dataset Model Is Hybrid
Decision

Report datasets are defined through a hybrid model consisting of:

Data Sources
Filters
Dataset Definition
Dimensions
Measures

Dimensions and Measures form the analytical model.

Dataset Definition forms the extraction model.

# ADR-003: Reports Consume Datasets, Not Storage Structures
Decision

Reports operate on logical datasets rather than physical storage structures.

Consequences

Reporting Architecture remains independent from:

Storage Architecture
Register implementation details
Totals implementation details
Database backend

# ADR-004: Report Data Sources Are Schema-Based
Decision

Every report data source exposes a logical schema describing available fields, dimensions, measures, and relationships.

Consequences
Reports are independent from physical storage.
Report Designer can work entirely from metadata.
New source types can be added without modifying Reporting Engine.
Report composition becomes possible.
Reporting Architecture remains compatible with future BI and Dashboard subsystems.

# ADR-005: Dataset Definition Is Declarative
Decision

Dataset Definition describes the desired dataset rather than execution steps.

Consequences
Reporting Engine controls optimization.
Runtime may choose different execution strategies.
Future caching and materialization become possible.
Dataset Definitions remain stable while execution evolves.

# ADR-006: Dimensions And Measures Are First-Class Metadata Objects
Decision

Dimensions and Measures are explicit metadata objects and are not inferred from report layout or presentation.

Consequences
Analytical semantics become part of metadata.
Dashboards can reuse report definitions.
Future OLAP capabilities become possible.
Drill-down and pivot operations become metadata-driven.

# ADR-007: Dimensions May Define Hierarchies
Decision

Dimensions may expose analytical hierarchies.

Consequences
Drill-down becomes possible.
Roll-up becomes possible.
Dashboards and pivot reports gain natural navigation paths.

# ADR-008: Measures Use Expression Engine
Decision

Calculated measures are evaluated through the platform Expression Engine.

Consequences
No second formula engine exists.
Report calculations remain consistent with the rest of the platform.
Optimization and dependency tracking are reused.

# ADR-009: Reports Are Compiled Before Execution
Decision

Reports are compiled into execution plans before runtime execution.

Consequences
Metadata remains immutable.
Runtime execution becomes deterministic.
Optimization becomes possible.
Caching becomes possible.
Multiple runtime implementations become possible.

# ADR-010: Report Execution Uses Execution Plans
Decision

Report Runtime executes compiled execution plans rather than report metadata.

Consequences
Runtime becomes independent from metadata structure.
Execution optimizations become possible.
Alternative runtimes become possible.

# ADR-011: Report Runtime Reuses Table Engine
Decision

Report Runtime delegates dataset processing to the platform Table Engine whenever possible.

Consequences
No duplicate analytical engine.
Shared optimization infrastructure.
Shared expression evaluation.
Shared memory model.
Shared execution model.

# ADR-012: Report Execution Produces Dataset
Status

Accepted

Decision

The output of report execution is always a platform-neutral analytical dataset.

Consequences
UI independence.
Export independence.
Dashboard compatibility.
API compatibility.
Testability.

# ADR-013: Reporting Is Implemented As Runtime Service
Decision

Reporting functionality is provided through Runtime Services rather than through standalone report-specific infrastructure.

Consequences
Reporting integrates naturally with Runtime Architecture.
Common service lifecycle is reused.
Dependency injection is reused.
Security and permissions can be reused.
Runtime Context can be reused.

# ADR-014: Report Manager Is Runtime Entry Point
Decision

All report execution requests are handled through Report Manager.

Consequences
Single runtime entry point.
Consistent lifecycle.
Consistent security checks.
Consistent logging and monitoring.

# ADR-015: Report Executor Operates On Execution Plans
Decision

Report Executor executes execution plans and does not access report metadata directly.

Consequences
Clear Metadata/Runtime separation.
Simpler runtime implementation.
Easier optimization.
Easier testing.

# ADR-016: Reporting Runtime Reuses Platform Services
Decision

Reporting Runtime reuses existing platform services whenever possible.

Consequences
Reduced implementation complexity.
Consistent behavior.
Shared optimizations.
Lower maintenance costs.

# ADR-017: Dataset And Presentation Are Independent
Decision

Report execution produces datasets.

Presentation consumes datasets.

Neither side depends on the implementation details of the other.

Consequences
Multiple presentation technologies become possible.
Runtime remains UI-independent.
Export mechanisms remain independent.
Dashboards can reuse report datasets.
APIs can reuse report datasets.


# ADR-018: Presentation Model Is Renderer Independent
Decision

Presentation metadata is independent from rendering technologies.

Consequences
Multiple renderers may reuse the same presentation definition.
UI technologies become replaceable.
Export mechanisms remain consistent.