using Microsoft.Data.Sqlite;
using SQLitePCL;
using System.Globalization;

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
