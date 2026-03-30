# Scheduler Web Interface (Sprint 2)
### Overview

This directory contains the Flask-based web interface for the Scheduler application.

Sprint 2 extends the Sprint 1 CLI application by adding a GUI implemented using Flask, while preserving all existing CLI functionality.

The architecture follows the required MVC (Model–View–Controller) design pattern.

## Architecture (MVC)
### Model (Domain / Business Logic)

The Model layer consists of the existing Sprint 1 modules:
- `app/config_ops/`
- `app/faculty_management/`
- `app/course_management/`
- `app/room_management/`
- `app/lab_management/`
- `app/scheduler_execution/`
- `scheduler_core/`

These modules:

- Load and save configuration files

- Perform CRUD operations on faculty, rooms, labs, courses, and conflicts

- Execute the scheduler to generate schedules

The `services/` folder inside `app/web/` acts as a thin orchestration layer that wraps the existing domain logic for use in the web interface.

No scheduler logic is duplicated in the web layer.

## View (User Interface)

Located in:
```swift
app/web/templates/
app/web/static/
```

This includes:

- HTML templates 

- CSS styling

- Optional JavaScript

Pages implemented:

- Config Editor

- Schedule Generator

- Schedule Viewer

## Controller (Flask Routes)

Located in:
```bash
app/web/routes/
```
Controllers handle:

- User form submissions

- Route navigation

- Calling service layer functions

- Rendering templates

- Redirecting between pages

Each page of the GUI corresponds to a Blueprint and route file.

## Directory Structure
```csharp
app/web/
│
├── app.py
├── README.md
│
├── routes/
│   ├── config_routes.py
│   ├── run_routes.py
│   └── viewer_routes.py
│
├── services/
│   ├── config_service.py
│   ├── run_service.py
│   └── schedule_service.py
│
├── templates/
│   ├── base.html
│   ├── config_editor.html
│   ├── generator.html
│   └── viewer.html
│
└── static/
    ├── styles.css
    └── app.js
```

## Running the Web App

From the project root:
```arduino
uv add flask
uv run flask --app app.web:create_app --debug run --with-threads
```
Then open the development server URL shown in the terminal.

## Pages Implemented
### 1. Config Editor (`/config`)

Features:

- Load configuration file

- Save configuration file

- Display summary counts (faculty, courses, rooms, labs)

- Foundation for adding full CRUD forms

Future expansion:

- Add/Edit/Delete faculty

- Add/Edit/Delete rooms

- Add/Edit/Delete labs

- Add/Edit/Delete courses and conflicts

### 2. Schedule Generator (/run)

Features:

- Limit override (number of schedules)

- Optimization toggle

- Generate button

- Redirects to Viewer

Current status:

- Uses placeholder schedule generation

- Designed to be replaced with real SchedulerExecution integration

Future integration:

Replace placeholder logic in:
```bash
app/web/services/run_service.py
```
with actual calls to `SchedulerExecution`.

### 3. Schedule Viewer (`/viewer`)

Features:

- Navigate between schedules (Next / Previous)

- View schedule metadata

- Tabular grouping:

    - By Room

    - By Faculty

- Import schedules (JSON)

- Export schedules (JSON)

This satisfies Sprint 2 requirements for:

- Navigation between generated schedules

- Tabular output

- Import/Export functionality

## Relationship to Sprint 1

Sprint 1 CLI remains fully functional:
```bash
app/main.py
```

Sprint 2 adds a web interface without modifying core scheduler logic.

This preserves:

- Backward compatibility

- Separation of concerns

- Clean architecture

- Test integrity

CLI and Web interface operate independently but use the same domain logic.

## Design Principles

- Clear separation between:

    - Domain logic

    - Web layer

    - Presentation

- No duplication of Sprint 1 logic

- Flask only orchestrates existing functionality

- Modular structure for maintainability

## Next Development Steps

1. Replace placeholder schedule generation with real SchedulerExecution integration.

2. Implement full CRUD forms in the Config Editor.

3. Add input validation.

4. Improve UI styling.

5. Add additional testing for web routes.

## README Author

Antonio Corona  
CSCI 420 – Scheduler Project
<br>Sprint 2