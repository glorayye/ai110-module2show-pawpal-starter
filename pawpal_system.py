# pawpal_system.py
# Logic layer for PawPal+ — all backend classes live here.
#
# Classes:
#   Task      — a single care task (walk, feeding, meds, etc.)
#   Pet       — a pet that owns a list of tasks
#   Owner     — the pet owner with daily time constraints and preferences
#   Scheduler — generates a priority-ordered daily plan within the owner's time budget
#
# Future work:
#   Reminder system — filter tasks due within the next hour, sorted by priority,
#   with conflict detection across multiple pets.

VALID_CATEGORIES = {"walk", "feeding", "meds", "grooming", "enrichment", "other"}
VALID_FREQUENCIES = {"daily", "weekly", "as-needed"}


class Task:
    def __init__(self, name: str, duration: int, priority: int, category: str,
                 frequency: str = "daily", due_time: str = ""):
        if not name.strip():
            raise ValueError("Task name cannot be empty.")
        if duration <= 0:
            raise ValueError("Duration must be a positive number of minutes.")
        if not (1 <= priority <= 5):
            raise ValueError("Priority must be between 1 (low) and 5 (high).")
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(sorted(VALID_CATEGORIES))}.")
        if frequency not in VALID_FREQUENCIES:
            raise ValueError(f"Frequency must be one of: {', '.join(sorted(VALID_FREQUENCIES))}.")

        self.name = name.strip()
        self.duration = duration        # minutes
        self.priority = priority        # 1 (low) to 5 (high)
        self.category = category        # walk, feeding, meds, grooming, enrichment, other
        self.frequency = frequency      # daily, weekly, as-needed
        self.due_time = due_time        # e.g. "08:00 AM" — optional, used by future reminder system
        self.completed = False

    def mark_complete(self):
        self.completed = True

    def mark_incomplete(self):
        self.completed = False

    def is_high_priority(self) -> bool:
        return self.priority >= 4

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duration": self.duration,
            "priority": self.priority,
            "category": self.category,
            "frequency": self.frequency,
            "due_time": self.due_time,
            "completed": self.completed,
        }

    def __repr__(self):
        status = "done" if self.completed else "pending"
        return f"Task({self.name!r}, {self.duration}min, priority={self.priority}, {self.frequency}, {status})"


class Pet:
    def __init__(self, name: str, species: str, age: int):
        if not name.strip():
            raise ValueError("Pet name cannot be empty.")
        if age < 0:
            raise ValueError("Age cannot be negative.")

        self.name = name.strip()
        self.species = species.strip()
        self.age = age
        self.tasks: list[Task] = []

    def add_task(self, task: Task):
        if any(t.name == task.name for t in self.tasks):
            raise ValueError(f"A task named {task.name!r} already exists.")
        self.tasks.append(task)

    def remove_task(self, task_name: str):
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.name != task_name]
        if len(self.tasks) == before:
            raise ValueError(f"No task named {task_name!r} found.")

    def update_task(self, task_name: str, **kwargs):
        for task in self.tasks:
            if task.name == task_name:
                for field, value in kwargs.items():
                    if not hasattr(task, field):
                        raise ValueError(f"Task has no field {field!r}.")
                    setattr(task, field, value)
                return
        raise ValueError(f"No task named {task_name!r} found.")

    def get_task(self, task_name: str) -> Task:
        for task in self.tasks:
            if task.name == task_name:
                return task
        raise ValueError(f"No task named {task_name!r} found.")

    def get_tasks(self) -> list[Task]:
        return list(self.tasks)

    def get_pending_tasks(self) -> list[Task]:
        return [t for t in self.tasks if not t.completed]

    def get_tasks_by_category(self, category: str) -> list[Task]:
        return [t for t in self.tasks if t.category == category]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def __repr__(self):
        return f"Pet({self.name!r}, {self.species}, age={self.age}, {len(self.tasks)} task(s))"


class Owner:
    def __init__(self, name: str, available_time: int):
        if not name.strip():
            raise ValueError("Owner name cannot be empty.")
        if available_time <= 0:
            raise ValueError("Available time must be a positive number of minutes.")

        self.name = name.strip()
        self.available_time = available_time    # total minutes available per day
        self.preferences: list[str] = []
        self.pets: list[Pet] = []

    def add_preference(self, pref: str):
        if pref.strip() and pref.strip() not in self.preferences:
            self.preferences.append(pref.strip())

    def get_available_time(self) -> int:
        return self.available_time

    def add_pet(self, pet: Pet):
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"A pet named {pet.name!r} is already registered.")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str):
        before = len(self.pets)
        self.pets = [p for p in self.pets if p.name != pet_name]
        if len(self.pets) == before:
            raise ValueError(f"No pet named {pet_name!r} found.")

    def get_pet(self, pet_name: str) -> Pet:
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        raise ValueError(f"No pet named {pet_name!r} found.")

    def get_pets(self) -> list[Pet]:
        return list(self.pets)

    def get_all_tasks(self) -> list[Task]:
        return [task for pet in self.pets for task in pet.get_tasks()]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "available_time": self.available_time,
            "preferences": list(self.preferences),
            "pets": [p.to_dict() for p in self.pets],
        }

    def __repr__(self):
        return f"Owner({self.name!r}, {self.available_time}min/day, {len(self.pets)} pet(s))"


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: list[Task] = []
        self._skipped: list[Task] = []
        self._generated = False

    def _all_pending_tasks(self) -> list[Task]:
        # Daily tasks are always included; weekly/as-needed only if not yet completed
        return [
            task
            for pet in self.owner.get_pets()
            for task in pet.get_pending_tasks()
            if task.frequency == "daily" or not task.completed
        ]

    def fits_in_time(self, task: Task) -> bool:
        scheduled_minutes = sum(t.duration for t in self.schedule)
        return scheduled_minutes + task.duration <= self.owner.available_time

    def get_remaining_time(self) -> int:
        return self.owner.available_time - sum(t.duration for t in self.schedule)

    def filter_by_priority(self) -> list[Task]:
        return sorted(self._all_pending_tasks(), key=lambda t: t.priority, reverse=True)

    def generate_schedule(self) -> list[Task]:
        self.schedule = []
        self._skipped = []

        # First pass: greedy by priority
        for task in self.filter_by_priority():
            if self.fits_in_time(task):
                self.schedule.append(task)
            else:
                self._skipped.append(task)

        # Second pass: fill remaining time with skipped tasks that now fit
        still_skipped = []
        for task in self._skipped:
            if self.fits_in_time(task):
                self.schedule.append(task)
            else:
                still_skipped.append(task)
        self._skipped = still_skipped

        self._generated = True
        return self.schedule

    @staticmethod
    def _priority_label(priority: int) -> str:
        if priority >= 4:
            return "HIGH"
        if priority == 3:
            return "MED"
        return "LOW"

    def _task_to_pet(self) -> dict:
        # keyed by object id to handle tasks with the same name across different pets
        return {
            id(task): pet.name
            for pet in self.owner.get_pets()
            for task in pet.get_tasks()
        }

    def explain_plan(self) -> str:
        if not self._generated:
            raise RuntimeError("Call generate_schedule() before explain_plan().")

        if not self.schedule:
            return "No tasks could be scheduled within the available time."

        total = sum(t.duration for t in self.schedule)
        skipped = self._skipped
        pet_lookup = self._task_to_pet()
        pet_names = ", ".join(p.name for p in self.owner.get_pets())

        divider = "=" * 58
        lines = [
            divider,
            f"  Daily Schedule — {self.owner.name}",
            f"  Pets: {pet_names}",
            f"  Budget: {total} of {self.owner.available_time} min used  |  "
            f"{self.get_remaining_time()} min remaining",
            divider,
            f"  {'TIME':<10} {'TASK':<20} {'PET':<12} {'DURATION':<10} {'PRIORITY':<8} {'CATEGORY'}",
            "-" * 80,
        ]

        for task in sorted(self.schedule, key=lambda t: (t.due_time or "~", -t.priority)):
            time  = task.due_time if task.due_time else "—"
            pet   = pet_lookup.get(id(task), "?")
            label = self._priority_label(task.priority)
            lines.append(
                f"  {time:<10} {task.name:<20} {pet:<12} {task.duration} min"
                f"{'':>5} {label:<8} {task.category}"
            )

        if skipped:
            lines.append("-" * 80)
            lines.append("  Skipped (not enough time):")
            for task in skipped:
                label = self._priority_label(task.priority)
                pet   = pet_lookup.get(id(task), "?")
                lines.append(f"    • {task.name} ({pet}) — {task.duration} min, {label}")

        if self.owner.preferences:
            lines.append("-" * 80)
            lines.append(f"  Notes: {', '.join(self.owner.preferences)}")

        lines.append(divider)
        return "\n".join(lines)
