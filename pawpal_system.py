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
        """Create a validated care task with name, duration, priority, category, and frequency."""
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
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self):
        """Reset this task to incomplete so it can be scheduled again."""
        self.completed = False

    def is_high_priority(self) -> bool:
        """Return True if priority is 4 or 5."""
        return self.priority >= 4

    def to_dict(self) -> dict:
        """Return a plain dictionary representation of this task for use in the UI."""
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
        """Create a pet with a name, species, and age."""
        if not name.strip():
            raise ValueError("Pet name cannot be empty.")
        if age < 0:
            raise ValueError("Age cannot be negative.")

        self.name = name.strip()
        self.species = species.strip()
        self.age = age
        self.tasks: list[Task] = []

    def add_task(self, task: Task):
        """Add a task to this pet; raises ValueError if a task with the same name already exists."""
        if any(t.name == task.name for t in self.tasks):
            raise ValueError(f"A task named {task.name!r} already exists.")
        self.tasks.append(task)

    def remove_task(self, task_name: str):
        """Remove a task by name; raises ValueError if not found."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.name != task_name]
        if len(self.tasks) == before:
            raise ValueError(f"No task named {task_name!r} found.")

    def update_task(self, task_name: str, **kwargs):
        """Update one or more fields on a task by name; raises ValueError for unknown fields."""
        for task in self.tasks:
            if task.name == task_name:
                for field, value in kwargs.items():
                    if not hasattr(task, field):
                        raise ValueError(f"Task has no field {field!r}.")
                    setattr(task, field, value)
                return
        raise ValueError(f"No task named {task_name!r} found.")

    def get_task(self, task_name: str) -> Task:
        """Return a single task by name; raises ValueError if not found."""
        for task in self.tasks:
            if task.name == task_name:
                return task
        raise ValueError(f"No task named {task_name!r} found.")

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that have not been marked complete."""
        return [t for t in self.tasks if not t.completed]

    def get_tasks_by_category(self, category: str) -> list[Task]:
        """Return all tasks matching the given category."""
        return [t for t in self.tasks if t.category == category]

    def to_dict(self) -> dict:
        """Return a plain dictionary representation of this pet for use in the UI."""
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
        """Create an owner with a daily time budget in minutes."""
        if not name.strip():
            raise ValueError("Owner name cannot be empty.")
        if available_time <= 0:
            raise ValueError("Available time must be a positive number of minutes.")

        self.name = name.strip()
        self.available_time = available_time    # total minutes available per day
        self.preferences: list[str] = []
        self.pets: list[Pet] = []

    def add_preference(self, pref: str):
        """Add a scheduling preference; silently ignores duplicates and blank strings."""
        if pref.strip() and pref.strip() not in self.preferences:
            self.preferences.append(pref.strip())

    def get_available_time(self) -> int:
        """Return the owner's total daily time budget in minutes."""
        return self.available_time

    def add_pet(self, pet: Pet):
        """Register a pet under this owner; raises ValueError if a pet with the same name exists."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"A pet named {pet.name!r} is already registered.")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str):
        """Remove a pet by name; raises ValueError if not found."""
        before = len(self.pets)
        self.pets = [p for p in self.pets if p.name != pet_name]
        if len(self.pets) == before:
            raise ValueError(f"No pet named {pet_name!r} found.")

    def get_pet(self, pet_name: str) -> Pet:
        """Return a single pet by name; raises ValueError if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        raise ValueError(f"No pet named {pet_name!r} found.")

    def get_pets(self) -> list[Pet]:
        """Return all pets registered to this owner."""
        return list(self.pets)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def to_dict(self) -> dict:
        """Return a plain dictionary representation of this owner for use in the UI."""
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
        """Create a scheduler for the given owner, operating across all their pets."""
        self.owner = owner
        self.schedule: list[Task] = []
        self._skipped: list[Task] = []
        self._generated = False

    def _all_pending_tasks(self) -> list[Task]:
        """Collect all incomplete tasks from every pet; daily tasks always included."""
        return [
            task
            for pet in self.owner.get_pets()
            for task in pet.get_pending_tasks()
            if task.frequency == "daily" or not task.completed
        ]

    def fits_in_time(self, task: Task) -> bool:
        """Return True if adding this task would not exceed the owner's time budget."""
        scheduled_minutes = sum(t.duration for t in self.schedule)
        return scheduled_minutes + task.duration <= self.owner.available_time

    def get_remaining_time(self) -> int:
        """Return how many minutes are left in the owner's daily budget after scheduling."""
        return self.owner.available_time - sum(t.duration for t in self.schedule)

    def filter_by_priority(self) -> list[Task]:
        """Return all pending tasks sorted from highest to lowest priority."""
        return sorted(self._all_pending_tasks(), key=lambda t: t.priority, reverse=True)

    def generate_schedule(self) -> list[Task]:
        """Build the daily plan using a two-pass greedy algorithm; returns the scheduled task list."""
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
        """Convert a numeric priority to a HIGH / MED / LOW label."""
        if priority >= 4:
            return "HIGH"
        if priority == 3:
            return "MED"
        return "LOW"

    def _task_to_pet(self) -> dict:
        """Build an object-id → pet name lookup to correctly handle tasks with shared names."""
        return {
            id(task): pet.name
            for pet in self.owner.get_pets()
            for task in pet.get_tasks()
        }

    def explain_plan(self) -> str:
        """Return a formatted schedule summary; raises RuntimeError if called before generate_schedule."""
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
