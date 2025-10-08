# 🧩 Task Management System — Multi-Agent State Management Exercise

## 🎯 Exercise Overview

Transform this starter code into a complete **project management system**!
You'll implement **state management with Pydantic models** and create **specialized agents** for task management.

---

## 📋 Exercise Tasks

### 🧱 Task 1: Implement Pydantic Models

**File:** `task_management_starter.py`

---

#### 1.1 Complete the `Task` Model

```python
class Task(BaseModel):
    task_id: str
    title: str
    description: str
    status: str  # todo, in_progress, review, done
    priority: str  # low, medium, high, critical
    assignee: Optional[str]  # member_id
    due_date: datetime
```

**Add validators:**

* `status` must be one of: `todo`, `in_progress`, `review`, `done`
* `priority` must be one of: `low`, `medium`, `high`, `critical`

---

#### 1.2 Complete the `TeamMember` Model

```python
class TeamMember(BaseModel):
    member_id: str
    name: str
    role: str
    skills: List[str]
    current_tasks: List[str]  # task_ids
```

**Add property:**

* `task_count`: returns the number of current tasks

---

#### 1.3 Complete the `Project` Model

```python
class Project(BaseModel):
    project_id: str
    name: str
    description: str
    status: str  # planning, active, on_hold, completed
    tasks: List[str]  # task_ids
    team_members: List[str]  # member_ids
```

**Add validators and properties:**

* `status` must be one of: `planning`, `active`, `on_hold`, `completed`
* `completion_percentage`: calculates % of completed tasks
* `overdue_tasks`: returns list of overdue tasks

---

### 🧩 Task 2: Implement `ProjectState`

**File:** `task_management_starter.py`

Complete the `ProjectState` class with:

**Fields:**

* `projects`, `team_members`, `tasks` — all `Dict`

**Methods:**

* `add_project(project: Project)`
* `add_team_member(member: TeamMember)`
* `add_task(task: Task)`
* `update_task_status(task_id: str, status: str)`
* `get_project_status()`: returns summary string

---

### 🤖 Task 3: Complete the Agents

**File:** `task_management_starter.py`

#### 3.1 Enhance `TaskAgent`

* Improve the prompt for task management
* Return actual counts for `pending_tasks` and `overdue_tasks`

#### 3.2 Enhance `ResourceAgent`

* Improve the prompt for resource management
* Return actual `team_members` count and `available_capacity`

#### 3.3 Implement `ProgressAgent`

* Tracks project progress and metrics
* Provides progress analysis and recommendations

---

### 🏗️ Task 4: Complete `ProjectManagementSystem`

**File:** `task_management_starter.py`

#### 4.1 Initialize Sample Data

In `_initialize_sample_data()`:

* 3 team members with different roles and skills
* 8–10 tasks with different statuses and priorities
* 1–2 projects with associated tasks and team members

#### 4.2 Add `ProgressAgent`

* Register the new agent in the agents dictionary

#### 4.3 Implement State Display

`display_project_state()` should show:

* Number of projects and their statuses
* Team member count and task distribution
* Task statistics (total, completed, overdue)

#### 4.4 Implement Task Completion Simulation

`simulate_task_completion()` should:

* Mark a random task as completed
* Update the project state
* Show before/after state

---

## 🛠️ Setup Instructions

### 1️⃣ Install Dependencies

```bash
pip install semantic-kernel==1.36.2 python-dotenv pydantic
```

### 2️⃣ Configure Environment

Create a `.env` file with your Azure OpenAI credentials:

```env
AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/completions?api-version=2025-01-01-preview
AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your-api-key
AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=your-deployment-name
```

### 3️⃣ Run Starter Code

```bash
python task_management_starter.py
```

---

## 💡 Implementation Hints

### For Pydantic Models

```python
@validator('status')
def validate_status(cls, v):
    allowed = ['todo', 'in_progress', 'review', 'done']
    if v not in allowed:
        raise ValueError(f'Status must be one of {allowed}')
    return v

@property
def task_count(self) -> int:
    return len(self.current_tasks)
```

---

### For ProjectState

```python
def add_task(self, task: Task) -> None:
    self.tasks[task.task_id] = task

def update_task_status(self, task_id: str, status: str) -> bool:
    if task_id in self.tasks:
        self.tasks[task_id].status = status
        return True
    return False
```

---

### For Sample Data

Create realistic sample data:

* **Team Members:** Project Manager, Developer, Designer
* **Tasks:** Varying priorities and due dates
* **Projects:** Different stages of completion

---

## 🧪 Testing Your Solution

After completing all tasks, your system should:

* Display project state with actual data
* Process all scenarios with detailed agent responses
* Simulate state changes during task completion
* Track progress metrics across projects
* Handle resource allocation recommendations

---

## 📊 Expected Output

```text
📋 PROJECT MANAGEMENT EXERCISE
==================================================

📊 CURRENT PROJECT STATE:
Projects: 2 (1 active, 1 planning)
Team Members: 3
Total Tasks: 10 (4 completed, 2 overdue)
Completion Rate: 40%

🎯 SCENARIO 1: We have 3 tasks overdue...
🤖 Consulting specialists...

TASKS AGENT:
Analysis: With 3 overdue tasks, I recommend...
📊 Task Stats: 4 pending, 2 overdue

RESOURCES AGENT:
Analysis: Current team capacity is at 70%...
👥 Team: 3 members, 30% available capacity

PROGRESS AGENT:
Analysis: Project is 60% complete but behind schedule...
📈 Metrics: 40% completion, 2 weeks behind
```

---

## ✅ Success Criteria

Your solution is complete when:

* [x] All Pydantic models are implemented with validation
* [x] `ProjectState` manages all entities correctly
* [x] All three agents provide detailed, context-aware analysis
* [x] Sample data initializes the system properly
* [x] State changes are visible during simulations
* [x] Progress tracking works across all scenarios

---

## 🆘 Need Help?

If you get stuck:

* Review the **Book Store demo** for state management patterns
* Check **Pydantic documentation** for model validation
* Start with simple models and gradually add complexity
* Test each component independently before integrating

---

**Good luck! 🚀**
