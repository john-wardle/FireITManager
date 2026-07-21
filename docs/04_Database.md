# Database

## Overview
The system will use SQLite as the initial persistence layer for local deployment simplicity.

## Schema areas
- Incidents
- Camps
- Buildings
- Network entities
- Devices and cables
- Inventory assets
- People and rentals
- Tickets

## Entity relationships
- Incidents own camps, assets, and tickets.
- Camps contain buildings and inventory assets.
- Networks contain devices and cables.
- Assets may be related to incidents, people, and rentals.

## Indexes
- Indexes should be added for incident identifiers, asset references, and relationship lookups.

## Versioning and migration strategy
- Track a schema version in the database.
- Apply incremental migrations for future changes.
- Preserve data integrity during updates and avoid destructive changes.

## Backup strategy
- Use regular file-based backups of the SQLite database.
- Keep backup retention simple and predictable for field deployments.
