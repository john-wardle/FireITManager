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
  device icons, and cable connections from the active incident graph.
- Menus and toolbars remain persistent at the top of the window.
- Status information remains visible in the bottom status bar.

## Colors
- Use a neutral, professional desktop palette with subtle accents.
- Reserve strong colors for warning states and active selection.

## Dock windows
- Left dock: Incident Explorer
- Right dock: Properties

## Menus
- File
- Edit
- View
- Incident
- Network
- Inventory
- Reports
- Tools
- Help

## Toolbars
- Actions include incident creation, open/save actions, undo/redo, and canvas view controls.
- Editor navigation belongs in the workspace folder tabs and View menu, not the primary toolbar.
- Placeholder actions should remain disabled until implemented.

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
