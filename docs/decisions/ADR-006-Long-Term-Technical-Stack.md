# ADR-006: Long-Term Technical Stack

## Status
Accepted

## Context
Phase 4 requires an intentional long-term technical stack decision before
starting the FireIT Manager rewrite. The selected stack must support the Phase
3 data model, air-gapped field execution, Windows-first ITSS desktop workflows,
local incident LAN collaboration, offline field work, local exports, audit
history, and eventual mobile/tablet checklist use.

The Python/PySide6 application remains the prototype and product reference. It
should not become the long-term production architecture.

## Decision
Use this stack for the first production-oriented C#/.NET architecture:

| Area | Decision |
| --- | --- |
| Desktop client | C# WPF on modern .NET |
| Desktop platform | Windows-only first, Windows x64 publish target first |
| Desktop deployment | Self-contained single-file WPF publish for air-gapped field use |
| Server | ASP.NET Core Web API on the incident LAN |
| First shared-server database | SQLite owned by the incident server process |
| Desktop offline cache | Local SQLite cache per WPF client |
| Mobile/tablet client | Browser-based PWA served by the incident server |
| Real-time updates | SignalR server-to-client notifications after successful writes |
| Authentication | Local incident-server accounts and roles |
| Reporting/export | Local .NET report/spreadsheet/archive generation, no cloud conversion |
| Cloud dependency | None required for normal incident operation |

The first field server is scoped to one active incident environment. Archived
or exported past incidents may be retained, but the first version is not a
multi-live-incident regional platform.

## Why
- WPF best matches the Windows-first, dense operational desktop workflow and
  the air-gapped copy-and-run deployment goal.
- ASP.NET Core provides a local API boundary for multi-user editing while
  keeping the incident server self-contained.
- SQLite minimizes field setup and keeps backup/export practical, while API
  ownership prevents unsafe shared-file writes from clients.
- SignalR fits ASP.NET Core and provides live incident LAN updates without
  external services.
- A PWA served by the incident server avoids app store, MDM, and native mobile
  build friction while supporting touch-friendly field checklists.
- Local accounts and roles keep authentication available when cloud identity,
  domain controllers, or agency SSO are unavailable.
- The stack preserves upgrade paths: PostgreSQL or SQL Server can replace the
  server database later, native mobile can be reconsidered after field testing,
  and WinUI 3 can be revisited only if a hard Windows App SDK requirement
  appears.

## First Migration Milestone
Build the smallest useful C#/.NET vertical slice:

1. Create a WPF desktop shell with Incident workspace navigation.
2. Create an ASP.NET Core incident server with health and incident summary
   endpoints.
3. Store one incident record in server-owned SQLite.
4. Let the WPF client connect to the local server and display/edit incident
   name, number, agency, and operational period.
5. Add local account sign-in with one administrator and one ITSS role.
6. Persist changes through the API and record audit events.
7. Broadcast accepted incident metadata changes through SignalR.
8. Publish the WPF client and incident server as self-contained Windows x64
   field builds.

This milestone is intentionally narrow. It proves the chosen stack, local
server ownership, authentication, audit, live updates, and deployment without
rebuilding every prototype screen.

## Alternatives Considered
- WinUI 3 desktop client: rejected first because WPF better fits air-gapped
  single-file field deployment and mature desktop workflow needs.
- Cross-platform desktop first: rejected because the first desktop target is
  Windows ITSS laptops.
- Native mobile app first: rejected because PWA deployment is simpler for
  incident LAN field use.
- PostgreSQL or SQL Server first: deferred until field testing proves SQLite is
  insufficient.
- Cloud-hosted API/database/identity: rejected for normal incident operation.
- Direct shared database files: rejected because server-owned writes are needed
  for multi-user editing and auditability.

## Consequences
- The rewrite can start after Phase 4 with a narrow stack-validation milestone.
- The API and persistence boundaries must be designed so SQLite can be replaced
  later without changing WPF/PWA workflows.
- Authentication, authorization, audit, and sync identity must be built before
  broad write workflows.
- Export, backup, restore, and deployment tests are part of field readiness.
- Prototype Python work should remain limited to product clarification,
  documentation, and migration evidence.

## Related Decisions
- ADR-004: Desktop UI Stack
- ADR-005: Air-Gapped Field Deployment
