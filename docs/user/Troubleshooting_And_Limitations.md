# Troubleshooting And Limitations

This document lists practical notes for the current prototype.

## The App Opens With Demo Data

Current behavior:

- The app starts with a demo incident named `Pine Gulch Incident`.

What to do:

- Use `Incident > Details > New Incident` to start a fresh incident.
- Use `File > Open` to load a saved incident file.

## I Changed A Field But Other Screens Did Not Update

Check:

- Did you select `Apply Changes`?
- Did you save after applying?

Most editor changes are applied in memory first. Other screens refresh after the editor
emits its update.

## I Saved But The File Is Not Where I Expected

Use `File > Save As` when you need control over the destination path.

The default save path is a temporary FireIT Manager location until the user chooses a
file path.

## Recent File Is Missing

If a recent file was moved or deleted, FireIT Manager reports that the recent file is
missing and removes it from the recent list.

## Assigned Person Not Found

Asset assignment by typed name requires the person to already exist in the incident.

Recommended fix:

1. Create or update the person in `Incident > Personnel`.
2. Return to `Inventory > Assets`.
3. Use the `People Picker`.
4. Select `Use Selected Person`.
5. Apply changes.

## Device Not Found

Person device assignment by typed hostname requires the device to already exist.

Recommended fix:

1. Create or update the device in `Inventory > Devices`.
2. Return to `Incident > Personnel`.
3. Use the device selector.
4. Select `Add Selected Device`.
5. Apply changes.

## Site Map Zoom Looks Wrong

Use:

- `View > Center View`
- `Network > Site Map > Center View`
- `Zoom In`
- `Zoom Out`

The status bar shows the current zoom percentage.

## Multi-User Editing Is Not Available Yet

The current prototype is a single-user desktop app using local save/load. It does not
yet provide live simultaneous updates between multiple ITSS users.

The planned architecture is:

- Incident-local server.
- Shared database.
- Live update channel.
- Windows desktop client.
- Mobile/tablet checklist client.

## Mobile Checklist Tool Is Not Available Yet

The planned checklist tool will support tablet/phone use around camp, but it is not yet
implemented in the current prototype.

Planned capabilities include:

- Standard ITSS checklists.
- Troubleshooting guides.
- Documentation library.
- Notes and photos.
- Sync to the incident record.

## Known Prototype Boundaries

- Primary editors usually focus on the first or currently selected object.
- Full multi-object management is still evolving.
- Cable editing is limited.
- Live telemetry and link-state monitoring are not yet implemented.
- User accounts, permissions, and audit history are not yet implemented.
- Data is currently saved as local JSON, not to a shared server database.
