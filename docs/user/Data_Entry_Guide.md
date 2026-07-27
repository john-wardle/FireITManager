# Data Entry Guide

This guide describes the main data fields used in the current prototype.

## Incident

Required:

- Incident Name

Optional:

- Incident Number
- Agency
- Operational Period

Notes:

- The incident summary appears throughout the app.
- Changing the incident name updates related editor summaries after `Apply Changes`.

## Camp

Required:

- Camp Name

Notes:

- The current prototype focuses on the primary camp.
- If an incident has no camp, a default `Base Camp` is created.

## Building

Required:

- Building Name

Optional:

- Building Type
- Location Name
- Latitude
- Longitude
- Elevation
- Notes

Validation:

- Latitude, longitude, and elevation must be numeric when entered.

Notes:

- If no location fields are entered, the building location can remain empty.
- If any location field is entered, a location record is attached to the building.

## Device

Required:

- Hostname

Optional:

- Manufacturer
- Model
- Serial Number
- IP Address
- MAC Address
- Device Type
- Status

Notes:

- Device network membership is shown in the device editor.
- Network membership is changed from `Network > Networks`.

## Network

Required:

- Network Name

Related data:

- Devices
- Cables

Notes:

- Devices are added to or removed from the network using the network editor.
- Cable editing is limited in the current prototype.

## Asset

Required:

- Asset Name

Optional:

- Owner
- Acquisition Type
- Barcode
- Assigned Person
- Status

Notes:

- Assigned person must match an existing incident person.
- Use `People Picker` and `Use Selected Person` to avoid typing mismatch.

## Person

Required:

- Name

Optional:

- Position
- Agency
- Assigned Devices

Notes:

- Assigned devices must exist in the incident.
- Use the device selector and add/remove buttons when possible.

## Properties Dock Editing

The Properties dock can edit selected concrete objects from the explorer or site map.

Editable object types include:

- Incident
- Camp
- Building
- Device
- Network
- Asset
- Person
- Cable

The Properties dock is useful for quick edits without changing workspace tabs.

## Save Behavior

Changes made with `Apply Changes` are in memory until saved.

Use:

- `File > Save`
- `File > Save As`
- `Incident > Details > Save`
- `Incident > Details > Save As`
