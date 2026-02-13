# Author: Antonio Corona
# Date: 2026-2-13
# app/main.py
from app.config_ops.config_ops import load_config, save_config, pretty_print_config
from app.faculty_management.faculty_management import add_faculty

def main() -> None:
    cfg = load_config("configs/config_dev.json")
    add_faculty(cfg, name="Dr. Rivera", appointment_type="full_time")
    print(pretty_print_config(cfg))
    save_config("configs/config_dev.json", cfg)

if __name__ == "__main__":
    main()
