# Register Events

## Purpose

Register Events communicate changes in register facts and register infrastructure state.

---

## Event Categories

### Movement Events

* MovementCreated
* MovementDeleted
* MovementChanged

### Totals Events

* TotalsUpdated
* TotalsRebuilt

### Register Events

* RegisterChanged

---

## Event Principles

Register Events are infrastructure events.

Register Events do not contain business logic.

Events communicate state changes only.

---

## Event Publication

Register Services publish events.

Consumers subscribe through runtime event infrastructure.

---

## Architectural Principle

Register Events describe changes in facts and infrastructure state while preserving subsystem independence.
