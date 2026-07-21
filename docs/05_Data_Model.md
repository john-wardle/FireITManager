# Data Model

## Core entities

### Incident
- Attributes: identifier, name, status, created date, description, owner
- Relationships: contains camps, assets, tickets, and related people
- Ownership: owned by a single incident record
- Lifecycle: created, active, closed, archived

### Camp
- Attributes: identifier, name, location, status, capacity
- Relationships: belongs to an incident; contains buildings and equipment
- Ownership: belongs to one incident
- Lifecycle: planned, active, decommissioned

### Building
- Attributes: identifier, name, type, location, capacity
- Relationships: belongs to a camp; contains rooms or assets
- Ownership: belongs to one camp
- Lifecycle: active, maintenance, retired

### Network
- Attributes: identifier, name, type, description
- Relationships: contains devices and cables; belongs to an incident or camp
- Ownership: may be scoped to an incident or camp
- Lifecycle: active, changed, archived

### Device
- Attributes: identifier, name, type, serial number, status
- Relationships: participates in network topology; owned by a person, asset, or location
- Ownership: may be assigned to a person or asset
- Lifecycle: deployed, repaired, retired

### Cable
- Attributes: identifier, type, length, status, endpoints
- Relationships: connects devices and network segments
- Ownership: belongs to a network or incident
- Lifecycle: installed, replaced, removed

### Asset
- Attributes: identifier, name, category, condition, location
- Relationships: associated with incidents, camps, buildings, and persons
- Ownership: may be assigned to a user or organization context
- Lifecycle: active, borrowed, repaired, disposed

### Person
- Attributes: identifier, name, role, contact information, qualification
- Relationships: linked to incidents, assets, tickets, and rentals
- Ownership: not owned by a single entity; references are shared
- Lifecycle: active, inactive, removed

### Rental
- Attributes: identifier, item, start date, end date, status
- Relationships: linked to assets and people
- Ownership: belongs to the incident or owning party
- Lifecycle: requested, active, returned, closed

### Ticket
- Attributes: identifier, title, priority, status, description
- Relationships: linked to incidents, assets, devices, and persons
- Ownership: belongs to an incident or support workflow
- Lifecycle: open, in progress, resolved, closed
