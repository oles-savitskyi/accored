# Configuration Model

## Purpose

The Configuration Model defines how configurations are assembled, extended, and executed on top of the AcCore platform.

The model describes:

- metadata composition;
- extension application;
- runtime metadata assembly;
- configuration isolation;
- configuration execution.

The model establishes the relationship between Platform, Configuration, Extension, and Runtime.

---

# Architectural Principles

## Platform And Configuration Are Independent

The platform provides infrastructure capabilities.

Configurations provide business functionality.

Neither layer owns the other.

Conceptually:

Platform
    +
Configuration
    =
Business Application

---

## Runtime Executes Metadata

Runtime never executes configurations directly.

Runtime executes metadata assembled from multiple sources.

---

## Single Runtime Metadata Model

At runtime there must be exactly one metadata model.

Conceptually:

Platform Metadata
        +
Configuration Metadata
        +
Extension Metadata
        =
Runtime Metadata Model

---

## Configuration Is Declarative

Configurations define structure and behavior through metadata.

Configurations do not modify platform implementation.

---

## Extensions Never Modify Platform

Extensions may extend configurations.

Extensions may not alter platform architecture.

---

# Metadata Layers

AcCore consists of three metadata layers.

Layer 1

Platform Metadata

Layer 2

Configuration Metadata

Layer 3

Extension Metadata

---

# Platform Metadata

Platform Metadata is owned by the platform.

Examples:

- object types;
- system metadata;
- runtime services;
- security metadata;
- workflow metadata.

Platform Metadata defines infrastructure capabilities.

---

# Configuration Metadata

Configuration Metadata defines business functionality.

Examples:

- catalogs;
- documents;
- registers;
- reports;
- workflows;
- processings.

Configuration Metadata depends on Platform Metadata.

---

# Extension Metadata

Extension Metadata customizes or extends a configuration.

Examples:

- additional fields;
- additional reports;
- additional workflows;
- additional processings.

Extensions depend on Configuration Metadata.

---

# Metadata Composition Model

Metadata composition follows a layered model.

Conceptually:

Platform Metadata
        ↓
Configuration Metadata
        ↓
Extension Metadata
        ↓
Runtime Metadata Model

---

# Runtime Metadata Model

Runtime operates exclusively on the Runtime Metadata Model.

Runtime never distinguishes between:

- platform metadata;
- configuration metadata;
- extension metadata.

After assembly:

All metadata becomes a single model.

---

# Metadata Assembly

Metadata assembly is performed during configuration loading.

Conceptually:

Load Platform Metadata
        ↓
Load Configuration Metadata
        ↓
Load Extension Metadata
        ↓
Validate Model
        ↓
Build Runtime Metadata Model

---

# Validation Rules

The assembly process validates:

- identifier uniqueness;
- dependency consistency;
- reference integrity;
- extension compatibility.

Assembly fails if validation fails.

---

# Dependency Model

Dependencies are directional.

Allowed:

Platform
      ↓
Configuration
      ↓
Extension

---

Forbidden:

Extension
      ↓
Platform

Configuration
      ↓
Platform Modification

Extension
      ↓
Extension

---

# Extension Model

Extensions are additive.

Extensions may:

- add metadata;
- augment metadata;
- configure metadata.

---

Extensions may not:

- replace platform components;
- modify runtime services;
- bypass security;
- bypass workflow;
- bypass integration.

---

# Metadata Augmentation

Extensions may augment existing metadata.

Examples:

Document
      ↓
Add Field

Report
      ↓
Add Dataset

Workflow
      ↓
Add State

Role
      ↓
Add Permission

---

# Metadata Override Policy

The default policy is:

Augment Rather Than Replace

Extensions should extend metadata instead of replacing it.

---

Replacement is considered exceptional behavior.

---

# Configuration Isolation

Each configuration is isolated from platform implementation details.

Configurations interact only through supported metadata contracts.

---

# Runtime Interaction

After assembly:

Runtime Metadata Model
          ↓
Runtime Architecture
          ↓
Execution

All runtime subsystems use the same model.

---

# Security Interaction

Security metadata participates in composition.

Examples:

Roles
Permissions
Policies

Security Runtime executes the assembled result.

---

# Workflow Interaction

Workflow definitions participate in composition.

Examples:

States
Transitions
Approvals
Automation Rules

Workflow Runtime executes the assembled result.

---

# Reporting Interaction

Report metadata participates in composition.

Examples:

Datasets
Reports
Layouts

Reporting Runtime executes the assembled result.

---

# Integration Interaction

Integration definitions participate in composition.

Examples:

Contracts
Endpoints
Events

Integration Runtime executes the assembled result.

---

# Upgrade Model

Configuration upgrades replace metadata versions.

Conceptually:

Version N
      ↓
Upgrade
      ↓
Version N+1

The platform remains unchanged.

---

# Extension Upgrade Model

Extensions evolve independently.

Conceptually:

Extension Version N
          ↓
Upgrade
          ↓
Extension Version N+1

---

# Composition Flow

Platform Metadata
        ↓
Configuration Metadata
        ↓
Extension Metadata
        ↓
Validation
        ↓
Runtime Metadata Model
        ↓
Runtime Execution

---

# Configuration Formula

Conceptually:

Platform
      +
Configuration
      +
Extensions
      =
Business Application

---

# Metadata Formula

Conceptually:

Platform Metadata
        +
Configuration Metadata
        +
Extension Metadata
        =
Runtime Metadata Model

---

# Model Summary

The Configuration Model defines a layered metadata composition architecture.

Core principles:

- Platform and Configuration are separate;
- Runtime executes metadata;
- Metadata is assembled into a unified model;
- Extensions are additive;
- Dependencies are directional;
- Runtime operates on a single metadata model.

The result is a predictable, upgradeable, and metadata-driven application architecture aligned with the core principles of AcCore.