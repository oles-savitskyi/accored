# Configuration Domain Model

## Purpose

The Configuration Domain Model defines the core concepts used to represent business applications built on top of the AcCore platform.

A configuration is a metadata-based business application assembled from platform capabilities and business metadata.

The Configuration Domain is responsible for:

- organizing metadata;
- grouping business functionality;
- versioning configurations;
- packaging configurations;
- extending configurations.

The Configuration Domain does not define business objects themselves.
Business objects belong to Metadata Architecture.

---

# Architectural Principles

## Platform And Configuration Are Separate

The platform provides infrastructure services.

Configurations provide business functionality.

Conceptually:

Platform
    +
Configuration
    =
Business Application

---

## Configuration Is Metadata-Based

Configurations are composed of metadata definitions.

Configurations do not require modification of platform code.

---

## Configuration Owns Business Structure

Configurations define:

- catalogs;
- documents;
- registers;
- reports;
- workflows;
- processings;
- integrations;
- security definitions.

The platform executes them.

---

## Extensions Are First-Class Citizens

Configurations may be extended without modifying the original configuration.

---

## Runtime Executes Unified Metadata

Runtime operates on a unified metadata model assembled from:

- platform metadata;
- configuration metadata;
- extension metadata.

---

# Domain Scope

The Configuration Domain consists of the following entities:

Configuration
ConfigurationVersion
ConfigurationPackage
Extension
ExtensionVersion
MetadataModule

---

# Configuration

## Purpose

Represents a business application built on top of the platform.

Examples:

- Standard ERP
- Retail ERP
- Manufacturing ERP

---

## Responsibilities

- define business functionality;
- organize metadata modules;
- provide deployment unit;
- define upgrade path.

---

## Attributes

Configuration
├── id
├── code
├── name
├── description
└── status

---

# ConfigurationVersion

## Purpose

Represents a version of a configuration.

Examples:

- 1.0
- 1.1
- 2.0

---

## Responsibilities

- version tracking;
- compatibility control;
- upgrade support.

---

## Attributes

ConfigurationVersion
├── id
├── version
├── released_at
└── compatibility_info

---

# ConfigurationPackage

## Purpose

Represents a distributable package.

Examples:

- accore-standard-1.0
- retail-extension-2.1

---

## Responsibilities

- installation;
- deployment;
- distribution.

---

## Attributes

ConfigurationPackage
├── id
├── package_name
├── package_version
└── checksum

---

# Extension

## Purpose

Represents an extension applied to a configuration.

Examples:

- CRM Extension
- Payroll Extension
- Warehouse Extension

---

## Responsibilities

- extend metadata;
- add functionality;
- customize behavior.

---

## Attributes

Extension
├── id
├── code
├── name
├── description
└── status

---

# ExtensionVersion

## Purpose

Represents a version of an extension.

---

## Responsibilities

- extension upgrades;
- compatibility tracking.

---

## Attributes

ExtensionVersion
├── id
├── version
├── released_at
└── compatibility_info

---

# MetadataModule

## Purpose

Represents a logical group of metadata.

Examples:

- Sales
- Purchasing
- Inventory
- Accounting
- CRM

---

## Responsibilities

- organize metadata;
- define business boundaries;
- simplify deployment.

---

## Attributes

MetadataModule
├── id
├── code
├── name
└── description

---

# Relationships

## Configuration → MetadataModule

Configuration
        1:N
MetadataModule

A configuration consists of multiple metadata modules.

---

## Configuration → ConfigurationVersion

Configuration
        1:N
ConfigurationVersion

A configuration evolves through versions.

---

## Configuration → ConfigurationPackage

Configuration
        1:N
ConfigurationPackage

Configurations may be distributed through packages.

---

## Configuration → Extension

Configuration
        1:N
Extension

A configuration may be extended.

---

## Extension → ExtensionVersion

Extension
      1:N
ExtensionVersion

Extensions evolve independently.

---

## Extension → MetadataModule

Extension
      1:N
MetadataModule

Extensions may contribute metadata modules.

---

# Domain Diagram

Configuration
      |
      +----------------------+
      |                      |
      v                      v
MetadataModule      ConfigurationVersion
      |
      v
ConfigurationPackage

Configuration
      |
      v
Extension
      |
      +----------------------+
      |                      |
      v                      v
MetadataModule      ExtensionVersion

---

# Ownership Boundaries

Configuration owns:

- configuration structure;
- module organization;
- packaging;
- versioning;
- extension model.

Configuration does not own:

- metadata definitions;
- runtime execution;
- security services;
- workflow execution;
- integration execution;
- storage implementation.

---

# Out Of Scope

The following concepts are intentionally excluded:

- Marketplace
- Plugin Repository
- Tenant Management
- Deployment Infrastructure
- Source Control Integration
- Arbitrary User Code

These concerns belong to other architectures.

---

# Domain Model Summary

The Configuration Domain consists of:

- Configuration
- ConfigurationVersion
- ConfigurationPackage
- Extension
- ExtensionVersion
- MetadataModule

The domain provides the structural foundation required to organize, version, package, install, and extend business applications built on the AcCore platform.