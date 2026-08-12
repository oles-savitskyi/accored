# AcCore Documentation Standard

**Status:** Draft

**Version:** 0.1

**Language:** English

---

# 1. Purpose

This document defines the documentation standards used throughout the AcCore project.

Its purpose is to ensure that all project documentation remains consistent, maintainable, and suitable as a long-term engineering specification.

This document is normative.

---

# 2. Documentation Philosophy

Documentation is considered a fundamental component of AcCore.

Normative documents define the platform before it is implemented.

Documentation is maintained together with the source code and evolves as an integral part of the project.

---

# 3. General Principles

All documentation shall be:

- clear;
- consistent;
- technology-independent whenever possible;
- implementation-independent unless implementation is the subject of the document;
- concise;
- logically structured;
- written in English.

Documentation should explain concepts before implementation details.

Each document shall answer one primary question.

---

# 4. Document Classification

AcCore documentation is divided into the following categories.

## Normative Documents

Normative documents define the platform specification and establish mandatory engineering rules.

Examples:

- ENGINEERING_PRINCIPLES.md
- SCOPE.md
- VISION.md
- GLOSSARY.md
- CONCEPT.md
- ARCHITECTURE.md
- ADR documents

---

## Informative Documents

Informative documents explain, demonstrate, or describe the implementation without defining the platform itself.

Examples:

- Developer Guide
- Administrator Guide
- User Guide
- Tutorials
- Examples

---

# 5. Documentation Hierarchy

Project documentation follows the hierarchy below.

```
Engineering Principles
        ↓
Scope
        ↓
Vision
        ↓
Glossary
        ↓
Concept
        ↓
Architecture
        ↓
Architecture Decision Records
        ↓
Module Specifications
        ↓
Implementation Documentation
```

A lower-level document shall not contradict a higher-level document.

---

# 6. Document Structure

Normative documents should follow a common structure.

- Title
- Status
- Version
- Language
- Purpose
- Main Content
- References (when applicable)
- Revision History (when applicable)

---

# 7. Language

All normative documentation shall be written in English.

Translations may be provided for user-facing documentation, including user manuals and administrator guides.

The English version is the authoritative version.

---

# 8. Terminology

Normative terms shall have a single definition.

Definitions shall be maintained in GLOSSARY.md.

Documents shall use glossary terms consistently.

---

# 9. Engineering Requirements

Normative documentation shall distinguish between:

- definitions;
- architectural principles;
- requirements;
- constraints;
- implementation guidance.

Normative language should be used where appropriate.

Examples include:

- shall
- shall not
- should
- may

Definitions should use declarative language.

---

# 10. Architecture Decisions

Major architectural decisions shall be documented using Architecture Decision Records (ADR).

Architecture shall not depend on undocumented decisions.

---

# 11. Documentation Before Implementation

Normative specifications should be completed before implementing corresponding platform functionality.

Implementation may refine documentation but shall not silently redefine it.

---

# 12. Documentation Quality

Every document should satisfy the following criteria.

- It answers a clearly defined question.
- It has a well-defined scope.
- It avoids duplication.
- It avoids implementation details unless required.
- It remains understandable years after publication.
- It contributes to architectural consistency.

---

# 13. Final Principle

Documentation is part of the platform.

A feature is not considered complete until its corresponding documentation has been reviewed and approved.

Architecture is understood through documentation before it is understood through code.