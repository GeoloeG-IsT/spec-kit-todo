<!--
Sync Impact Report:
- Version change: 1.0.0 (initial constitution)
- Principles defined: 8 core principles
- Added sections: Architecture Standards, Development Workflow
- Templates requiring updates: ✅ Compatible with all existing templates
- Follow-up TODOs: RATIFICATION_DATE needs confirmation
-->

# Spec Kit Todo Constitution

## Core Principles

### I. Clean Architecture
Every component MUST be organized into distinct layers with clear boundaries. Domain logic MUST be independent of frameworks, UI, and external agencies. Dependencies MUST point inward toward the domain layer, never outward. This ensures business logic remains testable and framework-agnostic.

### II. Domain-Driven Design (DDD)
The domain model MUST be the heart of the software design. Bounded contexts MUST be clearly defined with explicit interfaces. Ubiquitous language MUST be used consistently across code, documentation, and communication. Complex business logic MUST be encapsulated in domain entities and value objects.

### III. Test-First Development
TDD is mandatory: Tests MUST be written before implementation. Red-Green-Refactor cycle MUST be strictly enforced. Every feature MUST have comprehensive test coverage including unit, integration, and contract tests. Tests MUST fail before implementation and pass after.

### IV. Library-First Approach
Every feature MUST start as a standalone, reusable library. Libraries MUST be self-contained, independently testable, and well-documented. Libraries MUST expose functionality via clear interfaces and CLI commands. No organizational-only libraries without clear reusable purpose.

### V. SOLID Principles
Single Responsibility: Each class/module MUST have one reason to change. Open/Closed: Software entities MUST be open for extension but closed for modification. Liskov Substitution: Derived classes MUST be substitutable for base classes. Interface Segregation: Interfaces MUST be client-specific, not general-purpose. Dependency Inversion: High-level modules MUST NOT depend on low-level modules; both MUST depend on abstractions.

### VI. DRY (Don't Repeat Yourself)
Every piece of knowledge MUST have a single, unambiguous representation in the system. Code duplication MUST be eliminated through abstraction and modularization. Configuration and constants MUST be defined once and referenced everywhere.

### VII. KISS (Keep It Simple, Stupid)
Solutions MUST be as simple as possible but no simpler. Complexity MUST be justified and documented in the Complexity Tracking section. Prefer straightforward implementations over clever ones. Avoid premature optimization and over-engineering.

### VIII. YAGNI (You Aren't Gonna Need It)
Features MUST NOT be added until they are actually needed. Speculative generality MUST be avoided. Focus on current requirements, not hypothetical future needs. Refactor when requirements change, don't anticipate.

## Architecture Standards

All projects MUST follow the layered architecture pattern with clear separation of concerns. The domain layer MUST remain pure and free from infrastructure concerns. External dependencies MUST be abstracted behind interfaces defined in the domain layer. Event-driven patterns SHOULD be used for cross-boundary communication where appropriate.

## Development Workflow

1. Feature specification MUST be created before any implementation
2. Constitutional compliance MUST be verified at planning stage
3. Tests MUST be written and fail before implementation begins
4. Code review MUST verify adherence to all principles
5. Integration tests MUST validate bounded context interactions
6. Documentation MUST use ubiquitous language consistently

## Governance

The Constitution supersedes all other development practices and guidelines. Any deviation from constitutional principles MUST be documented with justification in the Complexity Tracking section of implementation plans. Amendments require technical justification, team consensus, and migration plan for existing code.

All pull requests and code reviews MUST verify constitutional compliance. Complexity beyond these principles MUST be explicitly justified. Development guidance is maintained in project-specific agent files (CLAUDE.md, .github/copilot-instructions.md, etc.) which MUST align with this constitution.

Amendment procedure:
1. Propose changes with clear rationale
2. Document impact on existing codebase
3. Update all dependent templates and documentation
4. Increment version following semantic versioning

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Needs user confirmation | **Last Amended**: 2025-01-19