# Author: Antonio Corona, Jacob Karasow
# Date: 2026-2-13
# app/main.py
import argparse

from app.config_ops.config_ops import load_config, save_config, pretty_print_config, summarize_config
from app.faculty_management.faculty_management import add_faculty, remove_faculty, parse_prefs, modify_faculty
from app.room_management.room_management import add_room, remove_room, modify_room
from app.lab_management.lab_management import add_lab, remove_lab, modify_lab
from app.course_management.course_management import add_course, remove_course, modify_course
from app.scheduler_execution.scheduler_execution import SchedulerExecution


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog = "scheduler-cli")
    sub = parser.add_subparsers(dest = "command")

    # --- config show/save ---
    cfg = sub.add_parser("config", help = "Configuration operations")
    cfg_sub = cfg.add_subparsers(dest = "cfg_cmd")

    show = cfg_sub.add_parser("show", help = "Show configuration")
    show.add_argument("--path", default = "configs/config_dev.json")
    show.add_argument("--full", action = "store_true", help="Show full JSON")

    save = cfg_sub.add_parser("save", help = "Save configuration (no-op if already saved)")
    save.add_argument("--path", default = "configs/config_dev.json")

    set_limit = cfg_sub.add_parser("set-limit", help="Set schedule generation limit in config file")
    set_limit.add_argument("--path", default="configs/config_dev.json")
    set_limit.add_argument("--limit", type=int, required=True)

    # --- faculty add/remove/modify ---
    fac = sub.add_parser("faculty", help = "Faculty operations")
    fac_sub = fac.add_subparsers(dest = "fac_cmd")

    fac_add = fac_sub.add_parser("add", help = "Add a faculty member")
    fac_add.add_argument("--path", default = "configs/config_dev.json")
    fac_add.add_argument("--name", required = True)
    fac_add.add_argument("--type", required = True, choices=["full_time", "adjunct"])
    fac_add.add_argument("--day", default = None)
    fac_add.add_argument("--time", default = None)
    fac_add.add_argument("--pref", action = "append", default=None,
                         help = 'Preference like "CSCI450:8" (repeatable)')

    fac_rm = fac_sub.add_parser("remove", help = "Remove a faculty member")
    fac_rm.add_argument("--path", default = "configs/config_dev.json")
    fac_rm.add_argument("--name", required = True)

    fac_mod = fac_sub.add_parser("modify", help = "Modify a faculty member")
    fac_mod.add_argument("--path", default = "configs/config_dev.json")
    fac_mod.add_argument("--name", required = True)
    fac_mod.add_argument("--type", choices = ["full_time", "adjunct"])
    fac_mod.add_argument("--day")
    fac_mod.add_argument("--time")
    fac_mod.add_argument("--pref", action = "append")
    fac_mod.add_argument("--maximum_credits", type = int)
    fac_mod.add_argument("--minimum_credits", type = int)
    fac_mod.add_argument("--unique_course_limit", type = int)

    # --- room add/remove/modify ---
    room = sub.add_parser("room", help = "Room operations")
    room_sub = room.add_subparsers(dest = "room_cmd")

    room_add = room_sub.add_parser("add", help = "add a room")
    room_add.add_argument("--path", default = "configs/config_dev.json")
    room_add.add_argument("--name", required = True)

    room_rm = room_sub.add_parser("remove", help = "Remove a room")
    room_rm.add_argument("--path", default = "configs/config_dev.json")
    room_rm.add_argument("--name", required = True)

    room_mod = room_sub.add_parser("modify", help = "Modify a room")
    room_mod.add_argument("--path", default = "configs/config_dev.json")
    room_mod.add_argument("--name", required = True)
    room_mod.add_argument("--new-name", required = True)

    # --- lab add/remove/modify ---
    lab = sub.add_parser("lab", help = "Lab operations")
    lab_sub = lab.add_subparsers(dest = "lab_cmd")

    lab_add = lab_sub.add_parser("add")
    lab_add.add_argument("--path", default = "configs/config_dev.json")
    lab_add.add_argument("--name", required = True)

    lab_rm = lab_sub.add_parser("remove")
    lab_rm.add_argument("--path", default = "configs/config_dev.json")
    lab_rm.add_argument("--name", required = True)

    lab_mod = lab_sub.add_parser("modify")
    lab_mod.add_argument("--path", default = "configs/config_dev.json")
    lab_mod.add_argument("--name", required = True)
    lab_mod.add_argument("--new-name", required = True)

    # --- course add/remove/modify ---
    course = sub.add_parser("course", help="Course operations")
    course_sub = course.add_subparsers(dest="course_cmd")

    course_add = course_sub.add_parser("add")
    course_add.add_argument("--path", default="configs/config_dev.json")
    course_add.add_argument("--id", required=True)
    course_add.add_argument("--credits", type=int, required=True)
    course_add.add_argument("--room", required=True)
    course_add.add_argument("--lab")
    course_add.add_argument("--faculty", action="append")

    course_rm = course_sub.add_parser("remove")
    course_rm.add_argument("--path", default="configs/config_dev.json")
    course_rm.add_argument("--id", required=True)

    course_mod = course_sub.add_parser("modify")
    course_mod.add_argument("--path", default="configs/config_dev.json")
    course_mod.add_argument("--id", required=True)
    course_mod.add_argument("--new-id")
    course_mod.add_argument("--credits", type=int)
    course_mod.add_argument("--room")
    course_mod.add_argument("--lab")
    course_mod.add_argument("--faculty", action="append")
    course_mod.add_argument("--conflicts", action="append")

    # --- run scheduler ---
    run = sub.add_parser("run", help="Run the scheduler")
    run.add_argument("--config", default="configs/config_dev.json")
    run.add_argument("--limit", type=int)
    run.add_argument("--format", choices=["csv", "json"], default="csv")
    run.add_argument("--output", default="schedules.csv")
    run.add_argument("--optimize", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "config" and args.cfg_cmd is None:
        parser.parse_args(["config", "-h"])
        return

    if args.command == "faculty" and args.fac_cmd is None:
        parser.parse_args(["faculty", "-h"])
        return
    
    if args.command == "room" and args.room_cmd is None:
        parser.parse_args(["room", "-h"])
        return 
    
    if args.command == "lab" and args.lab_cmd is None:
        parser.parse_args(["lab", "-h"])
        return

    if args.command == "course" and args.course_cmd is None:
        parser.parse_args(["course", "-h"])
        return

    # CONFIG SHOW
    if args.command == "config" and args.cfg_cmd == "show":
        cfg = load_config(args.path)
        print(pretty_print_config(cfg) if args.full else summarize_config(cfg))
        return

    # CONFIG SAVE (just rewrite file from current disk state)
    if args.command == "config" and args.cfg_cmd == "save":
        cfg = load_config(args.path)
        save_config(args.path, cfg)
        print(f"Saved {args.path}")
        return

    # CONFIG SET-LIMIT (persist to disk)
    if args.command == "config" and args.cfg_cmd == "set-limit":
        cfg = load_config(args.path)

        if args.limit <= 0:
            raise ValueError("limit must be a positive integer")

        cfg["limit"] = args.limit
        save_config(args.path, cfg)
        print(f"Updated limit to {args.limit} in {args.path}")
        return


    # FACULTY ADD
    if args.command == "faculty" and args.fac_cmd == "add":
        cfg = load_config(args.path)
        prefs = parse_prefs(args.pref)  # converts ["CSCI450:8"] -> list[dict]
        add_faculty(cfg, args.name, args.type, day=args.day, time_range=args.time, prefs=prefs)
        save_config(args.path, cfg)
        print(f"Added faculty {args.name}")
        return

    # FACULTY REMOVE
    if args.command == "faculty" and args.fac_cmd == "remove":
        cfg = load_config(args.path)
        remove_faculty(cfg, args.name)
        save_config(args.path, cfg)
        print(f"Removed faculty {args.name}")
        return
    
    # Faculty Modify
    if args.command == "faculty" and args.fac_cmd == "modify":
        cfg = load_config(args.path)
        prefs = parse_prefs(args.pref) if args.pref else None
        modify_faculty(
            cfg,
            args.name,
            appointment_type = args.type,
            day = args.day,
            time_range = args.time,
            prefs = prefs,
            maximum_credits = args.maximum_credits,
            minimum_credits = args.minimum_credits,
            unique_course_limit = args.unique_course_limit,

        )
        save_config(args.path, cfg)
        print(f"Modified faculty {args.name}")
        return

    # Room add
    if args.command == "room" and args.room_cmd == "add":
        cfg = load_config(args.path)
        add_room(cfg, args.name)
        save_config(args.path, cfg)
        print(f"Added room {args.name}")
        return

    # Room remove
    if args.command == "room" and args.room_cmd == "remove":
        cfg = load_config(args.path)
        remove_room(cfg, args.name)
        save_config(args.path, cfg)
        print(f"Removed room {args.name}")
        return

    # Room modify
    if args.command == "room" and args.room_cmd == "modify":
        cfg = load_config(args.path)
        modify_room(cfg, args.name, args.new_name)
        save_config(args.path, cfg)
        print(f"Renamed room {args.name} -> {args.new_name}")
        return

    # Lab add
    if args.command == "lab" and args.lab_cmd == "add":
        cfg = load_config(args.path)
        add_lab(cfg, args.name)
        save_config(args.path, cfg)
        print(f"Added lab {args.name}")
        return

    # Lab remove
    if args.command == "lab" and args.lab_cmd == "remove":
        cfg = load_config(args.path)
        remove_lab(cfg, args.name)
        save_config(args.path, cfg)
        print(f"Removed lab {args.name}")
        return

    # Lab modify
    if args.command == "lab" and args.lab_cmd == "modify":
        cfg = load_config(args.path)
        modify_lab(cfg, args.name, args.new_name)
        save_config(args.path, cfg)
        print(f"Renamed lab {args.name} -> {args.new_name}")
        return

    # Course add
    if args.command == "course" and args.course_cmd == "add":
        cfg = load_config(args.path)
        add_course(cfg, 
                   args.id, 
                   args.credits, 
                   args.room,
                   lab = args.lab,
                   faculty = args.faculty
        )
        save_config(args.path, cfg)
        print(f"Added course {args.id}")
        return

    # Course remove
    if args.command == "course" and args.course_cmd == "remove":
        cfg = load_config(args.path)
        remove_course(cfg, args.id)
        save_config(args.path, cfg)
        print(f"Removed course {args.id}")
        return

    # Course modify 
    if args.command == "course" and args.course_cmd == "modify":
        cfg = load_config(args.path)
        modify_course (
            cfg, 
            args.id, 
            new_course_id = args.new_id, 
            credits = args.credit, 
            room = args.room, 
            lab = args.lab, 
            faculty = args.faculty, 
            conflicts = args.conflicts, 
        )
        save_config(args.path, cfg)
        print(f"Modified course {args.id}")
        return

    # RUN SCHEDULER
    if args.command == "run":
        cfg = load_config(args.config)

        limit = args.limit if args.limit is not None else cfg.get("limit", 10)

        exec = SchedulerExecution(
            config_file=args.config,
            limit=limit,
            output_format=args.format,
            output_file=args.output,
            optimize=args.optimize,
        )
        exec.run()
        return


if __name__ == "__main__":
    main()

