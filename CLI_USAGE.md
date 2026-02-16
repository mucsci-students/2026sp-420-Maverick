# Scheduler CLI Usage Guide

Author: Antonio Corona<br>
Last updated: 2026-02-16

## Overview

This document explains how to run CLI commands for the Course Constraint Scheduler project.

The CLI allows you to:
- Modify configuration files (faculty, courses, rooms, labs)
- Run the scheduler
- View generated schedules

---

## Environment Setup

Before running CLI commands, activate the virtual environment.

### In GitHub Codespaces / Mac / Linux
```bash
uv sync
source .venv/bin/activate
```

## CLI Entry Point

### Run commands using:

python -m app.main <command> <subcommand> [options]

### To see help:

```bash
python -m app.main -h
python -m app.main config -h
python -m app.main faculty -h
python -m app.main room -h
python -m app.main lab -h
python -m app.main course -h
python -m app.main run -h
```

## Config Commands

### Show Configuration

#### Show a summarized view (default):

```bash
python -m app.main config show --path configs/config_dev.json
```

#### Show full JSON:

```bash
python -m app.main config show --path configs/config_dev.json --full
```

### Save Configuration

```Bash
# This reloads the file and writes it back out
python -m app.main config save --path configs/config_dev.json
```

### Set Schedule Generation Limit

```bash
python -m app.main config set-limit --path configs/config_dev.json --limit 10
```
## Faculty Commands

### Add Faculty

```bash
# Full-time faculty (default times 09:00–17:00 for MON–FRI):
python -m app.main faculty add --path configs/config_dev.json \
  --name "Dr. Rivera" \
  --type full_time
```

#### Adjunct faculty:

```bash
python -m app.main faculty add --path configs/config_dev.json \
  --name "Prof. Chen" \
  --type adjunct
```
#### Add faculty with a single-day time override:

```bash
python -m app.main faculty add --path configs/config_dev.json \
  --name "Prof. Chen" \
  --type adjunct \
  --day TUE \
  --time 13:00-16:00
```

#### Add faculty with preferences (repeatable --pref):

```bash
python -m app.main faculty add --path configs/config_dev.json \
  --name "Dr. Lee" \
  --type full_time \
  --pref CS101:8 \
  --pref CSCI450:5
```

### Remove Faculty

```bash
python -m app.main faculty remove --path configs/config_dev.json \
  --name "Dr. Rivera"
```

### Modify Faculty

```bash
python -m app.main faculty modify --path configs/config_dev.json \
  --name "Prof. Chen" \
  --type full_time \
  --day THU \
  --time 10:00-14:00
```

#### Update preferences (repeatable --pref):

```bash
python -m app.main faculty modify --path configs/config_dev.json \
  --name "Prof. Chen" \
  --pref CS101:6 \
  --pref CS201:9
``` 

#### Update credit limits directly (optional overrides):

```bash
python -m app.main faculty modify --path configs/config_dev.json \
  --name "Prof. Chen" \
  --maximum_credits 12 \
  --minimum_credits 6 \
  --unique_course_limit 2
# Note: If you pass --pref, it will be parsed and sent to modify_faculty. If you do not pass --pref, preferences are left unchanged.
```

## Room Commands

All room commands use --path (defaults to configs/config_dev.json).

### Add Room

```bash
python -m app.main room add --path configs/config_dev.json \
  --name "Room C"
```

### Remove Room

```bash
python -m app.main room remove --path configs/config_dev.json \
  --name "Room C"
``` 

### Modify Room (Rename)

```bash
python -m app.main room modify --path configs/config_dev.json \
  --name "Room B" \
  --new-name "Room B (Renamed)"
``` 

## Lab Commands

All lab commands use --path (defaults to configs/config_dev.json).

### Add Lab

```bash
python -m app.main lab add --path configs/config_dev.json \
  --name "Lab 2"
``` 

### Remove Lab

```bash
python -m app.main lab remove --path configs/config_dev.json \
  --name "Lab 2"
``` 

### Modify Lab (Rename)

```bash
python -m app.main lab modify --path configs/config_dev.json \
  --name "Lab 1" \
  --new-name "Lab 1 (Renamed)"
``` 

## Course Commands

### Add Course

Required fields:

--id

--credits

--room

Optional:

--lab

--faculty (repeatable)

```bash
python -m app.main course add --path configs/config_dev.json \
  --id CS201 \
  --credits 3 \
  --room "Room A"
``` 

#### Add with lab:

```bash
python -m app.main course add --path configs/config_dev.json \
  --id CS301 \
  --credits 3 \
  --room "Room B" \
  --lab "Lab 1"
``` 

#### Add with faculty (repeatable):

```bash
python -m app.main course add --path configs/config_dev.json \
  --id CS401 \
  --credits 3 \
  --room "Room A" \
  --faculty "Dr. Smith"
``` 

### Remove Course

```bash
python -m app.main course remove --path configs/config_dev.json \
  --id CS201
``` 

### Modify Course

Optional updates:

--new-id

--credits

--room

--lab

--faculty (repeatable)

--conflicts (repeatable)

```bash
python -m app.main course modify --path configs/config_dev.json \
  --id CS101 \
  --new-id CS101A \
  --credits 4 \
  --room "Room B"
``` 

#### Add/replace faculty list (repeatable):

```bash
python -m app.main course modify --path configs/config_dev.json \
  --id CS101 \
  --faculty "Dr. Smith"
``` 

#### Add conflicts list (repeatable --conflicts):

```bash
python -m app.main course modify --path configs/config_dev.json \
  --id CS101 \
  --conflicts CS102 \
  --conflicts CS201
``` 

## Course Conflict Commands (Dedicated Subcommands)

These commands directly manage conflicts on a course.

### Add Conflict

```bash
# By default, conflicts are symmetric (adds reverse conflict too):
python -m app.main course conflict-add --path configs/config_dev.json \
  --id CS101 \
  --conflict CS102
``` 

#### One-way conflict only:

```bash
python -m app.main course conflict-add --path configs/config_dev.json \
  --id CS101 \
  --conflict CS102 \
  --no-symmetric
``` 

## Remove Conflict

### Symmetric removal (default):

```bash
python -m app.main course conflict-remove --path configs/config_dev.json \
  --id CS101 \
  --conflict CS102
``` 

#### One-way removal only:

```bash
python -m app.main course conflict-remove --path configs/config_dev.json \
  --id CS101 \
  --conflict CS102 \
  --no-symmetric
``` 

## Modify Conflict

### Replace one conflict with another (default symmetric):

```bash
python -m app.main course conflict-modify --path configs/config_dev.json \
  --id CS101 \
  --old CS102 \
  --new CS201
``` 

#### One-way modify only:

```bash
python -m app.main course conflict-modify --path configs/config_dev.json \
  --id CS101 \
  --old CS102 \
  --new CS201 \
  --no-symmetric

``` 

## Run Scheduler

```bash
python -m app.main run --config configs/config_dev.json
``` 

### Example (generate 5 schedules as JSON to a file):

```bash
python -m app.main run --config configs/config_dev.json \
  --limit 5 \
  --format json \
  --output schedules.json \
  --optimize

``` 

## Notes
Most commands mutate the config file on disk: they load config, apply changes, then save.

Default config file for most subcommands is configs/config_dev.json.

If you make a mistake while testing, you can revert a config file with git:
```bash
git checkout -- configs/config_dev.json
``` 