# System Architecture

## Overview
FireIT Manager uses a layered architecture centered on a PySide6 desktop client. The application is designed to separate presentation, workflow orchestration, domain logic, and persistence concerns.

## Layered structure

```text
Presentation Layer
    │
Application Layer
    │
Business Layer
    │
Persistence Layer
```

## Major modules
- **app/** - Application entry points and startup
- **ui/** - Menus, toolbars, docks, canvas, and window shell
- **core/** - Cross-cutting services and workflow coordination
- **inventory/** - Inventory management domain
- **network/** - Network modeling and connectivity logic
- **reports/** - Report generation
- **persistence/** - Repositories and data access
- **graphics/** - Scene and visualization helpers
- **plugins/** - Extension hooks
- **resources/** - Static assets and configuration

## Communication patterns
- UI modules coordinate with application services rather than directly accessing storage.
- Domain logic remains independent of Qt widgets where practical.
- Data persistence is isolated behind repository abstractions.

## Design principles
- Separation of concerns
- Extensibility
- Testability
- Clear dependency flow
- Consistent naming and module boundaries

## Allowed dependencies
- PySide6 for desktop UI
- SQLite for local persistence
- NetworkX for graph-style network models

## Architectural reference
This document is the baseline for evaluating future architectural changes.
