# VALUATION_METHODS.md

## Purpose

This document defines the valuation method framework used by AcCoreD.

Valuation methods are responsible for transforming quantity consumption requests into valuation consumption facts.

Valuation methods are implementation strategies and are not part of the valuation data model.

---

# Architectural Role

Valuation methods participate in the Consumption Processing stage of the valuation lifecycle.

```text
Issue Movement
        ↓
Consumption Processor
        ↓
Valuation Method
        ↓
ValuationConsumption
```

Valuation methods do not create:

* valuation layers;
* valuation adjustments;
* valuation allocations;
* cost movements;
* cost balances.

---

# Responsibilities

Valuation methods are responsible for:

* selecting valuation layers;
* determining consumed quantities;
* producing valuation consumption facts.

Valuation methods are not responsible for valuation result calculation outside of consumption generation.

---

# Method Contract

## Input

A valuation method receives:

* asset type;
* valuation context;
* requested quantity;
* candidate valuation layers.

The valuation context may contain:

* valuation date;
* inventory dimensions;
* configuration-specific information.

---

## Output

A valuation method produces one or more:

```text
ValuationConsumption
```

records.

Each consumption record shall identify:

* consumed layer;
* consumed quantity;
* base cost contribution;
* source economic event.

---

# Determinism Requirement

Valuation methods shall be deterministic.

Given identical inputs:

```text
Asset Type
Valuation Context
Valuation Layers
Consumption Request
```

the method shall always produce identical valuation consumptions.

---

# Reproducibility Requirement

Valuation results shall be reproducible.

The same source facts shall always reconstruct identical valuation history.

Valuation methods shall not depend on:

* user interface state;
* session state;
* execution timing;
* external services.

---

# Auditability Requirement

Valuation methods shall produce explicit valuation facts.

The complete valuation chain shall be reconstructable:

```text
Layer
    ↓
Consumption
    ↓
Cost Movement
```

No hidden calculations are permitted.

---

# Registration Model

Valuation methods are metadata-registered extensions.

The platform provides a valuation method contract.

Methods are registered through metadata and resolved by the Valuation Engine at runtime.

Built-in and custom methods use the same registration mechanism.

---

# Method Resolution

Valuation method selection is determined by Asset Type metadata.

Example:

```text
Inventory
    → FIFO

Manufactured Goods
    → Average Cost

Precious Metals
    → Specific Identification
```

Valuation Engine resolves the method during consumption processing.

---

# Method Lifecycle

## Registration

Method becomes available to the system.

## Resolution

Method is selected based on Asset Type metadata.

## Execution

Method receives a consumption request.

## Consumption Generation

Method produces valuation consumptions.

## Completion

Processing returns control to the valuation pipeline.

---

# Built-In Methods

The platform may provide standard implementations.

Examples:

* FIFO;
* Average Cost;
* Specific Identification.

Built-in methods are ordinary valuation method extensions.

They do not receive special treatment from the platform.

---

# Custom Methods

Configurations may provide custom valuation methods.

Custom methods shall comply with:

* valuation method contract;
* determinism requirements;
* reproducibility requirements;
* auditability requirements.

---

# Architectural Principles

1. Valuation methods are strategies.

2. Valuation methods are metadata-registered extensions.

3. Valuation methods produce valuation consumptions.

4. Valuation methods do not define valuation storage structures.

5. Valuation methods do not create cost balances.

6. Valuation methods shall be deterministic.

7. Valuation methods shall be auditable.

8. Valuation methods shall be reproducible.
