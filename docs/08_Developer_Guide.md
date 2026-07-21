# Developer Guide

## Naming conventions
- Use descriptive Python module names in snake_case.
- Use class names in PascalCase.
- Use function names in snake_case.
- Use constants in uppercase with underscores.

## File layout
- Keep UI classes in the UI package.
- Keep domain entities and services in dedicated modules.
- Avoid placing business logic inside Qt widget classes.

## Import rules
- Prefer absolute imports from the package root.
- Keep imports ordered and minimal.
- Avoid circular imports by keeping dependencies flowing outward from domain logic to infrastructure.

## Coding standards
- Write clear, small functions.
- Prefer composition over deep inheritance.
- Handle errors explicitly and log meaningful context.
- Add docstrings to public classes and functions.

## Logging
- Use structured logging for runtime and debugging information.
- Avoid noisy logs in normal execution paths.

## Exception handling
- Catch specific exceptions where practical.
- Avoid swallowing errors silently.
- Raise meaningful domain exceptions when appropriate.

## Docstring format
Use concise docstrings that describe purpose, inputs, and outputs when relevant.

## Testing expectations
- Add tests for new behavior and regressions.
- Favor small unit tests around domain logic and integration tests around major workflows.
- Keep tests deterministic and isolated from desktop environment dependencies where possible.
