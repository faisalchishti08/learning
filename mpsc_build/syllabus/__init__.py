"""Ordered registry of MPSC subjects. Each module exports SUBJECT (a dict)."""
import importlib

# Order drives hub display.
_MODULES = [
    "history", "geography", "polity", "economy", "environment",
    "science_tech", "society", "international_relations", "internal_security",
    "ethics", "csat", "language", "essay", "current_affairs",
    "interview", "geography_optional",
]


def load_all():
    subjects = []
    for name in _MODULES:
        try:
            mod = importlib.import_module(f"mpsc_build.syllabus.{name}")
        except ModuleNotFoundError:
            continue  # module not authored yet — skipped until its task lands
        subjects.append(mod.SUBJECT)
    return subjects
