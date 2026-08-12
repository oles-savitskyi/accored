ADR-SEC-001

Title

Metadata-Driven Hybrid Access Control

Decision

AcCore uses a hybrid access control model combining:

RBAC (roles)
Permission-based authorization
Metadata-defined security objects
Context constraints

Authorization decisions are performed against metadata objects rather than implementation classes.

Consequences

Security remains independent from business code.
New metadata objects automatically participate in security.
Role explosion is avoided.
Fine-grained restrictions remain possible.
Security model scales from SMB installations to enterprise deployments.