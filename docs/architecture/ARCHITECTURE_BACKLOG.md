## AR-001

Title:
Valuation Architecture Introduction

Status:
Deferred

Origin:
Register Architecture Discussion

Description:
The platform distinguishes between
accounting facts and valuation facts.

Registers are expected to store accounting facts
and valuation inputs.

Valuation calculation is expected to be implemented
by a dedicated Valuation Architecture.

Affected Documents:
- REGISTER_ARCHITECTURE.md
- ARCHITECTURE_OVERVIEW.md
- REPORTING_ARCHITECTURE.md (future)

Review Trigger:
Start of Valuation Architecture design.

## AR-002

Title:
Movement Builder Status

Status:
Deferred

Origin:
Posting Architecture Audit

Description:
Movement Builder is currently treated as an
implementation detail.

Its architectural status will be revisited after
completion of Register Architecture.

Affected Documents:
- POSTING_ARCHITECTURE.md

Review Trigger:
Register Architecture completion.

## AR-003

Title:
Valuation Engine As Mandatory Cost Processing Layer

Status:
Accepted Architectural Assumption

Description:
All cost-related information must be processed
through the Valuation Engine, even when cost
calculation appears trivial.

The platform does not support direct cost facts.
Cost is always a valuation result.