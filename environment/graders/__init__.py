"""
ContractEnv Phase 3 — Graders Package
=======================================

Exports all three task graders and a factory function that returns
the correct grader for a given task ID.
"""

from __future__ import annotations

from typing import Union

from .task1_grader import GradeResult, Task1Grader
from .task2_grader import Task2Grader
from .task3_grader import Task3Grader

__all__ = [
    "GradeResult",
    "Task1Grader",
    "Task2Grader",
    "Task3Grader",
    "get_grader",
]


def get_grader(task_id: str) -> Union[Task1Grader, Task2Grader, Task3Grader]:
    """Return the correct grader instance for *task_id*.

    Parameters
    ----------
    task_id : str
        One of ``"task1"``, ``"task2"``, ``"task3"``.

    Returns
    -------
    Task1Grader | Task2Grader | Task3Grader

    Raises
    ------
    ValueError
        If *task_id* is not recognised.
    """
    graders = {
        "task1": Task1Grader,
        "task2": Task2Grader,
        "task3": Task3Grader,
    }
    cls = graders.get(task_id)
    if cls is None:
        raise ValueError(
            f"Unknown task_id '{task_id}'. "
            f"Expected one of: {sorted(graders)}"
        )
    return cls()
