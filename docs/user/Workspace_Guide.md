# Workspace Guide

This guide explains what each workspace folder is for.

## Incident

### Details

Use `Incident > Details` to manage high-level incident information:

- Incident Name
- Incident Number
- Agency
- Operational Period

The Details tab also shows counts for camps, personnel, and assets.

Actions available at the top of this tab:

- `New Incident`
- `Open`
- `Save`
- `Save As`

### Personnel

Use `Incident > Personnel` to manage the primary person record in the current prototype.

Current fields:

- Name
- Position
- Agency
- Assigned Devices
- Available Devices
- Assigned Device List

Available actions:

- `Apply Changes`
- `Reset`
- `New Person`
- `Add Selected Device`
- `Remove Selected Device`

## Camp Ops

### Camps

Use `Camp Ops > Camps` to edit the primary camp.

Current fields:

- Camp Name
- Building count
- Network count

### Buildings

Use `Camp Ops > Buildings` to edit buildings and location information.

Current fields:

- Building Name
- Building Type
- Location Name
- Latitude
- Longitude
- Elevation
- Notes
- Device count

Available actions:

- `Apply Changes`
- `Reset`
- `New Building`

## Inventory

### Assets

Use `Inventory > Assets` to manage tracked equipment and operational assets.

Current fields:

- Asset Name
- Owner
- Acquisition Type
- Barcode
- Assigned Person
- People Picker
- Status

Available actions:

- `Apply Changes`
- `Reset`
- `New Asset`
- `Use Selected Person`
- `Clear Assigned Person`

### Devices

Use `Inventory > Devices` to manage the primary device in the active building.

Current fields:

- Hostname
- Manufacturer
- Model
- Serial Number
- IP Address
- MAC Address
- Device Type
- Status
- Networks

Available actions:

- `Apply Changes`
- `Reset`
- `New Device`

## Network

### Site Map

Use `Network > Site Map` to visualize the active incident camp network.

The site map shows:

- Camp/building layout.
- Device icons.
- Cable connections.
- A pinned title overlay.
- A summary overlay with camp, device, network, cable, and inventory counts.

Available controls:

- `Undo`
- `Redo`
- `Zoom In`
- `Zoom Out`
- `Center View`

### Networks

Use `Network > Networks` to manage network membership.

Current fields:

- Network Name
- Device count
- Cable count
- Available Devices
- Network Members

Available actions:

- `Apply Changes`
- `Reset`
- `New Network`
- `Add Selected Device`
- `Remove Selected Device`

## Outputs

### Reports

Use `Outputs > Reports` to export incident summaries.

Current exports:

- Markdown summary
- CSV summary
- HTML summary

### Validation

Use `Outputs > Validation` to run workspace checks before saving or exporting.

Current action:

- `Validate Workspace`
