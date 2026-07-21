# Incident Specification

## Purpose
Define the expected behavior of incident management features in the application.

## Functional expectations
- Users can create a new incident.
- Each incident has a name, status, and description.
- Incidents can be associated with camps, assets, and support tickets.
- The UI should expose incidents through the incident explorer.

## Non-functional expectations
- The feature should remain modular and testable.
- No incident logic should be implemented in the UI layer directly.
