# Deployment

## Air-Gapped Field Deployment Plan

FireIT Manager must be able to run at an incident site with no internet access
and no external cloud dependency. The first C# field architecture is local
first: WPF desktop clients connect to an on-site ASP.NET Core incident server
over the incident LAN.

```text
WPF Client Binary
    Runs on ITSS laptops
        |
        | Local LAN, no internet required
        v
On-Site Incident Server
    ASP.NET Core Web API + server-owned SQLite database
```

## Desktop Client

- Target C# WPF on modern .NET.
- Publish the first field build as a Windows x64 self-contained single-file
  executable.
- Support launch from a local folder, thumb drive, or incident LAN share.
- Keep settings, local cache, unsynced work, and exports in explicit data
  directories so the executable can remain replaceable.
- Use a local SQLite cache for offline work when the incident server is
  unreachable.

Planned publish shape once the C# desktop project exists:

```powershell
dotnet publish .\src\FireITManager.Desktop\FireITManager.Desktop.csproj `
  -c Release `
  -r win-x64 `
  --self-contained true `
  -p:PublishSingleFile=true `
  -p:EnableCompressionInSingleFile=true
```

## Incident Server

- Target ASP.NET Core Web API.
- Run on a field server, ruggedized NUC, or designated incident laptop.
- Own the authoritative SQLite database file and attachment storage folder.
- Accept writes only through the API; clients must not edit a shared database
  file directly.
- Provide backup, restore, export, and health-check commands before field
  testing.
- Resolve runtime paths from the executable directory so startup does not depend
  on the user's current working directory.
- Write startup failures to `logs/server-startup-error.log` beside the server
  executable instead of depending on Windows Event Log permissions.

## Offline Sync

- The WPF client may continue work against its local SQLite cache when the
  server connection is lost.
- Offline changes must sync back through the server API.
- Sync acceptance must create audit events.
- Conflict handling must preserve both local and server-side history until a
  user or administrator resolves the conflict.

## Reports And Exports

Reports and handoff bundles must be generated locally.

- PDF candidate: QuestPDF, pending licensing review before production use.
- Spreadsheet candidate: ClosedXML for `.xlsx` exports without requiring
  Microsoft Excel.
- Archive bundles: `System.IO.Compression` for incident data, attachments,
  PDFs, spreadsheets, and audit history.
- The export workflow should produce a demobilization handoff bundle that can
  be copied by flash drive.

## Deployment Constraints

- No normal incident workflow may require external cloud services.
- Validate field builds on unmanaged Windows 10/11 machines with no internet
  and no developer tooling installed.
- Avoid dependencies that require machine-wide installers unless a later ADR
  accepts the field cost.
- Keep the server database replaceable behind repository/API boundaries so a
  later PostgreSQL or SQL Server migration remains possible.
