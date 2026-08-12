# MOVEMENT_VALIDATION.md

## 1. Purpose

This document defines the validation model for movements generated during posting.

The purpose of validation is to ensure that all generated movements comply with platform rules, register contracts, and metadata definitions before persistence.

---

## 2. Architectural Principles

### 2.1 Separation of Responsibilities

Posting Handlers generate movements.

Movement Validators validate movements.

Validation must not be delegated to posting handlers.

---

### 2.2 Validation Before Persistence

No movement may be persisted before successful validation.

---

### 2.3 Metadata-Driven Validation

Validation rules are derived from metadata.

The validator must not contain business-specific logic.

---

### 2.4 Fail Fast

Validation stops at the first critical violation.

Invalid movements must never reach storage.

---

## 3. Validation Levels

Movement validation consists of several independent stages.

### 3.1 Structural Validation

Verifies movement structure.

Checks:

* movement_id
* document_id
* register_id
* period

Required fields must exist.

---

### 3.2 Register Reference Validation

Verifies that the referenced register exists.

Checks:

* register metadata availability
* register accessibility

---

### 3.3 Dimension Validation

Verifies:

* required dimensions exist
* dimension names are valid
* dimension values match metadata types

---

### 3.4 Resource Validation

Verifies:

* required resources exist
* resource types are valid
* resource values satisfy platform constraints

---

### 3.5 Attribute Validation

Verifies:

* attribute names are valid
* attribute types match metadata definitions

---

### 3.6 Movement Type Validation

Verifies:

* movement_type presence when required
* movement_type value validity

Allowed values:

* INCOME
* EXPENSE

---

### 3.7 Register Contract Validation

Verifies compliance with register posting contracts.

Examples:

Accumulation Register:

* movement_type required
* resources required

Information Register:

* movement_type optional

Accounting Register:

* account dimensions required

---

### 3.8 Type System Validation

Verifies platform types.

Examples:

* ULID
* DateTime
* Money
* Quantity
* Boolean
* Reference

---

## 4. Validation Pipeline

MovementSet

→ Structural Validation

→ Register Validation

→ Dimension Validation

→ Resource Validation

→ Contract Validation

→ Success

---

## 5. Validation Results

### 5.1 Success

Movement passes all validation stages.

### 5.2 Failure

Validation terminates.

Persistence is prohibited.

---

## 6. Validation Errors

Errors should contain:

* error code
* message
* movement identifier
* register identifier
* offending field

Example:

MissingRequiredDimension

InvalidResourceType

InvalidMovementType

UnknownRegister

ContractViolation

---

## 7. Relationship with Posting Lifecycle

Validation occurs after MovementSet generation and before persistence.

Posting Lifecycle:

Generate MovementSet

→ Validate

→ Persist

---

## 8. Relationship with Register Contracts

Movement Validator is the primary consumer of Register Posting Contracts.

Register contracts define validation requirements.

Validator enforces them.

---

## 9. Related Documents

* POSTING_ARCHITECTURE.md
* MOVEMENT_MODEL.md
* REGISTER_POSTING_CONTRACTS.md
* POSTING_LIFECYCLE.md
