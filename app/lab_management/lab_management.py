# Authors: Tanner Ness, Jacob Karasow
# Date: 2026-02-15
"""
lab_management.py

Service module for Lab Management operations.

Implements business logic for adding, modifying, and deleting labs
within the scheduler configuration.

Related User Stories:
    A3 — Lab Management
"""

from typing import Any, Dict, List


# -----------------------------
# Internal Helpers
# -----------------------------

"""
Description: get_lab_list takes a config file and returns the labs in the config file.
Params     :
            cfg -> the configuration file.
Returns    :
            A list of labs.
            If it is missing from the config file, returns an empty list.
"""
def get_lab_list(cfg: Dict[str, Any]) -> List[str]:
    return cfg.setdefault("config", {}).setdefault("labs", [])


"""
Description: find_lab_index takes a list of labs and returns if the lab was found in the list or not.
Parameters :
           lab_list -> the list of labs.
           lab_name -> the name of the lab.
Returns    :
           If the lab is found, returns the index.
           If the lab was not found, -1.
"""
def find_lab_index(lab_list: List[str], lab_name: str) -> int:
    name_lower = lab_name.lower()

    for index, lab in enumerate(lab_list):
        # case insensitive
        if lab.lower() == name_lower:
            return index

    return -1

"""
Description: remove_lab_helper removes the given lab from faculty and courses
Parameters :
            cfg -> the configuration file.
            lab -> the lab to remove.
Returns    :
           Nothing.
"""
def remove_lab_helper(cfg: Dict[str, Any], lab: str) -> None:

    config = cfg.get('config', {})

    course_list = config.get('courses',[])

    faculty_list =  config.get('faculty', [])

    lab_lower = lab.lower()

    # Removes any instance(s) of lab in courses -> 'lab' if it exists.
    for course in course_list:

        labs = course.get('lab', [])

        for l in range(len(labs)):
            if labs[l].lower() == lab_lower:
                labs.pop(l)
                break


    # Removes any instance(s) of lab in faculty -> 'lab_preferences' if it exists.
    for faculty in faculty_list:

        lab_prefs = faculty.get('lab_preferences', {})
        
        for l in list(lab_prefs):
            if l.lower() == lab_lower:
                lab_prefs.pop(l, None)
                break



# -----------------------------
# CRUD Operations
# -----------------------------
"""
Description: add_lab adds a lab to the config file.
Parameters :
           cfg -> the configuration file.
           lab -> the lab to add to the configuration file
Returns    :
           Nothing.
           If a lab already exists in lab_list, returns ValueError.
"""
def add_lab(cfg: Dict[str, Any], lab: str) -> None:
    
    lab_list = get_lab_list(cfg)

    index = find_lab_index(lab_list, lab)

    match index:
        case -1:
           lab_list.append(lab)

        case _:
            raise ValueError(f"Lab '{lab}' already exists.")

"""
Description: remove_lab removes a given lab from the config file.
Parameters :
           cgf -> the configuration file.
           lab -> the lab to be removed from the config file.
Returns    :
           Nothing.
           If lab does not exist in lab_list, returns ValueError.
             
"""
def remove_lab(cfg: Dict[str, Any], lab: str) -> None:

    lab_list = get_lab_list(cfg)
    
    index = find_lab_index(lab_list, lab)

    match index:
        
        case -1:
            raise ValueError(f"Lab '{lab}' does not exist.")
        
        case _:
            lab_list.pop(index)
            remove_lab_helper(cfg, lab)

def modify_lab(
    cfg: Dict[str, Any], 
    lab: str, 
    new_name: str
) -> None:

    lab_list = get_lab_list(cfg)

    index = find_lab_index(lab_list, lab)

    # Lab must exist
    if index == -1:
        raise ValueError(f"Lab '{lab}' does not exist.")

    # Prevent duplicate rename
    if find_lab_index(lab_list, new_name) != -1:
        raise ValueError(f"Lab '{new_name}' already exists.")

    # ========== Update Lab Name ==========
    lab_list[index] = new_name

    config = cfg.get("config", {})
    course_list = config.get("courses", [])
    faculty_list = config.get("faculty", [])

    old_lower = lab.lower()

    # ========== Update Lab References in Courses
    for course in course_list:
        labs = course.get("lab", [])
        for i in range(len(labs)):
            if labs[i].lower() == old_lower:
                labs[i] = new_name
                break

    # ========= Update Lab References in Faculty ==========
    for faculty in faculty_list:
        lab_prefs = faculty.get("lab_preferences", {})
        for key in list(lab_prefs.keys()):
            if key.lower() == old_lower:
                lab_prefs[new_name] = lab_prefs.pop(key)
                break
