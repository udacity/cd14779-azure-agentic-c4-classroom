import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, GroupChatOrchestration
from semantic_kernel.agents import RoundRobinGroupChatManager, BooleanResult
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents import AuthorRole
from dotenv import load_dotenv

load_dotenv("../../.env")

class ApprovalGroupChatManager(RoundRobinGroupChatManager):
    """Custom group chat manager that terminates when coordinator approves the plan"""
    
    def __init__(self, coordinator_name: str, max_rounds: int = 10):
        super().__init__(max_rounds=max_rounds)
        self._coordinator_name = coordinator_name

    async def should_terminate(self, chat_history):
        """Terminate when coordinator sends a message containing 'approved'"""
        if not chat_history:
            return BooleanResult(result=False, reason="No conversation history")
            
        last_message = chat_history[-1]
        should_terminate = (
            getattr(last_message, 'author_name', None) == self._coordinator_name and
            'approved' in (last_message.content or '').lower()
        )
        return BooleanResult(
            result=should_terminate, 
            reason="Approved by coordinator." if should_terminate else "Waiting for coordinator approval."
        )

class SmartCityAgentManager:
    def __init__(self):
        self.kernel = Kernel()
        
        # Add Azure service to kernel
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
                
        # Initialize specialized agents with descriptions
        self.traffic_agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="Traffic_Manager",
            description="Expert in urban traffic flow and congestion management", # Add this line
            instructions="""You are an expert in urban traffic flow and congestion management. 
            Analyze traffic situations, provide insights on congestion patterns, and suggest 
            optimization strategies. Be specific and data-driven in your analysis."""
        )

        self.energy_agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="Energy_Analyst",
            description="Specialist in city energy consumption and distribution analysis", # Add this line
            instructions="""You specialize in city energy consumption and distribution analysis.
            Evaluate energy usage patterns, identify inefficiencies, and recommend sustainable 
            energy solutions. Focus on cost-effectiveness and environmental impact."""
        )

        self.safety_agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="Safety_Officer",
            description="Expert in public safety and emergency response", # Add this line
            instructions="""You are an expert in public safety and emergency response.
            Assess safety situations, identify risks, and propose comprehensive safety 
            measures. Consider both immediate and long-term safety implications."""
        )

        self.coordinator_agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="City_Coordinator",
            description="Coordinates between different city departments and provides final approval", # Add this line
            instructions="""You coordinate between different city departments and provide 
            final approval on city management plans. Review all analyses and say 'APPROVED' 
            when the comprehensive plan is satisfactory."""
        )
        
    async def run_individual_analysis(self, scenario: str):
        """Run individual agent analysis on a scenario"""
        print(f"🔍 Analyzing: {scenario}")
        print("-" * 50)
        
        agents = {
            "🚦 Traffic": self.traffic_agent,
            "⚡ Energy": self.energy_agent,
            "🚨 Safety": self.safety_agent
        }
        
        tasks = []
        for role, agent in agents.items():
            task = self._get_agent_response(agent, scenario, role)
            tasks.append(task)
        
        # Run all analyses in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for role, result in zip(agents.keys(), results):
            if isinstance(result, Exception):
                print(f"{role}: Error - {result}")
            else:
                print(f"{role}:\n{result}\n")

    async def run_group_chat_analysis(self, complex_scenario: str):
        """Run collaborative analysis using GroupChatOrchestration"""
        print(f"🤖 Starting Group Chat Analysis")
        print(f"Topic: {complex_scenario}")
        print("=" * 60)
        
        # Create GroupChatOrchestration with custom manager
        orchestration = GroupChatOrchestration(
            members=[self.traffic_agent, self.energy_agent, self.safety_agent, self.coordinator_agent],
            manager=ApprovalGroupChatManager(coordinator_name="City Coordinator", max_rounds=12)
        )
        
        # Create and start runtime
        runtime = InProcessRuntime()
        runtime.start()
        
        try:
            # Execute the orchestration
            orchestration_result = await orchestration.invoke(
                task=complex_scenario,
                runtime=runtime
            )
            
            # Get the final result
            final_result = await orchestration_result.get()
            
            print("🎯 Group Chat Completed!")
            print(f"Final Result:\n{final_result}")
            
        except Exception as e:
            print(f"❌ Orchestration error: {e}")
        finally:
            await runtime.stop_when_idle()

    async def _get_agent_response(self, agent: ChatCompletionAgent, scenario: str, role: str) -> str:
        """Get response from individual agent with error handling"""
        try:
            response = await agent.get_response(scenario)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"

async def main():
    """Main demo function"""
    print("🏙️ Smart City Multi-Agent System - Semantic Kernel 1.37.0")
    print("Using GroupChatOrchestration API")
    print("=" * 60)
    
    manager = SmartCityAgentManager()
    
    # Individual analysis scenarios
    scenarios = [
        "Heavy traffic congestion on Main Street during rush hour with increased energy demands from idling vehicles",
        "New residential development project requiring coordinated traffic, energy, and safety planning"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Scenario {i}: Individual Agent Analysis")
        await manager.run_individual_analysis(scenario)
    
    # Complex collaborative scenario
    complex_scenario = """
    MAJOR CITY INFRASTRUCTURE PROJECT:
    
    The city is planning a new subway line construction that will:
    1. Require 2 years of phased construction
    2. Affect major traffic arteries during construction  
    3. Increase energy demands for construction equipment
    4. Require safety planning for construction zones and public access
    5. Need long-term urban planning integration
    
    All departments must collaborate on a comprehensive plan. The City Coordinator must approve the final plan.
    """
    
    print("\n" + "=" * 60)
    print("🚀 Starting Collaborative Multi-Agent Analysis")
    print("=" * 60)
    await manager.run_group_chat_analysis(complex_scenario)
    print("✅ Demo completed successfully!")

if __name__ == "__main__":
    # Check for required environment variables
    required_vars = [
        "AZURE_TEXTGENERATOR_DEPLOYMENT_NAME",
        "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", 
        "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
    else:
        asyncio.run(main())