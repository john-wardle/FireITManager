# ADR-004: Desktop UI Stack

## Status
Accepted for the first C# desktop migration

## Context
FireIT Manager needs a Windows-first desktop client for ITSS users. The client
must support a familiar operational workspace, menu-driven workflows, docked
inspection panels, dense data entry screens, network map interactions, printing
or export workflows, and eventual server-backed multi-user updates.

The current Python prototype proves the product workflow but should not become
the production architecture. Phase 4 requires choosing between WPF and WinUI 3
before starting the rewrite.

Current Microsoft documentation describes WPF as a Windows-only .NET desktop UI
framework with XAML, controls, data binding, layout, graphics, animation, and
hardware-accelerated rendering. Microsoft documentation describes WinUI 3 as
the modern native Windows UI framework delivered through the Windows App SDK.
Windows App SDK deployment adds runtime/package decisions that must be managed
for packaged, unpackaged, framework-dependent, or self-contained apps.

Air-gapped incident camp deployment is now a first-class planning constraint.
The desktop client should run from a thumb drive, local folder, or incident LAN
share without relying on external cloud services or machine-wide runtime setup.
Microsoft's Windows App SDK self-contained deployment documentation says that
WinUI 3 apps can be self-contained, but native Windows App SDK dependencies
remain separate files and `dotnet publish` cannot produce a true single-file
EXE for WinUI 3 apps. .NET single-file publishing, by contrast, supports
single-file self-contained publishing for .NET applications, subject to normal
single-file compatibility rules and native-library extraction behavior.

## Decision
Use C# WPF first for the Windows desktop client.

The first C# desktop client is Windows-only and should be designed for
self-contained single-file publishing for the primary field distribution path.

Defer WinUI 3 unless a later requirement clearly depends on Windows App SDK UI
features that WPF cannot meet without unacceptable cost.

## Why
- WPF fits the immediate product shape: data-heavy operational screens,
  command menus, docked panes, tree navigation, property editing, validation,
  reports, and map/canvas-style workflows.
- WPF keeps the first migration smaller by relying on mature .NET desktop
  patterns instead of solving Windows App SDK packaging and runtime questions at
  the same time as the product rewrite.
- WPF is Windows-only, which matches the desktop-client target for the first
  C# version.
- WPF can still use modern .NET libraries and can integrate Windows App SDK
  features later if a specific feature justifies that dependency.
- The mobile/tablet checklist tool is expected to be separate from the desktop
  client, so the desktop UI framework does not need to solve mobile reach.
- WPF better matches the air-gapped deployment goal because the first desktop
  release can target a self-contained single-file .NET publish profile without
  Windows App SDK sidecar runtime files.

## Alternatives Considered

### WinUI 3
WinUI 3 is the modern native Windows UI framework and would be a strong choice
if the first desktop version required the latest Fluent controls, Windows App
SDK app lifecycle features, or a Microsoft Store/MSIX-centered distribution
model.

It is not selected first because FireIT Manager's immediate risk is rebuilding
the incident workflow and shared model, not achieving the newest Windows visual
style. WinUI 3 also introduces Windows App SDK runtime and deployment decisions
that should not be coupled to the first migration milestone unless needed.

### Keep PySide6
PySide6 remains useful for the Python prototype, but it is not the selected
long-term Windows desktop stack.

### Web/Electron Desktop
A web or Electron desktop app could share technology with a mobile/PWA client,
but it does not match the current Windows-first desktop goal as directly as WPF
and would add a larger runtime and different native integration tradeoffs.

## Consequences
- The first C# desktop project should be a WPF application on modern .NET.
- The first C# desktop project should target Windows x64 first. Additional
  Windows architectures can be added after the migration path is proven.
- The release process should include a self-contained single-file WPF publish
  profile and field tests on unmanaged Windows 10/11 machines with no internet
  access.
- The app must not assume files can be located by assembly path APIs that are
  incompatible with .NET single-file deployment; use `AppContext.BaseDirectory`
  or explicit configured data paths for local data and exports.
- UI code must stay separate from domain, persistence, validation, reporting,
  and synchronization logic.
- The first migration milestone should rebuild a narrow but real workflow,
  rather than reimplementing every prototype screen at once.
- Styling should be restrained and operational; do not chase a Fluent redesign
  until core workflows are stable.
- If WinUI 3-only requirements emerge, create a follow-up ADR before switching
  UI stacks.

## References
- Microsoft Learn: Windows Presentation Foundation overview -
  https://learn.microsoft.com/en-us/dotnet/desktop/wpf/overview/
- Microsoft Learn: WinUI 3 -
  https://learn.microsoft.com/en-us/windows/apps/winui/winui3/
- Microsoft Learn: Windows App SDK -
  https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/
- Microsoft Learn: Package and deploy Windows apps overview -
  https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/
- Microsoft Learn: Windows App SDK deployment guide for self-contained apps -
  https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/self-contained-deploy/deploy-self-contained-apps
- Microsoft Learn: .NET single-file deployment -
  https://learn.microsoft.com/en-us/dotnet/core/deploying/single-file/overview
