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

## Local AI and Flask Configuration

To run the AI Chat Tool locally with your own settings, create a local settings file:

```bash
cp app/local_settings.example.py app/local_settings.py
```

Then open `app/local_settings.py` and fill in your own values:

```
OPENAI_API_KEY = "your-openai-api-key"
FLASK_SECRET_KEY = "your-flask-secret-key"
MAVERICK_OPENAI_MODEL = "gpt-5-mini"
```

### Notes
- `app/local_settings.py` is ignored by Git and should not be committed
- Environment variables are still supported as a fallback
- `gpt-5-mini` is the default model if no model is provided

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

## Configuration Files

Example configurations are included in:

```
configs/config_dev.json
configs/config_test.json
configs/config_base.json
```

These can be loaded directly through the GUI.

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

## Design Pattern: Command

The application implements the **Command design pattern** in the AI configuration tool execution layer located in `app/web/services/ai_tools.py`.

### Problem

The AI chat tool can request many different configuration changes, such as adding faculty, removing rooms, modifying courses, or changing conflicts. Previously, these requests were routed through function dispatch logic. While this worked functionally, it did not fully implement the Command pattern because requests were not represented as command objects.

### Pattern

The Command pattern encapsulates a request as an object with a common execution interface. This allows the client to execute a request without knowing the specific receiver or operation being performed.

### Implementation

The implementation uses:

- `ToolCommand` as the shared command interface
- `ConfigToolCommand` as the concrete command for valid AI tool requests
- `UnsupportedToolCommand` as a safe command for unsupported requests
- `ToolCommandFactory` to create command objects based on tool names
- `execute_tool()` to validate input, create the command, and call `command.execute()`

### How It Solves the Problem

This turns AI tool requests into first-class command objects. The AI service no longer needs to know how each operation is performed; it only asks the command object to execute. This improves maintainability, supports future undo/redo or logging, and matches the course definition of Command as encapsulating a request as an object.

---

## Design Pattern: Adapter

The application implements the **Adapter design pattern** in `scheduler_core/main.py`.

### Problem

The project uses an external scheduler package that returns schedule models through its own API. The Maverick Scheduler web app needs a different representation: flat meeting-level dictionaries that can be grouped, displayed, exported, and tested by the rest of the application.

### Pattern

The Adapter pattern converts the interface of an existing class or system into the interface expected by the application.

### Implementation

`SchedulerAdapter` wraps the external scheduler integration. It creates the external `CombinedConfig` and `Scheduler`, calls `scheduler.get_models()`, and converts each model into the flat row format expected by `run_service.py` and the schedule viewer.

### How It Solves the Problem

The rest of the application no longer depends directly on the external scheduler API. It depends on the adapter’s app-specific `iter_flat_schedules()` interface. This isolates external library details and makes future scheduler integration changes easier.

---

## Design Pattern: Observer

2. Observer (Behavioral Pattern)
Located in 
```
app/web/templates/visual_schedule.html
```
Details:
- A central State object is used to control the filtering used with the visual calendar view (visual_schedule.html).
- When the state changes (e.g.: day changes to 'Monday') all parts of the UI that use the state update themselves automatically.

- Shown: CalendarState object manages the filters. Instead of one giant function (what it started as), there are smaller "listeners" that handle on job (e.g.: one listener for Day filter, one for Room filter).

- CalendarState holds the state of the calendar filtering. When a value changes, it notifies all "subscribed" functions to update themselves. 
- A new function is called when the state changes. 
- If a top category is changed then the sub-filters are reset.

- Observer 1 is used to update the main view sections.
(All, Faculty, Rooms, Labs)
- State also controls the visibility of the sub-filtering.
(e.g.: Show-Faculty, Filter - Hobbs)

- Observer 2 is used to update the calendar container visibility (sub-filtering).

- Observer 3 is used to update the day grid layout.

- Event handlers are used to update the UI button styles, and update the state.

---

## Design Pattern: State

3. State (Behavoiral Pattern)

Located in 
```
app/web/routes/run_routes.py
app/web/static/app.js
app/web/templates/generator.html
```
Details:

- The progress bar's behavior changes based on on how many schedules have currently been generated (app.js)

- Uses lots of conditionals to determine how it behaves (app.js)

- UI behavior tied to internal state (run_routes.py pinging for updates)

states:
- Initially, the progress bar is at 0% when no running/initially started.

- When running, the progress bar updates continuously and updates are made to the progress bar (i.e. the percentage increases and the bottom text changes)

- Completed at 100%, redirects the user automatically to the viewer page.

- When it encounters and error, show an error message instead of progressing. Allows for retrying.

---

## Design Pattern: Template Method

4. Template Method (Behavioral Pattern)

Our application implements the **Template Method design pattern** within the configuration routes located in `app/web/routes/config_routes.py`.

### Problem

The configuration editor includes many routes for modifying system data, such as adding, removing, and modifying faculty, courses, rooms, labs, timeslots, and meeting patterns.

Each route followed the same workflow:
    - Call a service-layer function
    - Handle exceptions
    - Display a success or error message
    - Redirect back to the editor

This resulted in significant code duplication, making the file harder to maintain and more error-prone when changes are needed. 

### Pattern

The **Template Method pattern** defines the skeleton of an algorithm in one place while allowing specific steps to vary.

In this case, the shared algoritm is:
    - Execute an action
    - Handle errors
    - Display feedback
    - Redirect to the editor
    
The vary parts are:
    - Which service function is executed 
    - What success message is shown
    
### Implementation

The pattern is implemented using helper functions that standarize route behavior:
    - handle_action(service_fn, success_msg, *args, **kwargs)
    - handle_form_action(service_fn, success_msg)

These functions define the common workflow for all routes.
Each route now delegates its logic instead of reimplementing it.
The helper function executes the service, handles errors, flashes a message, and redirects.

### How It Solves the Problem

By applying the Template Method pattern:
    - Duplicate code is eliminated across all route handlers
    - Route behavior is consistent and centralized 
    - Chnages to error handling or messaging only need to be made in one place
    - New routes can be added with minimal code 

This approach improves maintainability, readability, and scalability of the controller layer.

---

## Design Pattern: Builder

5. Builder (Creational Pattern)

Our application implements the **Builder design pattern** within the configuration editor interface located in `app/web/templates/config_editor.html`.

### Problem

The configuraton editor allows users to dynamically create and modify many different types of entities (faculty, rooms, labs, courses, conflicts, time slots, and meeting patterns). Each entity supports multiple operations such as add, remove, modify, resulting in a large number of possible form variations. 

### Pattern

The Builder pattern constructs a complex object step-by-step while separating the construction logic from the final representation. In this case, the "complex object" is the dynamically generated HTML form.
    
### Implementation

In our system, the FormBuilder class is responsible for constructing HTML forms based on the selected entity type and operation mode. 

Each form is built incrementally:
    - The builder is initialized with:
        - Entity type (e.g., faculty, course, room)
        - Operation mode (add, remove, modify)
    - The builder constructs the form in steps:
        - Initializes the <form> with the correct action route
        - Adds input fields specific to the entity type
        - Adjusts fields based on the operation mode 
        - Finalizes the form with a submit button

Key structure:
    - FormBuilder (builder class)
    - build() method
    - Specialized methods:
        - faculty()
        - course()
        - room()
        - lab()
        - timeslot()
        - pattern()

The renderForm() function acts as the director by 
    - Creating a builder instance 
    - Calling build()
    - Rendering the resulting HTML into the page

### How It Solves the Problem

By applying the Builder pattern:
    - Complex form construction logic is centralized in one class
    - The large conditional structure is eliminated, improving readability
    - New entity types or fields can be added without modifying existing logic
    - The UI becomes easier to maintain and extend

This approach improves modularity and keeps the form-generaton logic cleanly separated from the rest of the view code, making the system more scalable and easier to evolve. 

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

## Running Linting, Formatting, and Type Checks

After installing dependencies with:

```bash
uv sync --dev
```

Run the linter:
```
uv run ruff check .
```

Run the formatter:
```
uv run ruff format .
```

Check formatting without changing files:
```
uv run ruff format . --check
```

Run ty:
```
uv run ty check app tests
```

### What to run locally after you make changes

From the repo root:

```bash
uv sync --dev
uv run ruff check .
uv run ruff format .
uv run ty check app tests
uv run pytest --cov=app --cov-branch --cov-report=xml
```

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
