WORKFLOW_DOMAIN_MODEL.md
Purpose

The Workflow Domain Model defines the core entities used to represent business workflows within AcCore.

The model is independent from:

business applications;
user interfaces;
storage implementation;
security implementation;
integration mechanisms.

Workflow is responsible for coordinating business processes around business objects.

Workflow does not own business data.

Architectural Principles
Workflow Is Metadata-Driven

Workflow definitions are represented as metadata.

Workflow behavior must not be hardcoded in business objects.

Workflow Is Object-Centric

Every workflow is associated with a business object.

Examples:

Sales Order

Purchase Invoice

Inventory Count

Contract

Workflow exists to manage the lifecycle of objects.

Workflow Is State-Based

Workflow execution is driven by state transitions.

States represent business lifecycle stages.

Workflow Is Security-Aware

Workflow may require permissions to execute transitions.

Workflow does not implement its own security model.

Authorization is delegated to Security Architecture.

Workflow Is Audit-Aware

Workflow actions produce audit events.

Workflow history must be traceable.

Domain Entities

The Workflow Domain consists of seven core entities.

WorkflowDefinition
State
Transition
ApprovalRule
Task
AutomationRule
WorkflowInstance
WorkflowDefinition

Represents a workflow template.

Responsibilities
define workflow structure;
define states;
define transitions;
define automation rules.
Attributes
WorkflowDefinition
├── id
├── code
├── name
├── description
└── version
Examples
SalesOrderWorkflow

PurchaseApprovalWorkflow

InventoryCountWorkflow
State

Represents a lifecycle stage.

Responsibilities
describe object status;
define possible transitions.
Attributes
State
├── id
├── code
├── name
├── description
├── is_initial
└── is_final
Examples
Draft
Approved
Posted
Closed
Cancelled
Transition

Represents an allowed movement between states.

Responsibilities
control lifecycle progression;
define workflow paths.
Attributes
Transition
├── id
├── code
├── source_state
├── target_state
└── conditions
Example
Draft
      ↓
Approved
ApprovalRule

Represents approval requirements for transitions.

Responsibilities
define approval requirements;
connect workflow and security.
Attributes
ApprovalRule
├── id
├── code
├── approval_type
├── security_requirement
└── parameters
Examples
Manager Approval

Chief Accountant Approval

Director Approval
Task

Represents work assigned to a user or role.

Responsibilities
notify participants;
track required actions.
Attributes
Task
├── id
├── code
├── assignee
├── state
├── due_date
└── workflow_reference
Examples
Approve Invoice

Review Contract

Verify Inventory
AutomationRule

Represents an automatically executed action.

Responsibilities
automate workflow activities;
react to workflow events.
Attributes
AutomationRule
├── id
├── code
├── trigger
├── action
└── parameters
Examples
Send Notification

Create Task

Publish Event

Execute Processing
WorkflowInstance

Represents a running workflow.

Responsibilities
maintain runtime state;
track workflow execution.
Attributes
WorkflowInstance
├── id
├── workflow_definition
├── object_reference
├── current_state
├── started_at
└── completed_at
Notes

WorkflowDefinition is metadata.

WorkflowInstance is runtime state.

Relationships
WorkflowDefinition → State
WorkflowDefinition
          1:N
State

A workflow contains multiple states.

WorkflowDefinition → Transition
WorkflowDefinition
          1:N
Transition

A workflow contains multiple transitions.

Transition → State
State
   ↓
Transition
   ↓
State

Transitions connect states.

Transition → ApprovalRule
Transition
       0:N
ApprovalRule

A transition may require approvals.

Transition → AutomationRule
Transition
       0:N
AutomationRule

A transition may trigger automation.

WorkflowInstance → WorkflowDefinition
WorkflowInstance
          N:1
WorkflowDefinition

Runtime execution references metadata definition.

WorkflowInstance → State
WorkflowInstance
          N:1
State

Every instance has one current state.

WorkflowInstance → Task
WorkflowInstance
          0:N
Task

Workflow execution may generate tasks.

Domain Diagram
WorkflowDefinition
      |
      +----------------+
      |                |
      v                v
   State          Transition
                       |
              +--------+--------+
              |                 |
              v                 v
      ApprovalRule      AutomationRule

WorkflowDefinition
          |
          v
WorkflowInstance
          |
          +------> Current State
          |
          +------> Tasks
Workflow Boundaries

Workflow owns:

States
Transitions
Approvals
Tasks
Automation
Execution State

Workflow does not own:

Business Data
Posting
Registers
Valuation
Reports
Security
Integration

Workflow may invoke those subsystems but does not replace them.

Out Of Scope

The following concepts are intentionally excluded from the first version:

BPMN Engine
Parallel Branches
Compensation Transactions
Process Variables
Timers
Escalation Engine
Process Orchestration Language

These may be added later if required.

Domain Model Summary

The Workflow Domain Model consists of:

WorkflowDefinition
State
Transition
ApprovalRule
Task
AutomationRule
WorkflowInstance

The model implements the Hybrid Workflow approach adopted by AcCore and provides the foundation for workflow execution, approvals, task generation, and process automation.