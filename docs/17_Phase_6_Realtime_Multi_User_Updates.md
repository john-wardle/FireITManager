# Phase 6 Real-Time Multi-User Updates

Phase 6 establishes the first real-time incident update surface for the C# field architecture. The implementation keeps all traffic local to the incident LAN and does not require external cloud services.

## Server Surface

- `GET /api/realtime/connections` returns the active client connection registry.
- `GET /health` continues to expose server and SQLite migration health.
- `GET /mobile/` serves a lightweight mobile connection-status page for field tablets and phones.
- `SignalR /hubs/incident` accepts local desktop, mobile, and browser clients.

## Live Events

The incident hub broadcasts `IncidentChanged` events after successful writes for these records:

- Incident summary create, update, and delete.
- Camp status updates.
- Device status updates.
- Network status updates.
- Link status updates.
- Checklist run completion updates.

Each event carries an event id, sequence, entity type, entity id, incident id, actor id, version, summary, and UTC timestamp.

## Connection Tracking

Clients identify themselves with `userId`, `clientName`, and `clientKind` query values when they connect to `/hubs/incident`. The server records connection id, user id, client name, client kind, remote address, connected time, and last-seen time. Clients can call `Ping` to refresh last-seen state.

A hosted cleanup service removes connections that have not been seen for two minutes. Connected clients receive `ConnectionStatus` updates for their own connection and `ClientConnectionChanged` notifications when other clients connect or disconnect.

## Conflict Rules

Important mutable records now carry integer `version` tokens. Write APIs accept an optional `expectedVersion` value. If the submitted version is stale, the server returns `409 Conflict` with the current version so the client can refresh and retry deliberately.

Current early-version policy:

- A write without `expectedVersion` is allowed for simple field status changes.
- A write with a stale `expectedVersion` is rejected.
- Successful writes increment the record version and emit audit history.
- Manual conflict resolution is handled by refreshing the record, reviewing the current value, and submitting a new intentional write.

## Verification

Phase 6 verification is:

```powershell
dotnet build src\FireITManager.Server\FireITManager.Server.csproj
```

Runtime checks should confirm:

- `/health` returns `Healthy`.
- `/api/realtime/connections` returns a JSON list.
- `/hubs/incident/negotiate?negotiateVersion=1` accepts a SignalR negotiate request.
- `/mobile/` shows a connected or disconnected state and refreshes without a page reload.
- Two connected clients receive `IncidentChanged` events after incident, status, link, or checklist writes.
