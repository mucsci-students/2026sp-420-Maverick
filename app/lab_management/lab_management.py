# Author: Tanner Ness
# Date: 2026-02-10
"""
lab_management.py

Service module for Lab Management operations.

Implements business logic for adding, modifying, and deleting labs
within the scheduler configuration.

Related User Stories:
    A3 — Lab Management
"""

from typing import Any, Dict, List, Optional


# -----------------------------
# Internal Helpers
# -----------------------------

"""
Description: get_lab_list takes a config file and returns the labs in the config file.
Params     :
            cfg -> the configuration file.
Returns    :
            A list of labs.
            If it is missing from the file, returns an empty list.
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
def find_lab_index(lab_list: List[str], lab_name: str) -> Optional[int]:
    name_lower = lab_name.lower()

    for index, lab in enumerate(lab_list):
        # case insensitive
        if lab.lower() == name_lower:
            return index

    return -1

"""
Description: removes the given lab from faculty and courses
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

    # Removes the instance of lab in courses -> 'lab' if it exists.
    for course in course_list:

        labs = course.get('lab', [])

        for l in range(len(labs)):
            if labs[l].lower() == lab_lower:
                labs.pop(l)
                break


    # Removes the instance of lab in faculty -> 'lab_preferences' if it exists.
    for faculty in faculty_list:

        lab_prefs = faculty.get('lab_preferences', {})
        
        for r in list(lab_prefs):
            if r.lower() == lab_lower:
                lab_prefs.pop(r, None)
                break



# -----------------------------
# CRUD Operations
# -----------------------------
"""
Description: Add a lab to the config file.
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
Description: Removes a given lab from the config file.
Parameters :
           cgf -> the configuration file.
           lab -> the lab to be removed from the config file.
Returns    :
           Nothing.
           If lab_list is empty, returns LookupError.
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
