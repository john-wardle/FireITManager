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
                updated_at_utc
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
            UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 7));
    }

    public async Task<IncidentSummary?> CreateIncidentSummaryAsync(
        IncidentSummaryRequest request,
        string actorId,
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        if (await IncidentExistsAsync(connection, transaction, cancellationToken))
        {
            return null;
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

        return await GetIncidentSummaryAsync(cancellationToken);
    }

    public async Task<IncidentSummary?> UpdateIncidentSummaryAsync(
        IncidentSummaryRequest request,
        string actorId,
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        var existingIncidentId = await ReadCurrentIncidentIdAsync(connection, transaction, cancellationToken);
        if (existingIncidentId is null)
        {
            return null;
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
                    updated_at_utc = $updatedAtUtc
                WHERE id = $id;
                """;
            AddIncidentSummaryParameters(command, existingIncidentId, request, now);

            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        await RecordAuditEventAsync(
            connection,
            transaction,
            existingIncidentId,
            actorId,
            "update",
            "incident",
            existingIncidentId,
            $"Updated incident summary '{request.Name}'.",
            cancellationToken);

        await transaction.CommitAsync(cancellationToken);

        return await GetIncidentSummaryAsync(cancellationToken);
    }

    public async Task<bool> DeleteIncidentSummaryAsync(
        string actorId,
        CancellationToken cancellationToken = default)
    {
        await using var connection = CreateConnection();
        await connection.OpenAsync(cancellationToken);
        await using var transaction = connection.BeginTransaction();

        var existingIncidentId = await ReadCurrentIncidentIdAsync(connection, transaction, cancellationToken);
        if (existingIncidentId is null)
        {
            return false;
        }

        await RecordAuditEventAsync(
            connection,
            transaction,
            existingIncidentId,
            actorId,
            "delete",
            "incident",
            existingIncidentId,
            "Deleted incident summary.",
            cancellationToken);

        await using (var command = connection.CreateCommand())
        {
            command.Transaction = transaction;
            command.CommandText = "DELETE FROM incidents WHERE id = $id;";
            command.Parameters.AddWithValue("$id", existingIncidentId);

            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        await transaction.CommitAsync(cancellationToken);
        return true;
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
                Steps: ReadJsonElement(reader, 8),
                CreatedAtUtc: ReadRequiredDateTimeOffset(reader, 9),
                UpdatedAtUtc: ReadRequiredDateTimeOffset(reader, 10),
                Version: reader.GetInt32(11)));
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
    DateTimeOffset UpdatedAtUtc);

internal sealed record IncidentSummaryRequest(
    string? Id,
    string IncidentNumber,
    string Name,
    string Agency,
    DateTimeOffset? OperationalPeriodStartUtc,
    DateTimeOffset? OperationalPeriodEndUtc);

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
