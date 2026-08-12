# REGISTER_POSTING_CONTRACTS.md

## 1. Purpose

This document defines posting contracts used by registers.

A posting contract specifies the requirements that generated movements must satisfy before they can be accepted by a register.

Register contracts form the integration boundary between Posting Architecture and Register Architecture.

---

## 2. Architectural Principles

### 2.1 Register-Agnostic Posting

Posting Engine operates on a universal Movement model.

Register-specific requirements are defined through contracts.

---

### 2.2 Metadata-Driven Contracts

Register contracts are derived from register metadata.

Validation logic must not contain hardcoded register definitions.

---

### 2.3 Contract Enforcement

All generated movements must satisfy the target register contract.

Contract validation is mandatory.

---

### 2.4 Extensibility

New register types may introduce new contracts without requiring changes in Posting Engine.

---

## 3. Contract Structure

A contract may define:

* required dimensions;
* required resources;
* required attributes;
* movement type requirements;
* supported data types;
* custom validation rules.

---

## 4. Dimension Requirements

Dimensions define the accounting context of a movement.

Example:

Inventory Register

Required dimensions:

* warehouse
* product

A movement missing one of these dimensions is invalid.

---

## 5. Resource Requirements

Resources define measurable values.

Example:

Inventory Register

Required resources:

* quantity

Optional resources:

* amount

---

## 6. Attribute Requirements

Attributes provide additional analytical information.

Example:

* department
* project
* manager

Attributes may be optional or mandatory depending on register definition.

---

## 7. Movement Type Requirements

Contracts may require movement direction.

Supported values:

* INCOME
* EXPENSE

Example:

Accumulation Register

movement_type required

Example:

Information Register

movement_type not required

---

## 8. Contract Types

### 8.1 Accumulation Register Contract

Required:

* period
* dimensions
* resources
* movement_type

Optional:

* attributes

---

### 8.2 Information Register Contract

Required:

* period
* dimensions

Optional:

* resources
* attributes

movement_type not required

---

### 8.3 Accounting Register Contract (Future)

Required:

* account dimensions
* accounting resources

Additional accounting rules may apply.

---

### 8.4 Calculation Register Contract (Future)

Required:

* calculation dimensions
* result resources

Additional calculation rules may apply.

---

## 9. Contract Validation

Contracts are enforced by Movement Validator.

Validation includes:

* required field verification;
* type validation;
* movement type validation;
* metadata compliance.

---

## 10. Relationship with Register Metadata

Register metadata defines:

* dimensions;
* resources;
* attributes;
* register type.

Posting contracts are generated from this metadata.

---

## 11. Relationship with Posting Architecture

Posting Handlers generate movements.

Register Contracts define movement requirements.

Movement Validators enforce contracts.

---

## 12. Future Extensions

Possible future extensions:

* balance constraints;
* uniqueness constraints;
* temporal constraints;
* accounting-specific rules;
* calculation-specific rules.

These extensions must remain contract-based.

---

## 13. Related Documents

* POSTING_ARCHITECTURE.md
* MOVEMENT_MODEL.md
* MOVEMENT_VALIDATION.md
* POSTING_DEPENDENCIES.md
* REGISTER_ARCHITECTURE.md
