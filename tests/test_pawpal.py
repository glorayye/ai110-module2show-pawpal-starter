import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet, Owner, Scheduler


# ── Existing tests ────────────────────────────────────────────────────────────

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


# ── Sorting ───────────────────────────────────────────────────────────────────

def test_sort_by_time_timed_tasks_before_untimed():
    owner = Owner("Alex", available_time=120)
    pet = Pet("Buddy", species="Dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task("Fetch",    duration=20, priority=3, category="enrichment"))          # no due_time
    pet.add_task(Task("Walk",     duration=30, priority=5, category="walk", due_time="08:00 AM"))
    pet.add_task(Task("Feeding",  duration=10, priority=5, category="feeding", due_time="07:00 AM"))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    sorted_tasks = scheduler.sort_by_time()

    assert sorted_tasks[0].name == "Feeding"   # earliest time first
    assert sorted_tasks[1].name == "Walk"
    assert sorted_tasks[-1].name == "Fetch"    # no due_time goes last


def test_sort_by_time_all_untimed_tasks_returned():
    owner = Owner("Alex", available_time=60)
    pet = Pet("Buddy", species="Dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task("Fetch", duration=20, priority=3, category="enrichment"))
    pet.add_task(Task("Walk",  duration=30, priority=5, category="walk"))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    sorted_tasks = scheduler.sort_by_time()

    assert len(sorted_tasks) == 2


# ── Recurring task renewal ────────────────────────────────────────────────────

def test_daily_task_renews_with_next_day_date():
    pet = Pet("Buddy", species="Dog", age=3)
    pet.add_task(Task("Walk", duration=30, priority=5, category="walk", frequency="daily"))
    pet.complete_task("Walk")

    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    renewed = pet.get_task("Walk")
    assert renewed.completed is False
    assert renewed.due_time == tomorrow


def test_weekly_task_renews_with_seven_day_date():
    pet = Pet("Buddy", species="Dog", age=3)
    pet.add_task(Task("Grooming", duration=40, priority=2, category="grooming", frequency="weekly"))
    pet.complete_task("Grooming")

    next_week = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
    renewed = pet.get_task("Grooming")
    assert renewed.completed is False
    assert renewed.due_time == next_week


def test_as_needed_task_does_not_renew():
    pet = Pet("Buddy", species="Dog", age=3)
    pet.add_task(Task("Vet Visit", duration=60, priority=5, category="other", frequency="as-needed"))
    pet.complete_task("Vet Visit")

    # as-needed task should be gone — no renewal
    tasks = pet.get_tasks()
    assert all(t.name != "Vet Visit" or t.completed for t in tasks)


# ── Conflict detection ────────────────────────────────────────────────────────

def test_detect_cross_pet_conflict():
    owner = Owner("Alex", available_time=120)
    dog = Pet("Buddy", species="Dog", age=3)
    cat = Pet("Whiskers", species="Cat", age=5)
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Breakfast", duration=10, priority=5, category="feeding", due_time="08:00 AM"))
    cat.add_task(Task("Breakfast", duration=5,  priority=5, category="feeding", due_time="08:00 AM"))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "08:00 AM" in warnings[0]
    assert "Buddy" in warnings[0] or "Whiskers" in warnings[0]


def test_detect_same_pet_conflict():
    owner = Owner("Alex", available_time=120)
    pet = Pet("Buddy", species="Dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task("Walk",     duration=30, priority=5, category="walk",    due_time="08:00 AM"))
    pet.add_task(Task("Meds",     duration=5,  priority=4, category="meds",    due_time="08:00 AM"))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Buddy" in warnings[0]


def test_no_conflict_returns_empty_list():
    owner = Owner("Alex", available_time=120)
    pet = Pet("Buddy", species="Dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task("Walk",    duration=30, priority=5, category="walk",    due_time="08:00 AM"))
    pet.add_task(Task("Feeding", duration=10, priority=5, category="feeding", due_time="08:30 AM"))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()

    assert scheduler.detect_conflicts() == []


# ── Budget edge cases ─────────────────────────────────────────────────────────

def test_no_tasks_fit_within_budget():
    owner = Owner("Alex", available_time=10)
    pet = Pet("Buddy", species="Dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task("Walk", duration=30, priority=5, category="walk"))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()

    assert scheduler.schedule == []


def test_tasks_fill_budget_exactly():
    owner = Owner("Alex", available_time=40)
    pet = Pet("Buddy", species="Dog", age=3)
    owner.add_pet(pet)
    pet.add_task(Task("Walk",    duration=30, priority=5, category="walk"))
    pet.add_task(Task("Feeding", duration=10, priority=4, category="feeding"))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()

    assert scheduler.get_remaining_time() == 0
    assert len(scheduler.schedule) == 2


def test_completed_task_excluded_from_schedule():
    owner = Owner("Alex", available_time=60)
    pet = Pet("Buddy", species="Dog", age=3)
    owner.add_pet(pet)
    t = Task("Meds", duration=5, priority=5, category="meds", frequency="as-needed")
    pet.add_task(t)
    t.mark_complete()

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()

    assert t not in scheduler.schedule
