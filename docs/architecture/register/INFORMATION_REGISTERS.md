# Information Registers

## Purpose

Information Registers store informational business facts.

Information Registers do not participate in accumulation.

Information Registers provide historical and current-state information.

---

## Logical Model

Information Register Record

* Identity
* Period
* Dimensions
* Resources
* Attributes

---

## Identity Model

Every record has:

* ULID identity;
* Business key;
* Version information.

Identity is immutable.

Business keys may be modified according to business rules.

---

## Versioning

Information Register records are versionable.

Modifications create new versions while preserving historical records.

Current records are identified through:

* version
* is_current

Historical records remain available for auditing and dependency tracking.

---

## Record Origin

Every record must contain origin information.

Required fields:

* source_type
* source_id

Supported source types:

* MANUAL
* DOCUMENT
* PROCESSING
* IMPORT
* SYSTEM

---

## Historical Model

Information Registers support historical state reconstruction.

Queries may retrieve information as of a specified moment in time.

---

## Architectural Principle

Every information fact should be traceable to its origin and historical evolution.
