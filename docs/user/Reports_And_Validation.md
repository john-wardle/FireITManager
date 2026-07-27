# Reports And Validation

Use Outputs for checks and exports.

## Reports

Open `Outputs > Reports`.

Available report actions:

- `Export Summary Markdown`
- `Export Summary CSV`
- `Export Summary HTML`

The report contains a summary of the active incident workspace. Use reports for quick
handoff, review, and documentation snapshots.

## Validation

Open `Outputs > Validation`.

Available validation action:

- `Validate Workspace`

Validation checks the active incident workspace before saving or exporting. If issues
are found, the status bar reports the number of issues. If no issues are found, the
status bar reports that the workspace is valid.

## Recommended Practice

Before sharing a file or report:

1. Apply changes in the active editor.
2. Run `Validate Workspace`.
3. Save the incident.
4. Export the needed report.
5. Confirm the status bar shows the expected save or export path.

## Current Prototype Limits

- Reports are summary-level exports.
- Reports are not yet full incident documentation packages.
- Validation is basic and will expand as the incident data model becomes stricter.
