# ADR-005: Air-Gapped Field Deployment

## Status
Accepted for first shared-server field version

## Context
FireIT Manager is intended for incident IT work where internet access may be
unavailable, intentionally blocked, or unreliable. The system must support an
on-site incident LAN, local operators, local exports, local backups, and
demobilization handoff without external cloud dependencies.

Phase 4 planning must account for unmanaged Windows laptops, field servers such
as ruggedized NUCs or spare laptops, USB transfer, and local network shares.
The design must also preserve the Phase 3 data-model requirements for stable
identifiers, audit history, optimistic concurrency, mobile sync, and
server-backed multi-user editing.

## Decision
Use an air-gapped, local-first client/server deployment:

```text
WPF Desktop Client
        |
        | Local incident LAN, no internet required
        v
ASP.NET Core Incident Server
        |
        v
Server-owned SQLite incident database, audit log, exports, and attachments
```

For the first shared-server field version:

- Desktop client: C# WPF, Windows-only, self-contained single-file publish.
- Incident server: ASP.NET Core Web API hosted on the incident LAN.
- First shared-server database: SQLite owned by the incident server process.
- Offline desktop cache: local SQLite file per client.
- Export bundle: local compressed archive containing the incident database
  export, attachments, generated reports, and audit trail.
- External cloud services: none required for normal incident operation.

## Why
- A WPF self-contained desktop client supports the simplest copy-and-run field
  distribution path for unmanaged Windows laptops.
- ASP.NET Core gives the incident a single local authority for shared data
  without requiring internet or cloud services.
- SQLite keeps the first field-server deployment zero-configuration: no
  separate database server install, no administrator-run database service, and
  simple backup/export behavior.
- Keeping SQLite behind the server API avoids the unsafe pattern of multiple
  clients editing a shared database file directly.
- Local SQLite desktop caches allow offline field work and later sync without
  treating local files as the incident source of truth.
- Local report/export libraries can produce PDFs, spreadsheets, and archive
  bundles without using cloud conversion endpoints.

## Deployment Shape

### Desktop Client
- Publish as a self-contained Windows x64 single-file WPF executable.
- Support configuration of the local incident server URL or IP address.
- Store client cache, settings, and unsynced work in an explicit local data
  directory, not beside the executable unless the user chooses a portable mode.
- Validate on Windows 10/11 machines with no internet access and no developer
  tooling installed.

### Incident Server
- Publish as a self-contained ASP.NET Core executable for the field server.
- Bind only to the incident LAN interface by default.
- Own the authoritative SQLite database file and attachment storage folder.
- Provide backup, restore, and export commands before field testing.

### Offline Sync
- The WPF client may continue working from a local SQLite cache when the server
  is unavailable.
- Sync must preserve local created time, sync time, actor, source machine, and
  conflict state.
- Server acceptance of offline changes must create audit events.

### Reports And Handoff
- Generate reports locally with .NET libraries rather than cloud services.
- Candidate PDF library: QuestPDF, with licensing reviewed before production
  use.
- Candidate spreadsheet library: ClosedXML for `.xlsx` exports without
  requiring Microsoft Excel.
- Use `System.IO.Compression` for export bundles that include data, reports,
  attachments, and audit history.

## Alternatives Considered

### PostgreSQL or SQL Server for first field server
Both are stronger long-term shared database options, but they add setup,
service management, backup, and administrator complexity. They remain viable
later if field testing proves SQLite is too constrained.

### Direct shared SQLite file
Rejected. It is simpler than a server but does not provide a safe source of
truth for multi-user editing across incident laptops.

### Cloud-hosted API or database
Rejected for the first field version because normal operation must not require
internet, cloud identity, or external services.

### WinUI 3 desktop client
Rejected for the first desktop client in ADR-004. WinUI 3 remains an option
only if later requirements justify the Windows App SDK deployment tradeoffs.

## Consequences
- The first server implementation can stay small: incident summary, camps,
  devices, networks, links, checklists, audit, backup, and restore.
- SQLite schema design must be careful about transactions, migrations, backup,
  WAL/checkpoint behavior, and API-mediated writes.
- If concurrent field use exceeds SQLite's practical limits, the server data
  layer must be replaceable with PostgreSQL or SQL Server behind the same API
  contracts.
- Offline sync and conflict handling must be designed early enough that local
  caches do not become unofficial competing sources of truth.
- Export and backup workflows become core field features, not afterthoughts.

## References
- Microsoft Learn: Windows App SDK deployment guide for self-contained apps -
  https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/self-contained-deploy/deploy-self-contained-apps
- Microsoft Learn: .NET single-file deployment -
  https://learn.microsoft.com/en-us/dotnet/core/deploying/single-file/overview
- Microsoft Learn: ASP.NET Core overview -
  https://learn.microsoft.com/en-us/aspnet/core/introduction-to-aspnet-core
- Microsoft Learn: SQLite EF Core provider -
  https://learn.microsoft.com/en-us/ef/core/providers/sqlite/
