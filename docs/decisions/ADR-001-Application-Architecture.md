# ADR-001: Application Architecture

## Status
Accepted

## Context
The project requires a desktop application with a rich, dockable interface and a modular codebase that can evolve over time.

## Decision
Use PySide6 as the desktop UI framework.

## Why
- Provides a native desktop experience.
- Supports robust dockable interfaces and canvas-style interactions.
- Has a mature ecosystem and strong Python integration.

## Alternatives considered
- Tkinter
- Kivy
- Electron

## Consequences
- The project will depend on Qt and PySide6.
- The UI should remain modular and avoid tight coupling to business logic.
