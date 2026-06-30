from dataclasses import dataclass
from inspect import isawaitable


@dataclass
class PhaseTracker:
    current_phase: str = ""
    current_step: str = ""
    last_phase: str = ""
    last_step: str = ""


async def run_step(tracker, phase, step_name, fn, *args):
    tracker.current_phase = phase
    tracker.current_step = step_name
    result = fn(*args)
    if isawaitable(result):
        result = await result
    tracker.last_phase = phase
    tracker.last_step = step_name
    return result
