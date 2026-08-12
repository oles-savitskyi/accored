WORKFLOW_MODEL.md
Purpose

The Workflow Model defines how workflow instances are executed within AcCore.

The model describes:

state transitions;
approval evaluation;
task generation;
automation execution;
workflow completion.

The model is independent from business applications, storage implementation, and user interfaces.

Architectural Principles
Workflow Is State-Driven

Workflow execution is based on state transitions.

A workflow instance always exists in exactly one state.

WorkflowInstance
        ↓
Current State
Transitions Are Explicit

State changes occur only through defined transitions.

Forbidden:

Direct State Modification

Allowed:

Transition Execution
Workflow Does Not Bypass Security

Workflow may request a transition.

Security determines whether it is allowed.

Workflow
      ↓
Security
      ↓
Allow / Deny
Workflow Is Deterministic

Given the same:

Current State
Transition
Approvals
Conditions

the workflow must produce the same result.

Workflow Is Auditable

Every state transition produces audit events.

Execution Model

Workflow execution follows a single lifecycle.

Current State
       ↓
Transition Request
       ↓
Authorization Check
       ↓
Approval Evaluation
       ↓
Transition Execution
       ↓
Task Processing
       ↓
Automation Execution
       ↓
New State
Workflow Instance

A Workflow Instance represents a running workflow.

At any moment:

WorkflowInstance
       ↓
Current State

Example:

Sales Order
      ↓
Approved
State Model

A state represents a business lifecycle stage.

Examples:

Draft
Approved
Posted
Closed
Cancelled

States are metadata.

States do not contain business logic.

Transition Model

A transition moves an instance between states.

Conceptually:

Source State
       ↓
Transition
       ↓
Target State

Example:

Draft
   ↓ Approve
Approved
Transition Request

Workflow execution begins with a transition request.

Example:

Approve Sales Order

The system resolves:

Current State
Requested Transition
Target State
Transition Validation

The workflow engine validates:

Transition Exists
Current State Matches
Transition Enabled

If validation fails:

Transition Rejected
Security Evaluation

Before execution, workflow requests authorization.

Conceptually:

Transition
      ↓
Security Check
      ↓
Allow / Deny

Example:

Approve

requires:

Document.SalesOrder.Approve

permission.

Approval Evaluation

A transition may require approval.

Example:

Draft
      ↓
Approved

requires:

Manager Approval

The workflow engine evaluates all required approval rules.

Approval Outcomes

Possible results:

Approved
Rejected
Pending
Approved

Transition may continue.

Rejected

Transition is denied.

Pending

Workflow remains in the current state.

Additional actions may be required.

Task Model

Workflow may generate tasks.

Example:

Approve Invoice

assigned to:

Chief Accountant

Tasks support:

Assignment
Completion
Cancellation

Tasks do not execute transitions automatically.

Automation Model

Workflow supports lightweight automation.

Automation is event-driven.

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
Automation Execution

After successful transition:

Transition
      ↓
Automation Rules
      ↓
Actions

Automation does not alter workflow history.

State Change

If all checks pass:

Current State
      ↓
Target State

becomes:

New Current State
Workflow Completion

A workflow may reach a final state.

Example:

Closed

Cancelled

Final states terminate execution.

WorkflowInstance
       ↓
Completed
Workflow History

Every transition produces history records.

Example:

Draft → Approved

Approved → Posted

Posted → Closed

History supports:

Audit
Traceability
Investigation
Audit Integration

Workflow actions produce audit events.

Examples:

Transition Requested

Transition Executed

Approval Granted

Approval Rejected

Task Created
Security Integration

Workflow delegates authorization.

Workflow never evaluates permissions directly.

Workflow
      ↓
Security Architecture
      ↓
Decision
Integration Architecture Interaction

Workflow may trigger:

API Calls

Events

Imports

Exports

through Automation Rules.

Workflow does not implement integration logic.

Posting Interaction

Workflow may invoke Posting.

Example:

Approved
      ↓
Post Document

Posting remains part of Posting Architecture.

Workflow Execution Formula

Conceptually:

Transition Request
        +
Authorization
        +
Approvals
        +
Validation
        =
Transition Execution
Workflow Flow
Current State
       ↓
Transition Request
       ↓
Validate Transition
       ↓
Security Check
       ↓
Approval Evaluation
       ↓
Execute Transition
       ↓
Generate Tasks
       ↓
Run Automation
       ↓
New State
Workflow Model Summary

Workflow execution in AcCore is based on controlled state transitions.

Core execution chain:

State
      ↓
Transition
      ↓
Security
      ↓
Approval
      ↓
Execution
      ↓
Automation
      ↓
New State

The model provides:

deterministic workflow execution;
metadata-driven behavior;
approval support;
task generation;
automation support;
security integration;
auditability.