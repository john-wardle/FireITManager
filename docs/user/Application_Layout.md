# Application Layout

FireIT Manager uses a familiar desktop layout with menus, workspace tabs, dock panels,
and a status bar.

## Menu Bar

The top menu bar follows the current workspace order:

- `File`
- `Edit`
- `View`
- `Incident`
- `Camp Ops`
- `Inventory`
- `Network`
- `Outputs`
- `Help`

## File Menu

Use `File` for incident file actions:

- `New Incident`
- `Open`
- `Save`
- `Save As`
- `Recent Files`

## Edit Menu

Use `Edit` for standard text editing commands:

- `Undo`
- `Redo`
- `Cut`
- `Copy`
- `Paste`
- `Delete`
- `Select All`

When a text field is focused, these commands operate on that field. Undo and redo fall
back to the site-map canvas when no focused text field handles them.

## View Menu

Use `View` for site-map view controls:

- `Zoom In`
- `Zoom Out`
- `Center View`

The Network / Site Map tab also has bottom-centered buttons for these controls.

## Workspace Folders

The center workspace is organized into top-level folders with sub-tabs.

| Folder | Sub-tabs |
| --- | --- |
| Incident | Details, Personnel |
| Camp Ops | Camps, Buildings |
| Inventory | Assets, Devices |
| Network | Site Map, Networks |
| Outputs | Reports, Validation |

The top-level menus match these folders so a user can navigate either by menu or by tab.

## Incident Explorer

The left dock shows the active workspace tree. It includes the incident, camps, buildings,
devices, networks, cables, inventory, and personnel.

Use the explorer to:

- Inspect the incident structure.
- Select an object for details.
- Drive the Properties panel.
- Double-click some objects to open their editor tab.

## Properties Dock

The right dock shows details for the selected explorer or site-map object.

For concrete incident objects, the Properties dock also shows editable fields and an
`Apply` button. Group nodes may show details but do not expose editable fields.

## Status Bar

The bottom status bar shows:

- Current ready/action message.
- Active incident summary.
- Current selected item.
- Operational period.
- Site-map zoom percentage.
