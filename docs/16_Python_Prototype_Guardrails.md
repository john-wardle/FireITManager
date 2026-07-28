# Python Prototype Guardrails

Last updated: 2026-07-28

This note records the Phase 1 decision to avoid adding large new systems to the
Python app unless they clarify the product. The Python application remains the
working prototype while the long-term C#/.NET direction is designed.

## Decision

Do not expand the Python prototype into the final production architecture. Use
it to clarify workflows, data relationships, screen behavior, validation needs,
and migration evidence.

Large new Python systems should be deferred unless they answer a concrete
product question that cannot be answered with documentation, a small fixture, a
focused UI change, or a test.

## Allowed Python Prototype Work

These changes are acceptable during the remaining prototype phase:

- bug fixes that keep the current prototype demonstrable
- focused tests that protect current behavior
- small UI adjustments that clarify an ITSS workflow
- screenshot, workflow, and decision documentation
- sample data improvements for demos or field-test planning
- validation rule experiments that expose real data-quality needs
- export/import helpers needed to preserve prototype data for migration
- small data-model experiments that directly inform the future shared model

Each change should be small enough to review, test, and either keep or discard
without delaying the future architecture.

## Work To Avoid In Python

These systems should not be built in the Python prototype unless a separate
decision record explains why they are necessary:

- incident server
- multi-user synchronization
- real-time update bus
- production database schema and migrations
- authentication and role-based permissions
- mobile or tablet checklist client
- plugin system
- full help desk module
- large report designer
- GIS engine
- telemetry collection service
- production installer strategy
- major visual redesign unrelated to workflow clarity

These belong to later phases and should be designed for the long-term stack.

## Decision Checklist For Any New Python Feature

Before adding a Python feature, answer these questions:

- What product question does this clarify?
- Can the question be answered with documentation or a smaller test?
- Does the change preserve the current modular architecture?
- Does it touch fewer than five files?
- Can it be verified with existing or focused tests?
- Will it be easy to discard when the C# version replaces the prototype?
- Does it avoid creating new operational dependencies for users?

If the answer is unclear, document the question instead of building the feature.

## Stop Conditions

Stop and move the work to future architecture planning if a Python change would
require:

- background services
- shared network state
- a new database server
- user account management
- broad schema migration
- substantial new UI surface area
- more than one sprint of prototype-only code

## Phase 1 Operating Rule

The Python prototype should stay clean, demonstrable, and useful as reference
material. The next major investment should be product definition, data modeling,
technical stack decisions, and the first intentionally scoped C#/.NET migration
milestone.

## Phase 1 Conclusion

This guardrail completes the Phase 1 decision that the Python app remains a
prototype. Future Python work must preserve or clarify the product. It should
not become a parallel production build.
