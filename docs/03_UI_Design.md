# UI Design

## Design Principles
- Prioritize clarity and operational usefulness over ornamentation.
- Keep core navigation visible and stable.
- Use dock windows to support inspection and management workflows.
- Ensure the interface can grow into richer incident planning experiences.

## Layouts
- Main workspace uses folder-style navigation with top-level workflow folders and second-level task tabs.
- Current top-level folders: Incident, Camp Ops, Inventory, Network, Outputs.
- Docked explorer and properties panels remain visible beside the workspace.
- Network map workflows live under Network / Site Map and show draggable buildings,
  cardless device icons and cable connections from the active incident graph.
- Site Map title text remains pinned to the top of the visible viewport and scales
  with the current zoom level.
- Site Map summary information remains pinned to the left side of the viewport,
  scales with the current zoom level, and lists camps, location/device counts,
  network device/cable counts, and incident asset counts.
- Site Map location boxes are resizable. Equipment dropped within a location
  anchors to it and moves with the location while preserving relative placement.
- Menus and toolbars remain persistent at the top of the window.
- Status information remains visible in the bottom status bar.

## Colors
- Use a neutral, professional desktop palette with subtle accents.
- Reserve strong colors for warning states and active selection.

## Dock windows
- Left dock: Incident Explorer
- Right dock: Properties
- The Properties dock shows read-only selection context plus editable fields for
  concrete incident objects. Apply commits changes back to the active in-memory
  incident model and refreshes dependent views.

## Menus
- File
- Edit
- View
- Incident
- Camp Ops
- Inventory
- Network
- Outputs
- Help

## Toolbars
- Incident file actions live at the top of Incident / Details.
- Site Map view controls live at the bottom of Network / Site Map.
- Editor navigation belongs in workspace folder tabs and matching top-level menus.
- The redundant primary toolbar row is removed.

## Keyboard shortcuts
- Ctrl+N
- Ctrl+O
- Ctrl+S
- Ctrl+Z
- Ctrl+Y

## Accessibility Guidelines
- Ensure readable text contrast.
- Support keyboard navigation for primary actions.
- Keep labels and controls descriptive.
