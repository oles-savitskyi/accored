# ADR-WF-001

Я бы сформулировал решение так.

Title

Hybrid Workflow Model

Decision

AcCore adopts a metadata-driven hybrid workflow model combining:

State Machines
Approval Flows
Task Generation
Lightweight Process Automation

AcCore does not implement a full BPM engine.

Workflow definitions are represented through metadata and executed by Runtime.

Consequences

Workflow remains understandable for SMB deployments.
Approval processes are supported.
Automation is supported.
Security and Audit integration remain straightforward.
Runtime complexity remains controlled.
Future BPM integration remains possible without redesigning the platform.