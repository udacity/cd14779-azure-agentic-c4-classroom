import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
load_dotenv("../../../.env")

# Pydantic Models for State Management
class Task(BaseModel):
    """Model representing a task"""
    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    status: str = Field(default="todo", description="Task status")
    priority: str = Field(..., description="Task priority")
    assignee: Optional[str] = Field(None, description="Assigned team member")
    due_date: datetime = Field(..., description="Task due date")
    
    @field_validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['todo', 'in_progress', 'review', 'done']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of {allowed_statuses}')
        return v
    
    @field_validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ['low', 'medium', 'high', 'critical']
        if v not in allowed_priorities:
            raise ValueError(f'Priority must be one of {allowed_priorities}')
        return v
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        return self.status != 'done' and self.due_date < datetime.now()
    
    @property
    def days_until_due(self) -> int:
        """Calculate days until due date"""
        return (self.due_date - datetime.now()).days

class TeamMember(BaseModel):
    """Model representing a team member"""
    member_id: str = Field(..., description="Unique member identifier")
    name: str = Field(..., description="Member name")
    role: str = Field(..., description="Member role")
    skills: List[str] = Field(default_factory=list, description="Member skills")
    current_tasks: List[str] = Field(default_factory=list, description="Assigned task IDs")
    
    @property
    def task_count(self) -> int:
        """Get number of assigned tasks"""
        return len(self.current_tasks)
    
    @property
    def is_available(self) -> bool:
        """Check if member has capacity for more tasks"""
        return self.task_count < 5  # Max 5 tasks per member

class Project(BaseModel):
    """Model representing a project"""
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    status: str = Field(default="planning", description="Project status")
    tasks: List[str] = Field(default_factory=list, description="Project task IDs")
    team_members: List[str] = Field(default_factory=list, description="Project team member IDs")
    
    @field_validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['planning', 'active', 'on_hold', 'completed']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of {allowed_statuses}')
        return v
    
    def completion_percentage(self, task_dict: Dict[str, Task]) -> float:
        """Calculate project completion percentage"""
        if not self.tasks:
            return 0.0
        
        completed_tasks = 0
        for task_id in self.tasks:
            if task_id in task_dict and task_dict[task_id].status == 'done':
                completed_tasks += 1
        
        return (completed_tasks / len(self.tasks)) * 100
    
    def overdue_tasks(self, task_dict: Dict[str, Task]) -> List[str]:
        """Get list of overdue task titles"""
        overdue = []
        for task_id in self.tasks:
            if task_id in task_dict and task_dict[task_id].is_overdue:
                overdue.append(task_dict[task_id].title)
        return overdue

class ProjectState(BaseModel):
    """Central state management for the project"""
    projects: Dict[str, Project] = Field(default_factory=dict, description="All projects")
    team_members: Dict[str, TeamMember] = Field(default_factory=dict, description="All team members")
    tasks: Dict[str, Task] = Field(default_factory=dict, description="All tasks")
    
    def add_project(self, project: Project) -> None:
        """Add or update project"""
        self.projects[project.project_id] = project
    
    def add_team_member(self, member: TeamMember) -> None:
        """Add or update team member"""
        self.team_members[member.member_id] = member
    
    def add_task(self, task: Task) -> None:
        """Add or update task"""
        self.tasks[task.task_id] = task
        
        # Add task to assignee's current tasks if assigned
        if task.assignee and task.assignee in self.team_members:
            if task.task_id not in self.team_members[task.assignee].current_tasks:
                self.team_members[task.assignee].current_tasks.append(task.task_id)
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            return True
        return False
    
    def get_project_status(self) -> str:
        """Get overall project status summary"""
        total_projects = len(self.projects)
        active_projects = len([p for p in self.projects.values() if p.status == 'active'])
        completed_projects = len([p for p in self.projects.values() if p.status == 'completed'])
        
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == 'done'])
        overdue_tasks = len([t for t in self.tasks.values() if t.is_overdue])
        
        return f"""
        📊 PROJECT STATUS SUMMARY:
        Projects: {total_projects} total ({active_projects} active, {completed_projects} completed)
        Tasks: {total_tasks} total ({completed_tasks} completed, {overdue_tasks} overdue)
        Team: {len(self.team_members)} members
        Completion Rate: {(completed_tasks/total_tasks*100) if total_tasks > 0 else 0:.1f}%
        """

class ProjectAgent:
    """Base class for all project agents with shared state access"""
    
    def __init__(self, name: str, role: str, project_state: ProjectState):
        self.name = name
        self.role = role
        self.project_state = project_state
        self.kernel = Kernel()
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
    
    async def process_request(self, request: str) -> Dict:
        """Process project request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

class TaskAgent(ProjectAgent):
    """Agent specializing in task management"""
    
    def __init__(self, project_state: ProjectState):
        super().__init__("Task Manager", "Manage tasks and assignments", project_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle task-related requests"""
        
        prompt = """
        You are an expert task management specialist. Analyze the current task situation and provide recommendations.

        REQUEST: {{$request}}

        CURRENT TASK STATUS:
        {{$task_status}}

        Please provide:
        📋 TASK ANALYSIS:
        - Current task distribution and status
        - Priority assessment
        - Deadline management

        🔄 OPTIMIZATION RECOMMENDATIONS:
        - Task reassignment suggestions
        - Priority adjustments
        - Deadline extensions if needed

        ⚠️ RISK IDENTIFICATION:
        - Potential bottlenecks
        - Overloaded team members
        - Critical path tasks

        Focus on practical, actionable task management strategies.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="task_management",
            plugin_name="tasks",
            prompt=prompt
        )
        
        task_status = self._get_task_status_summary()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            task_status=task_status
        )
        
        return {
            "agent": self.name,
            "analysis": str(result),
            "pending_tasks": self._get_pending_task_count(),
            "overdue_tasks": self._get_overdue_task_count()
        }
    
    def _get_task_status_summary(self) -> str:
        """Generate task status summary"""
        status_count = {}
        priority_count = {}
        
        for task in self.project_state.tasks.values():
            status_count[task.status] = status_count.get(task.status, 0) + 1
            priority_count[task.priority] = priority_count.get(task.priority, 0) + 1
        
        summary = "📊 TASK DISTRIBUTION:\n"
        summary += "Status:\n"
        for status, count in status_count.items():
            summary += f"  - {status}: {count} tasks\n"
        
        summary += "\nPriority:\n"
        for priority, count in priority_count.items():
            summary += f"  - {priority}: {count} tasks\n"
        
        return summary
    
    def _get_pending_task_count(self) -> int:
        """Get count of pending tasks"""
        return len([t for t in self.project_state.tasks.values() if t.status != 'done'])
    
    def _get_overdue_task_count(self) -> int:
        """Get count of overdue tasks"""
        return len([t for t in self.project_state.tasks.values() if t.is_overdue])

class ResourceAgent(ProjectAgent):
    """Agent specializing in resource allocation"""
    
    def __init__(self, project_state: ProjectState):
        super().__init__("Resource Manager", "Manage team resources and allocation", project_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle resource-related requests"""
        
        prompt = """
        You are an expert resource management specialist. Analyze team capacity and provide allocation recommendations.

        REQUEST: {{$request}}

        TEAM CAPACITY:
        {{$team_capacity}}

        Please provide:
        👥 TEAM ANALYSIS:
        - Current workload distribution
        - Skill utilization
        - Capacity constraints

        📈 ALLOCATION RECOMMENDATIONS:
        - Optimal task assignments
        - Skill development opportunities
        - Workload balancing

        🔧 EFFICIENCY IMPROVEMENTS:
        - Process optimization suggestions
        - Tool and technology recommendations
        - Training needs identification

        Focus on maximizing team productivity while maintaining work-life balance.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="resource_management",
            plugin_name="resources",
            prompt=prompt
        )
        
        team_capacity = self._get_team_capacity_summary()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            team_capacity=team_capacity
        )
        
        return {
            "agent": self.name,
            "recommendations": str(result),
            "team_members": len(self.project_state.team_members),
            "available_capacity": self._get_available_capacity()
        }
    
    def _get_team_capacity_summary(self) -> str:
        """Generate team capacity summary"""
        summary = "👥 TEAM CAPACITY OVERVIEW:\n"
        
        for member in self.project_state.team_members.values():
            workload = "🟢 Light" if member.task_count <= 2 else "🟡 Moderate" if member.task_count <= 4 else "🔴 Heavy"
            summary += f"- {member.name} ({member.role}): {member.task_count} tasks {workload}\n"
            summary += f"  Skills: {', '.join(member.skills)}\n"
        
        return summary
    
    def _get_available_capacity(self) -> int:
        """Calculate total available capacity"""
        return sum(1 for member in self.project_state.team_members.values() if member.is_available)

class ProgressAgent(ProjectAgent):
    """Agent specializing in project progress tracking"""
    
    def __init__(self, project_state: ProjectState):
        super().__init__("Progress Tracker", "Track project progress and metrics", project_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle progress-related requests"""
        
        prompt = """
        You are an expert project progress analyst. Track project metrics and provide insights.

        REQUEST: {{$request}}

        PROJECT METRICS:
        {{$project_metrics}}

        Please provide:
        📈 PROGRESS ANALYSIS:
        - Current project status
        - Milestone achievement
        - Timeline adherence

        🎯 PERFORMANCE INSIGHTS:
        - Productivity trends
        - Quality metrics
        - Risk assessment

        🚀 IMPROVEMENT STRATEGIES:
        - Acceleration opportunities
        - Bottleneck removal
        - Success factor optimization

        Focus on data-driven insights and measurable outcomes.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="progress_tracking",
            plugin_name="progress",
            prompt=prompt
        )
        
        project_metrics = self._get_project_metrics()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            project_metrics=project_metrics
        )
        
        return {
            "agent": self.name,
            "insights": str(result),
            "completion_rate": self._get_overall_completion_rate(),
            "behind_schedule": self._get_behind_schedule_count()
        }
    
    def _get_project_metrics(self) -> str:
        """Generate project metrics summary"""
        metrics = "📈 PROJECT METRICS:\n"
        
        for project in self.project_state.projects.values():
            completion = project.completion_percentage(self.project_state.tasks)
            overdue = len(project.overdue_tasks(self.project_state.tasks))
            metrics += f"- {project.name}: {completion:.1f}% complete, {overdue} overdue tasks\n"
            metrics += f"  Status: {project.status}, Team: {len(project.team_members)} members\n"
        
        return metrics
    
    def _get_overall_completion_rate(self) -> float:
        """Calculate overall completion rate"""
        total_tasks = len(self.project_state.tasks)
        if total_tasks == 0:
            return 0.0
        
        completed_tasks = len([t for t in self.project_state.tasks.values() if t.status == 'done'])
        return (completed_tasks / total_tasks) * 100
    
    def _get_behind_schedule_count(self) -> int:
        """Count projects behind schedule"""
        behind_count = 0
        for project in self.project_state.projects.values():
            if project.status == 'active' and len(project.overdue_tasks(self.project_state.tasks)) > 2:
                behind_count += 1
        return behind_count

class ProjectManagementSystem:
    """Main project management system coordinating all agents"""
    
    def __init__(self):
        # Initialize shared project state
        self.project_state = ProjectState()
        self._initialize_sample_data()
        
        # Initialize specialized agents
        self.agents = {
            "tasks": TaskAgent(self.project_state),
            "resources": ResourceAgent(self.project_state),
            "progress": ProgressAgent(self.project_state)
        }
    
    def _initialize_sample_data(self):
        """Initialize the system with sample data"""
        # Sample team members
        team_members = [
            TeamMember(
                member_id="M001",
                name="Alice Chen",
                role="Project Manager",
                skills=["Planning", "Coordination", "Agile", "Stakeholder Management"]
            ),
            TeamMember(
                member_id="M002", 
                name="Bob Rodriguez",
                role="Senior Developer",
                skills=["Python", "API Development", "Database Design", "Testing"]
            ),
            TeamMember(
                member_id="M003",
                name="Carol Williams", 
                role="UI/UX Designer",
                skills=["Figma", "User Research", "Prototyping", "Design Systems"]
            ),
            TeamMember(
                member_id="M004",
                name="David Kim",
                role="DevOps Engineer",
                skills=["AWS", "Docker", "CI/CD", "Monitoring"]
            )
        ]
        
        for member in team_members:
            self.project_state.add_team_member(member)
        
        # Sample tasks
        base_date = datetime.now()
        tasks = [
            Task(
                task_id="T001",
                title="Project Planning",
                description="Create detailed project plan with milestones",
                status="done",
                priority="high",
                assignee="M001",
                due_date=base_date - timedelta(days=5)
            ),
            Task(
                task_id="T002",
                title="API Development",
                description="Develop core application APIs",
                status="in_progress", 
                priority="critical",
                assignee="M002",
                due_date=base_date + timedelta(days=3)
            ),
            Task(
                task_id="T003",
                title="UI Design",
                description="Create user interface mockups",
                status="in_progress",
                priority="high",
                assignee="M003",
                due_date=base_date + timedelta(days=7)
            ),
            Task(
                task_id="T004", 
                title="Database Setup",
                description="Set up production database",
                status="todo",
                priority="medium",
                assignee="M004",
                due_date=base_date + timedelta(days=10)
            ),
            Task(
                task_id="T005",
                title="User Testing",
                description="Conduct user acceptance testing",
                status="todo",
                priority="medium", 
                assignee="M003",
                due_date=base_date + timedelta(days=14)
            ),
            Task(
                task_id="T006",
                title="Documentation",
                description="Write technical documentation",
                status="todo",
                priority="low",
                assignee="M002",
                due_date=base_date + timedelta(days=12)
            ),
            Task(
                task_id="T007",
                title="Deployment Setup",
                description="Configure deployment pipeline",
                status="review",
                priority="high",
                assignee="M004", 
                due_date=base_date - timedelta(days=2)  # Overdue
            ),
            Task(
                task_id="T008",
                title="Security Audit",
                description="Conduct security review",
                status="todo",
                priority="critical",
                assignee="M002",
                due_date=base_date + timedelta(days=5)
            )
        ]
        
        for task in tasks:
            self.project_state.add_task(task)
        
        # Sample project
        project = Project(
            project_id="P001",
            name="E-Commerce Platform",
            description="Build modern e-commerce platform with React and Python",
            status="active",
            tasks=["T001", "T002", "T003", "T004", "T005", "T006", "T007", "T008"],
            team_members=["M001", "M002", "M003", "M004"]
        )
        
        self.project_state.add_project(project)
    
    async def run_demo(self):
        """Run the complete project management demo"""
        print("📋 PROJECT MANAGEMENT SYSTEM - COMPLETE SOLUTION")
        print("Multi-Agent State Management Demo")
        print("=" * 50)
        
        # Display initial state
        self.display_project_state()
        
        # Demo scenarios
        scenarios = [
            "We have 3 tasks overdue and 2 team members on vacation. How should we reassign tasks?",
            "Our project is 30% behind schedule. What's the best way to get back on track?",
            "We need to complete 5 high-priority tasks by Friday with limited resources.",
            "How can we better balance the workload among team members?",
            "What's the current project status and what risks should we address?"
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎯 SCENARIO {i}: {scenario}")
            print("-" * 50)
            
            await self.process_scenario(scenario)
            
            # Simulate task completion between scenarios
            if i < len(scenarios):
                self.simulate_task_completion()
        
        print("\n🎉 DEMO COMPLETED!")
        self.display_final_state()
    
    async def process_scenario(self, scenario: str):
        """Process a scenario with all agents"""
        print("🤖 Consulting all specialists...")
        
        # Process with all agents in parallel
        tasks = []
        for agent_name, agent in self.agents.items():
            tasks.append(agent.process_request(scenario))
        
        results = await asyncio.gather(*tasks)
        
        # Display results
        for (agent_name, _), result in zip(self.agents.items(), results):
            print(f"\n{agent_name.upper()} AGENT:")
            response = result.get('analysis', result.get('recommendations', result.get('insights', 'No response')))
            print(f"Response: {response}")
            
            # Show additional metrics
            if 'pending_tasks' in result:
                print(f"📊 Task Stats: {result['pending_tasks']} pending, {result['overdue_tasks']} overdue")
            if 'team_members' in result:
                print(f"👥 Team: {result['team_members']} members, {result['available_capacity']} available slots")
            if 'completion_rate' in result:
                print(f"📈 Progress: {result['completion_rate']:.1f}% complete, {result['behind_schedule']} projects behind")
    
    def display_project_state(self):
        """Display current project state"""
        print("\n📊 CURRENT PROJECT STATE:")
        print(self.project_state.get_project_status())
        
        # Show team workload
        print("👥 TEAM WORKLOAD:")
        for member in self.project_state.team_members.values():
            status = "✅ Available" if member.is_available else "⚠️  At capacity"
            print(f"  - {member.name}: {member.task_count} tasks ({status})")
    
    def simulate_task_completion(self):
        """Simulate task completion to demonstrate state updates"""
        print("\n✅ SIMULATING TASK COMPLETION...")
        
        # Find a task that's in progress or in review
        completable_tasks = [
            task for task in self.project_state.tasks.values() 
            if task.status in ['in_progress', 'review'] and not task.is_overdue
        ]
        
        if completable_tasks:
            task = completable_tasks[0]
            old_status = task.status
            self.project_state.update_task_status(task.task_id, 'done')
            print(f"📝 Marked '{task.title}' as completed (was {old_status})")
            
            # Show updated metrics
            completed_count = len([t for t in self.project_state.tasks.values() if t.status == 'done'])
            total_count = len(self.project_state.tasks)
            print(f"📈 Completion rate: {completed_count}/{total_count} tasks ({completed_count/total_count*100:.1f}%)")
        else:
            print("ℹ️  No tasks available for completion simulation")
    
    def display_final_state(self):
        """Display final state after demo"""
        print("\n📈 FINAL PROJECT STATE:")
        print(self.project_state.get_project_status())
        
        # Show completion statistics
        completed_tasks = [t for t in self.project_state.tasks.values() if t.status == 'done']
        print(f"🎯 Tasks completed during demo: {len(completed_tasks)}")
        
        # Show team utilization
        avg_tasks_per_member = sum(m.task_count for m in self.project_state.team_members.values()) / len(self.project_state.team_members)
        print(f"👥 Average tasks per team member: {avg_tasks_per_member:.1f}")

async def main():
    # Check environment variables
    required_vars = ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing environment variables. Please check your .env file.")
        print(f"Missing: {missing_vars}")
        return
    
    # Create and run the project management system
    project_system = ProjectManagementSystem()
    await project_system.run_demo()

if __name__ == "__main__":
    asyncio.run(main())