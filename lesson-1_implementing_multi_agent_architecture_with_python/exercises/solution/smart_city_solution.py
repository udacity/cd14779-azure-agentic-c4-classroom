import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents.runtime import InProcessRuntime
from dotenv import load_dotenv

load_dotenv("../../../.env")

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
        
        # Initialize specialized agents with proper descriptions
        self.agents = {
            "traffic": ChatCompletionAgent(
                kernel=self.kernel,
                name="Traffic_Manager",
                description="Expert in urban traffic flow and congestion management",
                instructions="""You are an expert in urban traffic flow and congestion management. 
                Analyze traffic situations, provide insights on congestion patterns, and suggest 
                optimization strategies. Be specific and data-driven in your analysis."""
            ),
            "energy": ChatCompletionAgent(
                kernel=self.kernel,
                name="Energy_Analyst",
                description="Specialist in city energy consumption and distribution analysis",
                instructions="""You specialize in city energy consumption and distribution analysis.
                Evaluate energy usage patterns, identify inefficiencies, and recommend sustainable 
                energy solutions. Focus on cost-effectiveness and environmental impact."""
            ),
            "safety": ChatCompletionAgent(
                kernel=self.kernel,
                name="Safety_Officer",
                description="Expert in public safety and emergency response",
                instructions="""You are an expert in public safety and emergency response.
                Assess safety situations, identify risks, and propose comprehensive safety 
                measures. Consider both immediate and long-term safety implications."""
            ),
            "environment": ChatCompletionAgent(
                kernel=self.kernel,
                name="Environment_Manager",
                description="Expert in environmental impact and sustainability",
                instructions="""You are an expert in environmental impact assessment and sustainability.
                Analyze environmental situations, identify ecological risks, and recommend 
                sustainable solutions. Focus on pollution control, green initiatives, and 
                long-term environmental health."""
            ),
            "coordinator": ChatCompletionAgent(
                kernel=self.kernel,
                name="City_Coordinator",
                description="Coordinates between different city departments",
                instructions="""You coordinate between different city departments and provide 
                integrated recommendations. Synthesize inputs from traffic, energy, safety, 
                and environment experts into comprehensive plans."""
            )
        }

    async def run_parallel_analysis(self, scenario: str):
        """Run all agent analyses in parallel with proper error handling"""
        print(f"🔍 Analyzing: {scenario}")
        print("-" * 50)
        
        # Create tasks for all agents including environment agent
        tasks = {
            "🚦 Traffic": self._get_agent_response(self.agents["traffic"], scenario),
            "⚡ Energy": self._get_agent_response(self.agents["energy"], scenario),
            "🚨 Safety": self._get_agent_response(self.agents["safety"], scenario),
            "🌳 Environment": self._get_agent_response(self.agents["environment"], scenario)
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
            traffic_response = await self.agents["traffic"].get_response(
                f"Scenario: {complex_scenario}\n\nProvide initial traffic impact analysis."
            )
            traffic_content = str(traffic_response.content)
            print(f"Traffic Analysis Complete: {len(traffic_content)} characters\n")
            
            # Step 2: Energy analysis (with traffic context)
            print("2. ⚡ Energy Analysis Starting...")
            energy_prompt = f"""Scenario: {complex_scenario}

            Previous Analysis from Traffic Department:
            {traffic_content}

            Provide energy consumption and distribution analysis considering the traffic implications."""
            
            energy_response = await self.agents["energy"].get_response(energy_prompt)
            energy_content = str(energy_response.content)
            print(f"Energy Analysis Complete: {len(energy_content)} characters\n")
            
            # Step 3: Safety analysis (with traffic and energy context)
            print("3. 🚨 Safety Analysis Starting...")
            safety_prompt = f"""Scenario: {complex_scenario}

            Traffic Department Analysis:
            {traffic_content}

            Energy Department Analysis:
            {energy_content}

            Provide comprehensive safety analysis integrating all previous assessments."""
            
            safety_response = await self.agents["safety"].get_response(safety_prompt)
            safety_content = str(safety_response.content)
            print(f"Safety Analysis Complete: {len(safety_content)} characters\n")
            
            # Step 4: Environmental analysis (with all previous context)
            print("4. 🌳 Environmental Analysis Starting...")
            environment_prompt = f"""Scenario: {complex_scenario}

            Traffic Department Analysis:
            {traffic_content}

            Energy Department Analysis:
            {energy_content}

            Safety Department Analysis:
            {safety_content}

            Provide comprehensive environmental impact assessment considering all previous analyses."""
            
            environment_response = await self.agents["environment"].get_response(environment_prompt)
            environment_content = str(environment_response.content)
            print(f"Environmental Analysis Complete: {len(environment_content)} characters\n")
            
            # Step 5: Generate integrated summary
            print("5. 📋 Generating Integrated Summary...")
            summary_prompt = f"""Based on all departmental analyses, create a comprehensive summary:

            ORIGINAL SCENARIO: {complex_scenario}

            TRAFFIC ANALYSIS:
            {traffic_content}

            ENERGY ANALYSIS:
            {energy_content}

            SAFETY ANALYSIS:
            {safety_content}

            ENVIRONMENTAL ANALYSIS:
            {environment_content}

            Provide a concise integrated summary with key recommendations and priorities."""
            
            summary_response = await self.agents["coordinator"].get_response(summary_prompt)
            summary_content = str(summary_response.content)
            
            print("🎯 Sequential Collaboration Completed!")
            print(f"\nFinal Integrated Summary:\n{summary_content}")
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
    print("🏙️ Smart City Multi-Agent System - Complete Solution")
    print("With Environment Manager and Full Sequential Collaboration")
    print("=" * 60)
    
    manager = SmartCityAgentManager()
    
    # Individual analysis scenarios (parallel processing)
    scenarios = [
        "Heavy traffic congestion on Main Street during rush hour with increased energy demands from idling vehicles",
        "New residential development project requiring coordinated traffic, energy, and safety planning",
        "High air pollution levels reported in industrial district exceeding safety standards"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Scenario {i}: Parallel Agent Analysis")
        await manager.run_parallel_analysis(scenario)
    
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
    print("🚀 Starting Complete Multi-Agent Collaboration")
    print("=" * 60)
    await manager.run_sequential_collaboration(complex_scenario)
    print("✅ Demo completed successfully!")

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