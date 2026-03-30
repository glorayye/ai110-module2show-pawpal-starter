class Task:
    def __init__(self, name: str, duration: int, priority: int, category: str):
        self.name = name
        self.duration = duration      # minutes
        self.priority = priority      # 1 (low) to 5 (high)
        self.category = category      # e.g. "walk", "feeding", "meds", "grooming", "enrichment"
        self.completed = False

    def mark_complete(self):
        self.completed = True

    def is_high_priority(self) -> bool:
        return self.priority >= 4

    def __repr__(self):
        return f"Task({self.name!r}, {self.duration}min, priority={self.priority})"


class Pet:
    def __init__(self, name: str, species: str, age: int):
        self.name = name
        self.species = species
        self.age = age
        self.tasks: list[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    def remove_task(self, task_name: str):
        self.tasks = [t for t in self.tasks if t.name != task_name]

    def update_task(self, task_name: str, **kwargs):
        for task in self.tasks:
            if task.name == task_name:
                for field, value in kwargs.items():
                    if hasattr(task, field):
                        setattr(task, field, value)
                return
        raise ValueError(f"No task named {task_name!r} found.")

    def get_tasks(self) -> list[Task]:
        return self.tasks

    def __repr__(self):
        return f"Pet({self.name!r}, {self.species}, age={self.age})"


class Owner:
    def __init__(self, name: str, available_time: int):
        self.name = name
        self.available_time = available_time   # total minutes available per day
        self.preferences: list[str] = []

    def add_preference(self, pref: str):
        self.preferences.append(pref)

    def get_available_time(self) -> int:
        return self.available_time

    def __repr__(self):
        return f"Owner({self.name!r}, {self.available_time}min/day)"


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.schedule: list[Task] = []

    def fits_in_time(self, task: Task) -> bool:
        scheduled_minutes = sum(t.duration for t in self.schedule)
        return scheduled_minutes + task.duration <= self.owner.available_time

    def filter_by_priority(self) -> list[Task]:
        return sorted(self.pet.get_tasks(), key=lambda t: t.priority, reverse=True)

    def generate_schedule(self) -> list[Task]:
        self.schedule = []
        for task in self.filter_by_priority():
            if self.fits_in_time(task):
                self.schedule.append(task)
        return self.schedule

def explain_plan(self) -> str:
        if not self.schedule:
            return "No tasks could be scheduled within the available time."

        total = sum(t.duration for t in self.schedule)
        skipped = [t for t in self.pet.get_tasks() if t not in self.schedule]

        lines = [
            f"Scheduled {len(self.schedule)} task(s) for {self.pet.name} "
            f"using {total} of {self.owner.available_time} available minutes.",
            "",
            "Included tasks (highest priority first):",
        ]
        for task in self.schedule:
            lines.append(f"  - {task.name} ({task.duration}min, priority {task.priority})")

        if skipped:
            lines.append("")
            lines.append("Skipped tasks (not enough time remaining):")
            for task in skipped:
                lines.append(f"  - {task.name} ({task.duration}min, priority {task.priority})")

        return "\n".join(lines)
