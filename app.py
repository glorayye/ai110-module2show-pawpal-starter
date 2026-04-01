import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, VALID_CATEGORIES, VALID_FREQUENCIES

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ── Priority mapping: UI label → integer ─────────────────────────────────────
PRIORITY_MAP = {"Low (1)": 1, "Low-Med (2)": 2, "Medium (3)": 3, "High (4)": 4, "Critical (5)": 5}

# ── Form counters — incrementing forces a fresh widget render ─────────────────
if "pet_form_key"  not in st.session_state:
    st.session_state.pet_form_key  = 0
if "task_form_key" not in st.session_state:
    st.session_state.task_form_key = 0

# ── Owner & Pet setup ────────────────────────────────────────────────────────
st.subheader("Owner & Pet")

col1, col2 = st.columns(2)
with col1:
    owner_name     = st.text_input("Owner name", placeholder="e.g. Jordan")
    available_time = st.number_input("Daily time budget (minutes)", min_value=10, max_value=480, value=90)
with col2:
    pet_name = st.text_input("Pet name", key=f"pet_name_{st.session_state.pet_form_key}")
    species  = st.selectbox("Species", ["Dog", "Cat", "Other"], key=f"species_{st.session_state.pet_form_key}")
    age      = st.number_input("Pet age", min_value=0, max_value=30, value=0, key=f"age_{st.session_state.pet_form_key}")

# Initialise session state on first load — runs before Save is ever clicked
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name or "Owner", available_time=available_time)
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)

# Save updates the owner and adds the pet if new — existing pets and tasks are preserved
if st.button("Save Owner & Pet"):
    st.session_state.owner.name           = owner_name
    st.session_state.owner.available_time = available_time

    existing_names = [p.name for p in st.session_state.owner.get_pets()]
    if pet_name in existing_names:
        st.info(f"'{pet_name}' is already registered — no duplicate added.")
    elif pet_name.strip():
        new_pet = Pet(name=pet_name, species=species, age=age)
        st.session_state.owner.add_pet(new_pet)
        st.session_state.pet = new_pet
        st.success(f"'{pet_name}' added to {owner_name}'s pets!")
        st.session_state.pet_form_key += 1  # clears pet_name, species, age

    st.session_state.scheduler = Scheduler(st.session_state.owner)

st.divider()

# ── Add a task ────────────────────────────────────────────────────────────────
st.subheader("Add a Task")

pet_names = [p.name for p in st.session_state.owner.get_pets()]

if not pet_names:
    st.info("No pets registered yet. Add a pet above first.")
    st.stop()

selected_pet_name = st.selectbox("Add task to", pet_names)
selected_pet = st.session_state.owner.get_pet(selected_pet_name)

col1, col2, col3 = st.columns(3)
with col1:
    task_name = st.text_input("Task name", key=f"task_name_{st.session_state.task_form_key}")
    category  = st.selectbox("Category", sorted(VALID_CATEGORIES))
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20, key=f"duration_{st.session_state.task_form_key}")
    time_col1, time_col2, time_col3 = st.columns(3)
    with time_col1:
        hour   = st.selectbox("Hour", [f"{h:02d}" for h in range(1, 13)], index=7, key=f"hour_{st.session_state.task_form_key}")
    with time_col2:
        minute = st.selectbox("Min", ["00", "15", "30", "45"], key=f"minute_{st.session_state.task_form_key}")
    with time_col3:
        ampm   = st.selectbox("AM/PM", ["AM", "PM"], key=f"ampm_{st.session_state.task_form_key}")
    due_time = f"{hour}:{minute} {ampm}"
with col3:
    priority  = st.selectbox("Priority", list(PRIORITY_MAP.keys()), index=4)
    frequency = st.selectbox("Frequency", sorted(VALID_FREQUENCIES))

if st.button("Add Task"):
    try:
        task = Task(
            name=task_name,
            duration=int(duration),
            priority=PRIORITY_MAP[priority],
            category=category,
            frequency=frequency,
            due_time=due_time,
        )
        selected_pet.add_task(task)
        st.success(f"'{task_name}' added to {selected_pet.name}'s tasks.")
        st.session_state.task_form_key += 1  # clears task_name, duration, due_time
    except ValueError as e:
        st.error(str(e))

# ── Task list — shows all pets with completion checkboxes ─────────────────────
st.divider()
st.subheader("All Tasks")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    pet_filter = st.selectbox(
        "Filter by pet", ["All pets"] + [p.name for p in st.session_state.owner.get_pets()]
    )
with filter_col2:
    status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])

status_map = {"All": None, "Pending": False, "Completed": True}
filtered = st.session_state.scheduler.filter_tasks(
    completed=status_map[status_filter],
    pet_name=None if pet_filter == "All pets" else pet_filter,
)
filtered_names = {id(t) for t in filtered}

for pet in st.session_state.owner.get_pets():
    tasks = [t for t in pet.get_tasks() if id(t) in filtered_names]
    st.markdown(f"**{pet.name}** ({pet.species}) — {len(tasks)} task(s)")
    if tasks:
        
        for task in tasks:
            col_check, col_info = st.columns([1, 8])
            with col_check:
                checked = st.checkbox(
                    "Done",
                    value=task.completed,
                    key=f"complete_{pet.name}_{task.name}"
                )
                if checked and not task.completed:
                    pet.complete_task(task.name)  # auto-renews daily/weekly tasks
                elif not checked and task.completed:
                    task.mark_incomplete()
            with col_info:
                status = "~~" if task.completed else ""
                st.markdown(
                    f"{status}**{task.name}** — {task.duration} min | "
                    f"{task.category} | {task.frequency} | "
                    f"Priority: {task.priority} | {task.due_time or 'No time set'}{status}"
                )
    else:
        st.caption("No tasks yet.")

# ── Generate schedule ─────────────────────────────────────────────────────────
st.divider()
st.subheader("Generate Schedule")

sort_order = st.radio("Sort schedule by", ["Priority (high → low)", "Due time"], horizontal=True)

if st.button("Generate Schedule"):
    scheduler = st.session_state.scheduler
    scheduler.generate_schedule()

    if scheduler.schedule:
        if sort_order == "Due time":
            sorted_tasks = scheduler.sort_by_time()
            lines = [f"  {'TIME':<12} {'TASK':<22} {'DURATION':<10} {'PRIORITY'}"]
            lines.append("-" * 58)
            for t in sorted_tasks:
                time = t.due_time if t.due_time else "—"
                lines.append(f"  {time:<12} {t.name:<22} {t.duration} min{'':>5} {t.priority}")
            st.code("\n".join(lines))
        else:
            st.code(scheduler.explain_plan())

        conflicts = scheduler.detect_conflicts()
        if conflicts:
            for warning in conflicts:
                st.warning(warning)
    else:
        st.warning("No tasks could be scheduled. Check your time budget or add tasks first.")
