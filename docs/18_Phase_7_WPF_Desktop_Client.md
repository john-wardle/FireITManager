# Phase 7 WPF Desktop Client

Phase 7 adds the first Windows desktop client for the C# field architecture. The client is a WPF app so the finished product can support air-gapped Windows incident camps and future single-file publishing.

## Project

- Project path: `src/FireITManager.Desktop`
- Target framework: `net10.0-windows`
- UI stack: WPF
- Live updates: SignalR client connected to `/hubs/incident`
- Local fallback: JSON cache under `%LOCALAPPDATA%\FireITManager\desktop-cache.json`
- Outputs: print-ready summary text and zipped incident bundle under `%LOCALAPPDATA%\FireITManager\Outputs`

## Desktop Shell

The main window includes the requested Windows menu surface:

- File
- Edit
- View
- Incident
- Camp Ops
- Inventory
- Network
- Outputs
- Help

Keyboard shortcuts are wired for common Windows actions:

- `Ctrl+N` new incident
- `Ctrl+S` save
- `Ctrl+R` or `F5` refresh
- `Ctrl+E` export bundle
- `Ctrl+P` print summary

## Workspaces

The client currently provides these tabs:

- Incident: incident summary data entry with optimistic concurrency versioning.
- Camp Ops: camp list loaded from the local incident server.
- Inventory: device list loaded from the local incident server.
- Network: network and link lists loaded from the local incident server.
- Outputs: export bundle, print summary, and output folder actions.
- Live: current real-time client connections.

## Role And User Controls

The top command strip includes server URL, user id, and role selection. Role-aware commands disable editing for the `Read-only Observer` role while leaving refresh, cache, and output workflows available.

## Real-Time Behavior

The desktop client connects to the local server hub with:

```text
/hubs/incident?userId=<user>&clientName=<machine>&clientKind=desktop
```

It displays connection state in the status bar, receives `IncidentChanged` events, refreshes server data after live changes, and surfaces reconnect/disconnect state through the same status area and activity log.

## Verification

Phase 7 verification is:

```powershell
dotnet build src\FireITManager.Desktop\FireITManager.Desktop.csproj
```

The server should also continue to build:

```powershell
dotnet build src\FireITManager.Server\FireITManager.Server.csproj
```
