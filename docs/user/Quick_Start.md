# Quick Start

This guide gets a new user oriented in the current FireIT Manager desktop prototype.

## Start The App

From the project folder, install and run the application:

```powershell
python -m pip install -e .
python -m fireitmanager.app
```

When the app opens, it loads a demo incident named `Pine Gulch Incident`.

## Main Screen

The app has four main areas:

- Top menu bar for file, edit, view, and workspace navigation.
- Center workspace with folder-style tabs.
- Left Incident Explorer dock.
- Right Properties dock.
- Bottom status bar.

## First Five Things To Try

1. Open `Incident` then `Details`.
2. Change the incident name or operational period.
3. Select `Apply Changes`.
4. Open `Network` then `Site Map`.
5. Use `Zoom In`, `Zoom Out`, or `Center View`.

## Save The Incident

Use one of these options:

- `File > Save`
- `File > Save As`
- `Incident > Details`, then the `Save` or `Save As` button at the top of the Details tab

The current prototype saves incident data as JSON.

## Open An Incident

Use:

- `File > Open`
- `Incident > Details`, then the `Open` button
- `File > Recent Files` after files have been opened or saved

## Important Prototype Note

Most changes are first applied in memory. Use `Apply Changes` in the active editor, then
save the incident file when you want the changes written to disk.
