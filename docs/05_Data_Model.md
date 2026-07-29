# Data Model

## Core entities

### Incident
- Definition: the top-level official record for one incident, test
  environment, or planned operational event. It is the boundary for incident
  data entry, reporting, permissions, synchronization, audit history, and
  future server-side tenancy.
- Current prototype mapping: `Incident` in
  `src/fireitmanager/models/incident.py` currently covers `incident_id`,
  `name`, `incident_number`, `agency`, `operational_period`, `camps`,
  `personnel`, `assets`, `created_at`, and `updated_at`.
- Long-term model note: the shared-server model must extend the prototype
  shape with lifecycle status, incident type, time zone, start/end dates,
  record state, and an optimistic concurrency token. These are product model
  requirements and do not require expanding the Python prototype immediately.

#### Incident Fields

| Field | Required | Value Type | Notes |
| --- | --- | --- | --- |
| `incident_id` | Yes | UUID | Stable internal identifier. Generated once and never reused. |
| `name` | Yes | Free text | Human-readable incident name used throughout the UI and reports. |
| `incident_number` | Required before active/official use | Free text with future validation | Agency or incident management identifier. It may be unknown during initial setup, but official records should not close without it. |
| `status` | Yes | Controlled list | `planned`, `mobilizing`, `active`, `demobilizing`, `closed`, `archived`. |
| `incident_type` | Yes | Controlled list | First list: `wildfire`, `planned_event`, `exercise`, `all_hazard`, `test`. |
| `lead_agency` | Required before active/official use | Controlled list with free-text fallback | Prototype field is `agency`. Future list should allow agencies such as USFS, CAL FIRE, county, state, tribal, and local entities without blocking uncommon values. |
| `operational_period` | Required while active | Free text initially | The prototype stores this as text. A future model may promote operational periods to child records if scheduling, reporting, or shift history requires it. |
| `time_zone` | Yes | Controlled list | IANA time zone for all incident-local timestamps and report display. |
| `start_datetime` | Required before active/official use | Datetime | Incident or IT support activation start. Must be earlier than `end_datetime` when both exist. |
| `end_datetime` | Required to close | Datetime or blank | Blank while the incident is active. |
| `situation_summary` | No | Free text | Operational context for ITSS users and reports. |
| `it_owner_person_id` | No | Relationship | Person responsible for the IT record or workspace, when known. |
| `record_state` | Yes | Controlled list | `active` or `archived`; archival is preferred over deletion for official records. |
| `created_at` | Yes | Datetime | System-created timestamp. |
| `updated_at` | Yes | Datetime | System-updated timestamp. |
| `version` | Yes in shared-server model | Integer or token | Used for optimistic concurrency and conflict detection. |

#### Incident Relationships

- Owns camps, incident-scoped assets, checklist runs, attachments, notes, audit
  events, reports, and incident-specific network data.
- References people who are assigned to or involved with the incident. A person
  record can be copied or re-associated across incidents later, but an
  incident-specific assignment belongs to one incident.
- Contains or scopes networks. Camp-level networks still roll up to the
  incident for search, reporting, validation, and synchronization.
- Is the synchronization boundary for future desktop and mobile clients. Cross
  incident links are not allowed in the first shared-server model; data should
  be imported, copied, or re-associated intentionally.

#### Incident Lifecycle

- `planned`: created for setup, testing, or a known upcoming incident.
- `mobilizing`: ITSS setup has started, but the record may still be incomplete.
- `active`: official day-to-day incident operations are underway.
- `demobilizing`: closeout is in progress and routine new work should slow down.
- `closed`: operational record is complete; edits should require a reason and
  create audit history.
- `archived`: hidden from normal active views but retained for search, export,
  audit, and historical reference.

Official incident records should be archived instead of deleted. Deletion is
allowed only for empty drafts, duplicate test records, or administrator-approved
cleanup before the record becomes official.

#### Incident Validation Rules

- `incident_id`, `name`, `status`, `incident_type`, `time_zone`,
  `record_state`, `created_at`, and `updated_at` are always required.
- `incident_number`, `lead_agency`, and `start_datetime` are required before an
  incident can be treated as active or official.
- `end_datetime` is required before moving to `closed`.
- `end_datetime` cannot be earlier than `start_datetime`.
- A closed or archived incident cannot receive routine child-record edits
  without a reopening workflow or an administrator-level override.
- The shared-server model must enforce optimistic concurrency on incident
  updates so two clients cannot silently overwrite official metadata.

#### Incident Audit Rules

Create audit history when:

- an incident is created, activated, closed, reopened, archived, or deleted
- `name`, `incident_number`, `status`, `incident_type`, `lead_agency`,
  `operational_period`, `time_zone`, `start_datetime`, or `end_datetime`
  changes
- the IT owner changes
- camps, networks, assets, people assignments, checklist runs, attachments, or
  notes are added to or removed from the incident
- an override allows editing a closed or archived incident

#### Mobile Rules

The mobile/tablet tool may view an assigned incident and create incident-scoped
field data such as checklist runs, notes, photos, and follow-up observations.
It should not create, close, archive, or delete the Incident record in the
first mobile version.

#### Open Decisions

- Final authoritative incident number format and validation source.
- Final controlled agency list and whether it is incident-local configurable.
- Whether `operational_period` remains a text field or becomes a child entity.
- Whether incident ownership is a single IT owner, a team role assignment, or
  both.

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
