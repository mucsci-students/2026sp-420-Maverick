# Author: Tanner Ness
# Date: 2026-02-15
"""
room_management.py

Service module for Room Management operations.

Implements business logic for adding, modifying, and deleting rooms
within the scheduler configuration.

Related User Stories:
    A4 — Room Management
"""

from typing import Any, Dict, List


# -----------------------------
# Internal Helpers
# -----------------------------

"""
Description: get_room_list takes a config file and returns the rooms in the config file.
Params     :
            cfg -> the configuration file.
Returns    :
            A list of rooms.
            If it is missing from the config file, returns an empty list.
"""


def get_room_list(cfg: Dict[str, Any]) -> List[str]:
    return cfg.setdefault("config", {}).setdefault("rooms", [])


"""
Description: find_room_index takes a list of rooms and returns if the room was found in the list or not.
Parameters :
           room_list -> the list of rooms.
           room_name -> the name of the room.
Returns    :
           If the room is found, returns the index.
           If the room was not found, -1.
"""


def find_room_index(room_list: List[str], room_name: str) -> int:
    name_lower = room_name.lower()

    for index, room in enumerate(room_list):
        # case insensitive
        if room.lower() == name_lower:
            return index

    return -1


"""
Description: remove_room_helper removes the given room from faculty and courses
Parameters :
            cfg -> the configuration file.
            room -> the room to remove.
Returns    :
           Nothing.
"""


def remove_room_helper(cfg: Dict[str, Any], room: str) -> None:

    config = cfg.get("config", {})

    course_list = config.get("courses", [])

    faculty_list = config.get("faculty", [])

    room_lower = room.lower()

    # Removes any instance(s) of room in courses -> 'room' if it exists.
    for course in course_list:
        rooms = course.get("room", [])

        for r in range(len(rooms)):
            if rooms[r].lower() == room_lower:
                rooms.pop(r)
                break

    # Removes any instance(s) of room in faculty -> 'room_preferences' if it exists.
    for faculty in faculty_list:
        room_prefs = faculty.get("room_preferences", {})

        for r in list(room_prefs):
            if r.lower() == room_lower:
                room_prefs.pop(r, None)
                break


# -----------------------------
# CRUD Operations
# -----------------------------
"""
Description: add_room adds a room to the config file.
Parameters :
           cfg -> the configuration file.
           room -> the room to add to the configuration file
Returns    :
           Nothing.
           If room already exists in room_list, returns ValueError.
"""


def add_room(cfg: Dict[str, Any], room: str) -> None:

    room_list = get_room_list(cfg)

    index = find_room_index(room_list, room)

    match index:
        case -1:
            room_list.append(room)

        case _:
            raise ValueError(f"Room '{room}' already exists.")


"""
Description: remove_room removes a given room from the config file.
Parameters :
           cgf -> the configuration file.
           room -> the room to be removed from the config file.
Returns    :
           Nothing.
           If room does not exist in room_list, returns ValueError.
             
"""


def remove_room(cfg: Dict[str, Any], room: str) -> None:

    room_list = get_room_list(cfg)

    index = find_room_index(room_list, room)

    match index:
        case -1:
            raise ValueError(f"Room '{room}' does not exist.")

        case _:
            room_list.pop(index)
            remove_room_helper(cfg, room)


def modify_room(cfg: Dict[str, Any], room: str, new_name: str) -> None:

    room_list = get_room_list(cfg)
    index = find_room_index(room_list, room)

    # Checks to see if room exists
    if index == -1:
        raise ValueError(f"Room '{room}' does not exist.")

    # Prevent duplicate rename
    if find_room_index(room_list, new_name) != -1:
        raise ValueError(f"Room '{new_name}' already exists.")

    # ========== Update Room Name ==========
    room_list[index] = new_name

    config = cfg.get("config", {})
    course_list = config.get("courses", [])
    faculty_list = config.get("faculty", [])

    old_lower = room.lower()

    # ========== Update Room References in Courses ==========
    for course in course_list:
        rooms = course.get("room", [])
        for i in range(len(rooms)):
            if rooms[i].lower() == old_lower:
                rooms[i] = new_name
                break

    # ========== Update Room References in Faculty ==========
    for faculty in faculty_list:
        room_prefs = faculty.get("room_preferences", {})
        for key in list(room_prefs.keys()):
            if key.lower() == old_lower:
                room_prefs[new_name] = room_prefs.pop(key)
                break
