# Maverick Scheduler

A Flask-based web application for managing configuration data and generating academic course schedules.

The project began as a Sprint 1 CLI scheduler and was extended in Sprint 2 with a web GUI built using **Flask**. The GUI supports loading and editing scheduler configurations, generating schedules with per-run overrides, browsing generated schedules, and importing/exporting schedule files.

> Note: This README focuses on how to run the **Flask web app** and the **test suite**. CLI usage can be found within **"CLI_USAGE.md"**.

---

## Authors

- Antonio Corona
- Andrew Jackson
- Ian Swartz
- Jacob Karasow
- Tanner Ness

---

## Requirements

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/) package manager
- Flask
- pytest
- `course-constraint-scheduler`

The project dependencies are already declared in `pyproject.toml`.

---

## Tech Stack

- **Flask** — web framework for the Sprint 2 GUI
- **pytest** — automated testing
- **uv** — dependency and virtual environment management
- **course-constraint-scheduler** — core scheduling engine

---

## Project Structure

```text
.
├── README.md
├── CLI_USAGE.md
├── pyproject.toml
├── uv.lock
├── main.py
│
├── app/
│   ├── main.py                    # Sprint 1 CLI entry point
│   ├── config_ops/                # Config load/save/summary helpers
│   ├── faculty_management/        # Faculty CRUD logic
│   ├── course_management/         # Course/conflict CRUD logic
│   ├── room_management/           # Room CRUD logic
│   ├── lab_management/            # Lab CRUD logic
│   ├── scheduler_execution/       # Scheduler runner integration
│   ├── schedule_viewing/          # Schedule display helpers
│   └── web/                       # Sprint 2 Flask web application
│       ├── app.py                 # Flask application factory
│       ├── routes/                # Flask controllers / blueprints
│       ├── services/              # Service layer for web features
│       ├── templates/             # Jinja HTML templates
│       ├── static/                # CSS / JavaScript
│       └── README.md              # Web-specific README
│
├── configs/
│   ├── config_base.json
│   ├── config_dev.json
│   ├── config_test.json
│   └── working_config.json
│
├── schedules/
│   └── export_000.json
│
├── scheduler_core/
│   └── main.py
│
└── tests/
    ├── conftest.py
    ├── test_config_service.py
    ├── test_course.py
    ├── test_faculty.py
    ├── test_lab.py
    └── test_room.py
```

---

## Getting Started

The steps below allow a new user to install dependencies, run tests, and start the web application.

---

### 1. Clone the Repository
```Bash
git clone <repository-url>
cd 2026sp-420-Maverick
```

---

### 2. Install uv

This project uses uv to manage Python environments and dependencies.

### macOS / Linux
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
### Or install with pip
pip install uv

---

### 3. Install Project Dependencies

From the project root directory run:
```Bash
uv sync
```

This will:
-   create a virtual environment
-   install dependencies defined in pyproject.toml
-   install Flask, pytest, and the scheduler engine

---

## Running the Web Application

The Sprint 2 GUI is built using Flask.

Start the development server:

```
uv run flask --app app.web:create_app --debug run
```
Open the address shown in your terminal:
```
http://127.0.0.1:5000
```
The application will redirect to the Config Editor.

Stop the server with:
```
Ctrl + C
```

---

## First-Time Usage Workflow

A typical workflow for a new user is:

### 1. Open the Config Editor

When the application launches, it redirects to:
```
/config
```
The Config Editor allows you to manage the scheduler configuration.

---

### 2. Load a Configuration

Load one of the included configs such as:
```
configs/config_dev.json
configs/config_test.json
```
Or upload a JSON configuration file from your computer.

---

### 3. Edit Configuration

The Config Editor supports managing:

=   Faculty
=   Courses
=   Conflicts
=   Rooms
-   Labs

Changes are applied to the working configuration.

---

### 4. Generate Schedules

Navigate to:
```
/run
```
Here you can:
-   override the generation limit
-   enable or disable optimizer flags
-   generate schedules using the solver

---

### 5. Browse Generated Schedules

Navigate to:

```
/viewer
```

The Schedule Viewer allows users to:

-   navigate between schedules
-   directly select schedules
-   inspect schedule metadata
-   view schedules grouped by:
-       faculty
-       room
-       lab
-   filter tables by:
-       specific faculty
-       specific room
-       specific lab
-   import previously saved schedules
-   export schedules to JSON or CSV
-   open grid or visual schedule views

---

## 🤖 AI Chat Tool (Natural Language Configuration)

The Maverick Scheduler includes an AI-powered assistant that allows users to modify configurations using natural language.

### Example Commands
- Add course CS102 with 3 credits in Roddy 140  
- Change the credits of CS199 to 4  
- Rename course CS163 to CS370  
- Add faculty Dr. Jones with appointment type full-time  

👉 Full command reference: [AI Command Guide](docs/ai-commands.md)

---

## Running Tests

The project uses **pytest**.

Run all tests:
```
uv run pytest
```
 
Run tests with verbose output:
```
uv run pytest -v
```

Run a specific test file:
```
uv run pytest tests/test_faculty.py
```

Other test files include:
```
tests/test_course.py
tests/test_room.py
tests/test_lab.py
tests/test_config_service.py
```

### Testing Commands

Run all tests:
uv run pytest

or 

uv run pytest tests/[filename] -q

---

## Running Tests with Coverage

To run all tests with coverage locally:

```bash
uv run pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=xml
```

---

## MVC Architecture

The project follows a **Model–View–Controller** architecture.

### Model / Domain Logic

Located in:
```
app/config_ops/
app/faculty_management/
app/course_management/
app/room_management/
app/lab_management/
scheduler_core/
```
Handles:
-   configuration logic
-   CRUD operations
-   scheduling constraints
-   scheduler execution

---

### View Layer

Located in:
```
app/web/templates/
app/web/static/
```
Contains:

-   Jinja templates
-   CSS styling
-   JavaScript UI behavior

---

### Controller Layer

Located in:
```
app/web/routes/
```
Responsible for:

-   Flask routes
-   request handling
-   redirect logic
-   calling services
-   updating session state

---

### Service Layer

Located in:
```
app/web/services/
```
Services connect Flask routes to the scheduling logic.

---

## Configuration Files

Example configurations are included in:

```
configs/config_dev.json
configs/config_test.json
configs/config_base.json
```

These can be loaded directly through the GUI.

---

### Service Layer

Located in:

```
app/web/services/
```

Services connect Flask routes to the scheduling logic.

---

## Troubleshooting
### Flask will not start

Make sure you run:

```Bash
uv run flask --app app.web:create_app --debug run
```
from the project root directory.

---

### Dependencies appear missing
Run:
```Bash
uv sync
```
again from the root directory.

---

### Port already in use

If the Flask server reports that the port is already in use, stop the existing process or restart the terminal session.

---

### Viewer shows no schedules

Make sure you:

1. loaded a configuration

2. generated schedules from /run

3. navigated to /viewer

---

### Visual view is blocked

The viewer disables the visual schedule view when time conflicts are detected in the current schedule.

---

## Acknowledgements

Built with: 
    - Flask
    - pytest
    - uv
    - course-constraint-scheduler

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright © 2026 Maverick

---