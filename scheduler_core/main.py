# scheduler_core/main.py
from typing import Any, Dict, List

from scheduler import Scheduler, CombinedConfig  # (example — adjust to your lib)

def generate_schedules(cfg: Dict[str, Any], limit: int, optimize: bool) -> List[Any]:
    combined = CombinedConfig(**cfg)         # or CombinedConfig.model_validate(cfg)
    combined.limit = limit                   # if limit is a field

    s = Scheduler(combined)
    schedules = []

    for schedule in s.get_models():          # or s.solve(), depends on lib
        schedules.append(schedule)
        if len(schedules) >= limit:
            break

    # If optimize is handled by library flags, apply them here.
    return schedules
