import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents import ChatHistory
from dotenv import load_dotenv

load_dotenv()

# Modern KernelBaseModel for State Management
class Task(KernelBaseModel):
    """Model representing a task using KernelBaseModel"""
    task_id: str
    title: str
    description: str
    status: str = "todo"
    priority: str
    assignee: Optional[str] = None
    due_date: datetime
    
    @kernel_function(
        name="check_task_overdue",
        description="Check if the task is overdue"
    )
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        return self.status != 'done' and self.due_date < datetime.now()
    
    @kernel_function(
        name="get_task_info",
        description="Get formatted task information"
    )
    def get_task_info(self) -> str:
        """Get formatted task information"""
        status_icon = "✅" if self.status == 'done' else "🟡" if self.status == 'in_progress' else "⏳"
        priority_icon = "🔴" if self.priority == 'critical' else "🟠" if self.priority == 'high' else "🟢"
        overdue = " 🚨 OVERDUE" if self.is_overdue() else ""
        return f"{status_icon} {priority_icon} {self.title} - Due: {self.due_date.strftime('%m/%d')}{overdue}"

class TeamMember(KernelBaseModel):
    """Model representing a team member using KernelBaseModel"""
    member_id: str
    name: str
    role: str
    skills: List[str] = []
    current_tasks: List[str] = []
    
    @kernel_function(
        name="get_task_count",
        description="Get number of assigned tasks"
    )
    def task_count(self) -> int:
        """Get number of assigned tasks"""
        return len(self.current_tasks)
    
    @kernel_function(
        name="check_member_availability",
        description="Check if member has capacity for more tasks"
    )
    def is_available(self) -> bool:
        """Check if member has capacity for more tasks"""
        return self.task_count() < 5  # Max 5 tasks per member
    
    @kernel_function(
        name="get_member_profile",
        description="Get formatted team member profile"
    )
    def get_member_profile(self) -> str:
        """Get formatted team member profile"""
        availability = "✅ Available" if self.is_available() else "⚠️ At Capacity"
        return f"👤 {self.name} ({self.role}) - {self.task_count()} tasks - {availability}"

class Project(KernelBaseModel):
    """Model representing a project using KernelBaseModel"""
    project_id: str
    name: str
    description: str
    status: str = "planning"
    tasks: List[str] = []
    team_members: List[str] = []
    
    @kernel_function(
        name="calculate_completion_percentage",
        description="Calculate project completion percentage"
    )
    def completion_percentage(self, task_dict: Dict[str, Task]) -> float:
        """Calculate project completion percentage"""
        if not self.tasks:
            return 0.0
        
        completed_tasks = 0
        for task_id in self.tasks:
            if task_id in task_dict and task_dict[task_id].status == 'done':
                completed_tasks += 1
        
        return (completed_tasks / len(self.tasks)) * 100
    
    @kernel_function(
        name="get_overdue_tasks",
        description="Get list of overdue task titles"
    )
    def overdue_tasks(self, task_dict: Dict[str, Task]) -> List[str]:
        """Get list of overdue task titles"""
        overdue = []
        for task_id in self.tasks:
            if task_id in task_dict and task_dict[task_id].is_overdue():
                overdue.append(task_dict[task_id].title)
        return overdue
    
    @kernel_function(
        name="get_project_status",
        description="Get comprehensive project status"
    )
    def get_project_status(self, task_dict: Dict[str, Task]) -> str:
        """Get comprehensive project status"""
        completion = self.completion_percentage(task_dict)
        overdue_count = len(self.overdue_tasks(task_dict))
        status_icon = "🚀" if self.status == 'active' else "📋" if self.status == 'planning' else "✅"
        
        return f"{status_icon} {self.name}: {completion:.1f}% complete, {overdue_count} overdue tasks"

class ProjectState(KernelBaseModel):
    """Central state management for the project using KernelBaseModel"""
    projects: Dict[str, Project] = {}
    team_members: Dict[str, TeamMember] = {}
    tasks: Dict[str, Task] = {}
    
    def add_project(self, project: Project) -> str:
        """Add or update project"""
        self.projects[project.project_id] = project
        return f"✅ Added project '{project.name}' to system"
    
    def add_team_member(self, member: TeamMember) -> str:
        """Add or update team member"""
        self.team_members[member.member_id] = member
        return f"✅ Added team member '{member.name}' to system"
    
    def add_task(self, task: Task) -> str:
        """Add or update task"""
        self.tasks[task.task_id] = task
        
        # Add task to assignee's current tasks if assigned
        if task.assignee and task.assignee in self.team_members:
            if task.task_id not in self.team_members[task.assignee].current_tasks:
                self.team_members[task.assignee].current_tasks.append(task.task_id)
        
        return f"✅ Added task '{task.title}' to system"
    
    def update_task_status(self, task_id: str, status: str) -> str:
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            return f"✅ Updated task status to '{status}'"
        return f"❌ Task {task_id} not found"
    
    def get_project_status(self) -> str:
        """Get overall project status summary"""
        total_projects = len(self.projects)
        active_projects = len([p for p in self.projects.values() if p.status == 'active'])
        completed_projects = len([p for p in self.projects.values() if p.status == 'completed'])
        
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == 'done'])
        overdue_tasks = len([t for t in self.tasks.values() if t.is_overdue()])
        
        completion_rate = (completed_tasks/total_tasks*100) if total_tasks > 0 else 0
        
        return f"""
        📊 PROJECT MANAGEMENT DASHBOARD:
        • Projects: {total_projects} total ({active_projects} active, {completed_projects} completed)
        • Tasks: {total_tasks} total ({completed_tasks} completed, {overdue_tasks} overdue)
        • Team: {len(self.team_members)} members
        • Overall Completion: {completion_rate:.1f}%
        • System Status: 🟢 Operational
        """

class ProjectManagementPlugin:
    """Plugin for project operations that can be properly registered with the kernel"""
    
    def __init__(self, project_state: ProjectState):
        self.project_state = project_state
    
    @kernel_function(
        name="get_comprehensive_project_status",
        description="Get overall project status summary with metrics"
    )
    def get_comprehensive_project_status(self) -> str:
        """Get overall project status summary"""
        return self.project_state.get_project_status()
    
    @kernel_function(
        name="add_project_to_system",
        description="Add or update project in the system"
    )
    def add_project(self, project: Project) -> str:
        """Add or update project"""
        return self.project_state.add_project(project)
    
    @kernel_function(
        name="add_team_member_to_system", 
        description="Add or update team member in the system"
    )
    def add_team_member(self, member: TeamMember) -> str:
        """Add or update team member"""
        return self.project_state.add_team_member(member)
    
    @kernel_function(
        name="add_task_to_system",
        description="Add or update task in the system"
    )
    def add_task(self, task: Task) -> str:
        """Add or update task"""
        return self.project_state.add_task(task)
    
    @kernel_function(
        name="update_task_status_in_system",
        description="Update task status with validation"
    )
    def update_task_status(self, task_id: str, status: str) -> str:
        """Update task status"""
        return self.project_state.update_task_status(task_id, status)
    
    @kernel_function(
        name="get_task_metrics",
        description="Get comprehensive task metrics and statistics"
    )
    def get_task_metrics(self) -> str:
        """Get task metrics and statistics"""
        status_count = {}
        priority_count = {}
        
        for task in self.project_state.tasks.values():
            status_count[task.status] = status_count.get(task.status, 0) + 1
            priority_count[task.priority] = priority_count.get(task.priority, 0) + 1
        
        metrics = "📋 TASK METRICS:\n"
        metrics += "Status Distribution:\n"
        for status, count in status_count.items():
            icon = "✅" if status == 'done' else "🟡" if status == 'in_progress' else "⏳"
            metrics += f"  {icon} {status}: {count} tasks\n"
        
        metrics += "\nPriority Distribution:\n"
        for priority, count in priority_count.items():
            icon = "🔴" if priority == 'critical' else "🟠" if priority == 'high' else "🟢"
            metrics += f"  {icon} {priority}: {count} tasks\n"
        
        overdue_count = len([t for t in self.project_state.tasks.values() if t.is_overdue()])
        metrics += f"\n🚨 Overdue Tasks: {overdue_count}"
        
        return metrics
    
    @kernel_function(
        name="get_team_capacity",
        description="Get team capacity analysis and workload distribution"
    )
    def get_team_capacity(self) -> str:
        """Get team capacity analysis"""
        capacity = "👥 TEAM CAPACITY ANALYSIS:\n"
        
        for member in self.project_state.team_members.values():
            workload = "🟢 Light" if member.task_count() <= 2 else "🟡 Moderate" if member.task_count() <= 4 else "🔴 Heavy"
            availability = "✅ Available" if member.is_available() else "⚠️ At Capacity"
            capacity += f"• {member.name} ({member.role}): {member.task_count()} tasks {workload} - {availability}\n"
            capacity += f"  Skills: {', '.join(member.skills)}\n"
        
        available_slots = sum(1 for member in self.project_state.team_members.values() if member.is_available())
        capacity += f"\n📈 Available Capacity: {available_slots} team members"
        
        return capacity
    
    @kernel_function(
        name="get_project_progress",
        description="Get comprehensive project progress analytics"
    )
    def get_project_progress(self) -> str:
        """Get project progress analytics"""
        progress = "📈 PROJECT PROGRESS ANALYTICS:\n"
        
        for project in self.project_state.projects.values():
            completion = project.completion_percentage(self.project_state.tasks)
            overdue_count = len(project.overdue_tasks(self.project_state.tasks))
            status_icon = "🚀" if project.status == 'active' else "📋" if project.status == 'planning' else "✅"
            
            progress += f"• {status_icon} {project.name}\n"
            progress += f"  Completion: {completion:.1f}% | Overdue: {overdue_count} tasks\n"
            progress += f"  Status: {project.status} | Team: {len(project.team_members)} members\n"
        
        overall_completion = self._get_overall_completion_rate()
        behind_schedule = self._get_behind_schedule_count()
        
        progress += f"\n🎯 Overall Completion: {overall_completion:.1f}%"
        progress += f"\n⚠️  Projects Behind Schedule: {behind_schedule}"
        
        return progress
    
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

class ProjectAgentManager:
    """Modern project management system using Semantic Kernel 1.37.0 agent framework"""
    
    def __init__(self):
        # Shared kernel instance for optimal resource usage
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_project_chat",
                deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_DEPLOYMENT_KEY"]
            )
        )
        
        # Initialize shared project state
        self.project_state = ProjectState()
        self._initialize_sample_data()
        
        # Initialize project management plugin and add to kernel
        self.project_plugin = ProjectManagementPlugin(self.project_state)
        self.kernel.add_plugin(self.project_plugin, "ProjectManagement")
        
        # Initialize specialized project agents with modern framework
        self.agents = {
            "tasks": ChatCompletionAgent(
                kernel=self.kernel,
                name="Task_Manager",
                description="Specialist in task management and assignments",
                instructions="""You are a task management expert. Use available project data and functions to manage tasks effectively.

                Available Functions:
                - get_task_metrics: Get comprehensive task statistics
                - get_comprehensive_project_status: Access project overview
                - update_task_status_in_system: Modify task status

                Always provide:
                - Current task analysis with data-driven insights
                - Priority assessment and deadline management
                - Risk identification and mitigation strategies
                - Practical task optimization recommendations

                Use the available metrics for accurate analysis and focus on actionable strategies."""
            ),
            "resources": ChatCompletionAgent(
                kernel=self.kernel,
                name="Resource_Manager",
                description="Specialist in resource allocation and team management",
                instructions="""You are a resource management expert. Analyze team capacity and optimize allocations.

                Available Functions:
                - get_team_capacity: Access team workload analysis
                - get_comprehensive_project_status: View project context
                - get_task_metrics: Understand task distribution

                Always provide:
                - Team capacity analysis with workload insights
                - Optimal resource allocation recommendations
                - Workload balancing strategies
                - Skill utilization optimization

                Focus on maximizing team productivity while maintaining sustainable workloads."""
            ),
            "progress": ChatCompletionAgent(
                kernel=self.kernel,
                name="Progress_Tracker",
                description="Specialist in project progress tracking and performance metrics",
                instructions="""You are a project progress analyst. Track metrics and provide data-driven insights.

                Available Functions:
                - get_project_progress: Access comprehensive progress analytics
                - get_comprehensive_project_status: View overall status
                - get_task_metrics: Analyze task performance

                Always provide:
                - Progress analysis with milestone tracking
                - Performance insights and trend identification
                - Risk assessment and mitigation planning
                - Acceleration opportunities

                Focus on measurable outcomes and data-driven project management."""
            ),
            "coordinator": ChatCompletionAgent(
                kernel=self.kernel,
                name="Project_Coordinator",
                description="Intelligent coordinator for project management and agent collaboration",
                instructions="""You are the central coordinator for the project management multi-agent system.

                Available Agents:
                - tasks: Task management, priority handling, deadline tracking
                - resources: Team allocation, capacity planning, workload optimization
                - progress: Progress tracking, metrics analysis, performance insights

                Available Data:
                - Comprehensive project metrics and analytics
                - Team capacity and workload information
                - Task distribution and status tracking

                Always:
                1. Analyze the request and determine which specialist(s) should handle it
                2. Provide brief reasoning for your routing decision based on the request type
                3. Suggest any inter-agent collaboration needed for complex scenarios

                Respond in this exact format:
                Primary Agent: [tasks/resources/progress]
                Supporting Agents: [comma-separated list or none]
                Reasoning: [brief explanation of routing decision]"""
            )
        }
        
        self.runtime = InProcessRuntime()
        self.chat_history = ChatHistory()

    def _initialize_sample_data(self):
        """Initialize the system with sample data using kernel functions"""
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

    async def coordinate_request(self, request: str) -> Dict:
        """Intelligent coordination of project requests"""
        print(f"📨 Project Request: {request}")
        print("🔄 Analyzing and coordinating with specialists...")
        
        # Get coordination decision
        coordination_prompt = f"""
        PROJECT REQUEST: {request}
        
        Please coordinate this request among our specialized project management agents.
        """
        
        coordination_response = await self.agents["coordinator"].get_response(coordination_prompt)
        coordination_decision = self._parse_coordination_decision(str(coordination_response.content))
        
        print(f"✅ Coordination Decision:")
        print(f"   Primary Agent: {coordination_decision['primary_agent']}")
        print(f"   Supporting Agents: {coordination_decision['supporting_agents']}")
        print(f"   Reasoning: {coordination_decision['reasoning']}")
        
        return coordination_decision

    def _parse_coordination_decision(self, coordination_text: str) -> Dict:
        """Parse the coordination decision from AI response"""
        lines = [line.strip() for line in coordination_text.strip().split('\n') if line.strip()]
        
        decision = {
            "primary_agent": "tasks",
            "supporting_agents": [],
            "reasoning": "Default coordination",
            "raw_response": coordination_text
        }
        
        for line in lines:
            lower_line = line.lower()
            if lower_line.startswith('primary agent:'):
                agent = line.split(':', 1)[1].strip()
                if agent in self.agents:
                    decision["primary_agent"] = agent
            elif lower_line.startswith('supporting agents:'):
                agents_text = line.split(':', 1)[1].strip()
                if agents_text.lower() != 'none':
                    decision["supporting_agents"] = [agent.strip() for agent in agents_text.split(',')]
            elif lower_line.startswith('reasoning:'):
                decision["reasoning"] = line.split(':', 1)[1].strip()
        
        return decision

    async def process_with_agent(self, request: str, agent_name: str, context: Dict = None) -> str:
        """Process request with specified agent using modern Semantic Kernel"""
        print(f"🔧 Engaging {agent_name} specialist...")
        
        # Build enhanced context with project analytics
        project_context = self.project_state.get_project_status()
        task_metrics = self.project_plugin.get_task_metrics()
        team_capacity = self.project_plugin.get_team_capacity()
        project_progress = self.project_plugin.get_project_progress()
        
        # Add coordination context if available
        coordination_context = ""
        if context:
            coordination_context = f"\n\nCOORDINATION CONTEXT: {context.get('reasoning', 'General request')}"
        
        enhanced_request = f"""
        PROJECT REQUEST: {request}
        
        CURRENT PROJECT STATUS:
        {project_context}
        
        TASK METRICS:
        {task_metrics}
        
        TEAM CAPACITY:
        {team_capacity}
        
        PROJECT PROGRESS:
        {project_progress}
        {coordination_context}
        
        Please provide your expert analysis and recommendations based on the available data.
        """
        
        try:
            agent_response = await self.agents[agent_name].get_response(enhanced_request)
            return self._format_agent_response(agent_name, str(agent_response.content))
            
        except Exception as e:
            return f"❌ Error in {agent_name} processing: {str(e)}"

    def _format_agent_response(self, agent_name: str, content: str) -> str:
        """Format agent response with appropriate branding"""
        icons = {
            "tasks": "📋",
            "resources": "👥", 
            "progress": "📈"
        }
        
        titles = {
            "tasks": "Task Management Analysis",
            "resources": "Resource Allocation Recommendations", 
            "progress": "Progress Tracking Insights"
        }
        
        icon = icons.get(agent_name, "🏢")
        title = titles.get(agent_name, "Project Analysis")
        
        return f"{icon} **{title}**\n\n{content}"

    async def handle_project_request(self, request: str) -> Dict:
        """Complete processing of a project request with modern agent framework"""
        # Add to chat history for context
        self.chat_history.add_user_message(request)
        
        # Step 1: Coordinate the request
        coordination_decision = await self.coordinate_request(request)
        
        # Step 2: Process with primary agent
        primary_agent = coordination_decision["primary_agent"]
        if primary_agent in self.agents:
            specialist_response = await self.process_with_agent(
                request, 
                primary_agent,
                coordination_decision
            )
            
            # Add assistant response to history
            self.chat_history.add_assistant_message(specialist_response)
            
            return {
                "coordination_decision": coordination_decision,
                "specialist_response": specialist_response,
                "agent_name": primary_agent.replace('_', ' ').title(),
                "project_status": self.project_state.get_project_status(),
                "chat_history": len(self.chat_history.messages)
            }
        else:
            error_response = "❌ No suitable agent available for this request."
            self.chat_history.add_assistant_message(error_response)
            
            return {
                "coordination_decision": coordination_decision,
                "specialist_response": error_response,
                "agent_name": "Coordination System",
                "project_status": self.project_state.get_project_status(),
                "chat_history": len(self.chat_history.messages)
            }

    def display_result(self, result: Dict):
        """Display the processing result with modern formatting"""
        print(f"\n🎯 PROJECT REQUEST PROCESSING COMPLETE")
        print(f"Handled by: {result['agent_name']}")
        print(f"Supporting: {', '.join(result['coordination_decision']['supporting_agents']) or 'None'}")
        print(f"Session: {result.get('chat_history', 0)} messages")
        print("\n" + "=" * 70)
        print(f"{result['specialist_response']}")
        print("=" * 70)

    async def simulate_project_operation(self):
        """Simulate a project operation to demonstrate state changes"""
        print("\n🔄 SIMULATING PROJECT OPERATION...")
        
        # Find a task that's in progress or in review
        completable_tasks = [
            task for task in self.project_state.tasks.values() 
            if task.status in ['in_progress', 'review'] and not task.is_overdue()
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

async def main():
    """Modern project management system demo"""
    print("🏢 MODERN PROJECT MANAGEMENT SYSTEM")
    print("Multi-Agent State Management Demo")
    print("Semantic Kernel 1.37.0 with Advanced Agent Framework")
    print("=" * 70)
    
    # Validate environment setup
    required_vars = [
        "AZURE_DEPLOYMENT_NAME",
        "AZURE_DEPLOYMENT_ENDPOINT", 
        "AZURE_DEPLOYMENT_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return
    
    # Initialize modern project management system
    project_system = ProjectAgentManager()
    
    # Display initial state
    print("\n📊 INITIAL PROJECT STATE:")
    print(project_system.project_state.get_project_status())
    
    # Enhanced demo scenarios
    project_scenarios = [
        "We have 3 tasks overdue and 2 team members on vacation. How should we reassign tasks?",
        "Our project is 30% behind schedule. What's the best way to get back on track?",
        "We need to complete 5 high-priority tasks by Friday with limited resources.",
        "How can we better balance the workload among team members?",
        "What's the current project status and what risks should we address?",
        "Analyze our team capacity and suggest optimization strategies"
    ]
    
    print("🚀 Starting multi-agent project management demonstrations...")
    print("Available Agents: Task Manager, Resource Manager, Progress Tracker, Project Coordinator")
    print("Available Functions: Task Metrics, Team Capacity, Project Progress, Status Tracking")
    print()
    
    # Process enhanced scenarios
    for i, scenario in enumerate(project_scenarios, 1):
        print(f"\n{'#' * 70}")
        print(f"PROJECT SCENARIO #{i}")
        print(f"{'#' * 70}")
        
        try:
            result = await project_system.handle_project_request(scenario)
            project_system.display_result(result)
            
            # Simulate project operation between scenarios
            if i < len(project_scenarios):
                await project_system.simulate_project_operation()
            
            await asyncio.sleep(1)  # Brief pause for demo flow
            
        except Exception as e:
            print(f"❌ System error: {e}")
            continue
    
    # Display final state
    print(f"\n📈 FINAL PROJECT STATE:")
    print(project_system.project_state.get_project_status())
    
    print(f"\n✅ Modern Project Management System Demo Completed!")
    print(f"📊 Session Summary: {len(project_system.chat_history.messages)} project interactions processed")
    print(f"🛠️  Features Used: Multi-Agent Coordination, KernelBaseModel, Kernel Functions, Real-time Analytics")

if __name__ == "__main__":
    asyncio.run(main())