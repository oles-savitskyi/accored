# ADR-STD-001
SMB-Oriented Standard Configuration

Status: Accepted

Date: 2026-08-09

Context

The AcCore Platform is designed as a universal business application platform capable of supporting multiple domains, industries, and organizational models through metadata-driven configuration.

However, a standard configuration cannot be simultaneously optimized for every possible type of organization.

Attempting to support large enterprises, government institutions, multinational corporations, holdings, and small businesses within a single standard configuration would introduce:

excessive model complexity;
large numbers of business objects;
complicated workflows;
difficult user onboarding;
higher maintenance costs;
reduced usability.

A primary target audience for the standard configuration must therefore be defined.

Decision

The AcCore Standard Configuration shall be optimized for Small and Medium Businesses (SMB).

The standard configuration is intended to support:

sole proprietors;
small businesses;
medium-sized businesses;
distributors;
wholesalers;
retailers;
service companies;
small manufacturing organizations;
organizations with workforce sizes ranging from a single employee to several hundred employees.

The standard configuration shall provide the functionality required by the majority of SMB organizations without requiring platform modifications.

Architectural Principle

The Standard Configuration Is Optimized For SMB Organizations.

When architectural trade-offs are required, solutions that improve simplicity, usability, maintainability, and implementation speed for SMB organizations shall be preferred over solutions intended primarily for large enterprises.

Consequences
Positive
Simpler Business Model

Business objects, documents, and workflows remain understandable for typical SMB users.

Faster Development

New functionality can be implemented and delivered more rapidly.

Better User Experience

Users interact with a business-oriented system rather than an enterprise framework.

Lower Maintenance Cost

The standard configuration remains easier to support and evolve.

Predictable Growth

The application can grow incrementally without introducing enterprise-level complexity.

Better Performance

Most business scenarios can be executed without requiring complex distributed architectures.

Negative
Limited Enterprise Functionality

Some enterprise-grade capabilities may not be available in the standard configuration, including:

complex organizational hierarchies;
multi-level approval chains;
holding consolidation;
advanced budgeting systems;
distributed accounting landscapes;
enterprise governance frameworks.
Additional Extensions May Be Required

Large organizations may need custom configurations built on top of the AcCore Platform.

Non-Goals

The standard configuration is not intended to become:

a large-enterprise ERP system;
a government accounting platform;
a banking system;
an insurance platform;
a telecommunications management system;
a manufacturing execution system (MES);
an industry-specific vertical solution.
Implications

Future design decisions for the standard configuration shall be evaluated primarily according to their value for SMB organizations.

The standard configuration shall:

Work out of the box.
Require minimal initial setup.
Support gradual business growth.
Remain understandable by non-technical users.
Avoid enterprise-level complexity unless justified by significant SMB value.
Relationship To Platform Architecture

This decision applies only to the AcCore Standard Configuration.

The AcCore Platform itself remains domain-independent and may be used to build solutions for organizations of any size.

# ADR-STD-002
Process-Oriented User Experience

Status: Accepted

Date: 2026-08-09

Context

Traditional accounting systems are often organized around accounting concepts:

registers;
postings;
ledger entries;
accounting movements;
balances;
technical transactions.

While these concepts are necessary for the internal operation of the system, they are not the concepts most business users work with daily.

Typical users think in terms of business processes:

purchasing goods;
receiving inventory;
selling products;
issuing invoices;
receiving payments;
paying suppliers;
managing stock;
tracking customer obligations.

Exposing accounting internals as primary user-facing concepts increases training costs and reduces usability.

Decision

The AcCore Standard Configuration shall be process-oriented rather than accounting-oriented.

Users shall interact primarily with business processes and business documents.

Accounting mechanics, postings, register movements, valuation calculations, and technical reconciliation mechanisms shall remain internal implementation details whenever possible.

Architectural Principle

Users Work With Business Processes, Not Accounting Internals.

Business operations shall be represented through understandable business workflows, while accounting structures shall serve as supporting infrastructure.

Consequences
Positive
Lower Learning Curve

Users can operate the system using familiar business terminology.

Better Adoption

The application becomes accessible to non-accountants.

Reduced Training Requirements

Organizations can onboard users more quickly.

Workflow-Centered Design

The system naturally aligns with how businesses operate.

Accounting Independence

Future accounting implementations can evolve without significantly affecting user workflows.

Negative
Additional Abstraction Layer

The platform must maintain mappings between business operations and accounting mechanisms.

More Complex Internal Architecture

User-facing simplicity requires additional internal orchestration.

User-Facing Model

Users primarily work with:

catalogs;
business documents;
tasks;
workflows;
reports;
dashboards;
approvals;
operational processes.

Users should rarely need direct interaction with:

register movements;
posting records;
valuation layers;
totals engines;
accounting balances;
technical transactions.
Implications

The standard configuration shall favor:

process-based navigation;
document-driven workflows;
operational dashboards;
role-oriented workspaces;
task-oriented interfaces.

The standard configuration shall avoid exposing technical accounting concepts unless explicitly required for audit, diagnostics, or advanced administration.

Relationship To Previous Decisions

This ADR complements:

ADR-STD-001 — SMB-Oriented Standard Configuration.

A process-oriented user experience is considered one of the primary mechanisms for making the standard configuration suitable for SMB organizations.

# ADR-STD-003
Continuous Cost Recognition

Status: Accepted

Date: 2026-08-09

Context

Traditional accounting and ERP systems typically recognize many business costs during periodic closing procedures.

Examples include:

payroll accruals;
depreciation;
indirect expenses;
cost allocations;
overhead distribution.

As a result, operational reports often differ from the actual economic state of the business until month-end processing has been completed.

This approach creates delays between business events and cost recognition.

Managers frequently operate on incomplete information during the accounting period.

AcCore aims to provide operational visibility that closely reflects the actual economic state of the organization at any moment.

Decision

The AcCore Standard Configuration shall recognize and distribute costs as close as possible to the moment they are economically incurred.

Cost recognition shall be performed continuously throughout the accounting period rather than being deferred to month-end closing procedures whenever practical.

Examples include:

labor costs;
depreciation costs;
indirect operating expenses;
acquisition-related expenses;
distribution-related expenses.

The system shall support ongoing accumulation and allocation of costs during daily operations.

Month-end procedures shall primarily serve reconciliation, verification, and adjustment purposes rather than initial cost recognition.

Architectural Principle

Costs Are Recognized At The Time Of Consumption.

Whenever economically feasible, expenses shall enter the accounting and costing model when resources are consumed rather than when accounting periods are closed.

Consequences
Positive
More Accurate Operational Reporting

Operational reports better reflect the current state of the business.

Reduced Month-End Workload

Periodic closing procedures become simpler and faster.

Continuous Cost Visibility

Managers can monitor cost formation throughout the accounting period.

Improved Cost Traceability

The relationship between business activities and resulting costs becomes more transparent.

Better Production And Inventory Costing

Production and inventory costs can be formed incrementally rather than retrospectively.

Negative
Increased Processing Activity

Cost allocation procedures execute more frequently.

More Complex Cost Allocation Logic

The system requires mechanisms for continuous allocation and redistribution.

Higher Dependency On Allocation Rules

Cost quality depends on the correctness of allocation policies.

Examples
Labor Cost

Employee work performed during a day generates labor cost recognition through Salary Booking.

Salary Rollout later performs deductions, settlements, and final payroll processing.

Depreciation Cost

Asset consumption generates depreciation cost continuously during the accounting period.

Depreciation Sharing distributes the resulting costs to cost centers and cost objects.

Monthly Depreciation serves primarily as a planning, verification, and reconciliation document.

Indirect Expenses

Indirect costs are accumulated and periodically distributed through Expense Sharing.

The distribution process may occur multiple times during the accounting period.

Relationship To Other Decisions

This ADR complements:

ADR-STD-001 — SMB-Oriented Standard Configuration
ADR-STD-002 — Process-Oriented User Experience

Continuous cost recognition supports both SMB usability and process-oriented business management by reducing dependence on complex accounting-period procedures.

Implications For Future Architecture

The following architectural elements shall be designed around this principle:

Cost Allocation Architecture;
Payroll Architecture;
Fixed Asset Architecture;
Inventory Costing;
Production Costing;
Expense Distribution;
Reporting Architecture.

The standard configuration shall prefer continuous cost formation over retrospective period-end calculations whenever practical.

# ADR-STD-004
Economic Objects Are Unified

Status: Accepted

Date: 2026-08-09

Context

Traditional ERP systems usually maintain separate catalogs for:

products;
materials;
services;
fixed assets;
intangible assets;
investments;
expense items;
revenue items.

While these objects have different business meanings, they share many common characteristics:

identification;
classification;
valuation;
participation in business transactions;
participation in cost allocation;
participation in reporting.

Maintaining independent catalogs often leads to duplicated structures, duplicated business logic, and complex cross-module integrations.

Decision

The AcCore Standard Configuration shall use a unified catalog named Assortment as the primary catalog of economic objects.

The Assortment catalog shall contain multiple economic object types including:

Products
Goods
Materials
Services
Fixed Assets
Intangible Assets
Investments
Expenses
Revenues

Object specialization shall be implemented through metadata and object attributes rather than separate catalogs.

Architectural Principle

Economic Objects Are Unified.

All economic objects participating in business operations, costing, valuation, and reporting shall be represented through a common economic object model.

Consequences
Positive
Simplified business model.
Unified reporting.
Unified pricing architecture.
Simplified cost allocation.
Reduced metadata duplication.
Consistent integration model.
Negative
More complex validation rules.
Additional type-specific behavior.
More sophisticated user interfaces.
Relationship To Cost Recognition

The Assortment catalog acts as the primary receiver of costs generated by:

Salary Sharing;
Depreciation Sharing;
Expense Sharing;
Purchasing;
Production;
Sales.

Economic objects become the primary carriers of business value and cost accumulation.

Implications

Future business modules should reference Assortment whenever possible instead of introducing additional economic object catalogs.

# ADR-STD-005
Business Operations Are Consolidated Into Universal Operational Documents

Status: Accepted

Date: 2026-08-09

Context

Traditional ERP systems typically represent a single business process through multiple specialized documents.

Examples include:

Purchase Order;
Goods Receipt;
Supplier Invoice;
Purchase Return;
Sales Order;
Shipment;
Customer Invoice;
Customer Return.

While flexible, such models increase system complexity, create duplicate workflows, and require users to navigate large numbers of document types.

The AcCore Standard Configuration is optimized for SMB organizations and prioritizes simplicity, usability, and process-oriented operation.

Decision

Business processes shall be represented through a small set of universal operational documents.

The standard configuration shall use the following primary operational documents:

Purchase
Sale
Production
Cash

The following specialized cost-recognition documents shall also exist:

Salary
Depreciation

Additionally, the system shall provide:

Unidoc

as a generic accounting and operational document.

Architectural Principle

A Business Process Should Be Represented By A Single Operational Document Whenever Practical.

Consequences
Positive
Reduced document complexity.
Simplified user experience.
Easier training.
Consistent document structure.
Lower maintenance costs.
Negative
More sophisticated document internals.
Increased reliance on document tabular sections.
More complex document validation rules.
Implications

Future business functionality should extend existing operational documents whenever practical rather than introducing additional document types.

# ADR-STD-006
Direct And Related Expenses Are Allocation Modes

Status: Accepted

Date: 2026-08-09

Context

Traditional accounting systems often classify expenses according to their economic nature.

Examples:

payroll expenses;
depreciation expenses;
material expenses;
service expenses.

However, the primary challenge in operational costing is often not the type of expense but the manner in which the expense is allocated to business objects.

Decision

The AcCore Standard Configuration shall classify expenses according to allocation mode rather than expense nature.

Two allocation modes shall exist:

Direct Expense

An expense that can be assigned immediately to a specific business object.

Related Expense

An expense that must be distributed among multiple business objects through allocation rules.

The same economic resource may appear in either category depending on the business scenario.

Examples:

Salary;
Depreciation;
Materials;
Services.
Architectural Principle

Expense Classification Is Allocation-Based.

Consequences
Positive
Unified cost allocation model.
Consistent processing architecture.
Simplified reporting.
Better support for continuous cost recognition.
Negative
More sophisticated allocation logic.
Increased dependency on allocation policies.
Implications

Cost allocation processes shall focus on identifying cost receivers rather than classifying expense types.

# ADR-STD-007
Business Facts And Business Intentions Are Separated

Status: Accepted

Date: 2026-08-09

Context

Business systems frequently mix planning information and accounting facts within the same model.

Examples include:

payment plans;
payment requests;
purchase intentions;
production plans.

This often results in accounting records being influenced by information that does not yet represent actual business events.

Decision

The AcCore Standard Configuration shall distinguish between:

Business Facts

Actual economic events.

Examples:

purchases;
sales;
payments;
production output;
salary recognition.

Business facts may create register movements and affect balances.

Business Intentions

Planned or proposed activities.

Examples:

Bill To Pay;
payment proposals;
allocation proposals;
planning documents.

Business intentions shall never create register movements or affect balances.

Architectural Principle

Registers Reflect Facts, Not Intentions.

Consequences
Positive
Cleaner accounting model.
Better auditability.
Reduced accidental postings.
Clear separation between planning and accounting.
Negative
Additional planning objects may be required.
Users must understand the distinction between intentions and facts.
Implications

Future planning functionality should be implemented through intention-oriented objects rather than accounting transactions.

# ADR-STD-008
Registers Store Quantities, Valuation Stores Costs

Status: Accepted

Date: 2026-08-10

Context

Traditional ERP systems often combine quantity and cost information within the same registers.

Examples include:

inventory quantity and inventory value;
production quantity and production cost;
labor quantity and labor cost.

Such models tightly couple operational accounting and valuation logic, making cost recalculation, delayed cost recognition, and cost redistribution significantly more complex.

The AcCore platform already defines independent architectures for:

Register Accounting;
Valuation Engine;
Cost Totals Engine.
Decision

Operational registers shall store only quantitative business facts.

Cost information shall not be stored in operational registers.

Cost information shall be produced and maintained by:

Valuation Engine;
Cost Totals Engine.
Architectural Principle

Registers Store Quantities. Valuation Stores Costs.

Examples
Inventory

Register:

Material A
100 pcs

Valuation:

Material A
100 pcs
1250 USD
Labor

Register:

Employee A
8 hours

Valuation:

Employee A
8 hours
80 USD
Asset Utilization

Register:

Machine A
5 machine-hours

Valuation:

Machine A
5 machine-hours
17.50 USD
Consequences
Positive
Clear separation of responsibilities.
Simplified register design.
Independent valuation recalculation.
Better support for delayed cost facts.
Consistent processing model for inventory, labor, and depreciation.
Negative
Cost information requires valuation processing.
Operational reporting may require valuation joins.
Implications

Future operational registers should store only resource quantities and business facts.

Cost-related functionality shall be implemented through valuation infrastructure.

# ADR-STD-009
Labor And Depreciation Follow The Same Resource Model As Inventory

Status: Accepted

Date: 2026-08-10

Context

Traditional accounting systems often treat:

inventory;
payroll;
depreciation;

as completely separate accounting domains.

However, all three domains share a common structure:

quantitative resource consumption;
cost recognition;
cost allocation.
Decision

The Standard Configuration shall model:

inventory resources;
labor resources;
asset utilization resources;

through a unified resource accounting approach.

Each domain shall record quantitative facts in registers.

Associated costs shall be maintained by valuation infrastructure.

Architectural Principle

Inventory, Labor, and Depreciation Are Resource Flows.

Examples
Inventory Resource

Quantity:

100 kg Material

Cost:

100 kg Material
500 USD
Labor Resource

Quantity:

8 hours Labor

Cost:

8 hours Labor
80 USD
Asset Utilization Resource

Quantity:

5 machine-hours

Cost:

5 machine-hours
20 USD
Consequences
Positive
Unified architecture.
Consistent allocation model.
Reusable valuation logic.
Simplified reporting.
Negative
Additional abstraction layer.
Requires resource-oriented thinking.
Implications

Future cost allocation functionality should operate on resource flows rather than accounting-specific categories.

# ADR-STD-010
Role Permissions Are Business-Object-Oriented

Status: Accepted

Date: 2026-08-10

Context

Traditional ERP systems often define permissions through technical operations such as:

Create
Read
Update
Delete

This approach exposes implementation details and does not accurately reflect business responsibilities.

AcCore Standard Configuration is organized around business domains and business objects:

Purchase
Sale
Production
Salary
Depreciation
Cash
Unidoc
Reference Data
Reports

Therefore authorization should be expressed using business objects rather than technical CRUD operations.

Decision

Permissions shall be defined against business domains and business objects.

A permission grants access to a business object and optionally restricts access through object-level and data-level scopes.

Permission Model
Role
    ↓
Domain
    ↓
Object
    ↓
Object Scope (optional)
    ↓
Data Scope (optional)
    ↓
Access Mode
Consequences
Positive
Business-oriented security model.
Easier understanding by end users.
Consistent with document-centric architecture.
Independent from implementation details.
Negative
More complex permission evaluation.
Requires explicit scope management.
Implications

Future security mechanisms should be built around business objects rather than CRUD actions.

# ADR-STD-011
Access Rights Are Defined Through Access Modes

Status: Accepted

Date: 2026-08-10

Context

Not all actions have equal business impact.

Viewing information is fundamentally different from executing business operations.

Some actions are administrative and potentially dangerous.

Examples:

deleting posted documents;
changing global settings;
modifying role definitions;
reopening closed periods.

A simple Read/Write model is insufficient.

Decision

The Standard Configuration shall define three access modes.

Access Modes
View

Read-only access.

Permitted actions:

open;
browse;
search;
print;
export.

No business facts may be changed.

Execute

Operational access.

Permitted actions may include:

create documents;
modify documents;
post documents;
run processings;
perform ordinary workflow activities.
Administer

Administrative access.

Permitted actions may include:

delete business objects;
modify security settings;
modify role definitions;
modify global settings;
reopen periods;
perform recovery operations.
Architectural Principle
View
    < Execute
        < Administer
Consequences

Operational users receive only the minimum permissions required for their work.

Administrative capabilities remain isolated.