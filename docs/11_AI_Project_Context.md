# FireIT Manager AI Context

## Purpose
FireIT Manager is a desktop application for Incident Technology Support Specialists working on NWCG wildland fires. The software models the physical IT infrastructure of a fire camp and serves as a digital twin for incident technology operations.

## What this project is
- A desktop-first application built with PySide6
- A domain-driven tool for modeling incident camp infrastructure
- A platform for incident IT planning, inventory awareness, and operational visibility

## What this project is not
- Not a ticketing system
- Not a GIS system
- Not a general incident command platform
- Not a web application

## Design principles
- Desktop-first experience
- Local-first operation
- Offline capable workflows where practical
- Data before visualization
- Modular architecture
- One source of truth for every core object
- Professional engineering quality
- Clear separation between UI, domain logic, and persistence

## Current status
Completed
- Main window
- Menu bar
- Toolbar
- Dock panels
- Domain models

Next
- Canvas engine
- Inventory workflows
- Network topology
- Reporting

## Architecture guidance
- Use PySide6 for UI components.
- Keep business logic out of widgets.
- Keep the domain layer free from persistence and GUI concerns.
- Prefer composition over inheritance.
- Use UUID and datetime values in memory.
- Store strings only when serializing.

## Coding expectations
- Follow the existing package structure.
- Use type hints on public classes and methods.
- Favor small, focused classes.
- Add docstrings to public modules, classes, and functions.
- Keep changes testable and modular.
