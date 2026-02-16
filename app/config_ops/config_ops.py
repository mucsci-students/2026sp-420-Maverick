# Author: Ian Swartz & Antonio Corona
# Date: 2026-02-14
"""
config_ops.py

Configuration operations module for the scheduler application.

Handles loading, saving, and formatting scheduler configuration files,
as well as generating readable output representations of configuration data.

Related User Stories:
    B1 — Print Configuration File
    B2 — Save Configuration File
    B3 — Load Configuration File
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_CONFIG: Dict[str, Any] = {
    "config": {"faculty": [], "courses": [], "rooms": [], "labs": []}
}

def ensure_defaults(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure required keys exist (shape only; no business rules)."""
    if "config" not in cfg or not isinstance(cfg["config"], dict):
        cfg["config"] = {}

    inner = cfg["config"]
    inner.setdefault("faculty", [])
    inner.setdefault("courses", [])
    inner.setdefault("rooms", [])
    inner.setdefault("labs", [])
    return cfg

def load_config(path: str) -> Dict[str, Any]:
    """
    Load JSON config from disk and normalize base structure.
    If the file does not exist, returns a default empty configuration.
    Raises ValueError for invalid JSON.
    """
    p = Path(path)
    if not p.exists():
        # Return a fresh copy of the default structure
        return json.loads(json.dumps(DEFAULT_CONFIG))

    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file '{path}': {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Config file '{path}' must contain a JSON object at the root.")

    return ensure_defaults(data)

# Print Configuration File function -
# Prints a summary of the current schedule data.
def summarize_config(config_data: Dict[str, Any]) -> None:
    inner_config = config_data.get("config", {})

    print("\n--- Current Scheduler Configuration Summary ---")

    # Iterate through the categories 
    categories = ["faculty", "courses", "rooms", "labs"]
    
    for category in categories:
        items = inner_config.get(category, [])
        count = len(items)
        print(f"{category.capitalize()}: {count} items loaded")
    
    print("-----------------------------------------------\n")

def save_config(path: str, config_data: Dict[str, Any]) -> None:
    """
    Save config dict to disk as JSON.
    Normalizes base structure before saving.
    Raises exceptions for permission/path errors (caller/CLI can catch).
    """
    config_data = ensure_defaults(config_data)
    p = Path(path)
    with p.open("w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

# Save Configuration File function -
# Writes/saves the configuration data to a Json file.
# Uses a try and except for error handling.
# def save_config(config_data: Dict[str, Any], filename: str) -> bool:
    # try:
    #     # 'w' used to create and write to a file (write mode)
    #     # used 'f' for file because "file" seems to be a Python variable
    #     with open(filename, 'w') as f:
    #         json.dump(config_data, f, indent=4)

    #     print(f"Saved configuration to: {filename}")
    #     return True

    # except Exception as error:
    #     print(f"Failed to save file. Error: {error}")
        # return False

    
# Load Configuration File function -
# A configuration dictionary from a Json file.
# Uses a try and except for error handling.
# def load_config(filename: str) -> Optional[Dict[str, Any]]:
#     try:
#         # 'r' opens in read mode
#         with open(filename, 'r') as f:
#             data = json.load(f)

#         print(f"Loaded: {filename}")
#         return data

#     # Exception for if file doesn't exist.
#     except FileNotFoundError:
#         print(f"Error: The file '{filename}' does not exist.")

#         # Return empty placeholder for each variable.
#         return {"config": {"faculty": [], "courses": [], "rooms": [], "labs": []}}
    
#     # Error for if file isn't a Json file.
#     except json.JSONDecodeError:
#         print(f"Error: '{filename}' is not a valid JSON file.")
#         return None
    
def pretty_print_config(config_data: Dict[str, Any]) -> str:
    """Return full human-readable config (pretty JSON)."""
    config_data = ensure_defaults(config_data)
    return json.dumps(config_data, indent=2, ensure_ascii=False)
