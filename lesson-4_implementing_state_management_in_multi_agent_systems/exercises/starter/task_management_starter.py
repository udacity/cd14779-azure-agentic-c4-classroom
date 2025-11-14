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

load_dotenv("../../../.env")

# TODO: Implement KernelBaseModel Models for State Management
# Create the following models using KernelBaseModel instead of BaseModel:
# 1. Task: Represents a task with id, title, description, status, priority, assignee, due_date
# 2. TeamMember: Represents a team member with id, name, role, skills, current_tasks
# 3. Project: Represents a project with id, name, description, status, tasks, team_members

class Task(KernelBaseModel):
    """Model representing a task using KernelBaseModel"""
    # TODO: Add fields: task_id, title, description, status, priority, assignee, due_date
    # TODO: Add kernel functions for task operations
    # TODO: Add validators for status and priority
    pass

class TeamMember(KernelBaseModel):
    """Model representing a team member using KernelBaseModel"""
    # TODO: Add fields: member_id, name, role, skills, current_tasks
    # TODO: Add kernel functions for team member operations
    # TODO: Add property method to calculate task_count
    pass

class Project(KernelBaseModel):
    """Model representing a project using KernelBaseModel"""
    # TODO: Add fields: project_id, name, description, status, tasks, team_members
    # TODO: Add kernel functions for project operations
    # TODO: Add validators for status
    # TODO: Add property methods for completion_percentage and overdue_tasks
    pass

class ProjectState(KernelBaseModel):
    """Central state management for the project using KernelBaseModel"""
    # TODO: Add fields: projects, team_members, tasks
    # TODO: Add kernel functions for: add_project, add_team_member, add_task, update_task_status
    
    @kernel_function(
        name="get_project_status_summary",
        description="Get overall project status summary"
    )
    def get_project_status(self) -> str:
        """Get overall project status summary"""
        # TODO: Implement comprehensive project status summary with metrics
        return "📊 Project status summary not implemented"

class ProjectOperationsPlugin:
    """Plugin for project operations that can be properly registered with the kernel"""
    
    def __init__(self, project_state: ProjectState):
        self.project_state = project_state
    
    # TODO: Implement kernel functions for project operations
    # @kernel_function(name="get_task_metrics", description="Get task metrics and statistics")
    # def get_task_metrics(self) -> str:
    #     pass
    
    # @kernel_function(name="get_team_capacity", description="Get team capacity analysis")
    # def get_team_capacity(self) -> str:
    #     pass
    
    # @kernel_function(name="get_project_progress", description="Get project progress analytics")
    # def get_project_progress(self) -> str:
    #     pass

class ProjectAgentManager:
    """Modern project management system using Semantic Kernel 1.37.0 agent framework"""
    
    def __init__(self):
        # Shared kernel instance for optimal resource usage
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_project_chat",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
        
        # TODO: Initialize shared project state
        self.project_state = ProjectState()
        
        # TODO: Initialize project operations plugin
        # self.project_plugin = ProjectOperationsPlugin(self.project_state)
        # self.kernel.add_plugin(self.project_plugin, "ProjectOperations")
        
        # TODO: Initialize sample data
        self._initialize_sample_data()
        
        # Initialize specialized project agents with modern framework
        self.agents = {
            "tasks": ChatCompletionAgent(
                kernel=self.kernel,
                name="Task_Manager",
                description="Specialist in task management and assignments",
                instructions="""You are a task management expert. Help with task-related requests.

                Available Functions:
                - get_project_status_summary: Get current project status
                - [MORE FUNCTIONS TO BE ADDED]

                Always provide:
                - Current task analysis and status
                - Priority assessment and recommendations
                - Deadline management strategies

                Use project data when available to provide data-driven responses.
                Be practical and focus on actionable task management strategies."""
            ),
            "resources": ChatCompletionAgent(
                kernel=self.kernel,
                name="Resource_Manager",
                description="Specialist in resource allocation and team management",
                instructions="""You are a resource management expert. Help with resource allocation.

                Available Functions:
                - get_project_status_summary: Get current project metrics
                - [MORE FUNCTIONS TO BE ADDED]

                Always provide:
                - Team capacity analysis
                - Workload balancing recommendations
                - Resource optimization strategies

                Focus on maximizing team productivity while maintaining balance."""
            ),
            # TODO: Implement the ProgressAgent
            # "progress": ChatCompletionAgent(
            #     kernel=self.kernel,
            #     name="Progress_Tracker", 
            #     description="Specialist in project progress tracking and metrics",
            #     instructions="""You are a project progress analyst. Track project metrics and provide insights.
            #
            #     Available Functions:
            #     - [FUNCTIONS TO BE ADDED]
            #
            #     Always provide:
            #     - Progress analysis and metrics
            #     - Timeline adherence assessment
            #     - Risk identification and mitigation
            #
            #     Focus on data-driven insights and measurable outcomes."""
            # ),
            "coordinator": ChatCompletionAgent(
                kernel=self.kernel,
                name="Project_Coordinator",
                description="Intelligent coordinator for project management and agent collaboration",
                instructions="""You are the central coordinator for the project management multi-agent system.

                Available Agents:
                - tasks: Task management, assignments, priority handling
                - resources: Team allocation, capacity planning, workload balancing
                - progress: Progress tracking, metrics, timeline management

                Always:
                1. Analyze the request and determine which specialist(s) should handle it
                2. Provide brief reasoning for your routing decision  
                3. Suggest any inter-agent collaboration needed

                Respond in this format:
                Primary Agent: [tasks/resources/progress]
                Supporting Agents: [comma-separated list or none]
                Reasoning: [brief explanation of routing decision]"""
            )
        }
        
        self.runtime = InProcessRuntime()
        self.chat_history = ChatHistory()

    def _initialize_sample_data(self):
        """Initialize the system with sample data"""
        # TODO: Create sample tasks, team members, and projects using kernel functions
        print("⚠️  Sample data initialization not implemented")
    
    async def coordinate_request(self, request: str) -> Dict:
        """Intelligent coordination of project requests"""
        print(f"📨 Project Request: {request}")
        print("🔄 Analyzing and coordinating with specialists...")
        
        # Use coordinator agent to analyze the request
        coordination_prompt = f"PROJECT REQUEST: {request}"
        
        coordination_response = await self.agents["coordinator"].get_response(coordination_prompt)
        coordination_decision = self._parse_coordination_decision(str(coordination_response.content))
        
        print(f"✅ Coordination Decision:")
        print(f"   Primary Agent: {coordination_decision['primary_agent']}")
        print(f"   Supporting Agents: {coordination_decision['supporting_agents']}")
        print(f"   Reasoning: {coordination_decision['reasoning']}")
        
        return coordination_decision

    def _parse_coordination_decision(self, coordination_text: str) -> Dict:
        """Parse the coordination decision from the AI response"""
        # TODO: Implement parsing logic for coordination decisions
        lines = coordination_text.strip().split('\n')
        decision = {
            "primary_agent": "tasks",  # default
            "supporting_agents": [],
            "reasoning": "Parse logic not implemented",
            "raw_response": coordination_text
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('Primary Agent:'):
                decision["primary_agent"] = line.split(':')[1].strip().lower()
            elif line.startswith('Supporting Agents:'):
                agents_text = line.split(':')[1].strip()
                if agents_text.lower() != 'none':
                    decision["supporting_agents"] = [agent.strip() for agent in agents_text.split(',')]
            elif line.startswith('Reasoning:'):
                decision["reasoning"] = line.split(':')[1].strip()
        
        return decision

    async def process_with_agent(self, request: str, agent_name: str, context: Dict = None) -> str:
        """Process request with specified agent using modern Semantic Kernel"""
        print(f"🔧 Engaging {agent_name} specialist...")
        
        # TODO: Integrate project data and context
        project_context = self.project_state.get_project_status()
        
        # Add coordination context if available
        coordination_context = ""
        if context:
            coordination_context = f"\n\nCOORDINATION CONTEXT: {context.get('reasoning', 'General request')}"
        
        enhanced_request = f"""
        PROJECT REQUEST: {request}
        
        PROJECT CONTEXT:
        {project_context}
        {coordination_context}
        
        Please provide your expert analysis and recommendations.
        """
        
        if agent_name in self.agents:
            specialist_response = await self.agents[agent_name].get_response(enhanced_request)
            return self._format_agent_response(agent_name, str(specialist_response.content))
        else:
            return f"❌ Agent '{agent_name}' not available for this request."

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
        """Complete processing of a project request"""
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
        """Display the processing result"""
        print(f"\n🎯 PROJECT REQUEST PROCESSING COMPLETE")
        print(f"Handled by: {result['agent_name']}")
        print(f"Supporting: {', '.join(result['coordination_decision']['supporting_agents']) or 'None'}")
        print(f"Session: {result.get('chat_history', 0)} messages")
        print("\n" + "=" * 60)
        print(f"{result['specialist_response']}")
        print("=" * 60)

    async def simulate_project_operation(self):
        """Simulate a project operation to demonstrate state changes"""
        print("\n🔄 SIMULATING PROJECT OPERATION...")
        # TODO: Implement project operation simulation
        print("Project operation simulation not implemented")

async def main():
    """Main project management system exercise"""
    print("🏢 MODERN PROJECT MANAGEMENT SYSTEM")
    print("Multi-Agent State Management Exercise")
    print("Semantic Kernel 1.37.0 with Advanced Agent Framework")
    print("=" * 70)
    print("Complete the TODOs to make this system work!")
    print()
    
    # Validate environment setup
    required_vars = [
        "AZURE_TEXTGENERATOR_DEPLOYMENT_NAME",
        "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", 
        "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return
    
    project_system = ProjectAgentManager()
    
    # Display initial state
    print("\n📊 INITIAL PROJECT STATE:")
    print(project_system.project_state.get_project_status())
    
    # Exercise scenarios
    project_scenarios = [
        "We have 3 tasks overdue and 2 team members on vacation. How should we reassign tasks?",
        "Our project is 30% behind schedule. What's the best way to get back on track?",
        "We need to complete 5 high-priority tasks by Friday with limited resources.",
        "How can we better balance the workload among team members?",
        "What's the current project status and what risks should we address?"
    ]
    
    print("🚀 Starting multi-agent project management exercise...")
    print("Available Agents: Task Manager, Resource Manager, Project Coordinator")
    print("TODO: Implement Progress Tracker agent")
    print()
    
    # Process exercise scenarios
    for i, scenario in enumerate(project_scenarios[:3], 1):
        print(f"\n{'#' * 70}")
        print(f"PROJECT SCENARIO #{i}")
        print(f"{'#' * 70}")
        
        try:
            result = await project_system.handle_project_request(scenario)
            project_system.display_result(result)
            
            # Simulate project operation between scenarios
            if i < len(project_scenarios):
                await project_system.simulate_project_operation()
            
            await asyncio.sleep(1)  # Brief pause for exercise flow
            
        except Exception as e:
            print(f"❌ System error: {e}")
            continue
    
    print(f"\n✅ Project Management Exercise Completed!")
    print(f"📝 Remember to complete all TODOs for full functionality")
    print(f"🛠️  Features to implement: KernelBaseModel, Kernel Functions, Progress Agent, Project Operations")

if __name__ == "__main__":
    asyncio.run(main())