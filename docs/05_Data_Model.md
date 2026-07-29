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
- Definition: an incident-scoped operating area, camp, ICP, staging area,
  spike camp, communications site, warehouse, or other named place where ITSS
  work, users, assets, devices, networks, and checklists are organized.
- Current prototype mapping: `Camp` in `src/fireitmanager/models/camp.py`
  currently covers `camp_id`, `name`, `buildings`, `networks`, `created_at`,
  and `updated_at`.
- Long-term model note: the shared-server model must distinguish camp identity
  from physical buildings/locations. A camp can contain many locations and
  networks, and an incident can have more than one camp or operating area.

#### Camp Fields

| Field | Required | Value Type | Notes |
| --- | --- | --- | --- |
| `camp_id` | Yes | UUID | Stable internal identifier. Generated once and never reused. |
| `incident_id` | Yes | Relationship | Parent Incident. A camp belongs to exactly one incident in the first shared-server model. |
| `name` | Yes | Free text | Human-readable camp or operating-area name. Must be unique within the parent incident. |
| `camp_type` | Yes | Controlled list | First list: `base_camp`, `icp`, `staging_area`, `spike_camp`, `communications_site`, `warehouse`, `helibase`, `other`. |
| `status` | Yes | Controlled list | `planned`, `mobilizing`, `active`, `limited`, `demobilizing`, `closed`, `archived`. |
| `primary_location_id` | No | Relationship | Optional primary Building/Location used for map centering, reports, and mobile summaries. |
| `address_or_directions` | No | Free text | Field-friendly directions when a formal address is unavailable. |
| `latitude` | No | Decimal | Optional approximate camp coordinate for map and navigation context. |
| `longitude` | No | Decimal | Optional approximate camp coordinate for map and navigation context. |
| `capacity` | No | Integer | Optional operational capacity, such as personnel or work area capacity. |
| `it_contact_person_id` | No | Relationship | ITSS or other contact responsible for this camp, if known. |
| `notes` | No | Free text | Operational notes that do not belong to a more specific building, network, or asset. |
| `record_state` | Yes | Controlled list | `active` or `archived`; archival is preferred over deletion once a camp has child records. |
| `created_at` | Yes | Datetime | System-created timestamp. |
| `updated_at` | Yes | Datetime | System-updated timestamp. |
| `version` | Yes in shared-server model | Integer or token | Used for optimistic concurrency and conflict detection. |

#### Camp Relationships

- Belongs to exactly one Incident.
- Contains Buildings/Locations, networks, devices through locations and
  networks, physical links, wireless links, WAN links, camp-scoped checklist
  runs, attachments, photos, notes, and audit events.
- Can reference one primary location for map centering and field summaries, but
  that reference does not replace the full list of locations.
- Can reference one IT contact person for ownership and escalation. That person
  must be part of the parent incident's personnel or assignment set.
- Child records must remain scoped to the same parent incident as the camp.
  Cross-incident child records are not allowed in the first shared-server
  model.

#### Camp Lifecycle

- `planned`: expected operating area, not yet built or verified.
- `mobilizing`: setup work has started.
- `active`: camp is in normal operational use.
- `limited`: camp is operating with known constraints, partial service, or
  restricted access.
- `demobilizing`: closeout or teardown is in progress.
- `closed`: camp is no longer operational but remains part of the incident
  record.
- `archived`: hidden from normal active views but retained for reporting,
  audit, export, and historical reference.

Camp records with buildings, networks, devices, checklists, notes, attachments,
or audit history should be archived instead of deleted. Deletion is allowed
only for empty drafts or duplicate setup mistakes before the camp has official
child records.

#### Camp Validation Rules

- `camp_id`, `incident_id`, `name`, `camp_type`, `status`, `record_state`,
  `created_at`, and `updated_at` are always required.
- `name` must be unique within the parent incident, ignoring case and leading
  or trailing whitespace.
- `primary_location_id`, when set, must reference a Building/Location contained
  by the same camp.
- `it_contact_person_id`, when set, must reference a person assigned to the
  same parent incident.
- `latitude` and `longitude` must either both be blank or both be present.
- `capacity`, when set, must be zero or greater.
- A camp cannot move to `active` unless it has at least one Building/Location.
- A camp cannot move to `closed` while child networks or links are still marked
  active unless a closeout workflow records the reason.
- The shared-server model must enforce optimistic concurrency on camp updates
  so clients cannot silently overwrite camp status, map context, or ownership.

#### Camp Audit Rules

Create audit history when:

- a camp is created, activated, limited, closed, reopened, archived, or deleted
- `name`, `camp_type`, `status`, `primary_location_id`,
  `address_or_directions`, `latitude`, `longitude`, `capacity`,
  `it_contact_person_id`, or `notes` changes
- a Building/Location, network, link, checklist run, attachment, photo, or note
  is added to or removed from the camp
- an override allows deleting or editing a closed or archived camp

#### Mobile Rules

The mobile/tablet tool may view camps, camp summaries, camp maps, and assigned
camp checklists. It may create camp-scoped notes, photos, checklist runs, and
follow-up observations. It should not create, close, archive, delete, or
re-parent Camp records in the first mobile version.

#### Open Decisions

- Final controlled list for `camp_type`.
- Whether camp coordinates live directly on Camp or only through the primary
  Building/Location.
- Whether capacity should track people, beds, workstations, network drops, or a
  broader operational capacity record.
- Whether `limited` status needs structured reason codes.

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
