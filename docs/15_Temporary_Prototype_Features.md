# Temporary Prototype Features

Last updated: 2026-07-28

This note identifies current Python prototype features that are temporary and
can be discarded, replaced, or redesigned later. It complements
[C# Carry-Forward Features](14_CSharp_Carry_Forward_Features.md), which records
the behavior that must survive the future rewrite.

Temporary means the feature helped prove the product direction, but the future
C#/.NET version should not copy it as-is.

## Temporary Implementation Choices

### PySide6-Specific UI Implementation

The future C# version should not copy the PySide widget tree, signal wiring,
object names, or custom Qt painting. The current UI proves the workspace shape,
but the implementation can be replaced with native C# desktop patterns.

Keep the behavior:

- persistent workflow navigation
- Incident Explorer
- Properties pane
- status bar
- editor screens
- site map workflow

Discard or replace:

- custom PySide6 folder tab painting
- Qt widget object-name contracts except as test inspiration
- PySide-specific signal and slot structure
- Qt layout details that only exist to make the prototype usable

### Single-User In-Memory Workspace

The current prototype uses an in-memory incident object graph as the working
state. This is useful for quick iteration, but it is not the long-term
collaboration model.

Keep the behavior:

- edits update a single authoritative incident record
- dependent views refresh after changes
- relationships remain consistent across screens

Discard or replace:

- assuming one user owns the whole active workspace
- treating local memory as the durable source of truth
- refreshing every UI view from a local object graph without server conflict
  handling

### JSON Files As Primary Storage

JSON save/load is useful for the prototype and should remain valuable as an
import/export or migration format. It should not be the main shared-data
storage model for the future product.

Keep the behavior:

- users can save and reopen incident data
- incident records can be exported for transfer, backup, or troubleshooting
- prototype data can be migrated forward

Discard or replace:

- JSON files as the primary operational database
- file-path based recent records as the only reopen workflow
- schema version 1 as the final long-term schema

### Demo Incident Bootstrap

The Pine Gulch demo incident is a useful test fixture and screenshot source.
It should not drive production behavior.

Keep the behavior:

- sample incident data for demos, tests, and onboarding
- realistic seed data for field-test scenarios

Discard or replace:

- auto-loading demo data as the normal startup state
- hardcoded demo names, devices, or relationships in production workflows

### Prototype Report Plumbing

Markdown, CSV, and HTML report generation proves that outputs matter. The exact
report code can be replaced.

Keep the behavior:

- human-readable incident summary output
- structured export output
- asset/person/network counts and assignments in reports

Discard or replace:

- direct file-writing report functions as the only report path
- fixed report layouts that do not support incident-specific templates
- output actions that only report the current demo-level fields

### Prototype Validation Rules

The current validation rules are a good first baseline, but they are not the
final operational rule set.

Keep the behavior:

- validation before save, export, or closeout
- specific messages that identify fixable issues

Discard or replace:

- a single flat list of validation strings as the final rule engine
- validation limited to demo-level structural checks
- lack of severity, category, responsible role, or resolution guidance

### Current Site Map Mechanics

The current QGraphics-based site map proves the network map interaction model.
The future implementation can use a different rendering/control stack.

Keep the behavior:

- buildings or locations on a map surface
- device icons attached to containers
- cable/link lines between endpoints
- drag, resize, anchor, zoom, center, undo, and redo
- summary overlay or equivalent quick status

Discard or replace:

- QGraphicsScene and QGraphicsView internals
- current coordinate defaults
- current icon loading implementation
- current visual styling and color choices

### Prototype Packaging

The current Python packaging and PyInstaller output are useful for trying the
prototype. They are not the long-term deployment model.

Keep the behavior:

- a simple way for a Windows user to launch the app
- repeatable build or packaging instructions

Discard or replace:

- PyInstaller as the default future installer
- Python virtual environment setup as an end-user requirement
- prototype build artifacts as release artifacts

## Features Not Yet Product Commitments

The following prototype details should not become requirements unless later
workflow design proves they are needed:

- exact folder-tab appearance
- exact menu item order beyond preserving familiar workflow areas
- exact field labels where the future data model improves terminology
- direct editing from every possible selected object
- report formats beyond the need for readable and structured outputs
- current controlled-list values as final agency-approved lists
- current test fixture names and sample incident values

## Migration Notes

Before discarding temporary pieces, preserve enough information to support the
future product:

- keep sample incident data for tests and demos
- keep a JSON import path until prototype incidents can be migrated
- keep screenshot and workflow docs as behavioral references
- keep validation examples as seed requirements for the future rule model

## Phase 1 Conclusion

The Python prototype should remain a product-learning tool. Its durable value is
the validated workflow shape and domain understanding, not the specific Python,
PySide, JSON, or PyInstaller implementation.
