# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
I have four classes: 
Owner (stores name, time available), 
Pet (stores name, species, tasks list), 
Task (stores name, duration, priority, category), 
Scheduler (takes an owner and pet, applies constraints, and produces an ordered task list)

- What classes did you include, and what responsibilities did you assign to each?
Pet → owns add_task(), remove_task()
Task → holds duration, priority, category
Scheduler → owns the schedule() logic
Owner → holds name, available time, preferences

**c. Class Diagram**

```mermaid
classDiagram
    class Owner {
        +String name
        +int available_time
        +List~String~ preferences
        +add_preference(pref: String)
        +get_available_time() int
    }

    class Pet {
        +String name
        +String species
        +int age
        +List~Task~ tasks
        +add_task(task: Task)
        +remove_task(task_name: String)
        +get_tasks() List~Task~
    }

    class Task {
        +String name
        +int duration
        +int priority
        +String category
        +bool completed
        +mark_complete()
        +is_high_priority() bool
    }

    class Scheduler {
        +Owner owner
        +Pet pet
        +List~Task~ schedule
        +generate_schedule() List~Task~
        +filter_by_priority() List~Task~
        +fits_in_time(task: Task) bool
        +explain_plan() String
    }

    Owner "1" --> "1" Pet : owns
    Pet "1" o-- "many" Task : has
    Scheduler "1" --> "1" Owner : uses
    Scheduler "1" --> "1" Pet : uses
```

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
