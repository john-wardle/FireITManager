# ADR-003: Data Storage

## Status
Proposed

## Context
The application needs local, structured persistence that can grow with incident data and future reporting workflows.

## Decision
Use SQLite as the initial persistence layer.

## Why
- Simple deployment and local file-based storage.
- Well suited to desktop and offline workflows.
- Easy to evolve with migrations as the schema grows.

## Alternatives considered
- JSON files
- PostgreSQL only
- Cloud-only storage

## Consequences
- Data will be stored locally by default.
- Future sync or multi-user features would require a separate architecture layer.
