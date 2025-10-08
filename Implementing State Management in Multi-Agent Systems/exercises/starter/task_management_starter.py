import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
load_dotenv("../../../.env")

# TODO: Implement Pydantic Models for State Management
# Create the following models:
# 1. Task: Represents a task with id, title, description, status, priority, assignee, due_date
# 2. TeamMember: Represents a team member with id, name, role, skills, current_tasks
# 3. Project: Represents a project with id, name, description, status, tasks, team_members

class Task(BaseModel):
    """Model representing a task"""
    # TODO: Add fields: task_id, title, description, status, priority, assignee, due_date
    # Add validators for status and priority
    pass

class TeamMember(BaseModel):
    """Model representing a team member"""
    # TODO: Add fields: member_id, name, role, skills, current_tasks
    # Add property method to calculate task_count
    pass

class Project(BaseModel):
    """Model representing a project"""
    # TODO: Add fields: project_id, name, description, status, tasks, team_members
    # Add validators for status
    # Add property methods for completion_percentage and overdue_tasks
    pass

class ProjectState(BaseModel):
    """Central state management for the project"""
    # TODO: Add fields: projects, team_members, tasks
    # Add methods: add_project, add_team_member, add_task, update_task_status
    
    def get_project_status(self) -> str:
        """Get overall project status summary"""
        # TODO: Implement project status summary
        return "Project status summary not implemented"

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
        
        # TODO: Create a comprehensive prompt for task management
        prompt = """
        You are a task management expert. Help with task-related requests.

        REQUEST: {{$request}}

        Please provide task management advice.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="task_management",
            plugin_name="tasks",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        
        return {
            "agent": self.name,
            "analysis": str(result),
            "pending_tasks": 0,  # TODO: Get actual count from project_state
            "overdue_tasks": 0   # TODO: Get actual count from project_state
        }

class ResourceAgent(ProjectAgent):
    """Agent specializing in resource allocation"""
    
    def __init__(self, project_state: ProjectState):
        super().__init__("Resource Manager", "Manage team resources and allocation", project_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle resource-related requests"""
        
        # TODO: Create a comprehensive prompt for resource management
        prompt = """
        You are a resource management expert. Help with resource allocation.

        REQUEST: {{$request}}

        Please provide resource management advice.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="resource_management",
            plugin_name="resources",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        
        return {
            "agent": self.name,
            "recommendations": str(result),
            "team_members": 0,  # TODO: Get actual count from project_state
            "available_capacity": 0  # TODO: Calculate from project_state
        }

# TODO: Implement the ProgressAgent class
# class ProgressAgent(ProjectAgent):
#     def __init__(self, project_state: ProjectState):
#         super().__init__("Progress Tracker", "Track project progress and metrics", project_state)
    
#     async def process_request(self, request: str) -> Dict:
#         # TODO: Create prompt for progress tracking
#         # TODO: Implement progress analysis
#         pass

class ProjectManagementSystem:
    """Main project management system coordinating all agents"""
    
    def __init__(self):
        # TODO: Initialize shared project state
        self.project_state = ProjectState()
        # TODO: Initialize sample data
        self._initialize_sample_data()
        
        # Initialize agents (currently incomplete)
        self.agents = {
            "tasks": TaskAgent(self.project_state),
            "resources": ResourceAgent(self.project_state)
            # TODO: Add ProgressAgent to the agents dictionary
        }
    
    def _initialize_sample_data(self):
        """Initialize the system with sample data"""
        # TODO: Create sample tasks, team members, and projects
        print("Sample data initialization not implemented")
    
    async def run_exercise(self):
        """Run the project management exercise"""
        print("📋 PROJECT MANAGEMENT EXERCISE - STARTER CODE")
        print("Multi-Agent State Management")
        print("=" * 50)
        print("Complete the TODOs to make this system work!")
        print()
        
        # Display initial state (when implemented)
        self.display_project_state()
        
        # Exercise scenarios
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
    
    async def process_scenario(self, scenario: str):
        """Process a scenario with all agents"""
        print("🤖 Consulting specialists...")
        
        # Process with available agents
        tasks = []
        for agent_name, agent in self.agents.items():
            tasks.append(agent.process_request(scenario))
        
        results = await asyncio.gather(*tasks)
        
        # Display results
        for (agent_name, _), result in zip(self.agents.items(), results):
            print(f"\n{agent_name.upper()} AGENT:")
            print(f"Analysis: {result.get('analysis', result.get('recommendations', 'No response'))}")
    
    def display_project_state(self):
        """Display current project state"""
        print("\n📊 CURRENT PROJECT STATE:")
        # TODO: Display actual project state information
        print("Project state display not implemented")
    
    def simulate_task_completion(self):
        """Simulate task completion to demonstrate state updates"""
        print("\n✅ SIMULATING TASK COMPLETION...")
        # TODO: Implement task completion simulation
        print("Task completion simulation not implemented")

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
    await project_system.run_exercise()

if __name__ == "__main__":
    asyncio.run(main())