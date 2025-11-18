import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents.runtime import InProcessRuntime
from dotenv import load_dotenv

# load_dotenv("../../.env")
load_dotenv()

class SmartCityAgentManager:
    def __init__(self):
        # Single shared kernel instance for all agents
        self.kernel = Kernel()
        
        # Add Azure service to kernel once
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
        
        # TODO: Initialize specialized agents with proper descriptions
        # Create Traffic Manager agent
        self.agents = {
            "traffic": None,  # TODO: Create Traffic Manager agent
            
            # TODO: Create Energy Analyst agent
            "energy": None,
            
            # TODO: Create Safety Officer agent  
            "safety": None,
            
            # TODO: Create Environment Manager agent
            "environment": None,
            
            # TODO: Create City Coordinator agent
            "coordinator": None
        }

    async def run_parallel_analysis(self, scenario: str):
        """Run all agent analyses in parallel with proper error handling"""
        print(f"🔍 Analyzing: {scenario}")
        print("-" * 50)
        
        # TODO: Create tasks for all agents including the new environment agent
        tasks = {
            "🚦 Traffic": self._get_agent_response(self.agents["traffic"], scenario),
            "⚡ Energy": self._get_agent_response(self.agents["energy"], scenario),
            "🚨 Safety": self._get_agent_response(self.agents["safety"], scenario),
            # TODO: Add Environment agent to parallel analysis
            # "🌳 Environment": self._get_agent_response(self.agents["environment"], scenario)
        }
        
        # Execute all analyses in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Display results
        for (role, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                print(f"{role}: Error - {result}")
            else:
                print(f"{role}:\n{result}\n")

    async def run_sequential_collaboration(self, complex_scenario: str):
        """Run sequential collaboration between all agents"""
        print(f"🤖 Starting Sequential Collaboration")
        print(f"Topic: {complex_scenario}")
        print("=" * 60)
        
        runtime = InProcessRuntime()
        runtime.start()
        
        try:
            # Step 1: Traffic analysis
            print("1. 🚦 Traffic Analysis Starting...")
            # TODO: Get traffic analysis
            
            # Step 2: Energy analysis (with traffic context)
            print("2. ⚡ Energy Analysis Starting...")
            # TODO: Get energy analysis using traffic context
            
            # Step 3: Safety analysis (with traffic and energy context)
            print("3. 🚨 Safety Analysis Starting...")
            # TODO: Get safety analysis using traffic and energy context
            
            # Step 4: Environmental analysis (with all previous context)
            print("4. 🌳 Environmental Analysis Starting...")
            # TODO: Get environmental analysis using all previous context
            
            # Step 5: Generate integrated summary
            print("5. 📋 Generating Integrated Summary...")
            # TODO: Generate comprehensive summary using coordinator
            
            print("🎯 Sequential Collaboration Completed!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Collaboration error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await runtime.stop_when_idle()

    async def _get_agent_response(self, agent: ChatCompletionAgent, scenario: str) -> str:
        """Get response from individual agent with optimized error handling"""
        try:
            response = await agent.get_response(scenario)
            return str(response.content)
        except Exception as e:
            return f"Error processing request: {str(e)}"

async def main():
    """Main demo function"""
    print("🏙️ Smart City Multi-Agent System - Student Exercise")
    print("Complete the TODOs to build your multi-agent system!")
    print("=" * 60)
    
    manager = SmartCityAgentManager()
    
    # Individual analysis scenarios (parallel processing)
    scenarios = [
        "Heavy traffic congestion on Main Street during rush hour with increased energy demands from idling vehicles",
        "New residential development project requiring coordinated traffic, energy, and safety planning",
        "High air pollution levels reported in industrial district exceeding safety standards"
    ]
    
    # TODO: Uncomment when agents are implemented
    # for i, scenario in enumerate(scenarios, 1):
    #     print(f"\n📋 Scenario {i}: Parallel Agent Analysis")
    #     await manager.run_parallel_analysis(scenario)
    
    # Complex collaborative scenario (sequential processing)
    complex_scenario = """MAJOR CITY INFRASTRUCTURE PROJECT:

    The city is planning a new subway line construction that will:
    1. Require 2 years of phased construction
    2. Affect major traffic arteries during construction  
    3. Increase energy demands for construction equipment
    4. Require safety planning for construction zones and public access
    5. Need long-term urban planning integration
    6. Has long-term environmental impact considerations

    All departments must collaborate on a comprehensive plan."""
    
    print("\n" + "=" * 60)
    print("🚀 Sequential Collaboration (Complete TODOs to enable)")
    print("=" * 60)
    # TODO: Uncomment when sequential collaboration is implemented
    # await manager.run_sequential_collaboration(complex_scenario)
    
    print("\n🎓 Exercise Instructions:")
    print("1. Create all agents in the __init__ method")
    print("2. Add Environment Manager agent to parallel analysis") 
    print("3. Implement sequential collaboration with all agents")
    print("4. Test with the provided scenarios")

if __name__ == "__main__":
    # Validate environment variables
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