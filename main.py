# main.py
# Temporary testing ground — run with: python main.py

from pawpal_system import Task, Pet, Owner, Scheduler

# ── 1. Setup ─────────────────────────────────────────────────────────────────
owner = Owner(name="Alex", available_time=90)
owner.add_preference("morning walks preferred")

dog = Pet(name="Buddy", species="Dog", age=3)
cat = Pet(name="Whiskers", species="Cat", age=5)
owner.add_pet(dog)
owner.add_pet(cat)

# ── 2. Add tasks ─────────────────────────────────────────────────────────────
dog.add_task(Task("Morning Walk",  duration=30, priority=5, category="walk",        frequency="daily",     due_time="08:00 AM"))
dog.add_task(Task("Breakfast",     duration=10, priority=5, category="feeding",     frequency="daily",     due_time="08:30 AM"))
dog.add_task(Task("Heartworm Med", duration=5,  priority=4, category="meds",        frequency="weekly"))
dog.add_task(Task("Grooming",      duration=40, priority=2, category="grooming",    frequency="weekly"))
dog.add_task(Task("Fetch",         duration=25, priority=4, category="enrichment",  frequency="daily"))

cat.add_task(Task("Breakfast",     duration=5,  priority=5, category="feeding",     frequency="daily",     due_time="08:30 AM"))
cat.add_task(Task("Litter Box",    duration=5,  priority=4, category="other",       frequency="daily"))
cat.add_task(Task("Playtime",      duration=15, priority=3, category="enrichment",  frequency="as-needed"))

# ── 5. Generate schedule ──────────────────────────────────────────────────────
scheduler = Scheduler(owner)

print("\n>>> Heartworm Med is PENDING (weekly task, not yet given)")
scheduler.generate_schedule()
print(scheduler.explain_plan())

tasks_to_complete = [
    dog.get_task("Heartworm Med"),
]

for task in tasks_to_complete:
    task.mark_complete()
    print(f"\n>>> '{task.name}' marked COMPLETE — regenerating schedule")
    scheduler.generate_schedule()
    print(scheduler.explain_plan())

# ── 7. Test edge cases ────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("EDGE CASES")
print("=" * 50)

# Duplicate task
try:
    dog.add_task(Task("Morning Walk", duration=30, priority=5, category="walk"))
except ValueError as e:
    print(f"Duplicate task blocked:     {e}")

# Bad priority
try:
    Task("Bad Task", duration=10, priority=9, category="walk")
except ValueError as e:
    print(f"Bad priority blocked:       {e}")

# Bad category
try:
    Task("Bad Task", duration=10, priority=3, category="nap")
except ValueError as e:
    print(f"Bad category blocked:       {e}")

# Bad frequency
try:
    Task("Bad Task", duration=10, priority=3, category="walk", frequency="monthly")
except ValueError as e:
    print(f"Bad frequency blocked:      {e}")

# explain_plan before generate_schedule
try:
    Scheduler(owner).explain_plan()
except RuntimeError as e:
    print(f"Early explain_plan blocked: {e}")

# update_task with unknown field
try:
    dog.update_task("Morning Walk", colour="blue")
except ValueError as e:
    print(f"Bad field blocked:          {e}")

print("\nAll checks passed.")
