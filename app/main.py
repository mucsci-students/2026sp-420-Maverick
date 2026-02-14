# Author: Antonio Corona
# Date: 2026-2-13
# app/main.py
# app/main.py
import argparse

from app.config_ops.config_ops import load_config, save_config, pretty_print_config, summarize_config
from app.faculty_management.faculty_management import add_faculty, remove_faculty, parse_prefs
from app.scheduler_execution.scheduler_execution import SchedulerExecution


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scheduler-cli")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- config show/save ---
    cfg = sub.add_parser("config", help="Configuration operations")
    cfg_sub = cfg.add_subparsers(dest="cfg_cmd", required=True)

    show = cfg_sub.add_parser("show", help="Show configuration")
    show.add_argument("--path", default="configs/config_dev.json")
    show.add_argument("--full", action="store_true", help="Show full JSON")

    save = cfg_sub.add_parser("save", help="Save configuration (no-op if already saved)")
    save.add_argument("--path", default="configs/config_dev.json")

    # --- faculty add/remove ---
    fac = sub.add_parser("faculty", help="Faculty operations")
    fac_sub = fac.add_subparsers(dest="fac_cmd", required=True)

    fac_add = fac_sub.add_parser("add", help="Add a faculty member")
    fac_add.add_argument("--path", default="configs/config_dev.json")
    fac_add.add_argument("--name", required=True)
    fac_add.add_argument("--type", required=True, choices=["full_time", "adjunct"])
    fac_add.add_argument("--day", default=None)
    fac_add.add_argument("--time", default=None)
    fac_add.add_argument("--pref", action="append", default=None,
                         help='Preference like "CSCI450:8" (repeatable)')

    fac_rm = fac_sub.add_parser("remove", help="Remove a faculty member")
    fac_rm.add_argument("--path", default="configs/config_dev.json")
    fac_rm.add_argument("--name", required=True)

    # --- run scheduler ---
    run = sub.add_parser("run", help="Run the scheduler")
    run.add_argument("--config", default="configs/config_dev.json")
    run.add_argument("--limit", type=int, default=10)
    run.add_argument("--format", choices=["csv", "json"], default="csv")
    run.add_argument("--output", default="schedules.csv")
    run.add_argument("--optimize", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

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

    # RUN SCHEDULER
    if args.command == "run":
        exec = SchedulerExecution(
            config_file=args.config,
            limit=args.limit,
            output_format=args.format,
            output_file=args.output,
            optimize=args.optimize,
        )
        exec.run()
        return


if __name__ == "__main__":
    main()

