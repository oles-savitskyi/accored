# AcCore Metadata Model

**Status:** Draft

**Version:** 0.1

**Language:** English

---

# 1. Purpose

This document defines the conceptual model of metadata in the AcCore platform.

Its purpose is to describe the fundamental concepts from which all business information systems are constructed.

The Metadata Model is independent of implementation technologies and serves as the foundation for the Metadata Architecture.

This document is normative.

---

# 2. Design Principles

Metadata is the declarative description of a business information system.

Metadata defines the structure and behavior of a system rather than its implementation.

The Metadata Model represents business concepts independently of programming languages, storage technologies, and user interface frameworks.

Metadata is the single source of truth for the structure and behavior of configurations.

---

# 3. Fundamental Concepts

## 3.1 Metadata

Metadata is a declarative model describing a business information system.

Metadata defines business structures, relationships, and behavior independently of implementation.

---

## 3.2 Metadata Object

A Metadata Object is the fundamental building block of metadata.

Every element of a configuration is represented as a Metadata Object.

Metadata Objects may contain other Metadata Objects.

---

## 3.3 Metadata Type

A Metadata Type defines the semantic role of a Metadata Object.

Examples of Metadata Types include business objects, user interface objects, and system objects.

The complete set of Metadata Types is defined by the Platform.

---

## 3.4 Metadata Property

A Metadata Property describes a characteristic of a Metadata Object.

Properties define the attributes of metadata rather than business data.

---

## 3.5 Metadata Relationship

A Metadata Relationship defines a conceptual connection between Metadata Objects.

Relationships express structure rather than execution.

---

# 4. Hierarchical Organization

Metadata is organized as a hierarchy.

Metadata
    │
    ▼
Metadata Objects
    │
    ├── contain Metadata Objects
    ├── have Properties
    └── participate in Relationships


The hierarchy represents ownership rather than execution.

---

# 5. Separation of Responsibilities

The Metadata Model defines structure.

The Runtime defines execution.

The User Interface defines presentation.

Storage defines persistence.

These responsibilities remain independent.

---

# 6. Conceptual Rules

Every Metadata Object has exactly one Metadata Type.

Metadata Objects may contain other Metadata Objects.

Metadata Relationships connect Metadata Objects.

Properties belong to Metadata Objects.

Metadata remains independent of Runtime implementation.

---

# 7. Evolution

New platform functionality should extend the Metadata Model by introducing new Metadata Types rather than modifying existing concepts whenever possible.

The conceptual integrity of the Metadata Model shall be preserved throughout the evolution of the platform.

---

# 8. Final Principle

Everything that defines a business information system is represented as metadata.

Everything that executes a business information system is outside the Metadata Model.
