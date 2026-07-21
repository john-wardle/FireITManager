# Project Rules

## Core rules
- Never put business logic inside PySide widgets.
- Always use UUID values in memory.
- Always use datetime values in memory.
- Prefer composition over inheritance.
- Every public class should have type hints.
- Avoid code duplication.
- Keep UI and persistence separate.
- Use dataclasses where appropriate.
- Follow the existing package structure.
- Keep new features modular and testable.

## Domain model rules
- Treat the domain layer as the source of truth for business concepts.
- Do not add persistence logic to the models.
- Do not add GUI code to the models.
- Keep relationships explicit and readable.

## Documentation expectations
- Update the relevant documentation when behavior changes.
- Keep ADRs current when architectural decisions change.

# FireIT Manager Rules

You are working inside the FireIT Manager workspace.

Assume you have access to the indexed codebase through Continue.

Before answering questions about the project:

1. Search the codebase.
2. Read any relevant files.
3. Summarize existing implementation.
4. Never state that you cannot access the project unless a search fails.

The project documentation is authoritative.

Read these before making changes:

docs/00_Project_Charter.md
docs/01_System_Architecture.md
docs/02_Requirements.md
docs/03_UI_Design.md

Do not duplicate functionality.

Maintain architectural consistency.

Explain WHY changes are made.

Never implement an entire milestone in one response.

Break milestones into logical engineering tasks.

Each task should:
- modify fewer than 5 files
- contain fewer than 400 lines of generated code
- compile independently
- be testable
- preserve project architecture

Wait for user review before continuing.
