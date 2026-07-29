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

### Building / Location
- Definition: a camp-scoped physical place used to organize devices, assets,
  users, links, map layout, field work, and checklist activity. It may be a
  building, tent, trailer, cache, pad, communications site, room, outdoor work
  area, or map-only location.
- Current prototype mapping: `Building` in
  `src/fireitmanager/models/building.py` currently covers `building_id`,
  `name`, `building_type`, optional `location`, `devices`, `created_at`, and
  `updated_at`. `Location` in `src/fireitmanager/models/location.py` currently
  covers `location_id`, `name`, `latitude`, `longitude`, `elevation_ft`,
  `notes`, `created_at`, and `updated_at`.
- Long-term model note: the shared-server model should treat Building/Location
  as the camp's operational place record. Physical buildings, rooms, tents,
  trailers, pads, and map-only locations should use the same relationship
  rules so network maps, inventory, and mobile checklists do not need separate
  concepts for every field layout.

#### Building / Location Fields

| Field | Required | Value Type | Notes |
| --- | --- | --- | --- |
| `location_id` | Yes | UUID | Stable internal identifier. Generated once and never reused. This may replace or map from prototype `building_id` during migration. |
| `camp_id` | Yes | Relationship | Parent Camp. A Building/Location belongs to exactly one camp in the first shared-server model. |
| `name` | Yes | Free text | Human-readable place name used in maps, explorer views, reports, and mobile checklists. Must be unique within the parent camp when practical. |
| `location_type` | Yes | Controlled list | First list: `command_post`, `operations`, `communications`, `logistics`, `medical`, `storage`, `lodging`, `warehouse`, `helibase`, `tent`, `trailer`, `outdoor_area`, `room`, `other`. |
| `status` | Yes | Controlled list | `planned`, `active`, `limited`, `maintenance`, `closed`, `archived`. |
| `parent_location_id` | No | Relationship | Optional parent place for room, tent, trailer, or sub-area nesting. Must stay within the same camp. |
| `map_x` | No | Decimal | Optional site-map coordinate for desktop and future shared map layout. |
| `map_y` | No | Decimal | Optional site-map coordinate for desktop and future shared map layout. |
| `map_width` | No | Decimal | Optional rendered width for map containers. |
| `map_height` | No | Decimal | Optional rendered height for map containers. |
| `latitude` | No | Decimal | Optional geographic coordinate for field navigation and GIS context. |
| `longitude` | No | Decimal | Optional geographic coordinate for field navigation and GIS context. |
| `elevation_ft` | No | Decimal | Optional elevation in feet. |
| `address_or_directions` | No | Free text | Field-friendly directions when a formal address is unavailable. |
| `capacity` | No | Integer | Optional operating capacity, such as workstations, beds, personnel, or equipment footprint. |
| `access_notes` | No | Free text | Access instructions, gate notes, safety notes, or restricted-entry context. |
| `notes` | No | Free text | General place notes. |
| `record_state` | Yes | Controlled list | `active` or `archived`; archival is preferred over deletion once child records exist. |
| `created_at` | Yes | Datetime | System-created timestamp. |
| `updated_at` | Yes | Datetime | System-updated timestamp. |
| `version` | Yes in shared-server model | Integer or token | Used for optimistic concurrency and conflict detection. |

#### Building / Location Relationships

- Belongs to exactly one Camp and therefore exactly one Incident through that
  camp.
- May contain devices, assets, rooms or sub-locations, checklist runs,
  attachments, photos, notes, and audit events.
- May be the endpoint context for physical links, wireless links, WAN links, or
  service availability, but links should still connect explicit devices or
  link endpoints when known.
- May have a parent Building/Location for room or sub-area structure. Parent
  and child records must remain in the same camp.
- Devices and assets assigned to a Building/Location must belong to the same
  parent incident as the location.
- Camp `primary_location_id` can reference one Building/Location for map
  centering and summaries.

#### Building / Location Lifecycle

- `planned`: expected place or layout object, not yet verified.
- `active`: place is operational and available for ITSS use.
- `limited`: place is usable with known constraints, access limits, or partial
  service.
- `maintenance`: place is temporarily unavailable or undergoing work.
- `closed`: place is no longer operational but remains part of the incident
  record.
- `archived`: hidden from normal active views but retained for reporting,
  audit, export, and historical reference.

Building/Location records with devices, assets, links, checklists, notes,
attachments, or audit history should be archived instead of deleted. Deletion
is allowed only for empty drafts or duplicate setup mistakes before the place
has official child records.

#### Building / Location Validation Rules

- `location_id`, `camp_id`, `name`, `location_type`, `status`, `record_state`,
  `created_at`, and `updated_at` are always required.
- `name` should be unique within the parent camp, ignoring case and leading or
  trailing whitespace.
- `parent_location_id`, when set, must reference another Building/Location in
  the same camp and must not create a cycle.
- `map_x` and `map_y` must either both be blank or both be present.
- `map_width` and `map_height`, when set, must be greater than zero.
- `latitude` and `longitude` must either both be blank or both be present.
- `capacity`, when set, must be zero or greater.
- A Building/Location cannot move to `closed` while assigned devices, assets,
  or links are still active unless a closeout workflow records the reason.
- The shared-server model must enforce optimistic concurrency on
  Building/Location updates so clients cannot silently overwrite map placement,
  status, or assignments.

#### Building / Location Audit Rules

Create audit history when:

- a Building/Location is created, activated, limited, moved to maintenance,
  closed, reopened, archived, or deleted
- `name`, `location_type`, `status`, `parent_location_id`, map coordinates,
  dimensions, latitude, longitude, elevation, capacity, access notes, or notes
  change
- a device, asset, checklist run, attachment, photo, note, or child location is
  added to or removed from the Building/Location
- an override allows deleting or editing a closed or archived Building/Location

#### Mobile Rules

The mobile/tablet tool may view Building/Location details, map summaries,
assigned devices, assigned assets, checklists, notes, and photos. It may create
field notes, photos, checklist runs, and follow-up observations for a selected
Building/Location. It may create a draft field-discovered location only if the
desktop/server workflow clearly marks it as unverified. It should not delete,
archive, close, or re-parent Building/Location records in the first mobile
version.

#### Open Decisions

- Whether the long-term class/table name is `Location`, `Place`,
  `CampLocation`, or keeps `Building` for prototype continuity.
- Final controlled list for `location_type`.
- Whether nested rooms/sub-locations are required in the first shared-server
  milestone.
- Whether map coordinates should be incident-wide, camp-relative, or tied to a
  future map layer record.
- Whether field-discovered mobile locations should be allowed in version one or
  deferred until review workflows exist.

### Person
- Definition: an incident-scoped person or contact who may use equipment,
  receive support, own follow-up work, approve changes, or appear in reports.
- Current prototype mapping: `Person` covers `person_id`, `name`, `position`,
  `agency`, `assigned_devices`, `created_at`, and `updated_at`.

| Field | Required | Value Type | Notes |
| --- | --- | --- | --- |
| `person_id` | Yes | UUID | Stable internal identifier. |
| `incident_id` | Yes | Relationship | Parent Incident assignment scope. |
| `display_name` | Yes | Free text | Prototype field is `name`. |
| `role` | Yes | Controlled list with free-text detail | First list: `itss`, `coml`, `comt`, `trainee`, `logistics`, `operations`, `vendor`, `observer`, `other`. |
| `agency` | No | Controlled list with free-text fallback | Owning or home agency. |
| `contact_methods` | No | Structured list | Phone, email, radio, or local contact note. |
| `qualification` | No | Free text or controlled list | Incident qualification or relevant capability. |
| `status` | Yes | Controlled list | `active`, `demobilized`, `inactive`, `archived`. |
| `created_at`, `updated_at`, `version` | Yes | Timestamp/token | Audit and concurrency fields. |

- Relationships: assigned devices, assigned assets, checklist ownership,
  notes, audit actor references, and optional camp/location assignments.
- Validation: name, role, status, incident, timestamps, and version are
  required; assigned devices and assets must belong to the same incident.
- Audit: create history for role/status/contact changes and for assigning or
  clearing devices, assets, or checklist ownership.
- Mobile: mobile may view people and select assignees for notes/checklists, but
  should not create or archive people in the first version.

### Device
- Definition: a networked, powered, or operational technology endpoint tracked
  during the incident, including routers, switches, access points, servers,
  printers, workstations, phones, radios with IP dependencies, and other IT
  equipment.
- Current prototype mapping: `Device` covers `device_id`, `hostname`,
  `manufacturer`, `model`, `serial_number`, `ip_address`, `mac_address`,
  `device_type`, `status`, `assigned_building`, `created_at`, and `updated_at`.

| Field | Required | Value Type | Notes |
| --- | --- | --- | --- |
| `device_id` | Yes | UUID | Stable internal identifier. |
| `incident_id` | Yes | Relationship | Parent incident scope. |
| `hostname` | Yes | Free text | Unique within the incident when practical. |
| `device_type` | Yes | Controlled list | Start from prototype `DeviceType`; expand for printer, firewall, modem, camera, radio_gateway, sensor, and other. |
| `status` | Yes | Controlled list | `unknown`, `planned`, `online`, `degraded`, `offline`, `maintenance`, `retired`, `archived`. |
| `location_id` | No | Relationship | Current Building/Location assignment. |
| `manufacturer`, `model`, `serial_number` | No | Free text | Asset/inventory identity fields. |
| `primary_ip_assignment_id` | No | Relationship | Preferred IP assignment for display and search. |
| `mac_addresses` | No | Structured list | One or more interfaces. Prototype has one `mac_address`. |
| `asset_id` | No | Relationship | Optional inventory asset record for the same equipment. |
| `created_at`, `updated_at`, `version` | Yes | Timestamp/token | Audit and concurrency fields. |

- Relationships: belongs to one incident; may be assigned to one
  Building/Location, one person, one asset, many networks, many IP assignments,
  many links, and many service checks.
- Validation: hostname, type, status, incident, timestamps, and version are
  required; active devices assigned to closed locations need a closeout reason.
- Audit: create history for identity, status, location, person, asset, network,
  IP, and link changes.
- Mobile: mobile may view devices and add notes/photos/checklist evidence; it
  may create unverified field-discovered devices only through a review workflow.

### Asset
- Definition: incident-scoped equipment, supply, vehicle, kit, consumable, or
  tracked resource that may or may not be a network device.
- Current prototype mapping: `Asset` covers `asset_id`, `name`, `owner`,
  `acquisition_type`, `barcode`, `status`, `assigned_person`, `created_at`,
  and `updated_at`.

| Field | Required | Value Type | Notes |
| --- | --- | --- | --- |
| `asset_id` | Yes | UUID | Stable internal identifier. |
| `incident_id` | Yes | Relationship | Parent incident scope. |
| `name` | Yes | Free text | Human-readable asset name. |
| `category` | Yes | Controlled list | `network_equipment`, `computer`, `printer`, `power`, `tool`, `vehicle`, `supply`, `consumable`, `other`. |
| `status` | Yes | Controlled list | Start from prototype `AssetStatus`; add `archived` for long-term records. |
| `owner`, `acquisition_type`, `barcode` | No | Free text | Prototype identity and ownership fields. |
| `assigned_person_id`, `location_id`, `device_id` | No | Relationships | Current assignment links. |
| `condition` | No | Controlled list | `new`, `good`, `fair`, `poor`, `damaged`, `unknown`. |
| `created_at`, `updated_at`, `version` | Yes | Timestamp/token | Audit and concurrency fields. |

- Relationships: belongs to one incident; may be assigned to a person,
  Building/Location, device record, checklist run, attachment, or note.
- Validation: name, category, status, incident, timestamps, and version are
  required; assigned person/location/device must be in the same incident.
- Audit: create history for status, assignment, ownership, barcode, condition,
  and archive/delete changes.
- Mobile: mobile may view assets, scan/search identifiers, and attach
  notes/photos; asset creation should be draft-only until reviewed.

### Network
- Definition: an incident or camp scoped logical network grouping used for
  topology, membership, IP plans, services, links, reporting, and map filters.
- Current prototype mapping: `Network` covers `network_id`, `name`, `devices`,
  `cables`, `created_at`, and `updated_at`.

| Field | Required | Value Type | Notes |
| --- | --- | --- | --- |
| `network_id` | Yes | UUID | Stable internal identifier. |
| `incident_id` | Yes | Relationship | Parent incident scope. |
| `camp_id` | No | Relationship | Optional camp scope for camp-local networks. |
| `name` | Yes | Free text | Unique within the incident or camp scope. |
| `network_type` | Yes | Controlled list | `lan`, `wan`, `wifi`, `management`, `voice`, `printer`, `iot`, `service`, `other`. |
| `status` | Yes | Controlled list | `planned`, `active`, `degraded`, `down`, `maintenance`, `disabled`, `archived`. |
| `description` | No | Free text | Operational purpose or notes. |
| `created_at`, `updated_at`, `version` | Yes | Timestamp/token | Audit and concurrency fields. |

- Relationships: contains devices, physical links, virtual links, VLAN/subnets,
  IP assignments, wireless/WAN links, and services.
- Validation: name, type, status, incident, timestamps, and version are
  required; camp-scoped networks must belong to the same incident as the camp.
- Audit: create history for status, scope, membership, link, IP, VLAN/subnet,
  and service changes.
- Mobile: mobile may view network summaries, link states, and device lists; it
  should not create or archive networks in the first version.

### Physical Link
- Definition: a tangible or directly field-verifiable connection between
  endpoints, such as copper cable, fiber, patch cable, powerline bridge, or
  documented wired handoff.
- Current prototype mapping: `Cable` covers `cable_id`, `cable_type`,
  `source_device`, `destination_device`, `length`, `notes`, `created_at`, and
  `updated_at`.

Required fields: `physical_link_id`, `incident_id`, `network_id`, `link_type`,
`status`, at least one endpoint, `created_at`, `updated_at`, and `version`.
Controlled `link_type` starts with `copper`, `fiber`, `patch`, `uplink`,
`handoff`, `other`; controlled `status` is `unknown`, `planned`, `up`,
`degraded`, `down`, `disabled`, `maintenance`, `archived`.

- Relationships: connects source/destination devices or explicit endpoint
  records, belongs to one network, and may reference locations, ports, cable
  labels, attachments, notes, and link state history.
- Validation: endpoint records must belong to the same incident; active links
  should have two endpoints unless documented as a handoff or pending install.
- Audit: create history for endpoint, type, label, length, path, status, and
  archive/delete changes.
- Mobile: mobile may verify, photograph, label, and note physical links, but
  should create only draft field-discovered links until reviewed.

### Virtual Link
- Definition: a logical dependency or tunnel between network endpoints that
  does not represent a single physical cable, such as VPN, VLAN trunk path,
  route, firewall path, NAT path, overlay, or service dependency.

Required fields: `virtual_link_id`, `incident_id`, `network_id`, `link_type`,
`source_ref`, `destination_ref`, `status`, `created_at`, `updated_at`, and
`version`. Controlled `link_type` starts with `vpn`, `vlan_trunk`, `route`,
`firewall_rule`, `nat`, `overlay`, `service_dependency`, `other`.

- Relationships: references devices, networks, VLAN/subnets, services, WAN
  links, or other approved endpoint records within the same incident.
- Validation: source and destination cannot be identical; active virtual links
  need a purpose or rule/path description.
- Audit: create history for endpoint, dependency, status, rule, and path
  changes.
- Mobile: mobile may view virtual links for troubleshooting but should not
  create or modify them in the first version.

### Service
- Definition: an incident-scoped technology service that users depend on, such
  as internet access, printing, Wi-Fi SSID, file share, VoIP, radio gateway,
  DNS, DHCP, camera feed, or application access.

Required fields: `service_id`, `incident_id`, `name`, `service_type`, `status`,
`created_at`, `updated_at`, and `version`. Controlled `service_type` starts
with `internet`, `wifi_ssid`, `printing`, `dhcp`, `dns`, `file_share`, `voip`,
`radio_gateway`, `camera`, `application`, `other`.

- Relationships: may depend on devices, networks, VLAN/subnets, IP
  assignments, physical links, virtual links, WAN links, people contacts, and
  checklist templates.
- Validation: active services need at least one dependency or owning contact;
  service names should be unique within the incident.
- Audit: create history for status, dependency, owner, published endpoint, and
  archive/delete changes.
- Mobile: mobile may view services, status, troubleshooting notes, and
  checklists; service creation/modification stays desktop/server-side first.

### VLAN / Subnet
- Definition: a network segment or addressing domain used to group devices,
  route traffic, isolate services, or document an incident network plan.

Required fields: `vlan_subnet_id`, `incident_id`, `network_id`, `name`,
`segment_type`, `status`, `created_at`, `updated_at`, and `version`.
Controlled `segment_type` starts with `vlan`, `subnet`, `management`,
`guest_wifi`, `operations`, `printer`, `voice`, `iot`, `other`.

Optional fields include `vlan_id`, `cidr`, `gateway_ip`, `dhcp_scope`,
`dns_servers`, `purpose`, and `notes`.

- Relationships: belongs to one network and contains IP address assignments,
  services, virtual links, and devices through interfaces.
- Validation: `vlan_id`, when set, must be 1-4094; CIDR and gateway must be
  valid when present; overlapping active subnets require an explicit reason.
- Audit: create history for VLAN ID, CIDR, gateway, DHCP, DNS, status, and
  membership changes.
- Mobile: mobile may view VLAN/subnet details for troubleshooting and search.

### IP Address Assignment
- Definition: a record that assigns or reserves an IP address for a device
  interface, service endpoint, gateway, printer, WAN handoff, or manual note.

Required fields: `ip_assignment_id`, `incident_id`, `address`, `assignment_type`,
`status`, `created_at`, `updated_at`, and `version`. Controlled
`assignment_type` starts with `static`, `dhcp`, `reservation`, `gateway`,
`service`, `wan`, `unknown`.

Optional fields include `vlan_subnet_id`, `device_id`, `interface_name`,
`service_id`, `mac_address`, `hostname`, `lease_start`, `lease_end`, and
`notes`.

- Relationships: may link to one VLAN/subnet, device, service, WAN link, or
  observed MAC address.
- Validation: IP address must be valid; duplicate active assignments in the
  same subnet require an override; assignments must stay within the same
  incident.
- Audit: create history for address, target, MAC, hostname, status, lease, and
  archive/delete changes.
- Mobile: mobile may search and view IP assignments; creating assignments from
  mobile should be draft-only until reviewed.

### Wireless Link
- Definition: a wireless point-to-point, point-to-multipoint, mesh, Wi-Fi
  uplink, or radio-backed network connection used by the incident.

Required fields: `wireless_link_id`, `incident_id`, `network_id`, `link_type`,
`status`, `created_at`, `updated_at`, and `version`. Controlled `link_type`
starts with `wifi_ptp`, `wifi_ptmp`, `mesh`, `microwave`, `lte_bridge`,
`radio_gateway`, `other`.

Optional fields include source/destination device IDs, source/destination
location IDs, SSID, frequency band, channel, signal strength, expected
throughput, antenna notes, and alignment notes.

- Relationships: connects devices or locations and may support networks,
  services, WAN links, virtual links, and link state history.
- Validation: active wireless links need at least one endpoint pair or a
  documented survey note; signal metrics must include units.
- Audit: create history for endpoint, SSID, channel, signal, status, alignment,
  and archive/delete changes.
- Mobile: mobile may add photos, signal observations, and notes from the field;
  new links should remain draft until reviewed.

### Satellite / WAN Link
- Definition: an external connectivity path such as satellite internet,
  cellular modem, microwave backhaul, agency WAN handoff, commercial ISP, or
  other internet/WAN service.

Required fields: `wan_link_id`, `incident_id`, `link_type`, `provider_or_owner`,
`status`, `created_at`, `updated_at`, and `version`. Controlled `link_type`
starts with `satellite`, `starlink`, `cellular`, `microwave`, `agency_wan`,
`commercial_isp`, `fiber_handoff`, `other`.

Optional fields include account/reference, modem/device ID, network ID,
location ID, public IP, bandwidth, data limit, failover priority, support
contact, and service notes.

- Relationships: may attach to one device, network, location, service, virtual
  link, wireless link, and link state history.
- Validation: active WAN links need provider/owner and either a device,
  location, or handoff note; public IP values must be valid when entered.
- Audit: create history for provider, status, bandwidth, public IP, failover,
  support contact, and archive/delete changes.
- Mobile: mobile may view setup details, checklists, status, notes, and photos;
  provisioning changes stay desktop/server-side first.

### Link State History
- Definition: append-only status observations for physical links, virtual
  links, wireless links, WAN links, services, or monitored devices.

Required fields: `link_state_id`, `incident_id`, `observed_at`,
`target_type`, `target_id`, `state`, `source`, `created_at`, and `created_by`.
Controlled `state` is `unknown`, `up`, `degraded`, `down`, `disabled`,
`planned`, `maintenance`; controlled `source` is `manual`, `mobile_checklist`,
`ping`, `snmp`, `http_check`, `system`, `import`.

Optional fields include latency, packet loss, throughput, signal, reason,
notes, related checklist run, and manual override flag.

- Relationships: references exactly one monitored target within the same
  incident and may link to audit events, notes, photos, or checklist runs.
- Validation: history is append-only; corrections create new events rather than
  editing old observations except for administrator-approved data repair.
- Audit: manual overrides and data repair must create audit events.
- Mobile: mobile may create manual observations and checklist-linked state
  records.

### Checklist Template
- Definition: reusable checklist content for ITSS setup, troubleshooting,
  daily checks, closeout, documentation, safety, or field verification.

Required fields: `template_id`, `title`, `template_type`, `version_label`,
`status`, `steps`, `created_at`, `updated_at`, and `version`. Controlled
`template_type` starts with `setup`, `daily_check`, `troubleshooting`,
`maintenance`, `closeout`, `documentation`, `safety`, `other`.

Each step needs a stable `step_id`, title, order, completion mode, and expected
result. Optional step fields include role, required photo/note flag,
troubleshooting hint, safety note, related object type, and blocker behavior.

- Relationships: may be global, incident-scoped, camp-scoped, service-scoped,
  device-type-scoped, or network-type-scoped.
- Validation: published templates require at least one step, stable step IDs,
  ordered steps, and a version label.
- Audit: create history for publish/archive/version changes and step edits.
- Mobile: mobile may download and run published templates; editing templates is
  desktop/server-side first.

### Checklist Run / Completed Checklist
- Definition: an incident record of a person or team performing a checklist
  against an incident, camp, location, device, network, link, service, or other
  approved target.

Required fields: `checklist_run_id`, `incident_id`, `template_id`, `status`,
`started_at`, `created_at`, `updated_at`, and `version`. Controlled `status`
is `not_started`, `in_progress`, `blocked`, `completed`, `cancelled`,
`archived`.

Run steps record step ID, completion state, completed_at, completed_by,
required notes/photos, blocker notes, and field observations.

- Relationships: references template version, assignee/person, target object,
  notes, photos, attachments, link state observations, and follow-up work.
- Validation: completed runs must satisfy required steps, required notes/photos,
  and completion criteria from the template version used.
- Audit: create history for start, assignment, blocker, completion,
  cancellation, reopen, and archive changes.
- Mobile: mobile may start, update, complete, and sync checklist runs.

### Attachment / Photo / Note
- Definition: supporting incident evidence or documentation attached to an
  incident object, checklist run, checklist step, link observation, device,
  asset, person, camp, or location.

Required fields: `entry_id`, `incident_id`, `entry_type`, `target_type`,
`target_id`, `created_at`, `created_by`, and `version`. Controlled
`entry_type` is `note`, `photo`, `file`, `link`, `observation`.

Notes require text. Photos/files require storage reference, filename, media
type, size, and checksum when available. Optional fields include caption,
visibility, captured_at, device/location metadata, and tags.

- Relationships: belongs to exactly one incident and one target object; may
  link to checklist runs, audit events, or link state history.
- Validation: target must exist in the same incident; files need a storage
  reference; official records should archive rather than delete attachments.
- Audit: create history for add, edit note text, replace file, archive, and
  administrator delete.
- Mobile: mobile may create notes/photos/files while offline and sync them when
  connected.

### Audit Event
- Definition: immutable record of meaningful user, system, import, sync, or
  administrator action affecting incident data.

Required fields: `audit_event_id`, `incident_id`, `occurred_at`, `actor_type`,
`actor_id`, `action`, `target_type`, `target_id`, and `summary`. Controlled
`action` starts with `create`, `update`, `status_change`, `assign`, `unassign`,
`archive`, `delete`, `restore`, `override`, `import`, `export`, `sync`,
`login`, `logout`.

Optional fields include changed fields, old/new values, reason, source client,
correlation ID, related checklist run, related link state, and IP/device
metadata.

- Relationships: belongs to one incident and references one primary target;
  may reference related records for grouped operations.
- Validation: audit events are append-only; data repair requires a new audit
  event explaining the correction.
- Retention: audit events are never normally deleted and must export with the
  incident record.
- Mobile: mobile creates audit events for synced checklist, note, photo, and
  field observation changes.

## Data Rules

### Required Fields

Required fields are the minimum data needed to create a durable shared-server
record without losing identity, incident scope, lifecycle state, auditability,
or multi-user conflict protection. UI drafts may start with fewer values, but a
record cannot become official incident data until its required fields are
present and valid.

#### Required Field Policy

- Every persistent incident record requires a stable UUID, creation timestamp,
  updated timestamp, and concurrency token.
- Every incident-scoped record requires `incident_id` unless it is a global
  reusable template that is explicitly not tied to one incident.
- Records with operational lifecycle require a controlled `status` and
  `record_state` or equivalent archive state.
- Child records require the parent relationship that defines their scope, such
  as `camp_id`, `network_id`, `template_id`, or `target_id`.
- Append-only history records require actor/source information and an event or
  observation timestamp.
- Fields listed as "required before active/official use" may be missing during
  early setup, but validation must block active, closed, exported-official, or
  server-synchronized official states until those fields are complete.

#### Required Fields By Record Type

| Record Type | Required Fields |
| --- | --- |
| Incident | `incident_id`, `name`, `status`, `incident_type`, `time_zone`, `record_state`, `created_at`, `updated_at`, `version` |
| Incident before active/official use | `incident_number`, `lead_agency`, `start_datetime` |
| Incident before close | `end_datetime` |
| Camp | `camp_id`, `incident_id`, `name`, `camp_type`, `status`, `record_state`, `created_at`, `updated_at`, `version` |
| Building / Location | `location_id`, `camp_id`, `name`, `location_type`, `status`, `record_state`, `created_at`, `updated_at`, `version` |
| Person | `person_id`, `incident_id`, `display_name`, `role`, `status`, `created_at`, `updated_at`, `version` |
| Device | `device_id`, `incident_id`, `hostname`, `device_type`, `status`, `created_at`, `updated_at`, `version` |
| Asset | `asset_id`, `incident_id`, `name`, `category`, `status`, `created_at`, `updated_at`, `version` |
| Network | `network_id`, `incident_id`, `name`, `network_type`, `status`, `created_at`, `updated_at`, `version` |
| Physical Link | `physical_link_id`, `incident_id`, `network_id`, `link_type`, `status`, at least one endpoint, `created_at`, `updated_at`, `version` |
| Virtual Link | `virtual_link_id`, `incident_id`, `network_id`, `link_type`, `source_ref`, `destination_ref`, `status`, `created_at`, `updated_at`, `version` |
| Service | `service_id`, `incident_id`, `name`, `service_type`, `status`, `created_at`, `updated_at`, `version` |
| VLAN / Subnet | `vlan_subnet_id`, `incident_id`, `network_id`, `name`, `segment_type`, `status`, `created_at`, `updated_at`, `version` |
| IP Address Assignment | `ip_assignment_id`, `incident_id`, `address`, `assignment_type`, `status`, `created_at`, `updated_at`, `version` |
| Wireless Link | `wireless_link_id`, `incident_id`, `network_id`, `link_type`, `status`, `created_at`, `updated_at`, `version` |
| Satellite / WAN Link | `wan_link_id`, `incident_id`, `link_type`, `provider_or_owner`, `status`, `created_at`, `updated_at`, `version` |
| Link State History | `link_state_id`, `incident_id`, `observed_at`, `target_type`, `target_id`, `state`, `source`, `created_at`, `created_by` |
| Checklist Template | `template_id`, `title`, `template_type`, `version_label`, `status`, `steps`, `created_at`, `updated_at`, `version` |
| Checklist Template Step | `step_id`, `title`, `order`, `completion_mode`, `expected_result` |
| Checklist Run / Completed Checklist | `checklist_run_id`, `incident_id`, `template_id`, `status`, `started_at`, `created_at`, `updated_at`, `version` |
| Checklist Run Step | `step_id`, `completion_state` |
| Attachment / Photo / Note | `entry_id`, `incident_id`, `entry_type`, `target_type`, `target_id`, `created_at`, `created_by`, `version` |
| Audit Event | `audit_event_id`, `incident_id`, `occurred_at`, `actor_type`, `actor_id`, `action`, `target_type`, `target_id`, `summary` |

#### Required Field Validation

- Required text fields must contain non-whitespace text.
- Required UUID relationship fields must reference existing records in the same
  incident scope unless the field explicitly references a global template.
- Required timestamps must be timezone-aware in storage and displayable in the
  incident's configured time zone.
- Required controlled-list fields must use valid list values for the record's
  current schema version.
- Required endpoint fields may use a draft or unknown endpoint only when the
  record status is `planned`, `unknown`, or otherwise explicitly unverified.
- Required fields may not be removed by mobile sync, import, or conflict
  resolution.
