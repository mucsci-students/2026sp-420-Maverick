# Author: Ian Swartz
# Date: 2026-02-12
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

import json
from typing import Dict, Any, Optional

# Print Configuration File function -
# Prints a summary of the current schedule data.
def print_config(config_data: Dict[str, Any]) -> None:
    inner_config = config_data.get("config", {})

    print("\n--- Current Scheduler Configuration Summary ---")

    # Iterate through the categories 
    categories = ["faculty", "courses", "rooms", "labs"]
    
    for category in categories:
        items = inner_config.get(category, [])
        count = len(items)
        print(f"{category.capitalize()}: {count} items loaded")
    
    print("-----------------------------------------------\n")


# Save Configuration File function -
# Writes/saves the configuration data to a Json file.
# Uses a try and except for error handling.
def save_config(config_data: Dict[str, Any], filename: str) -> bool:
    try:
        # 'w' used to create and write to a file (write mode)
        # used 'f' for file because "file" seems to be a Python variable
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=4)

        print(f"Saved configuration to: {filename}")
        return True

    except Exception as error:
        print(f"Failed to save file. Error: {error}")
        return False

    
# Load Configuration File function -
# A configuration dictionary from a Json file.
# Uses a try and except for error handling.
def load_config(filename: str) -> Optional[Dict[str, Any]]:
    try:
        # 'r' opens in read mode
        with open(filename, 'r') as f:
            data = json.load(f)

        print(f"Loaded: {filename}")
        return data

    # Exception for if file doesn't exist.
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")

        # Return empty placeholder for each variable.
        return {"config": {"faculty": [], "course": [], "rooms": [], "labs": []}}
    
    # Error for if file isn't a Json file.
    except json.JSONDecodeError:
        print(f"Error: '{filename}' is not a valid JSON file.")
        return
