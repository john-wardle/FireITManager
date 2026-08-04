using Microsoft.Data.Sqlite;
using SQLitePCL;
using System.Globalization;
using System.Text.Json;

namespace FireITManager.Server.Data;

internal sealed class IncidentDatabase
{
    private const string DatabasePathConfigKey = "IncidentServer:DatabasePath";
    private const string DefaultDatabaseFileName = "fireitmanager.incident.sqlite";

    private static readonly Migration[] Migrations =
    [
        new(
            "001_initial_incident_store",
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                incident_number TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL DEFAULT '',
                agency TEXT NOT NULL DEFAULT '',
                operational_period_start_utc TEXT NULL,
                operational_period_end_utc TEXT NULL,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                actor_user_id TEXT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                occurred_at_utc TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_audit_events_entity
                ON audit_events(entity_type, entity_id);

            CREATE INDEX IF NOT EXISTS idx_audit_events_occurred_at_utc
                ON audit_events(occurred_at_utc);
            """),
        new(
            "002_camp_store",
            """
            CREATE TABLE IF NOT EXISTS camps (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                name TEXT NOT NULL,
                camp_type TEXT NOT NULL,
                status TEXT NOT NULL,
                primary_location_id TEXT NULL,
                address_or_directions TEXT NOT NULL DEFAULT '',
                latitude REAL NULL,
                longitude REAL NULL,
                capacity INTEGER NULL,
                it_contact_person_id TEXT NULL,
                notes TEXT NOT NULL DEFAULT '',
                record_state TEXT NOT NULL DEFAULT 'active',
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                CONSTRAINT fk_camps_incident
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                    ON DELETE CASCADE,
                CONSTRAINT ck_camps_name_not_blank
                    CHECK (length(trim(name)) > 0),
                CONSTRAINT ck_camps_coordinates_complete
                    CHECK ((latitude IS NULL AND longitude IS NULL)
                        OR (latitude IS NOT NULL AND longitude IS NOT NULL)),
                CONSTRAINT ck_camps_capacity_not_negative
                    CHECK (capacity IS NULL OR capacity >= 0),
                CONSTRAINT ck_camps_version_positive
                    CHECK (version >= 1)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_camps_incident_name
                ON camps(incident_id, name COLLATE NOCASE);

            CREATE INDEX IF NOT EXISTS idx_camps_incident
                ON camps(incident_id);

            CREATE INDEX IF NOT EXISTS idx_camps_status
                ON camps(status, record_state);
            """),
        new(
            "003_device_store",
            """
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                hostname TEXT NOT NULL,
                device_type TEXT NOT NULL,
                status TEXT NOT NULL,
                location_id TEXT NULL,
                manufacturer TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                serial_number TEXT NOT NULL DEFAULT '',
                primary_ip_assignment_id TEXT NULL,
                mac_addresses_json TEXT NOT NULL DEFAULT '[]',
                asset_id TEXT NULL,
                notes TEXT NOT NULL DEFAULT '',
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                CONSTRAINT fk_devices_incident
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                    ON DELETE CASCADE,
                CONSTRAINT ck_devices_hostname_not_blank
                    CHECK (length(trim(hostname)) > 0),
                CONSTRAINT ck_devices_version_positive
                    CHECK (version >= 1)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_devices_incident_hostname
                ON devices(incident_id, hostname COLLATE NOCASE);

            CREATE INDEX IF NOT EXISTS idx_devices_incident
                ON devices(incident_id);

            CREATE INDEX IF NOT EXISTS idx_devices_location
                ON devices(location_id);

            CREATE INDEX IF NOT EXISTS idx_devices_status
                ON devices(status);
            """),
        new(
            "004_network_and_link_store",
            """
            CREATE TABLE IF NOT EXISTS networks (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                camp_id TEXT NULL,
                name TEXT NOT NULL,
                network_type TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                CONSTRAINT fk_networks_incident
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_networks_camp
                    FOREIGN KEY (camp_id) REFERENCES camps(id)
                    ON DELETE SET NULL,
                CONSTRAINT ck_networks_name_not_blank
                    CHECK (length(trim(name)) > 0),
                CONSTRAINT ck_networks_version_positive
                    CHECK (version >= 1)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_networks_scope_name
                ON networks(incident_id, ifnull(camp_id, ''), name COLLATE NOCASE);

            CREATE INDEX IF NOT EXISTS idx_networks_incident
                ON networks(incident_id);

            CREATE INDEX IF NOT EXISTS idx_networks_camp
                ON networks(camp_id);

            CREATE INDEX IF NOT EXISTS idx_networks_status
                ON networks(status);

            CREATE TABLE IF NOT EXISTS links (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                network_id TEXT NULL,
                link_category TEXT NOT NULL,
                link_type TEXT NOT NULL,
                status TEXT NOT NULL,
                source_device_id TEXT NULL,
                destination_device_id TEXT NULL,
                source_location_id TEXT NULL,
                destination_location_id TEXT NULL,
                source_ref TEXT NOT NULL DEFAULT '',
                destination_ref TEXT NOT NULL DEFAULT '',
                label TEXT NOT NULL DEFAULT '',
                length TEXT NOT NULL DEFAULT '',
                path TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                CONSTRAINT fk_links_incident
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_links_network
                    FOREIGN KEY (network_id) REFERENCES networks(id)
                    ON DELETE SET NULL,
                CONSTRAINT ck_links_type_not_blank
                    CHECK (length(trim(link_type)) > 0),
                CONSTRAINT ck_links_category_not_blank
                    CHECK (length(trim(link_category)) > 0),
                CONSTRAINT ck_links_version_positive
                    CHECK (version >= 1)
            );

            CREATE INDEX IF NOT EXISTS idx_links_incident
                ON links(incident_id);

            CREATE INDEX IF NOT EXISTS idx_links_network
                ON links(network_id);

            CREATE INDEX IF NOT EXISTS idx_links_status
                ON links(status);
            """),
        new(
            "005_checklist_store",
            """
            CREATE TABLE IF NOT EXISTS checklist_templates (
                id TEXT PRIMARY KEY,
                incident_id TEXT NULL,
                title TEXT NOT NULL,
                template_type TEXT NOT NULL,
                version_label TEXT NOT NULL,
                status TEXT NOT NULL,
                scope_type TEXT NOT NULL DEFAULT 'global',
                scope_id TEXT NULL,
                steps_json TEXT NOT NULL DEFAULT '[]',
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                CONSTRAINT fk_checklist_templates_incident
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                    ON DELETE CASCADE,
                CONSTRAINT ck_checklist_templates_title_not_blank
                    CHECK (length(trim(title)) > 0),
                CONSTRAINT ck_checklist_templates_version_label_not_blank
                    CHECK (length(trim(version_label)) > 0),
                CONSTRAINT ck_checklist_templates_version_positive
                    CHECK (version >= 1)
            );

            CREATE INDEX IF NOT EXISTS idx_checklist_templates_incident
                ON checklist_templates(incident_id);

            CREATE INDEX IF NOT EXISTS idx_checklist_templates_status
                ON checklist_templates(status);

            CREATE TABLE IF NOT EXISTS checklist_runs (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                template_id TEXT NOT NULL,
                status TEXT NOT NULL,
                target_type TEXT NOT NULL DEFAULT '',
                target_id TEXT NULL,
                assignee_person_id TEXT NULL,
                started_at_utc TEXT NOT NULL,
                completed_at_utc TEXT NULL,
                steps_json TEXT NOT NULL DEFAULT '[]',
                notes TEXT NOT NULL DEFAULT '',
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                CONSTRAINT fk_checklist_runs_incident
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_checklist_runs_template
                    FOREIGN KEY (template_id) REFERENCES checklist_templates(id)
                    ON DELETE RESTRICT,
                CONSTRAINT ck_checklist_runs_version_positive
                    CHECK (version >= 1)
            );

            CREATE INDEX IF NOT EXISTS idx_checklist_runs_incident
                ON checklist_runs(incident_id);

            CREATE INDEX IF NOT EXISTS idx_checklist_runs_template
                ON checklist_runs(template_id);

            CREATE INDEX IF NOT EXISTS idx_checklist_runs_target
                ON checklist_runs(target_type, target_id);

            CREATE INDEX IF NOT EXISTS idx_checklist_runs_status
                ON checklist_runs(status);
            """),
        new(
            "006_audit_event_context",
            """
            ALTER TABLE audit_events
                ADD COLUMN incident_id TEXT NOT NULL DEFAULT '';

            ALTER TABLE audit_events
                ADD COLUMN actor_type TEXT NOT NULL DEFAULT 'user';

            ALTER TABLE audit_events
                ADD COLUMN actor_id TEXT NOT NULL DEFAULT '';

            ALTER TABLE audit_events
                ADD COLUMN target_type TEXT NOT NULL DEFAULT '';

            ALTER TABLE audit_events
                ADD COLUMN target_id TEXT NOT NULL DEFAULT '';

            UPDATE audit_events
            SET
                actor_id = ifnull(actor_user_id, ''),
                target_type = entity_type,
                target_id = entity_id
            WHERE target_type = '';

            CREATE INDEX IF NOT EXISTS idx_audit_events_incident
                ON audit_events(incident_id);

            CREATE INDEX IF NOT EXISTS idx_audit_events_target
                ON audit_events(target_type, target_id);
            """),
        new(
            "007_incident_version",
            """
            ALTER TABLE incidents
                ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
            """),
        new(
            "008_standard_itss_checklist_templates",
            """
            INSERT OR IGNORE INTO checklist_templates (
                id, incident_id, title, template_type, version_label, status,
                scope_type, scope_id, steps_json, created_at_utc, updated_at_utc, version)
            VALUES
            (
                'standard-initial-itss-arrival', NULL, 'Initial ITSS Arrival', 'setup.initial_arrival', '1.0', 'published',
                'global', NULL,
                '[{"id":"arrival-briefing","title":"Check in with COML or incident supervisor","expectedResult":"ITSS arrival is known and assignment is confirmed.","troubleshootingHint":"If no supervisor is available, record the contact attempt and continue with site assessment.","requiredNote":true},{"id":"arrival-safety","title":"Confirm camp safety, access, and radio/contact procedure","expectedResult":"Safety constraints and escalation contact are recorded.","troubleshootingHint":"Do not begin physical network work until access and safety limits are clear.","requiredNote":true},{"id":"arrival-network-walk","title":"Walk ICP or camp network area and identify service points","expectedResult":"Primary network, power, WAN, and work areas are identified.","troubleshootingHint":"Photograph or note unknown demarcation points for later verification.","requiredPhoto":true},{"id":"arrival-open-tasks","title":"Record blockers and immediate follow-up tasks","expectedResult":"Known blockers are captured before setup work begins.","troubleshootingHint":"Use blocker notes when a dependency is outside ITSS control.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-icp-camp-network-setup', NULL, 'ICP / Camp Network Setup', 'setup.network', '1.0', 'published',
                'global', NULL,
                '[{"id":"network-layout","title":"Confirm router, switch, AP, printer, and user work areas","expectedResult":"Network layout is matched to the camp or ICP plan.","troubleshootingHint":"Separate public, staff, and infrastructure paths before connecting users.","requiredNote":true},{"id":"network-power","title":"Verify stable power and UPS for network core","expectedResult":"Core devices are on protected power where available.","troubleshootingHint":"Unstable power causes false network failures and equipment resets.","requiredNote":true},{"id":"network-connect-core","title":"Connect and label core network devices","expectedResult":"Core router, switch, and uplinks are connected and labeled.","troubleshootingHint":"Label both ends of any long cable path.","requiredPhoto":true},{"id":"network-smoke-test","title":"Run a basic LAN and WAN smoke test","expectedResult":"A client can reach local services and upstream internet when available.","troubleshootingHint":"Test from a user port, not only from the router.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-starlink-satellite-setup', NULL, 'Starlink / Satellite Setup', 'setup.wan', '1.0', 'published',
                'global', NULL,
                '[{"id":"satellite-location","title":"Choose dish or terminal location with clear sky view","expectedResult":"Terminal has a safe mount point and acceptable sky visibility.","troubleshootingHint":"Trees, vehicles, and metal structures can cause intermittent loss.","requiredPhoto":true},{"id":"satellite-cable","title":"Route and protect cable path","expectedResult":"Cable path is safe, labeled, and protected from traffic.","troubleshootingHint":"Avoid pinch points and trip hazards.","requiredPhoto":true},{"id":"satellite-online","title":"Verify satellite online status and upstream handoff","expectedResult":"WAN status is known and handoff device is documented.","troubleshootingHint":"If online status is unstable, record obstruction and power notes.","requiredNote":true},{"id":"satellite-failover","title":"Document failover or backup WAN status","expectedResult":"Backup path availability is recorded.","troubleshootingHint":"If no backup exists, mark blocker for command awareness.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-router-setup', NULL, 'Router Setup', 'setup.router', '1.0', 'published',
                'global', NULL,
                '[{"id":"router-identity","title":"Confirm router hostname, asset tag, and management access","expectedResult":"Router identity and access path are recorded.","troubleshootingHint":"Use a local console or trusted management port if LAN access is unavailable.","requiredNote":true},{"id":"router-wan","title":"Configure or verify WAN interface","expectedResult":"WAN interface status and addressing are documented.","troubleshootingHint":"Check link lights and upstream device status before changing config.","requiredNote":true},{"id":"router-lan","title":"Configure or verify LAN networks and DHCP/DNS handoff","expectedResult":"LAN clients receive expected addressing and name resolution.","troubleshootingHint":"Capture observed client IP, gateway, and DNS if validation fails.","requiredNote":true},{"id":"router-save","title":"Save configuration and record backup location","expectedResult":"Router configuration is saved or export path is noted.","troubleshootingHint":"If export is not possible, record exact reason.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-switch-setup', NULL, 'Switch Setup', 'setup.switch', '1.0', 'published',
                'global', NULL,
                '[{"id":"switch-identity","title":"Confirm switch identity, location, and uplink","expectedResult":"Switch record has location and uplink details.","troubleshootingHint":"Trace cable path before assuming topology.","requiredNote":true},{"id":"switch-ports","title":"Label critical ports and cable paths","expectedResult":"Uplink, AP, printer, and workgroup ports are labeled.","troubleshootingHint":"Photograph patching before major changes.","requiredPhoto":true},{"id":"switch-vlan","title":"Verify VLAN or port profile assignment","expectedResult":"Ports match intended network function.","troubleshootingHint":"Wrong VLAN assignment often presents as DHCP failure.","requiredNote":true},{"id":"switch-health","title":"Check link status for connected devices","expectedResult":"Unexpected down or degraded ports are recorded.","troubleshootingHint":"Swap cable or port before replacing endpoint device.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-wifi-access-point-setup', NULL, 'Wi-Fi Access Point Setup', 'setup.wireless', '1.0', 'published',
                'global', NULL,
                '[{"id":"wifi-placement","title":"Place AP for coverage and safe cable routing","expectedResult":"AP placement supports expected work areas.","troubleshootingHint":"Avoid placing AP behind metal walls, appliances, or radio equipment.","requiredPhoto":true},{"id":"wifi-uplink","title":"Verify AP uplink and power","expectedResult":"AP has link, power, and expected network assignment.","troubleshootingHint":"Check PoE budget and switch port profile if AP is offline.","requiredNote":true},{"id":"wifi-ssid","title":"Verify SSID, security, and client join","expectedResult":"A field client can join and reach required resources.","troubleshootingHint":"Record error messages from client devices when join fails.","requiredNote":true},{"id":"wifi-coverage","title":"Walk coverage area and record weak spots","expectedResult":"Weak coverage or interference areas are documented.","troubleshootingHint":"Do not solve by adding APs until channel/interference is understood.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-printer-setup', NULL, 'Printer Setup', 'setup.printer', '1.0', 'published',
                'global', NULL,
                '[{"id":"printer-location","title":"Confirm printer location, power, and network path","expectedResult":"Printer is placed and connected safely.","troubleshootingHint":"Avoid sharing circuits with unstable high-load equipment.","requiredNote":true},{"id":"printer-network","title":"Verify printer addressing and hostname","expectedResult":"Printer IP or hostname is recorded.","troubleshootingHint":"Reserve or document the address to avoid duplicate conflicts.","requiredNote":true},{"id":"printer-test","title":"Print a test page from a user workstation","expectedResult":"At least one user workstation can print successfully.","troubleshootingHint":"If test fails, verify driver, queue, firewall, and subnet path.","requiredNote":true},{"id":"printer-supplies","title":"Record toner, paper, and support notes","expectedResult":"Supply state and known limitations are documented.","troubleshootingHint":"Supply issues should be visible before operational period starts.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-user-workstation-setup', NULL, 'User Workstation Setup', 'setup.workstation', '1.0', 'published',
                'global', NULL,
                '[{"id":"workstation-identity","title":"Record workstation user, asset, and location","expectedResult":"Workstation assignment is traceable.","troubleshootingHint":"Use role or function if user name is not available.","requiredNote":true},{"id":"workstation-network","title":"Verify wired or Wi-Fi connectivity","expectedResult":"Workstation reaches required local and internet resources.","troubleshootingHint":"Capture IP, gateway, and DNS details if connectivity fails.","requiredNote":true},{"id":"workstation-printer","title":"Verify print or shared service access","expectedResult":"User can reach assigned shared resources.","troubleshootingHint":"Separate network path problems from application or permission problems.","requiredNote":true},{"id":"workstation-handoff","title":"Confirm user handoff and known limitations","expectedResult":"User accepts workstation or limitations are recorded.","troubleshootingHint":"Record unresolved blockers before leaving the work area.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-account-access-request', NULL, 'Account / Access Request Handling', 'support.access', '1.0', 'published',
                'global', NULL,
                '[{"id":"access-requester","title":"Confirm requester identity, role, and required access","expectedResult":"Request has enough context for approval.","troubleshootingHint":"Do not grant access based only on verbal relay when approval is unclear.","requiredNote":true},{"id":"access-approval","title":"Record approval source or escalation path","expectedResult":"Approval path is documented.","troubleshootingHint":"If approval is delayed, mark blocker and follow-up owner.","requiredNote":true},{"id":"access-action","title":"Complete access action or document handoff","expectedResult":"Request outcome is recorded.","troubleshootingHint":"Separate account creation, password reset, and application permission issues.","requiredNote":true},{"id":"access-verify","title":"Verify user can sign in or use assigned resource","expectedResult":"User confirms access works or blocker is documented.","troubleshootingHint":"Capture exact error text when verification fails.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-daily-network-health-check', NULL, 'Daily Network Health Check', 'daily_check.network', '1.0', 'published',
                'global', NULL,
                '[{"id":"daily-wan","title":"Check WAN and backup WAN status","expectedResult":"WAN state is recorded for operational period.","troubleshootingHint":"Compare symptoms against upstream device and satellite status.","requiredNote":true},{"id":"daily-core","title":"Check router, switch, AP, and printer status","expectedResult":"Critical devices are up or exceptions are logged.","troubleshootingHint":"Prioritize command post and communications paths first.","requiredNote":true},{"id":"daily-user-symptoms","title":"Record user-reported network issues","expectedResult":"Open issues have location and impact details.","troubleshootingHint":"Group repeated reports by area, SSID, or switch path.","requiredNote":true},{"id":"daily-summary","title":"Summarize health check and follow-up work","expectedResult":"Daily health state is ready for handoff.","troubleshootingHint":"Mark blockers if dependency is outside ITSS control.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-daily-backup-export-check', NULL, 'Daily Backup / Export Check', 'daily_check.backup', '1.0', 'published',
                'global', NULL,
                '[{"id":"backup-location","title":"Confirm backup destination is available","expectedResult":"Local backup/export destination is reachable.","troubleshootingHint":"Use removable media or local server storage when internet is unavailable.","requiredNote":true},{"id":"backup-run","title":"Run or verify incident backup/export","expectedResult":"Backup or export result is recorded.","troubleshootingHint":"If export fails, capture exact error and free space state.","requiredNote":true},{"id":"backup-verify","title":"Verify backup file exists and has expected size","expectedResult":"Backup file is present and not empty.","troubleshootingHint":"Do not assume success from command completion alone.","requiredNote":true},{"id":"backup-handoff","title":"Record handoff or storage location","expectedResult":"Next ITSS can find the latest backup.","troubleshootingHint":"Do not store only on a single laptop when avoidable.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-link-outage-troubleshooting', NULL, 'Link Outage Troubleshooting', 'troubleshooting.link_outage', '1.0', 'published',
                'global', NULL,
                '[{"id":"link-scope","title":"Identify affected users, devices, and path","expectedResult":"Outage scope is known.","troubleshootingHint":"Separate one endpoint failure from shared path failure.","requiredNote":true},{"id":"link-physical","title":"Check power, link lights, cable path, and labels","expectedResult":"Physical state is documented.","troubleshootingHint":"Photograph questionable cable paths before changing them.","requiredPhoto":true},{"id":"link-logical","title":"Check addressing, VLAN, route, and service reachability","expectedResult":"Logical fault domain is narrowed.","troubleshootingHint":"Use gateway, DNS, and upstream tests in order.","requiredNote":true},{"id":"link-resolution","title":"Record resolution, workaround, or escalation","expectedResult":"Incident record includes current state and next action.","troubleshootingHint":"If unresolved, mark blocker and owner.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-slow-network-troubleshooting', NULL, 'Slow Network Troubleshooting', 'troubleshooting.slow_network', '1.0', 'published',
                'global', NULL,
                '[{"id":"slow-scope","title":"Identify affected area, SSID, switch, or service","expectedResult":"Slow network scope is recorded.","troubleshootingHint":"Avoid treating one slow workstation as a camp-wide issue.","requiredNote":true},{"id":"slow-wan-lan","title":"Compare LAN and WAN performance symptoms","expectedResult":"LAN or WAN side is suspected with evidence.","troubleshootingHint":"Test local resource access before blaming upstream internet.","requiredNote":true},{"id":"slow-load","title":"Check user load, streaming, updates, and large transfers","expectedResult":"High-use sources are identified or ruled out.","troubleshootingHint":"Look for background updates or unmanaged devices.","requiredNote":true},{"id":"slow-action","title":"Record action taken and re-test result","expectedResult":"Before and after state is documented.","troubleshootingHint":"If no improvement, escalate with measured symptoms.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-no-internet-troubleshooting', NULL, 'No Internet Troubleshooting', 'troubleshooting.no_internet', '1.0', 'published',
                'global', NULL,
                '[{"id":"internet-scope","title":"Confirm whether outage is one user, one area, or all users","expectedResult":"Internet outage scope is recorded.","troubleshootingHint":"Check a known-good wired client before changing WAN settings.","requiredNote":true},{"id":"internet-upstream","title":"Check upstream WAN or satellite status","expectedResult":"Upstream state is known.","troubleshootingHint":"Power-cycle only after recording current indicators and status.","requiredNote":true},{"id":"internet-local","title":"Check local gateway, DNS, DHCP, and routing","expectedResult":"Local service state is known.","troubleshootingHint":"DNS failure can look like full internet outage.","requiredNote":true},{"id":"internet-resolution","title":"Record fix, workaround, or escalation","expectedResult":"Current internet state and next owner are documented.","troubleshootingHint":"If upstream vendor issue, record ticket/contact details.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-radio-cache-coml-notes', NULL, 'Radio Cache / COML Coordination Notes', 'coordination.coml', '1.0', 'published',
                'global', NULL,
                '[{"id":"coml-contact","title":"Confirm COML or radio cache contact and availability","expectedResult":"Coordination contact is recorded.","troubleshootingHint":"Use role and location if a specific person is not assigned.","requiredNote":true},{"id":"coml-needs","title":"Capture network support needs for radio or comms work","expectedResult":"COML-related IT needs are documented.","troubleshootingHint":"Separate radio programming issues from network/IT service issues.","requiredNote":true},{"id":"coml-dependencies","title":"Record dependencies, cables, power, or network handoff details","expectedResult":"Shared dependency state is visible to ITSS and COML.","troubleshootingHint":"Label any shared paths or ports.","requiredPhoto":true},{"id":"coml-followup","title":"Record follow-up owner and operational period need","expectedResult":"Coordination work has a clear next action.","troubleshootingHint":"Mark blocker if the action waits on COML or logistics.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-documentation-handoff', NULL, 'Documentation Handoff', 'handoff.documentation', '1.0', 'published',
                'global', NULL,
                '[{"id":"handoff-assets","title":"Review asset, device, network, and link records","expectedResult":"Key records are current before handoff.","troubleshootingHint":"Prioritize operationally important gaps first.","requiredNote":true},{"id":"handoff-open-items","title":"Record open issues, blockers, and next actions","expectedResult":"Incoming ITSS can continue work without verbal-only context.","troubleshootingHint":"Every blocker should have owner or escalation path.","requiredNote":true},{"id":"handoff-exports","title":"Confirm reports, exports, or backup bundle location","expectedResult":"Handoff package location is recorded.","troubleshootingHint":"Verify the file exists before reporting handoff complete.","requiredNote":true},{"id":"handoff-brief","title":"Complete handoff briefing or written substitute","expectedResult":"Shift or demob handoff is complete.","troubleshootingHint":"If no receiver is present, note where the handoff package was left.","requiredNote":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            ),
            (
                'standard-demobilization-checklist', NULL, 'Demobilization Checklist', 'closeout.demobilization', '1.0', 'published',
                'global', NULL,
                '[{"id":"demob-inventory","title":"Verify equipment inventory, missing items, and return path","expectedResult":"Equipment disposition is recorded.","troubleshootingHint":"Record serial or asset identifiers for disputed items.","requiredNote":true},{"id":"demob-network","title":"Document network teardown plan and retained services","expectedResult":"Teardown sequence and exceptions are known.","troubleshootingHint":"Confirm command staff no longer depends on service before disconnecting.","requiredNote":true},{"id":"demob-data","title":"Export final incident bundle and backup","expectedResult":"Final records are preserved for handoff.","troubleshootingHint":"Verify export file before shutting down the server.","requiredNote":true},{"id":"demob-handoff","title":"Complete final documentation and equipment handoff","expectedResult":"Closeout state is recorded and transferable.","troubleshootingHint":"Use photos for packed kits or unusual equipment condition.","requiredPhoto":true}]',
                strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'), 1
            );
            """),
        new(
            "009_checklist_template_metadata",
            """
            ALTER TABLE checklist_templates
                ADD COLUMN purpose TEXT NOT NULL DEFAULT '';

            ALTER TABLE checklist_templates
                ADD COLUMN role_owner TEXT NOT NULL DEFAULT '';

            ALTER TABLE checklist_templates
                ADD COLUMN required_tools TEXT NOT NULL DEFAULT '';

            ALTER TABLE checklist_templates
                ADD COLUMN safety_notes TEXT NOT NULL DEFAULT '';

            ALTER TABLE checklist_templates
                ADD COLUMN prerequisites TEXT NOT NULL DEFAULT '';

            ALTER TABLE checklist_templates
                ADD COLUMN completion_criteria TEXT NOT NULL DEFAULT '';

            UPDATE checklist_templates
            SET
                purpose = CASE
                    WHEN template_type LIKE 'setup.%'
                        THEN 'Guide initial field setup work so equipment, access, power, network paths, and user handoff are documented consistently.'
                    WHEN template_type LIKE 'daily_check.%'
                        THEN 'Guide recurring operational-period checks so ITSS can spot service issues early and leave a usable handoff.'
                    WHEN template_type LIKE 'troubleshooting.%'
                        THEN 'Guide field troubleshooting so symptoms, scope, physical checks, logical checks, actions, and escalation are captured.'
                    WHEN template_type LIKE 'coordination.%'
                        THEN 'Guide coordination with communications and logistics partners so shared dependencies and follow-up owners are visible.'
                    WHEN template_type LIKE 'handoff.%'
                        THEN 'Guide shift or role handoff so incoming ITSS can continue work from documented facts instead of verbal-only context.'
                    WHEN template_type LIKE 'closeout.%'
                        THEN 'Guide demobilization so equipment, services, data exports, and final transfer status are preserved.'
                    ELSE 'Provide a repeatable ITSS field checklist that can be completed offline and synced back to the incident server.'
                END,
                role_owner = CASE
                    WHEN template_type LIKE 'coordination.%'
                        THEN 'Assigned ITSS with COML/COMT coordination.'
                    WHEN template_type LIKE 'closeout.%'
                        THEN 'Assigned ITSS lead or demobilization ITSS.'
                    WHEN template_type LIKE 'handoff.%'
                        THEN 'Outgoing ITSS with incoming ITSS or supervisor acknowledgement.'
                    ELSE 'Assigned ITSS; coordinate with ITSS lead, COML/COMT, and logistics as needed.'
                END,
                required_tools = CASE
                    WHEN template_type LIKE 'setup.wan'
                        THEN 'FireIT Mobile, satellite/vendor status app if available, labels, camera, cable protection, power tester, and basic hand tools.'
                    WHEN template_type LIKE 'setup.router'
                        THEN 'FireIT Mobile, console or management access, patch cables, labels, known-good client, and configuration backup location.'
                    WHEN template_type LIKE 'setup.switch'
                        THEN 'FireIT Mobile, cable labels, patch cables, camera, known-good endpoint, and switch management access when available.'
                    WHEN template_type LIKE 'setup.wireless'
                        THEN 'FireIT Mobile, mounting supplies, labels, known-good Wi-Fi client, camera, and AP management access when available.'
                    WHEN template_type LIKE 'setup.printer'
                        THEN 'FireIT Mobile, printer supplies, known-good workstation, labels, network details, and local driver/package source when available.'
                    WHEN template_type LIKE 'setup.workstation'
                        THEN 'FireIT Mobile, workstation asset details, user assignment notes, network credentials or local access process, and printer/service test path.'
                    WHEN template_type LIKE 'daily_check.backup'
                        THEN 'FireIT Mobile, incident server access, backup/export destination, removable media if used, and file-size verification.'
                    ELSE 'FireIT Mobile, incident server access, labels or asset identifiers, camera, notes, and equipment-specific field tools.'
                END,
                safety_notes = CASE
                    WHEN template_type LIKE 'setup.%'
                        THEN 'Confirm access permission before touching equipment; avoid unsafe power, trip hazards, heat, vehicle paths, and unstable mounting locations.'
                    WHEN template_type LIKE 'troubleshooting.%'
                        THEN 'Record observed state before changing equipment; do not disturb shared services without command/communications awareness.'
                    WHEN template_type LIKE 'closeout.%'
                        THEN 'Do not disconnect active services until the supported function confirms release; use safe lifting, packing, and cable removal practices.'
                    ELSE 'Follow incident safety rules, respect restricted areas, document hazards, and escalate unsafe conditions before continuing.'
                END,
                prerequisites = CASE
                    WHEN template_type LIKE 'daily_check.%'
                        THEN 'Current operational period is known; incident server or cached mobile app is available; prior blockers and handoff notes have been reviewed.'
                    WHEN template_type LIKE 'troubleshooting.%'
                        THEN 'Affected user, service, device, area, or link is identified; safety/access limits are known; current symptoms are captured before changes.'
                    WHEN template_type LIKE 'handoff.%'
                        THEN 'Current records, open blockers, generated exports, and receiving party or storage location are known.'
                    WHEN template_type LIKE 'closeout.%'
                        THEN 'Demobilization direction is confirmed; retained service needs are known; export/backup destination is available.'
                    ELSE 'Assignment is confirmed; physical access is approved; incident server or cached mobile app is available; required equipment details are known or discoverable.'
                END,
                completion_criteria = CASE
                    WHEN template_type LIKE 'troubleshooting.%'
                        THEN 'Scope, checks, action taken, result, blocker or escalation owner, and follow-up status are recorded; required notes/photos are attached or explicitly blocked.'
                    WHEN template_type LIKE 'daily_check.%'
                        THEN 'Current state, exceptions, blockers, and follow-up items are recorded; checklist run is synced or queued for sync.'
                    WHEN template_type LIKE 'handoff.%'
                        THEN 'Records are reviewed, open work is documented, exports or backup locations are recorded, and receiving party or substitute handoff path is captured.'
                    WHEN template_type LIKE 'closeout.%'
                        THEN 'Inventory disposition, teardown status, final export/backup, and equipment or record handoff are documented.'
                    ELSE 'All checklist steps are completed or blocked with notes; required photos/notes are captured; the run is synced or queued for sync.'
                END,
                updated_at_utc = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
                version = version + 1
            WHERE id LIKE 'standard-%';
            """),
        new(
            "010_location_store",
            """
            CREATE TABLE IF NOT EXISTS locations (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                camp_id TEXT NOT NULL,
                name TEXT NOT NULL,
                location_type TEXT NOT NULL,
                status TEXT NOT NULL,
                parent_location_id TEXT NULL,
                map_x REAL NULL,
                map_y REAL NULL,
                map_width REAL NULL,
                map_height REAL NULL,
                latitude REAL NULL,
                longitude REAL NULL,
                elevation_ft REAL NULL,
                address_or_directions TEXT NOT NULL DEFAULT '',
                capacity INTEGER NULL,
                access_notes TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                record_state TEXT NOT NULL DEFAULT 'active',
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                CONSTRAINT fk_locations_incident
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_locations_camp
                    FOREIGN KEY (camp_id) REFERENCES camps(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_locations_parent
                    FOREIGN KEY (parent_location_id) REFERENCES locations(id)
                    ON DELETE SET NULL,
                CONSTRAINT ck_locations_name_not_blank
                    CHECK (length(trim(name)) > 0),
                CONSTRAINT ck_locations_type_not_blank
                    CHECK (length(trim(location_type)) > 0),
                CONSTRAINT ck_locations_status_not_blank
                    CHECK (length(trim(status)) > 0),
                CONSTRAINT ck_locations_map_position_complete
                    CHECK ((map_x IS NULL AND map_y IS NULL)
                        OR (map_x IS NOT NULL AND map_y IS NOT NULL)),
                CONSTRAINT ck_locations_map_size_positive
                    CHECK ((map_width IS NULL OR map_width > 0)
                        AND (map_height IS NULL OR map_height > 0)),
                CONSTRAINT ck_locations_coordinates_complete
                    CHECK ((latitude IS NULL AND longitude IS NULL)
                        OR (latitude IS NOT NULL AND longitude IS NOT NULL)),
                CONSTRAINT ck_locations_capacity_not_negative
                    CHECK (capacity IS NULL OR capacity >= 0),
                CONSTRAINT ck_locations_version_positive
                    CHECK (version >= 1)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_locations_camp_name
                ON locations(camp_id, name COLLATE NOCASE);

            CREATE INDEX IF NOT EXISTS idx_locations_incident
                ON locations(incident_id);

            CREATE INDEX IF NOT EXISTS idx_locations_camp
                ON locations(camp_id);

            CREATE INDEX IF NOT EXISTS idx_locations_status
                ON locations(status, record_state);
            """),
    ];

    private readonly string _connectionString;

    private IncidentDatabase(string databasePath)
    {
        Batteries_V2.Init();

        DatabasePath = databasePath;
        _connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = DatabasePath,
        }.ToString();
    }

    public string DatabasePath { get; }

    public static IncidentDatabase Create(IConfiguration configuration)
    {
        var configuredPath = configuration[DatabasePathConfigKey];
        var databasePath = string.IsNullOrWhiteSpace(configuredPath)
            ? Path.Combine(AppContext.BaseDirectory, "data", DefaultDatabaseFileName)
            : configuredPath;

        if (!Path.IsPathRooted(databasePath))
        {
            databasePath = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, databasePath));
        }

        return new IncidentDatabase(databasePath);
    }

    public async Task MigrateAsync(CancellationToken cancellationToken = default)
    {
        var directory = Path.GetDirectoryName(DatabasePath);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }

        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await ExecuteNonQueryAsync(connection, "PRAGMA foreign_keys = ON;", cancellationToken);
        await ExecuteNonQueryAsync(connection, "PRAGMA journal_mode = WAL;", cancellationToken);
        await ExecuteNonQueryAsync(connection, CreateMigrationTableSql, cancellationToken);

        foreach (var migration in Migrations)
        {
            if (await MigrationHasBeenAppliedAsync(connection, migration.Id, cancellationToken))
            {
                continue;
            }

            await using var transaction = connection.BeginTransaction();
            await ExecuteNonQueryAsync(connection, migration.Sql, transaction, cancellationToken);
            await RecordMigrationAsync(connection, migration.Id, transaction, cancellationToken);
            await transaction.CommitAsync(cancellationToken);
        }
    }

    public async Task<DatabaseHealth> CheckHealthAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        var appliedMigrations = await ReadAppliedMigrationsAsync(connection, cancellationToken);
        return new DatabaseHealth("Connected", appliedMigrations);
    }

    public async Task<IncidentSummary?> GetIncidentSummaryAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT
                id,
                incident_number,
                name,
                agency,
                operational_period_start_utc,
                operational_period_end_utc,
                created_at_utc,
                updated_at_utc,
                version
            FROM incidents
            ORDER BY created_at_utc ASC
            LIMIT 1;
            """;

        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            return null;
        }

        return new IncidentSummary(
            Id: reader.GetString(0),
            IncidentNumber: reader.GetString(1),
            Name: reader.GetString(2),
            Agency: reader.GetString(3),
            OperationalPeriodStartUtc: ReadOptionalDateTimeOffset(reader, 4),
            OperationalPeriodEndUtc: ReadOptionalDateTimeOffset(reader, 5),
            CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 6),
            UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 7),
            Version: reader.GetInt32(8));
    }

    public async Task<DatabaseSaveResult<IncidentSummary>> CreateIncidentSummaryAsync(
        IncidentSummaryRequest request,
        string actorId,
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        if (await IncidentExistsAsync(connection, transaction, cancellationToken))
        {
            return DatabaseSaveResult<IncidentSummary>.Duplicate();
        }

        var now = DateTimeOffset.UtcNow;
        var incidentId = string.IsNullOrWhiteSpace(request.Id)
            ? Guid.NewGuid().ToString()
            : request.Id;

        await using (var command = connection.CreateCommand())
        {
            command.Transaction = transaction;
            command.CommandText =
                """
                INSERT INTO incidents (
                    id,
                    incident_number,
                    name,
                    agency,
                    operational_period_start_utc,
                    operational_period_end_utc,
                    created_at_utc,
                    updated_at_utc)
                VALUES (
                    $id,
                    $incidentNumber,
                    $name,
                    $agency,
                    $operationalPeriodStartUtc,
                    $operationalPeriodEndUtc,
                    $createdAtUtc,
                    $updatedAtUtc);
                """;
            AddIncidentSummaryParameters(command, incidentId, request, now);

            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        await RecordAuditEventAsync(
            connection,
            transaction,
            incidentId,
            actorId,
            "create",
            "incident",
            incidentId,
            $"Created incident summary '{request.Name}'.",
            cancellationToken);

        await transaction.CommitAsync(cancellationToken);

        var incidentSummary = await GetIncidentSummaryAsync(cancellationToken);
        return incidentSummary is null
            ? DatabaseSaveResult<IncidentSummary>.NotFound()
            : DatabaseSaveResult<IncidentSummary>.Saved(incidentSummary);
    }

    public async Task<DatabaseSaveResult<IncidentSummary>> UpdateIncidentSummaryAsync(
        IncidentSummaryRequest request,
        string actorId,
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        var existingIncident = await ReadCurrentIncidentRecordAsync(connection, transaction, cancellationToken);
        if (existingIncident is null)
        {
            return DatabaseSaveResult<IncidentSummary>.NotFound();
        }

        if (request.ExpectedVersion.HasValue && request.ExpectedVersion.Value != existingIncident.Version)
        {
            return DatabaseSaveResult<IncidentSummary>.Conflict(existingIncident.Version);
        }

        var now = DateTimeOffset.UtcNow;
        await using (var command = connection.CreateCommand())
        {
            command.Transaction = transaction;
            command.CommandText =
                """
                UPDATE incidents
                SET
                    incident_number = $incidentNumber,
                    name = $name,
                    agency = $agency,
                    operational_period_start_utc = $operationalPeriodStartUtc,
                    operational_period_end_utc = $operationalPeriodEndUtc,
                    updated_at_utc = $updatedAtUtc,
                    version = version + 1
                WHERE id = $id;
                """;
            AddIncidentSummaryParameters(command, existingIncident.Id, request, now);

            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        await RecordAuditEventAsync(
            connection,
            transaction,
            existingIncident.Id,
            actorId,
            "update",
            "incident",
            existingIncident.Id,
            $"Updated incident summary '{request.Name}'.",
            cancellationToken);

        await transaction.CommitAsync(cancellationToken);

        var incidentSummary = await GetIncidentSummaryAsync(cancellationToken);
        return incidentSummary is null
            ? DatabaseSaveResult<IncidentSummary>.NotFound()
            : DatabaseSaveResult<IncidentSummary>.Saved(incidentSummary);
    }

    public async Task<DatabaseSaveResult<EntityChangeSummary>> DeleteIncidentSummaryAsync(
        string actorId,
        int? expectedVersion,
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        var existingIncident = await ReadCurrentIncidentRecordAsync(connection, transaction, cancellationToken);
        if (existingIncident is null)
        {
            return DatabaseSaveResult<EntityChangeSummary>.NotFound();
        }

        if (expectedVersion.HasValue && expectedVersion.Value != existingIncident.Version)
        {
            return DatabaseSaveResult<EntityChangeSummary>.Conflict(existingIncident.Version);
        }

        await RecordAuditEventAsync(
            connection,
            transaction,
            existingIncident.Id,
            actorId,
            "delete",
            "incident",
            existingIncident.Id,
            "Deleted incident summary.",
            cancellationToken);

        await using (var command = connection.CreateCommand())
        {
            command.Transaction = transaction;
            command.CommandText = "DELETE FROM incidents WHERE id = $id;";
            command.Parameters.AddWithValue("$id", existingIncident.Id);

            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        await transaction.CommitAsync(cancellationToken);
        return DatabaseSaveResult<EntityChangeSummary>.Saved(
            new EntityChangeSummary(
                EntityType: "incident",
                EntityId: existingIncident.Id,
                IncidentId: existingIncident.Id,
                ChangeType: "delete",
                Status: "deleted",
                Version: existingIncident.Version,
                UpdatedAtUtc: DateTimeOffset.UtcNow));
    }

    public async Task<IReadOnlyList<AuditEventSummary>> ListAuditEventsAsync(
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                actor_type,
                actor_id,
                action,
                target_type,
                target_id,
                occurred_at_utc,
                summary
            FROM audit_events
            ORDER BY occurred_at_utc ASC, id ASC;
            """;

        var auditEvents = new List<AuditEventSummary>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            auditEvents.Add(new AuditEventSummary(
                Id: reader.GetString(0),
                IncidentId: reader.GetString(1),
                ActorType: reader.GetString(2),
                ActorId: reader.GetString(3),
                Action: reader.GetString(4),
                TargetType: reader.GetString(5),
                TargetId: reader.GetString(6),
                OccurredAtUtc: ReadRequiredDateTimeOffset(reader, 7),
                Summary: reader.GetString(8)));
        }

        return auditEvents;
    }

    public async Task<IReadOnlyList<CampSummary>> ListCampsAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                name,
                camp_type,
                status,
                primary_location_id,
                address_or_directions,
                latitude,
                longitude,
                capacity,
                it_contact_person_id,
                notes,
                record_state,
                created_at_utc,
                updated_at_utc,
                version
            FROM camps
            ORDER BY name COLLATE NOCASE ASC, created_at_utc ASC;
            """;

        var camps = new List<CampSummary>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            camps.Add(new CampSummary(
                Id: reader.GetString(0),
                IncidentId: reader.GetString(1),
                Name: reader.GetString(2),
                CampType: reader.GetString(3),
                Status: reader.GetString(4),
                PrimaryLocationId: ReadOptionalString(reader, 5),
                AddressOrDirections: reader.GetString(6),
                Latitude: ReadOptionalDouble(reader, 7),
                Longitude: ReadOptionalDouble(reader, 8),
                Capacity: ReadOptionalInt32(reader, 9),
                ItContactPersonId: ReadOptionalString(reader, 10),
                Notes: reader.GetString(11),
                RecordState: reader.GetString(12),
                CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 13),
                UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 14),
                Version: reader.GetInt32(15)));
        }

        return camps;
    }

    public async Task<IReadOnlyList<DeviceSummary>> ListDevicesAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                hostname,
                device_type,
                status,
                location_id,
                manufacturer,
                model,
                serial_number,
                primary_ip_assignment_id,
                mac_addresses_json,
                asset_id,
                notes,
                created_at_utc,
                updated_at_utc,
                version
            FROM devices
            ORDER BY hostname COLLATE NOCASE ASC, created_at_utc ASC;
            """;

        var devices = new List<DeviceSummary>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            devices.Add(new DeviceSummary(
                Id: reader.GetString(0),
                IncidentId: reader.GetString(1),
                Hostname: reader.GetString(2),
                DeviceType: reader.GetString(3),
                Status: reader.GetString(4),
                LocationId: ReadOptionalString(reader, 5),
                Manufacturer: reader.GetString(6),
                Model: reader.GetString(7),
                SerialNumber: reader.GetString(8),
                PrimaryIpAssignmentId: ReadOptionalString(reader, 9),
                MacAddresses: ReadStringListJson(reader, 10),
                AssetId: ReadOptionalString(reader, 11),
                Notes: reader.GetString(12),
                CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 13),
                UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 14),
                Version: reader.GetInt32(15)));
        }

        return devices;
    }

    public async Task<IReadOnlyList<LocationSummary>> ListLocationsAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                camp_id,
                name,
                location_type,
                status,
                parent_location_id,
                map_x,
                map_y,
                map_width,
                map_height,
                latitude,
                longitude,
                elevation_ft,
                address_or_directions,
                capacity,
                access_notes,
                notes,
                record_state,
                created_at_utc,
                updated_at_utc,
                version
            FROM locations
            ORDER BY camp_id ASC, name COLLATE NOCASE ASC, created_at_utc ASC;
            """;

        var locations = new List<LocationSummary>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            locations.Add(new LocationSummary(
                Id: reader.GetString(0),
                IncidentId: reader.GetString(1),
                CampId: reader.GetString(2),
                Name: reader.GetString(3),
                LocationType: reader.GetString(4),
                Status: reader.GetString(5),
                ParentLocationId: ReadOptionalString(reader, 6),
                MapX: ReadOptionalDouble(reader, 7),
                MapY: ReadOptionalDouble(reader, 8),
                MapWidth: ReadOptionalDouble(reader, 9),
                MapHeight: ReadOptionalDouble(reader, 10),
                Latitude: ReadOptionalDouble(reader, 11),
                Longitude: ReadOptionalDouble(reader, 12),
                ElevationFt: ReadOptionalDouble(reader, 13),
                AddressOrDirections: reader.GetString(14),
                Capacity: ReadOptionalInt32(reader, 15),
                AccessNotes: reader.GetString(16),
                Notes: reader.GetString(17),
                RecordState: reader.GetString(18),
                CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 19),
                UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 20),
                Version: reader.GetInt32(21)));
        }

        return locations;
    }

    public async Task<IReadOnlyList<NetworkSummary>> ListNetworksAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                camp_id,
                name,
                network_type,
                status,
                description,
                created_at_utc,
                updated_at_utc,
                version
            FROM networks
            ORDER BY name COLLATE NOCASE ASC, created_at_utc ASC;
            """;

        var networks = new List<NetworkSummary>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            networks.Add(new NetworkSummary(
                Id: reader.GetString(0),
                IncidentId: reader.GetString(1),
                CampId: ReadOptionalString(reader, 2),
                Name: reader.GetString(3),
                NetworkType: reader.GetString(4),
                Status: reader.GetString(5),
                Description: reader.GetString(6),
                CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 7),
                UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 8),
                Version: reader.GetInt32(9)));
        }

        return networks;
    }

    public async Task<IReadOnlyList<LinkSummary>> ListLinksAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                network_id,
                link_category,
                link_type,
                status,
                source_device_id,
                destination_device_id,
                source_location_id,
                destination_location_id,
                source_ref,
                destination_ref,
                label,
                length,
                path,
                notes,
                created_at_utc,
                updated_at_utc,
                version
            FROM links
            ORDER BY link_category ASC, label COLLATE NOCASE ASC, created_at_utc ASC;
            """;

        var links = new List<LinkSummary>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            links.Add(new LinkSummary(
                Id: reader.GetString(0),
                IncidentId: reader.GetString(1),
                NetworkId: ReadOptionalString(reader, 2),
                LinkCategory: reader.GetString(3),
                LinkType: reader.GetString(4),
                Status: reader.GetString(5),
                SourceDeviceId: ReadOptionalString(reader, 6),
                DestinationDeviceId: ReadOptionalString(reader, 7),
                SourceLocationId: ReadOptionalString(reader, 8),
                DestinationLocationId: ReadOptionalString(reader, 9),
                SourceRef: reader.GetString(10),
                DestinationRef: reader.GetString(11),
                Label: reader.GetString(12),
                Length: reader.GetString(13),
                Path: reader.GetString(14),
                Notes: reader.GetString(15),
                CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 16),
                UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 17),
                Version: reader.GetInt32(18)));
        }

        return links;
    }

    public async Task<IReadOnlyList<ChecklistTemplateSummary>> ListChecklistTemplatesAsync(
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                title,
                template_type,
                version_label,
                status,
                scope_type,
                scope_id,
                purpose,
                role_owner,
                required_tools,
                safety_notes,
                prerequisites,
                completion_criteria,
                steps_json,
                created_at_utc,
                updated_at_utc,
                version
            FROM checklist_templates
            ORDER BY title COLLATE NOCASE ASC, version_label ASC, created_at_utc ASC;
            """;

        var templates = new List<ChecklistTemplateSummary>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            templates.Add(new ChecklistTemplateSummary(
                Id: reader.GetString(0),
                IncidentId: ReadOptionalString(reader, 1),
                Title: reader.GetString(2),
                TemplateType: reader.GetString(3),
                VersionLabel: reader.GetString(4),
                Status: reader.GetString(5),
                ScopeType: reader.GetString(6),
                ScopeId: ReadOptionalString(reader, 7),
                Purpose: reader.GetString(8),
                RoleOwner: reader.GetString(9),
                RequiredTools: reader.GetString(10),
                SafetyNotes: reader.GetString(11),
                Prerequisites: reader.GetString(12),
                CompletionCriteria: reader.GetString(13),
                Steps: ReadJsonElement(reader, 14),
                CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 15),
                UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 16),
                Version: reader.GetInt32(17)));
        }

        return templates;
    }

    public async Task<IReadOnlyList<ChecklistRunSummary>> ListChecklistRunsAsync(
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);

        await using var command = connection.CreateCommand();
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                template_id,
                status,
                target_type,
                target_id,
                assignee_person_id,
                started_at_utc,
                completed_at_utc,
                steps_json,
                notes,
                created_at_utc,
                updated_at_utc,
                version
            FROM checklist_runs
            ORDER BY started_at_utc DESC, created_at_utc DESC;
            """;

        var runs = new List<ChecklistRunSummary>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            runs.Add(new ChecklistRunSummary(
                Id: reader.GetString(0),
                IncidentId: reader.GetString(1),
                TemplateId: reader.GetString(2),
                Status: reader.GetString(3),
                TargetType: reader.GetString(4),
                TargetId: ReadOptionalString(reader, 5),
                AssigneePersonId: ReadOptionalString(reader, 6),
                StartedAtUtc: ReadRequiredDateTimeOffset(reader, 7),
                CompletedAtUtc: ReadOptionalDateTimeOffset(reader, 8),
                Steps: ReadJsonElement(reader, 9),
                Notes: reader.GetString(10),
                CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 11),
                UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 12),
                Version: reader.GetInt32(13)));
        }

        return runs;
    }

    public async Task<DatabaseSaveResult<ChecklistRunSummary>> CreateChecklistRunAsync(
        ChecklistRunCreateRequest request,
        string actorId,
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        var incidentId = await ReadCurrentIncidentIdAsync(connection, transaction, cancellationToken);
        if (incidentId is null)
        {
            return DatabaseSaveResult<ChecklistRunSummary>.NotFound();
        }

        var template = await ReadChecklistTemplateDraftAsync(
            connection,
            transaction,
            request.TemplateId,
            cancellationToken);
        if (template is null ||
            (template.IncidentId is not null && template.IncidentId != incidentId))
        {
            return DatabaseSaveResult<ChecklistRunSummary>.NotFound();
        }

        var now = DateTimeOffset.UtcNow;
        var id = string.IsNullOrWhiteSpace(request.Id)
            ? Guid.NewGuid().ToString()
            : request.Id.Trim();
        var status = string.IsNullOrWhiteSpace(request.Status)
            ? "in-progress"
            : request.Status.Trim();

        await using (var command = connection.CreateCommand())
        {
            command.Transaction = transaction;
            command.CommandText =
                """
                INSERT INTO checklist_runs (
                    id,
                    incident_id,
                    template_id,
                    status,
                    target_type,
                    target_id,
                    assignee_person_id,
                    started_at_utc,
                    completed_at_utc,
                    steps_json,
                    notes,
                    created_at_utc,
                    updated_at_utc,
                    version)
                VALUES (
                    $id,
                    $incidentId,
                    $templateId,
                    $status,
                    $targetType,
                    $targetId,
                    $assigneePersonId,
                    $startedAtUtc,
                    $completedAtUtc,
                    $stepsJson,
                    $notes,
                    $createdAtUtc,
                    $updatedAtUtc,
                    1);
                """;
            command.Parameters.AddWithValue("$id", id);
            command.Parameters.AddWithValue("$incidentId", incidentId);
            command.Parameters.AddWithValue("$templateId", request.TemplateId.Trim());
            command.Parameters.AddWithValue("$status", status);
            command.Parameters.AddWithValue("$targetType", CleanOrDefault(request.TargetType));
            command.Parameters.AddWithValue("$targetId", ToDbValue(request.TargetId));
            command.Parameters.AddWithValue("$assigneePersonId", ToDbValue(request.AssigneePersonId));
            command.Parameters.AddWithValue("$startedAtUtc", (request.StartedAtUtc ?? now).ToUniversalTime().ToString("O"));
            command.Parameters.AddWithValue("$completedAtUtc", ToDbValue(request.CompletedAtUtc));
            command.Parameters.AddWithValue("$stepsJson", template.StepsJson);
            command.Parameters.AddWithValue("$notes", CleanOrDefault(request.Notes));
            command.Parameters.AddWithValue("$createdAtUtc", now.ToString("O"));
            command.Parameters.AddWithValue("$updatedAtUtc", now.ToString("O"));

            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        await RecordAuditEventAsync(
            connection,
            transaction,
            incidentId,
            actorId,
            "create",
            "checklist-run",
            id,
            $"Started checklist run from template '{template.Title}'.",
            cancellationToken);

        var saved = await ReadChecklistRunAsync(connection, transaction, id, cancellationToken);
        await transaction.CommitAsync(cancellationToken);

        return saved is null
            ? DatabaseSaveResult<ChecklistRunSummary>.NotFound()
            : DatabaseSaveResult<ChecklistRunSummary>.Saved(saved);
    }

    public async Task<DatabaseSaveResult<ChecklistRunSummary>> UpdateChecklistRunProgressAsync(
        string id,
        ChecklistRunProgressRequest request,
        string actorId,
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        var existingRecord = await ReadTrackedRecordAsync(
            connection,
            transaction,
            "checklist_runs",
            id,
            cancellationToken);
        if (existingRecord is null)
        {
            return DatabaseSaveResult<ChecklistRunSummary>.NotFound();
        }

        if (request.ExpectedVersion.HasValue && request.ExpectedVersion.Value != existingRecord.Version)
        {
            return DatabaseSaveResult<ChecklistRunSummary>.Conflict(existingRecord.Version);
        }

        var now = DateTimeOffset.UtcNow;
        var status = string.IsNullOrWhiteSpace(request.Status)
            ? "in-progress"
            : request.Status.Trim();
        var completedAtUtc = request.CompletedAtUtc;
        if (completedAtUtc is null && IsChecklistCompleteStatus(status))
        {
            completedAtUtc = now;
        }

        await using (var command = connection.CreateCommand())
        {
            command.Transaction = transaction;
            command.CommandText =
                """
                UPDATE checklist_runs
                SET
                    status = $status,
                    completed_at_utc = $completedAtUtc,
                    steps_json = $stepsJson,
                    notes = $notes,
                    updated_at_utc = $updatedAtUtc,
                    version = version + 1
                WHERE id = $id;
                """;
            command.Parameters.AddWithValue("$id", id);
            command.Parameters.AddWithValue("$status", status);
            command.Parameters.AddWithValue("$completedAtUtc", ToDbValue(completedAtUtc));
            command.Parameters.AddWithValue("$stepsJson", SerializeJsonElement(request.Steps, "[]"));
            command.Parameters.AddWithValue("$notes", CleanOrDefault(request.Notes));
            command.Parameters.AddWithValue("$updatedAtUtc", now.ToString("O"));

            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        await RecordAuditEventAsync(
            connection,
            transaction,
            existingRecord.IncidentId,
            actorId,
            IsChecklistCompleteStatus(status) ? "complete" : "update",
            "checklist-run",
            id,
            $"Saved checklist run '{id}' progress with status '{status}'.",
            cancellationToken);

        var saved = await ReadChecklistRunAsync(connection, transaction, id, cancellationToken);
        await transaction.CommitAsync(cancellationToken);

        return saved is null
            ? DatabaseSaveResult<ChecklistRunSummary>.NotFound()
            : DatabaseSaveResult<ChecklistRunSummary>.Saved(saved);
    }

    public Task<DatabaseSaveResult<EntityChangeSummary>> UpdateCampStatusAsync(
        string id,
        EntityStatusUpdateRequest request,
        string actorId,
        CancellationToken cancellationToken = default) =>
        UpdateTrackedStatusAsync(
            tableName: "camps",
            entityType: "camp",
            id,
            request.Status,
            request.ExpectedVersion,
            actorId,
            cancellationToken);

    public Task<DatabaseSaveResult<EntityChangeSummary>> UpdateDeviceStatusAsync(
        string id,
        EntityStatusUpdateRequest request,
        string actorId,
        CancellationToken cancellationToken = default) =>
        UpdateTrackedStatusAsync(
            tableName: "devices",
            entityType: "device",
            id,
            request.Status,
            request.ExpectedVersion,
            actorId,
            cancellationToken);

    public Task<DatabaseSaveResult<EntityChangeSummary>> UpdateNetworkStatusAsync(
        string id,
        EntityStatusUpdateRequest request,
        string actorId,
        CancellationToken cancellationToken = default) =>
        UpdateTrackedStatusAsync(
            tableName: "networks",
            entityType: "network",
            id,
            request.Status,
            request.ExpectedVersion,
            actorId,
            cancellationToken);

    public Task<DatabaseSaveResult<EntityChangeSummary>> UpdateLinkStatusAsync(
        string id,
        EntityStatusUpdateRequest request,
        string actorId,
        CancellationToken cancellationToken = default) =>
        UpdateTrackedStatusAsync(
            tableName: "links",
            entityType: "link",
            id,
            request.Status,
            request.ExpectedVersion,
            actorId,
            cancellationToken);

    public async Task<DatabaseSaveResult<EntityChangeSummary>> CompleteChecklistRunAsync(
        string id,
        ChecklistCompletionRequest request,
        string actorId,
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        var existingRecord = await ReadTrackedRecordAsync(
            connection,
            transaction,
            "checklist_runs",
            id,
            cancellationToken);

        if (existingRecord is null)
        {
            return DatabaseSaveResult<EntityChangeSummary>.NotFound();
        }

        if (request.ExpectedVersion.HasValue && request.ExpectedVersion.Value != existingRecord.Version)
        {
            return DatabaseSaveResult<EntityChangeSummary>.Conflict(existingRecord.Version);
        }

        var now = DateTimeOffset.UtcNow;
        var completedAtUtc = request.CompletedAtUtc ?? now;
        await using (var command = connection.CreateCommand())
        {
            command.Transaction = transaction;
            command.CommandText =
                """
                UPDATE checklist_runs
                SET
                    status = $status,
                    completed_at_utc = $completedAtUtc,
                    updated_at_utc = $updatedAtUtc,
                    version = version + 1
                WHERE id = $id;
                """;
            command.Parameters.AddWithValue("$id", id);
            command.Parameters.AddWithValue("$status", request.Status.Trim());
            command.Parameters.AddWithValue("$completedAtUtc", completedAtUtc.ToUniversalTime().ToString("O"));
            command.Parameters.AddWithValue("$updatedAtUtc", now.ToString("O"));

            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        var updatedVersion = existingRecord.Version + 1;
        await RecordAuditEventAsync(
            connection,
            transaction,
            existingRecord.IncidentId,
            actorId,
            "complete",
            "checklist-run",
            id,
            $"Completed checklist run '{id}' with status '{request.Status.Trim()}'.",
            cancellationToken);

        await transaction.CommitAsync(cancellationToken);

        return DatabaseSaveResult<EntityChangeSummary>.Saved(
            new EntityChangeSummary(
                EntityType: "checklist-run",
                EntityId: id,
                IncidentId: existingRecord.IncidentId,
                ChangeType: "complete",
                Status: request.Status.Trim(),
                Version: updatedVersion,
                UpdatedAtUtc: now));
    }

    private async Task<DatabaseSaveResult<EntityChangeSummary>> UpdateTrackedStatusAsync(
        string tableName,
        string entityType,
        string id,
        string status,
        int? expectedVersion,
        string actorId,
        CancellationToken cancellationToken)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        var existingRecord = await ReadTrackedRecordAsync(
            connection,
            transaction,
            tableName,
            id,
            cancellationToken);

        if (existingRecord is null)
        {
            return DatabaseSaveResult<EntityChangeSummary>.NotFound();
        }

        if (expectedVersion.HasValue && expectedVersion.Value != existingRecord.Version)
        {
            return DatabaseSaveResult<EntityChangeSummary>.Conflict(existingRecord.Version);
        }

        var now = DateTimeOffset.UtcNow;
        await using (var command = connection.CreateCommand())
        {
            command.Transaction = transaction;
            command.CommandText =
                $"""
                UPDATE {tableName}
                SET
                    status = $status,
                    updated_at_utc = $updatedAtUtc,
                    version = version + 1
                WHERE id = $id;
                """;
            command.Parameters.AddWithValue("$id", id);
            command.Parameters.AddWithValue("$status", status.Trim());
            command.Parameters.AddWithValue("$updatedAtUtc", now.ToString("O"));

            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        var updatedVersion = existingRecord.Version + 1;
        await RecordAuditEventAsync(
            connection,
            transaction,
            existingRecord.IncidentId,
            actorId,
            "update-status",
            entityType,
            id,
            $"Updated {entityType} '{id}' status to '{status.Trim()}'.",
            cancellationToken);

        await transaction.CommitAsync(cancellationToken);

        return DatabaseSaveResult<EntityChangeSummary>.Saved(
            new EntityChangeSummary(
                EntityType: entityType,
                EntityId: id,
                IncidentId: existingRecord.IncidentId,
                ChangeType: "update-status",
                Status: status.Trim(),
                Version: updatedVersion,
                UpdatedAtUtc: now));
    }

    private static async Task<bool> MigrationHasBeenAppliedAsync(
        SqliteConnection connection,
        string migrationId,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = "SELECT 1 FROM schema_migrations WHERE id = $id LIMIT 1;";
        command.Parameters.AddWithValue("$id", migrationId);

        var result = await command.ExecuteScalarAsync(cancellationToken);
        return result is not null;
    }

    private static async Task<IReadOnlyList<string>> ReadAppliedMigrationsAsync(
        SqliteConnection connection,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = "SELECT id FROM schema_migrations ORDER BY id;";

        var migrations = new List<string>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            migrations.Add(reader.GetString(0));
        }

        return migrations;
    }

    private static async Task RecordMigrationAsync(
        SqliteConnection connection,
        string migrationId,
        SqliteTransaction transaction,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText =
            """
            INSERT INTO schema_migrations (id, applied_at_utc)
            VALUES ($id, $appliedAtUtc);
            """;
        command.Parameters.AddWithValue("$id", migrationId);
        command.Parameters.AddWithValue("$appliedAtUtc", DateTimeOffset.UtcNow.ToString("O"));

        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    private static async Task RecordAuditEventAsync(
        SqliteConnection connection,
        SqliteTransaction transaction,
        string incidentId,
        string actorId,
        string action,
        string targetType,
        string targetId,
        string summary,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText =
            """
            INSERT INTO audit_events (
                id,
                actor_user_id,
                action,
                entity_type,
                entity_id,
                occurred_at_utc,
                summary,
                incident_id,
                actor_type,
                actor_id,
                target_type,
                target_id)
            VALUES (
                $id,
                $actorUserId,
                $action,
                $entityType,
                $entityId,
                $occurredAtUtc,
                $summary,
                $incidentId,
                $actorType,
                $actorId,
                $targetType,
                $targetId);
            """;
        command.Parameters.AddWithValue("$id", Guid.NewGuid().ToString());
        command.Parameters.AddWithValue("$actorUserId", actorId);
        command.Parameters.AddWithValue("$action", action);
        command.Parameters.AddWithValue("$entityType", targetType);
        command.Parameters.AddWithValue("$entityId", targetId);
        command.Parameters.AddWithValue("$occurredAtUtc", DateTimeOffset.UtcNow.ToString("O"));
        command.Parameters.AddWithValue("$summary", summary);
        command.Parameters.AddWithValue("$incidentId", incidentId);
        command.Parameters.AddWithValue("$actorType", "user");
        command.Parameters.AddWithValue("$actorId", actorId);
        command.Parameters.AddWithValue("$targetType", targetType);
        command.Parameters.AddWithValue("$targetId", targetId);

        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    private static async Task<bool> IncidentExistsAsync(
        SqliteConnection connection,
        SqliteTransaction transaction,
        CancellationToken cancellationToken)
    {
        return await ReadCurrentIncidentIdAsync(connection, transaction, cancellationToken) is not null;
    }

    private static async Task<string?> ReadCurrentIncidentIdAsync(
        SqliteConnection connection,
        SqliteTransaction transaction,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = "SELECT id FROM incidents ORDER BY created_at_utc ASC LIMIT 1;";

        var result = await command.ExecuteScalarAsync(cancellationToken);
        return result as string;
    }

    private static async Task<TrackedRecord?> ReadCurrentIncidentRecordAsync(
        SqliteConnection connection,
        SqliteTransaction transaction,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText =
            """
            SELECT id, id, version
            FROM incidents
            ORDER BY created_at_utc ASC
            LIMIT 1;
            """;

        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            return null;
        }

        return new TrackedRecord(
            Id: reader.GetString(0),
            IncidentId: reader.GetString(1),
            Version: reader.GetInt32(2));
    }

    private static async Task<TrackedRecord?> ReadTrackedRecordAsync(
        SqliteConnection connection,
        SqliteTransaction transaction,
        string tableName,
        string id,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText =
            $"""
            SELECT id, incident_id, version
            FROM {tableName}
            WHERE id = $id
            LIMIT 1;
            """;
        command.Parameters.AddWithValue("$id", id);

        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            return null;
        }

        return new TrackedRecord(
            Id: reader.GetString(0),
            IncidentId: reader.GetString(1),
            Version: reader.GetInt32(2));
    }

    private static async Task<ChecklistTemplateDraft?> ReadChecklistTemplateDraftAsync(
        SqliteConnection connection,
        SqliteTransaction transaction,
        string templateId,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                title,
                steps_json
            FROM checklist_templates
            WHERE id = $id
                AND status NOT IN ('archived', 'disabled')
            LIMIT 1;
            """;
        command.Parameters.AddWithValue("$id", templateId.Trim());

        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            return null;
        }

        return new ChecklistTemplateDraft(
            Id: reader.GetString(0),
            IncidentId: ReadOptionalString(reader, 1),
            Title: reader.GetString(2),
            StepsJson: reader.GetString(3));
    }

    private static async Task<ChecklistRunSummary?> ReadChecklistRunAsync(
        SqliteConnection connection,
        SqliteTransaction transaction,
        string id,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText =
            """
            SELECT
                id,
                incident_id,
                template_id,
                status,
                target_type,
                target_id,
                assignee_person_id,
                started_at_utc,
                completed_at_utc,
                steps_json,
                notes,
                created_at_utc,
                updated_at_utc,
                version
            FROM checklist_runs
            WHERE id = $id
            LIMIT 1;
            """;
        command.Parameters.AddWithValue("$id", id);

        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        if (!await reader.ReadAsync(cancellationToken))
        {
            return null;
        }

        return new ChecklistRunSummary(
            Id: reader.GetString(0),
            IncidentId: reader.GetString(1),
            TemplateId: reader.GetString(2),
            Status: reader.GetString(3),
            TargetType: reader.GetString(4),
            TargetId: ReadOptionalString(reader, 5),
            AssigneePersonId: ReadOptionalString(reader, 6),
            StartedAtUtc: ReadRequiredDateTimeOffset(reader, 7),
            CompletedAtUtc: ReadOptionalDateTimeOffset(reader, 8),
            Steps: ReadJsonElement(reader, 9),
            Notes: reader.GetString(10),
            CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 11),
            UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 12),
            Version: reader.GetInt32(13));
    }

    private static void AddIncidentSummaryParameters(
        SqliteCommand command,
        string incidentId,
        IncidentSummaryRequest request,
        DateTimeOffset updatedAtUtc)
    {
        command.Parameters.AddWithValue("$id", incidentId);
        command.Parameters.AddWithValue("$incidentNumber", request.IncidentNumber.Trim());
        command.Parameters.AddWithValue("$name", request.Name.Trim());
        command.Parameters.AddWithValue("$agency", request.Agency.Trim());
        command.Parameters.AddWithValue(
            "$operationalPeriodStartUtc",
            ToDbValue(request.OperationalPeriodStartUtc));
        command.Parameters.AddWithValue(
            "$operationalPeriodEndUtc",
            ToDbValue(request.OperationalPeriodEndUtc));
        command.Parameters.AddWithValue("$createdAtUtc", updatedAtUtc.ToString("O"));
        command.Parameters.AddWithValue("$updatedAtUtc", updatedAtUtc.ToString("O"));
    }

    private static object ToDbValue(DateTimeOffset? value)
    {
        return value.HasValue
            ? value.Value.ToUniversalTime().ToString("O")
            : DBNull.Value;
    }

    private static object ToDbValue(string? value)
    {
        return string.IsNullOrWhiteSpace(value)
            ? DBNull.Value
            : value.Trim();
    }

    private static async Task ExecuteNonQueryAsync(
        SqliteConnection connection,
        string sql,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = sql;

        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    private static async Task ExecuteNonQueryAsync(
        SqliteConnection connection,
        string sql,
        SqliteTransaction transaction,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = sql;

        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    private SqliteConnection CreateConnection() => new(_connectionString);

    private static DateTimeOffset? ReadOptionalDateTimeOffset(SqliteDataReader reader, int ordinal)
    {
        return reader.IsDBNull(ordinal)
            ? null
            : ReadDateTimeOffset(reader.GetString(ordinal));
    }

    private static DateTimeOffset ReadRequiredDateTimeOffset(SqliteDataReader reader, int ordinal)
    {
        return ReadDateTimeOffset(reader.GetString(ordinal));
    }

    private static string? ReadOptionalString(SqliteDataReader reader, int ordinal)
    {
        return reader.IsDBNull(ordinal)
            ? null
            : reader.GetString(ordinal);
    }

    private static double? ReadOptionalDouble(SqliteDataReader reader, int ordinal)
    {
        return reader.IsDBNull(ordinal)
            ? null
            : reader.GetDouble(ordinal);
    }

    private static int? ReadOptionalInt32(SqliteDataReader reader, int ordinal)
    {
        return reader.IsDBNull(ordinal)
            ? null
            : reader.GetInt32(ordinal);
    }

    private static IReadOnlyList<string> ReadStringListJson(SqliteDataReader reader, int ordinal)
    {
        var json = reader.GetString(ordinal);
        return JsonSerializer.Deserialize<List<string>>(json) ?? [];
    }

    private static JsonElement ReadJsonElement(SqliteDataReader reader, int ordinal)
    {
        return JsonSerializer.Deserialize<JsonElement>(reader.GetString(ordinal));
    }

    private static string SerializeJsonElement(JsonElement value, string fallback)
    {
        return value.ValueKind is JsonValueKind.Undefined or JsonValueKind.Null
            ? fallback
            : JsonSerializer.Serialize(value);
    }

    private static string CleanOrDefault(string? value) => value?.Trim() ?? "";

    private static bool IsChecklistCompleteStatus(string status) =>
        string.Equals(status, "complete", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(status, "completed", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(status, "done", StringComparison.OrdinalIgnoreCase);

    private static DateTimeOffset ReadDateTimeOffset(string value)
    {
        return DateTimeOffset.Parse(
            value,
            CultureInfo.InvariantCulture,
            DateTimeStyles.RoundtripKind);
    }

    private const string CreateMigrationTableSql =
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id TEXT PRIMARY KEY,
            applied_at_utc TEXT NOT NULL
        );
        """;

    private sealed record Migration(string Id, string Sql);

    private sealed record TrackedRecord(
        string Id,
        string IncidentId,
        int Version);

    private sealed record ChecklistTemplateDraft(
        string Id,
        string? IncidentId,
        string Title,
        string StepsJson);
}

internal sealed record DatabaseHealth(
    string Status,
    IReadOnlyList<string> AppliedMigrations);

internal sealed record IncidentSummary(
    string Id,
    string IncidentNumber,
    string Name,
    string Agency,
    DateTimeOffset? OperationalPeriodStartUtc,
    DateTimeOffset? OperationalPeriodEndUtc,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int Version);

internal sealed record IncidentSummaryRequest(
    string? Id,
    string IncidentNumber,
    string Name,
    string Agency,
    DateTimeOffset? OperationalPeriodStartUtc,
    DateTimeOffset? OperationalPeriodEndUtc,
    int? ExpectedVersion);

internal sealed record EntityStatusUpdateRequest(
    string Status,
    int? ExpectedVersion);

internal sealed record ChecklistCompletionRequest(
    string Status,
    DateTimeOffset? CompletedAtUtc,
    int? ExpectedVersion);

internal sealed record ChecklistRunCreateRequest(
    string? Id,
    string TemplateId,
    string? Status,
    string? TargetType,
    string? TargetId,
    string? AssigneePersonId,
    DateTimeOffset? StartedAtUtc,
    DateTimeOffset? CompletedAtUtc,
    string? Notes);

internal sealed record ChecklistRunProgressRequest(
    string Status,
    JsonElement Steps,
    string? Notes,
    DateTimeOffset? CompletedAtUtc,
    int? ExpectedVersion);

internal sealed record EntityChangeSummary(
    string EntityType,
    string EntityId,
    string IncidentId,
    string ChangeType,
    string Status,
    int Version,
    DateTimeOffset UpdatedAtUtc);

internal enum DatabaseSaveStatus
{
    Saved,
    NotFound,
    Conflict,
    Duplicate,
}

internal sealed record DatabaseSaveResult<T>(
    DatabaseSaveStatus Status,
    T? Value,
    int? CurrentVersion)
{
    public static DatabaseSaveResult<T> Saved(T value) =>
        new(DatabaseSaveStatus.Saved, value, null);

    public static DatabaseSaveResult<T> NotFound() =>
        new(DatabaseSaveStatus.NotFound, default, null);

    public static DatabaseSaveResult<T> Conflict(int currentVersion) =>
        new(DatabaseSaveStatus.Conflict, default, currentVersion);

    public static DatabaseSaveResult<T> Duplicate() =>
        new(DatabaseSaveStatus.Duplicate, default, null);
}

internal sealed record CampSummary(
    string Id,
    string IncidentId,
    string Name,
    string CampType,
    string Status,
    string? PrimaryLocationId,
    string AddressOrDirections,
    double? Latitude,
    double? Longitude,
    int? Capacity,
    string? ItContactPersonId,
    string Notes,
    string RecordState,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int Version);

internal sealed record DeviceSummary(
    string Id,
    string IncidentId,
    string Hostname,
    string DeviceType,
    string Status,
    string? LocationId,
    string Manufacturer,
    string Model,
    string SerialNumber,
    string? PrimaryIpAssignmentId,
    IReadOnlyList<string> MacAddresses,
    string? AssetId,
    string Notes,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int Version);

internal sealed record LocationSummary(
    string Id,
    string IncidentId,
    string CampId,
    string Name,
    string LocationType,
    string Status,
    string? ParentLocationId,
    double? MapX,
    double? MapY,
    double? MapWidth,
    double? MapHeight,
    double? Latitude,
    double? Longitude,
    double? ElevationFt,
    string AddressOrDirections,
    int? Capacity,
    string AccessNotes,
    string Notes,
    string RecordState,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int Version);

internal sealed record NetworkSummary(
    string Id,
    string IncidentId,
    string? CampId,
    string Name,
    string NetworkType,
    string Status,
    string Description,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int Version);

internal sealed record LinkSummary(
    string Id,
    string IncidentId,
    string? NetworkId,
    string LinkCategory,
    string LinkType,
    string Status,
    string? SourceDeviceId,
    string? DestinationDeviceId,
    string? SourceLocationId,
    string? DestinationLocationId,
    string SourceRef,
    string DestinationRef,
    string Label,
    string Length,
    string Path,
    string Notes,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int Version);

internal sealed record ChecklistTemplateSummary(
    string Id,
    string? IncidentId,
    string Title,
    string TemplateType,
    string VersionLabel,
    string Status,
    string ScopeType,
    string? ScopeId,
    string Purpose,
    string RoleOwner,
    string RequiredTools,
    string SafetyNotes,
    string Prerequisites,
    string CompletionCriteria,
    JsonElement Steps,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int Version);

internal sealed record ChecklistRunSummary(
    string Id,
    string IncidentId,
    string TemplateId,
    string Status,
    string TargetType,
    string? TargetId,
    string? AssigneePersonId,
    DateTimeOffset StartedAtUtc,
    DateTimeOffset? CompletedAtUtc,
    JsonElement Steps,
    string Notes,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int Version);

internal sealed record AuditEventSummary(
    string Id,
    string IncidentId,
    string ActorType,
    string ActorId,
    string Action,
    string TargetType,
    string TargetId,
    DateTimeOffset OccurredAtUtc,
    string Summary);
