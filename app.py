import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, VALID_CATEGORIES, VALID_FREQUENCIES

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ── Priority mapping: UI label → integer ─────────────────────────────────────
PRIORITY_MAP = {"Low (1)": 1, "Low-Med (2)": 2, "Medium (3)": 3, "High (4)": 4, "Critical (5)": 5}

# ── Owner & Pet setup ────────────────────────────────────────────────────────
st.subheader("Owner & Pet")

col1, col2 = st.columns(2)
with col1:
    owner_name    = st.text_input("Owner name", value="Jordan")
    available_time = st.number_input("Daily time budget (minutes)", min_value=10, max_value=480, value=90)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species  = st.selectbox("Species", ["Dog", "Cat", "Other"])
    age      = st.number_input("Pet age", min_value=0, max_value=30, value=2)

# Initialise session state on first load — runs before Save is ever clicked
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_time=available_time)
if "pet" not in st.session_state:
    st.session_state.pet = Pet(name=pet_name, species=species, age=age)
    st.session_state.owner.add_pet(st.session_state.pet)
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)

# Save updates the owner and adds the pet if new — existing pets and tasks are preserved
if st.button("Save Owner & Pet"):
    st.session_state.owner.name           = owner_name
    st.session_state.owner.available_time = available_time

    existing_names = [p.name for p in st.session_state.owner.get_pets()]
    if pet_name in existing_names:
        st.info(f"'{pet_name}' is already registered — no duplicate added.")
    else:
        new_pet = Pet(name=pet_name, species=species, age=age)
        st.session_state.owner.add_pet(new_pet)
        st.session_state.pet = new_pet
        st.success(f"'{pet_name}' added to {owner_name}'s pets!")

    st.session_state.scheduler = Scheduler(st.session_state.owner)

st.divider()

# ── Add a task ────────────────────────────────────────────────────────────────
st.subheader("Add a Task")

pet_names = [p.name for p in st.session_state.owner.get_pets()]
selected_pet_name = st.selectbox("Add task to", pet_names)
selected_pet = st.session_state.owner.get_pet(selected_pet_name)

col1, col2, col3 = st.columns(3)
with col1:
    task_name = st.text_input("Task name", value="Morning walk")
    category  = st.selectbox("Category", sorted(VALID_CATEGORIES))
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    time_col1, time_col2, time_col3 = st.columns(3)
    with time_col1:
        hour   = st.selectbox("Hour", [f"{h:02d}" for h in range(1, 13)], index=7)
    with time_col2:
        minute = st.selectbox("Min", ["00", "15", "30", "45"])
    with time_col3:
        ampm   = st.selectbox("AM/PM", ["AM", "PM"])
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
    except ValueError as e:
        st.error(str(e))

# ── Task list — shows all pets ────────────────────────────────────────────────
st.divider()
st.subheader("All Tasks")

for pet in st.session_state.owner.get_pets():
    tasks = pet.get_tasks()
    st.markdown(f"**{pet.name}** ({pet.species}) — {len(tasks)} task(s)")
    if tasks:
        st.table([t.to_dict() for t in tasks])
    else:
        st.caption("No tasks yet.")

# ── Generate schedule ─────────────────────────────────────────────────────────
st.divider()
st.subheader("Generate Schedule")

if st.button("Generate Schedule"):
    scheduler = st.session_state.scheduler
    scheduler.generate_schedule()
    if scheduler.schedule:
        st.code(scheduler.explain_plan())
    else:
        st.warning("No tasks could be scheduled. Check your time budget or add tasks first.")
