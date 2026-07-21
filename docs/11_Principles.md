# Principles

## Core design principles for FireIT Manager

### Local-first operation
The application should work effectively in local desktop environments and avoid unnecessary dependence on network connectivity for core functionality.

### Offline capable
Core workflows should remain usable when connectivity is unavailable or intermittent, especially in field conditions.

### Data before visualization
Reliable data models and persistence come before rich visual interfaces. Visual features should be built on top of trustworthy underlying data.

### Modular architecture
The system should be organized into clear modules so features can be added, tested, and maintained independently.

### Desktop-first UX
The primary experience should be optimized for professional desktop workflows, including dockable panels, keyboard navigation, and efficient information layout.

### One source of truth for every object
Each important domain object should have a clear authoritative representation within the system to avoid duplication and inconsistent state.

### Support the ITSS workflow
Every major feature should support the incident support workflow, including planning, coordination, tracking, reporting, and operational follow-through.

### Every major feature must be testable
New features should be designed so they can be exercised through automated tests, regression scenarios, and clear verification paths.

## Intent
These principles should guide architecture decisions, implementation choices, and future product evolution.
