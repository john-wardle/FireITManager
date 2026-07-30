# ITSS Live Incident Network Project Checklist

Use this checklist as a hardcopy project tracker. Mark each item only when it is actually complete and verified.

Project:

Incident / Test Environment:

Owner:

Last Updated:

## Target Outcome

Build FireIT Manager into a Windows-first incident IT management platform that supports:

- A core desktop application with a familiar Windows feel for ITSS users.
- Simultaneous multi-user incident updates.
- A live camp network map showing physical and virtual connections.
- Clear visual link states for all important network paths.
- A mobile/tablet checklist tool for field work, troubleshooting, documentation, and help.

## Guiding Architecture

```text
Windows Desktop Client
        |
        | API and live updates
        v
Incident Server on the incident LAN
        |
        v
Database, audit log, telemetry collectors, checklist content
        |
        v
Mobile / Tablet Checklist Client
```

## Phase 1: Stabilize The Current Python Prototype

Goal: Keep current progress useful while the long-term architecture is designed.

- [ ] Confirm the current Python app remains the working prototype.
- [ ] Keep current GitHub repository clean and committed after each meaningful change.
- [ ] Maintain passing tests before making large changes.
- [x] Document current screens and workflows with screenshots.
- [x] Identify which prototype features must exist in the future C# version.
- [x] Identify which prototype features are temporary and can be discarded later.
- [x] Avoid adding large new systems to the Python app unless they clarify the product.

Done when:

- [ ] The prototype can demonstrate incident details, camp operations, inventory, network views, reports, and validation.
- [ ] The current workflow is documented well enough to rebuild intentionally in another stack.

## Phase 2: Define The Incident Operating Model

Goal: Describe how ITSS users will actually use the tool during an incident.

- [ ] List primary user roles: ITSS, COML, COMT, trainee, logistics, read-only observer.
- [ ] Define what each role can view.
- [ ] Define what each role can edit.
- [ ] Define the normal daily ITSS workflow.
- [ ] Define the initial incident setup workflow.
- [ ] Define demobilization and closeout workflow.
- [ ] Define how users work when disconnected from the local network.
- [ ] Define what must be printable for command staff.
- [ ] Define what must be available on phone/tablet in the field.
- [ ] Define what is considered official incident record data.

Done when:

- [ ] A written workflow exists for setup, daily operations, troubleshooting, reporting, and closeout.
- [ ] User permissions are clear enough to design screens and database rules.

## Phase 3: Define Core Data Model

Goal: Make the shared data model solid before rebuilding the application.

- [x] Define Incident.
- [x] Define Camp.
- [x] Define Building / Location.
- [x] Define Person.
- [x] Define Device.
- [x] Define Asset.
- [x] Define Network.
- [x] Define Physical Link.
- [x] Define Virtual Link.
- [x] Define Service.
- [x] Define VLAN / subnet.
- [x] Define IP address assignment.
- [x] Define wireless link.
- [x] Define satellite / WAN link.
- [x] Define link state history.
- [x] Define checklist template.
- [x] Define checklist run / completed checklist.
- [x] Define attachment / photo / note.
- [x] Define audit event.

Data rules to decide:

- [x] What fields are required.
- [x] What fields are optional.
- [x] What values are controlled lists.
- [x] What values can be free text.
- [x] What records can be archived instead of deleted.
- [x] What changes must create audit history.
- [x] What objects can be created from the mobile tool.

Done when:

- [x] The model can represent a real camp network, not just a demo.
- [x] The model can support multi-user editing without relying on shared JSON files.

## Phase 4: Choose The Long-Term Technical Stack

Goal: Make an intentional architecture decision before a rewrite.

- [x] Decide between WPF and WinUI 3 for the Windows desktop client.
- [x] Decide whether the first C# version must run only on Windows.
- [x] Decide whether the mobile/tablet tool is web/PWA first.
- [x] Choose database: PostgreSQL, SQL Server, or SQLite for first shared-server version.
- [x] Choose real-time update mechanism.
- [x] Choose authentication approach for incident-local use.
- [x] Choose installer/deployment approach for the desktop client.
- [x] Write an architecture decision record before starting the rewrite.

Recommended default:

- [x] Desktop client: C# WPF first, unless WinUI 3 features are required.
- [x] Server: ASP.NET Core.
- [x] Live updates: SignalR.
- [x] Database: SQLite for first air-gapped shared server and local/offline cache; PostgreSQL or SQL Server later if field testing proves the need.
- [x] Mobile/tablet checklist client: browser-based PWA served by the incident server.

Done when:

- [x] The selected stack is documented.
- [x] The reason for the choice is documented.
- [x] The first migration milestone is small enough to finish.

## Phase 5: Build The Incident Server Foundation

Goal: Create the central authority for shared incident data.

- [x] Create server project.
- [x] Add database connection.
- [x] Add schema migrations.
- [x] Add API endpoint for incident summary.
- [x] Add API endpoint for camps.
- [x] Add API endpoint for devices.
- [ ] Add API endpoint for networks.
- [ ] Add API endpoint for links.
- [ ] Add API endpoint for checklist templates.
- [ ] Add API endpoint for checklist runs.
- [ ] Add audit logging for create, update, delete.
- [x] Add server health endpoint.
- [ ] Add backup/export command.
- [ ] Add restore/import command.

Done when:

- [ ] Two clients can read the same incident data from the server.
- [ ] All changes are stored in the database.
- [ ] Changes are traceable to a user and time.

## Phase 6: Add Real-Time Multi-User Updates

Goal: Make changes visible to all connected users without manual refresh.

- [ ] Add real-time connection endpoint.
- [ ] Add client connection tracking.
- [ ] Broadcast incident changes.
- [ ] Broadcast camp changes.
- [ ] Broadcast device changes.
- [ ] Broadcast network changes.
- [ ] Broadcast link status changes.
- [ ] Broadcast checklist completion changes.
- [ ] Add reconnect behavior.
- [ ] Add stale connection cleanup.
- [ ] Add visible connection status in the desktop client.
- [ ] Add visible connection status in the mobile client.

Conflict rules:

- [ ] Decide whether last write wins is acceptable for early versions.
- [ ] Add optimistic concurrency tokens for important records.
- [ ] Show a conflict warning when a user edits stale data.
- [ ] Keep audit history even when conflicts are resolved manually.

Done when:

- [ ] Two users can update the same incident and see changes appear live.
- [ ] The app gives clear feedback when the server connection is lost.

## Phase 7: Build The Windows Desktop Client

Goal: Replace the prototype UI with a polished Windows-first client.

- [ ] Create desktop shell with File, Edit, View, Incident, Camp Ops, Inventory, Network, Outputs, Help.
- [ ] Rebuild Incident workspace.
- [ ] Rebuild Camp Ops workspace.
- [ ] Rebuild Inventory workspace.
- [ ] Rebuild Network workspace.
- [ ] Rebuild Outputs workspace.
- [ ] Add standard Windows keyboard shortcuts.
- [ ] Add role-aware menus and actions.
- [ ] Add server connection settings.
- [ ] Add user sign-in or incident user selection.
- [ ] Add local cache if offline mode is required.
- [ ] Add error and validation display.
- [ ] Add print/export workflows.

Done when:

- [ ] The desktop app can replace the Python prototype for day-to-day incident data entry.
- [ ] The UI feels familiar to Windows users and does not require training for basic navigation.

## Phase 8: Build The Live Network Map

Goal: Show the incident network as a live operational picture.

- [ ] Define map object types: camp, building, device, link, service, VLAN, WAN, wireless.
- [ ] Define visual status colors.
- [ ] Define status labels: unknown, up, degraded, down, disabled, planned, maintenance.
- [ ] Define status priority when several signals conflict.
- [ ] Draw camps and buildings.
- [ ] Draw physical device links.
- [ ] Draw virtual links.
- [ ] Draw WAN / satellite / internet paths.
- [ ] Draw wireless links.
- [ ] Show link direction and type where useful.
- [ ] Show hover/click details for each object.
- [ ] Show last-seen time for each status.
- [ ] Show manual override indicator.
- [ ] Show historical status for a selected link.
- [ ] Add filtering by network, camp, device type, and status.
- [ ] Add search for device, IP, MAC, hostname, or person.

Telemetry sources to evaluate:

- [ ] ICMP ping.
- [ ] SNMP.
- [ ] HTTP/HTTPS checks.
- [ ] SSH reachability.
- [ ] Router/switch API where available.
- [ ] LLDP/CDP where available.
- [ ] Manual ITSS status override.

Done when:

- [ ] A user can look at the map and quickly identify what is down, degraded, or unknown.
- [ ] Link state changes appear live for all connected users.

## Phase 9: Build The Mobile / Tablet Checklist Tool

Goal: Give ITSS users field access to checklists, troubleshooting steps, notes, and documentation.

Recommended first version:

- [ ] Browser-based mobile tool served by the incident server.
- [ ] Works on tablet and phone.
- [ ] Uses large touch targets.
- [ ] Works on incident LAN without internet.
- [ ] Caches checklist content for short outages.

Core mobile features:

- [ ] View assigned incident.
- [ ] View camp map summary.
- [ ] View device list.
- [ ] View link status list.
- [ ] Search hostname, IP, MAC, asset tag, building, or checklist.
- [ ] Open standard ITSS checklists.
- [ ] Start a checklist run.
- [ ] Check off steps.
- [ ] Add notes to checklist steps.
- [ ] Attach photos.
- [ ] Mark blockers.
- [ ] Assign follow-up task.
- [ ] Sync completed checklist to server.
- [ ] View troubleshooting guides.
- [ ] View documentation library.
- [ ] View contact / escalation information.

Checklist content areas:

- [ ] Initial ITSS arrival.
- [ ] ICP / camp network setup.
- [ ] Starlink / satellite setup.
- [ ] Router setup.
- [ ] Switch setup.
- [ ] Wi-Fi access point setup.
- [ ] Printer setup.
- [ ] User workstation setup.
- [ ] Account / access request handling.
- [ ] Daily network health check.
- [ ] Daily backup/export check.
- [ ] Link outage troubleshooting.
- [ ] Slow network troubleshooting.
- [ ] No internet troubleshooting.
- [ ] Radio cache / COML coordination notes.
- [ ] Documentation handoff.
- [ ] Demobilization checklist.

Checklist template fields:

- [ ] Title.
- [ ] Purpose.
- [ ] Role / owner.
- [ ] Required tools.
- [ ] Safety notes.
- [ ] Prerequisites.
- [ ] Steps.
- [ ] Expected result per step.
- [ ] Troubleshooting hint per step.
- [ ] Required photo or note flag.
- [ ] Completion criteria.
- [ ] Version.

Done when:

- [ ] An ITSS can walk camp with a tablet or phone and complete a checklist without returning to the desktop app.
- [ ] Completed checklist runs become part of the incident record.

## Phase 10: Security, Access, And Audit

Goal: Keep incident data usable while protecting it from accidental or unauthorized changes.

- [ ] Define user roles.
- [ ] Define local incident authentication.
- [ ] Define emergency access procedure.
- [ ] Add role-based permissions.
- [ ] Add audit log viewer.
- [ ] Record user, time, object, and change summary.
- [ ] Protect destructive actions.
- [ ] Add exportable audit trail.
- [ ] Add backup schedule.
- [ ] Add restore drill.

Done when:

- [ ] Important changes can be traced.
- [ ] A mistaken change can be understood and corrected.

## Phase 11: Field Testing

Goal: Prove the system against real ITSS workflows before depending on it.

- [ ] Build a test incident.
- [ ] Enter a realistic camp layout.
- [ ] Enter realistic devices.
- [ ] Enter realistic links.
- [ ] Run two desktop clients at once.
- [ ] Run one tablet or phone client.
- [ ] Simulate link down.
- [ ] Simulate server restart.
- [ ] Simulate client disconnect and reconnect.
- [ ] Simulate conflicting edits.
- [ ] Complete an initial setup checklist.
- [ ] Complete a daily health checklist.
- [ ] Export reports.
- [ ] Backup and restore the incident.
- [ ] Record user feedback.
- [ ] Prioritize fixes before adding features.

Done when:

- [ ] At least one ITSS can use the system without developer help.
- [ ] The top five field issues are documented.
- [ ] The next development cycle is based on field feedback.

## Weekly Execution Checklist

Use this section every week.

- [ ] Pick one main objective for the week.
- [ ] Write the expected finished state.
- [ ] Confirm current Git branch is clean before starting.
- [ ] Make the smallest useful change.
- [ ] Run tests.
- [ ] Update documentation.
- [ ] Commit.
- [ ] Push to GitHub.
- [ ] Write down what changed.
- [ ] Write down what is next.

## Stop Conditions

Pause and reassess if any of these happen:

- [ ] The data model is being changed repeatedly for the same concept.
- [ ] Multi-user behavior depends on shared files.
- [ ] The live map cannot explain why a link is marked down.
- [ ] Mobile checklist data cannot sync back into the incident record.
- [ ] Users need training to find basic screens.
- [ ] A feature cannot be tested without a real incident.

## Near-Term Next Steps

- [ ] Finish documenting the Python prototype workflows.
- [ ] Create an architecture decision record for the future C#/.NET direction.
- [ ] Draft the first shared incident data model.
- [ ] Draft the first checklist template format.
- [ ] Build one real ITSS checklist in markdown or JSON.
- [ ] Decide the first field test scenario.
- [ ] Keep all current prototype changes committed and pushed.
