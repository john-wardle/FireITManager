# Common ITSS Workflows

This document describes practical workflows for the current prototype and the planned
future product.

## Start A New Incident Workspace

1. Open FireIT Manager.
2. Go to `Incident > Details`.
3. Select `New Incident`.
4. Enter the incident name.
5. Enter the incident number if known.
6. Enter the agency.
7. Enter the operational period.
8. Select `Apply Changes`.
9. Use `File > Save As` to create the first saved incident file.

## Update The Operational Period

1. Go to `Incident > Details`.
2. Update `Operational Period`.
3. Select `Apply Changes`.
4. Confirm the bottom status bar updates.
5. Save the incident.

## Update Camp Information

1. Go to `Camp Ops > Camps`.
2. Enter the camp name.
3. Select `Apply Changes`.
4. Confirm the Incident Explorer updates.
5. Save the incident.

## Add Or Edit A Building

1. Go to `Camp Ops > Buildings`.
2. Select `New Building` if creating a new building.
3. Enter the building name.
4. Choose the building type.
5. Enter location fields if known.
6. Select `Apply Changes`.
7. Open `Network > Site Map` to confirm the site layout updates.
8. Save the incident.

## Add Or Edit A Device

1. Go to `Inventory > Devices`.
2. Select `New Device` if creating a new device.
3. Enter hostname.
4. Enter manufacturer, model, serial number, IP address, and MAC address where known.
5. Choose device type.
6. Choose status.
7. Select `Apply Changes`.
8. Save the incident.

## Add A Device To A Network

1. Go to `Network > Networks`.
2. Choose the device from `Available Devices`.
3. Select `Add Selected Device`.
4. Confirm the device appears in `Network Members`.
5. Save the incident.

## Assign A Device To A Person

1. Go to `Incident > Personnel`.
2. Select or create the person record.
3. Choose a device from `Available Devices`.
4. Select `Add Selected Device`.
5. Select `Apply Changes`.
6. Save the incident.

## Assign An Asset To A Person

1. Go to `Inventory > Assets`.
2. Select or create the asset.
3. Choose the person in `People Picker`.
4. Select `Use Selected Person`.
5. Select `Apply Changes`.
6. Save the incident.

## Inspect The Incident Structure

1. Use the left Incident Explorer.
2. Select an item.
3. Review the details in the right Properties dock.
4. If editable fields appear, change values and select `Apply`.
5. Save the incident after changes.

## Export A Summary Report

1. Go to `Outputs > Reports`.
2. Select the desired export format.
3. Choose the destination file.
4. Confirm the status bar shows the report path.

## Validate Before Saving Or Reporting

1. Go to `Outputs > Validation`.
2. Select `Validate Workspace`.
3. Review the status bar message.
4. Resolve issues if any are reported.
5. Save or export after validation passes.

## Planned Mobile Checklist Workflow

The current prototype does not yet include the mobile checklist tool. The intended future
workflow is:

1. ITSS opens the mobile/tablet client on the incident LAN.
2. ITSS chooses a standard checklist.
3. ITSS completes steps while walking camp.
4. ITSS adds notes, photos, or blockers.
5. Checklist completion syncs to the incident server.
6. Desktop users see completion status in the shared incident record.
