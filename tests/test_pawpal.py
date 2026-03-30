import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    t = Task("Walk", duration=30, priority=3, category="walk")
    assert t.completed is False
    t.mark_complete()
    assert t.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Buddy", species="Dog", age=3)
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Walk", duration=30, priority=5, category="walk"))
    assert len(pet.get_tasks()) == 1
