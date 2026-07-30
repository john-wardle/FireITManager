# Phase 9 Mobile / Tablet Checklist Tool

## Decision

The first mobile tool is a browser-based PWA served by the incident server at `/mobile/`. It is designed for phones and tablets on the incident LAN and does not require external cloud services, package CDNs, or internet access.

## Implemented Field Workflow

The mobile app now supports:

- Server connection status with cached fallback.
- Current incident heading.
- Camp summary, device list, and link status list.
- Search across loaded incident records and checklist templates.
- Standard ITSS checklist template list.
- Starting checklist runs from templates.
- Checking off steps.
- Step notes.
- Step photo capture/attachment stored inside the run step JSON.
- Blocker flags per step.
- Follow-up task text per step.
- Run notes.
- Offline local save queue for short LAN outages.
- Sync of created and completed checklist runs back to the incident server.
- Troubleshooting guide cards.
- Documentation library cards.
- Contact/escalation cards.

The mobile client uses local storage for cached incident data and pending checklist work. A service worker caches the app shell, stylesheet, script, manifest, and icon so the page remains available after it has been loaded once.

Search indexes camps, devices, links, checklist templates, checklist runs, and nested checklist step data. It includes hostname, known IP assignment identifiers, MAC addresses, asset IDs, location/building identifiers already exposed by the server, camp directions, link endpoints, checklist titles, checklist metadata, notes, blockers, and follow-up text.

## Server Changes

The server now exposes:

- `POST /api/checklist-runs` to start a checklist run from a published template.
- `PUT /api/checklist-runs/{id}/progress` to save status, step progress, notes, blockers, follow-up tasks, and photo metadata/data.

Both endpoints use the existing SQLite database, audit logging, optimistic versioning, and SignalR incident-change broadcast path.

Migration `009_checklist_template_metadata` adds these checklist template fields to SQLite and the `/api/checklist-templates` response:

- Purpose
- Role / owner
- Required tools
- Safety notes
- Prerequisites
- Completion criteria

## Standard Templates

Migration `008_standard_itss_checklist_templates` seeds these global published templates:

- Initial ITSS Arrival
- ICP / Camp Network Setup
- Starlink / Satellite Setup
- Router Setup
- Switch Setup
- Wi-Fi Access Point Setup
- Printer Setup
- User Workstation Setup
- Account / Access Request Handling
- Daily Network Health Check
- Daily Backup / Export Check
- Link Outage Troubleshooting
- Slow Network Troubleshooting
- No Internet Troubleshooting
- Radio Cache / COML Coordination Notes
- Documentation Handoff
- Demobilization Checklist

Each seeded template includes stable step IDs, step titles, expected results, troubleshooting hints, required note/photo flags where appropriate, purpose, owner, required tools, safety notes, prerequisites, and completion criteria.

## Known Gaps

Photo attachments are stored inside checklist run step JSON for this first field version. A later attachment/photo table should move larger media into first-class records with size limits and export controls.
