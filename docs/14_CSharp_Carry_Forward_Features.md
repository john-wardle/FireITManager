# C# Carry-Forward Features

Last updated: 2026-07-28

This note identifies the current Python prototype features that must exist in
the future C# version of FireIT Manager. It is Phase 1 evidence for deciding
what product behavior must survive the rewrite.

The future C# version does not need to copy the Python implementation. It does
need to preserve the workflows, domain concepts, and user-facing behavior below.

## Evidence

- [Current Python Prototype Workflows](13_Current_Python_Prototype_Workflows.md)
- [Common ITSS Workflows](user/Common_ITSS_Workflows.md)
- [Application Layout](user/Application_Layout.md)
- [Requirements](02_Requirements.md)
- [Data Model](05_Data_Model.md)

## Required Product Shape

The future C# version must remain a Windows-first desktop application for the
primary ITSS workflow. The application should still feel like an operational
workspace, not a form collection or report viewer.

The core workspace must keep these top-level workflow areas:

- Incident
- Camp Ops
- Inventory
- Network
- Outputs

The exact visual treatment can change, but the future UI must preserve stable,
visible navigation across those areas and must support fast movement between
incident details, camp operations, inventory, network views, and outputs.

## Must Carry Forward

### 1. Incident Workspace Shell

The C# version must preserve the main workspace structure:

- menu bar with File, Edit, View, Incident, Camp Ops, Inventory, Network,
  Outputs, and Help areas
- central workspace with top-level workflow folders and task-level screens
- left Incident Explorer
- right Properties pane
- bottom status bar with current incident, selection, operational period, and
  readiness/action feedback

The prototype proves this layout is a useful operating model for ITSS work and
should be the default structure for the rewrite.

### 2. Incident Explorer And Properties

The future version must provide a persistent incident tree that shows:

- incident
- camps
- buildings or locations
- devices
- networks
- cables or links
- inventory assets
- personnel

Selecting an item must update a properties/details pane. Concrete incident
objects must be editable from that pane when the current user has permission.
Double-click or equivalent selection-driven navigation should take the user to
the matching editor screen.

### 3. Core Domain Model

The C# version must carry forward these domain objects:

- Incident
- Camp
- Building or Location
- Device
- Cable or Physical Link
- Network
- Asset
- Person

Each persistent object must have a stable identifier, creation timestamp, and
updated timestamp. Relationships must survive save/load or server round trips:

- incidents contain camps, assets, and personnel
- camps contain buildings and networks
- buildings contain devices
- networks contain devices and links
- links connect source and destination devices
- assets can be assigned to people
- people can be assigned devices

The C# model should be designed for the future shared-server architecture, not
only for single-user JSON files.

### 4. Incident File And Persistence Workflow

The future version must support the same user workflow shape:

- create a new incident
- open an existing incident
- save the active incident
- save as a new file or record
- reopen recent incidents

The storage technology can change, but users must still have a clear way to
start, persist, reopen, and move incident records. Any migration away from JSON
must preserve a practical import/export path for prototype incident data.

### 5. Editor Workflows

The C# version must preserve editor coverage for:

- incident metadata: name, incident number, agency, operational period
- camp information
- building/location information, including type and optional geographic fields
- asset information, including owner, acquisition type, barcode, assigned
  person, and status
- person information, including position, agency, and assigned devices
- device information, including hostname, manufacturer, model, serial number,
  IP address, MAC address, type, and status
- network information, including network membership and links

Applying edits must update the authoritative in-memory or server-backed model
and refresh dependent views without requiring users to manually reload screens.

### 6. Relationship Editing

The future version must keep explicit workflows for operational relationships:

- assign a device to a building
- add a device to a network
- connect devices with a cable or link
- assign a device to a person
- assign an asset to a person
- clear or change assignments

These relationships are central to the incident record and must not be treated
as display-only details.

### 7. Live Site Map Workflow

Network / Site Map must remain a first-class workflow. The future version must
support:

- visual placement of buildings or locations
- device icons attached to buildings or locations
- visible cable/link connections between devices
- movement of devices and containers
- device movement with a parent building/location when anchored
- link redraws when endpoints move
- zoom controls
- center view
- undo and redo for map interactions
- summary information for camps, devices, networks, links, and inventory

The graphic style can change, but the future version must preserve the ability
to understand camp network layout at a glance.

### 8. Reports And Exports

The C# version must preserve incident summary outputs. At minimum it must export
or generate:

- an incident overview
- camp/building counts
- network/device/link counts
- asset status and assignments
- personnel and assigned devices

The prototype currently exports Markdown, CSV, and HTML. The future version can
choose different report plumbing, but it must retain human-readable and
structured export paths.

### 9. Validation Before Operational Use

The future version must keep a validation workflow that checks workspace
structure before save, export, or closeout. The first C# validation rules should
cover at least:

- missing incident name
- incident with no camps
- camp with no buildings
- camp with no networks
- building with no devices
- network with no devices
- asset assigned to an unknown person
- person assigned to an unknown device

Validation results must be visible to the user and specific enough to fix.

### 10. Windows Desktop Usability

The future version must preserve these usability expectations:

- familiar Windows menus and shortcuts
- persistent status feedback
- readable, utilitarian desktop layout
- docked inspection panels
- keyboard-friendly primary actions
- clear separation between navigation, editing, map interaction, and output
  workflows

The current folder-style tabs are a prototype design choice. The required
carry-forward behavior is clear persistent workflow navigation, not the exact
custom tab drawing.

### 11. Architecture And Testability

The C# version must preserve the architectural separation proven by the Python
prototype:

- domain model independent from UI widgets
- persistence isolated behind repository or service boundaries
- report generation separate from UI code
- validation separate from UI code
- UI screens coordinating model updates without owning business rules

Equivalent automated tests should cover domain relationships, persistence or API
round trips, report output, validation rules, and key UI workflow behavior.

## Not Decided In This Task

The following decisions are intentionally left for later phases:

- WPF versus WinUI 3
- final database choice
- server API shape
- authentication and permissions model
- real-time update mechanism
- mobile/tablet checklist implementation
- installer and deployment model

Those choices should be made in the technical stack and architecture decision
phases after the carry-forward product behavior is stable.

## Phase 1 Conclusion

The C# version must carry forward the prototype's incident-centered workspace,
domain relationships, editing workflows, site map, reports, validation, and
Windows desktop operating model. The rewrite should improve the technical
foundation without losing the field workflow demonstrated by the Python
prototype.
