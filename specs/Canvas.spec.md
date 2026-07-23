# Canvas Specification

## Purpose
Define the baseline behavior for the camp Site Map workspace.

## Functional expectations
- The central canvas should host incident planning and network topology content.
- The canvas should support zoom, pan, and selection interactions.
- The Site Map title should remain pinned to the top of the visible view and scale
  with the current zoom level.
- Camp and network summary information should remain pinned to the left side of
  the visible view and scale with the current zoom level.
- Location boxes should be draggable and resizable.
- Equipment dropped inside a location box should anchor to it and move with it.
- Cable connections should follow devices as they move.
- Selecting a map item should update the Properties pane with editable object data.
- The workspace should remain visually distinct from inspector panels.

## Non-functional expectations
- The canvas should be implemented as a dedicated module.
- It should be possible to extend the canvas without reworking the rest of the UI shell.
