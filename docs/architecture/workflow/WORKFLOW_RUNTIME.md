WORKFLOW_RUNTIME.md
Purpose

The Workflow Runtime defines the runtime components responsible for executing workflows within AcCore.

The Workflow Runtime is responsible for:

workflow execution;
transition processing;
approval coordination;
task management;
automation execution;
workflow history tracking.

The Workflow Runtime executes workflow definitions but does not own business data.

Architectural Principles
Metadata-Driven Execution

Workflow behavior is derived from metadata definitions.

Runtime components execute metadata.

Runtime components do not contain workflow-specific business logic.

Stateless Engine

Workflow engines should be stateless whenever possible.

Workflow state is stored in Workflow Instances.

Workflow Is Runtime-Orchestrated

Business objects do not manage their own workflows.

Workflow execution is coordinated by Workflow Runtime.

Security Delegation

Workflow Runtime delegates authorization decisions to Security Architecture.

Workflow Runtime never evaluates permissions directly.

Audit Integration

Workflow Runtime produces audit events for workflow operations.

Runtime Architecture

The Workflow Runtime consists of six primary components.

Workflow Runtime
├── Workflow Engine
├── Workflow Instance Manager
├── Approval Manager
├── Task Manager
├── Automation Engine
└── Workflow History Service
Workflow Engine
Purpose

The Workflow Engine coordinates workflow execution.

It is the central orchestrator of Workflow Runtime.

Responsibilities
Receive Transition Requests
Validate Transitions
Coordinate Approvals
Execute State Changes
Invoke Automation
Produce Events
Workflow Engine Flow
Transition Request
       ↓
Validation
       ↓
Security Check
       ↓
Approval Check
       ↓
State Change
       ↓
Automation
       ↓
History Recording
Workflow Instance Manager
Purpose

Manages Workflow Instances.

Responsibilities
Create Workflow Instance
Load Instance
Persist State
Complete Instance
Terminate Instance
Ownership

Workflow Instance Manager owns:

WorkflowInstance Runtime State

It does not own:

Business Objects
Approval Manager
Purpose

Coordinates approval processing.

Responsibilities
Resolve Approval Rules
Track Approval Status
Collect Decisions
Determine Approval Outcome
Approval States
Pending
Approved
Rejected
Approval Flow
Transition
      ↓
Approval Rules
      ↓
Approval Manager
      ↓
Decision
Task Manager
Purpose

Manages workflow-generated tasks.

Responsibilities
Create Tasks
Assign Tasks
Update Tasks
Complete Tasks
Cancel Tasks
Task Lifecycle
Created
      ↓
Assigned
      ↓
Completed

or

Created
      ↓
Cancelled
Task Ownership

Tasks belong to Workflow Runtime.

Tasks are not business objects.

Automation Engine
Purpose

Executes workflow automation rules.

Responsibilities
Evaluate Triggers
Execute Actions
Publish Events
Create Tasks
Invoke Processings
Automation Triggers

Examples:

State Entered
State Exited
Transition Completed
Approval Granted
Approval Rejected
Automation Actions

Examples:

Create Task
Send Notification
Publish Event
Execute Processing
Start Integration
Execution Principle

Automation execution must be deterministic.

The same trigger and context must produce the same actions.

Workflow History Service
Purpose

Maintains workflow execution history.

Responsibilities
Record State Changes
Record Approvals
Record Tasks
Record Automation Actions
Provide History Queries
History Example
Draft → Approved

Approved → Posted

Posted → Closed
Relationship To Audit

Workflow History:

Workflow-Oriented

Audit:

Security And Platform-Oriented

Both may reference the same events.

Runtime Interactions
Security Architecture

Workflow Runtime requests authorization.

Workflow Engine
        ↓
Authorization Service
        ↓
Allow / Deny
Audit Architecture

Workflow Runtime emits audit events.

Transition Executed
Approval Granted
Task Created
Workflow Completed
Integration Architecture

Automation Engine may trigger:

API Calls
Events
Imports
Exports

through Integration Architecture.

Posting Architecture

Workflow may invoke:

Post
Unpost

operations.

Posting execution remains outside Workflow Runtime.

Workflow Runtime Context

Every workflow execution operates within a Workflow Context.

Conceptually:

WorkflowContext
├── workflow_instance
├── current_state
├── principal
├── business_object
├── transition
└── runtime_metadata
Runtime Flow
Workflow Instance
       ↓
Transition Request
       ↓
Workflow Engine
       ↓
Approval Manager
       ↓
State Change
       ↓
Task Manager
       ↓
Automation Engine
       ↓
Workflow History Service
Failure Handling
Validation Failure
Reject Transition
Security Failure
Deny Execution
Approval Failure
Reject Transition
Automation Failure

Workflow policy determines behavior.

Supported approaches:

Fail Workflow

or

Continue Workflow And Log Failure

The policy must be explicit.

Scalability

The Workflow Runtime supports:

Single User
Multi User
Client/Server
Distributed Deployment

No runtime component assumes local execution.

Runtime Diagram
Workflow Engine
       |
       +----------------------+
       |                      |
       v                      v
Approval Manager       Task Manager
       |
       v
Automation Engine
       |
       v
Workflow History Service

Workflow Instance Manager
provides execution state
for all components
Workflow Runtime Summary

The Workflow Runtime executes workflow definitions using a lightweight orchestration model.

Core runtime components:

Workflow Engine
Workflow Instance Manager
Approval Manager
Task Manager
Automation Engine
Workflow History Service

Execution flow:

Transition Request
       ↓
Workflow Engine
       ↓
Approval
       ↓
State Change
       ↓
Tasks
       ↓
Automation
       ↓
History

The runtime remains:

metadata-driven;
security-aware;
audit-aware;
integration-aware;
lightweight compared to BPM engines.