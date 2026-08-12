# Register Dependency Integration

## Purpose

Register Dependency Integration defines how registers participate in the platform Dependency Graph.

---

## Dependency Unit

Register State is the primary dependency node.

Movements are not dependency nodes.

---

## Change Propagation

RegisterChanged
↓
Dependency Graph
↓
Dirty Objects
↓
Recalculation

---

## Dependency Publishing

Registers publish change notifications.

Dependency Graph consumes register events and determines affected objects.

---

## Dirty Propagation

Register changes may affect:

* Reports;
* Analytics;
* Valuation calculations;
* Other dependent runtime objects.

Dependency propagation is managed exclusively by the Dependency Graph.

---

## Reposting Integration

Reposting participates in the same dependency mechanism as normal posting.

No special dependency model exists for reposting.

---

## Architectural Principle

Registers publish changes.

Dependency Graph manages propagation.
