import asyncio
import os
from typing import Dict
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from dotenv import load_dotenv
load_dotenv()

class CityAgent:
    """Base agent class for smart city monitoring"""
    
    def __init__(self, name: str, expertise: str):
        self.name = name
        self.expertise = expertise
        self.kernel = Kernel()
        
        # Add Azure OpenAI service with explicit authentication:cite[7]
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"]
            )
        )
    
    async def process_request(self, request: str) -> str:
        """Process a monitoring request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

class TrafficAgent(CityAgent):
    """Specialized agent for traffic monitoring and management"""
    
    def __init__(self):
        super().__init__("Traffic Manager", "Urban traffic flow and congestion management")
        
        # Add traffic-specific functions as a plugin:cite[6]
        self.kernel.add_plugin(self.TrafficPlugin(), "TrafficPlugin")
    
    class TrafficPlugin:
        @kernel_function(description="Analyze traffic congestion patterns")
        def analyze_congestion(self, location: str) -> str:
            """Simulate traffic congestion analysis"""
            return f"Moderate congestion detected at {location}. Average speed: 25 mph. Recommended actions: Adjust traffic signals."
    
    async def process_request(self, request: str) -> str:
        """Process traffic-related requests"""
        # Use the traffic plugin to analyze congestion
        traffic_function = self.kernel.get_function("TrafficPlugin", "analyze_congestion")
        result = await self.kernel.invoke(traffic_function, location="downtown")
        
        return f"Traffic Analysis by {self.name}: {result}"

class EnergyAgent(CityAgent):
    """Specialized agent for energy consumption monitoring"""
    
    def __init__(self):
        super().__init__("Energy Analyst", "City energy consumption and distribution")
        
        # Add energy-specific functions as a plugin:cite[6]
        self.kernel.add_plugin(self.EnergyPlugin(), "EnergyPlugin")
    
    class EnergyPlugin:
        @kernel_function(description="Analyze energy consumption patterns")
        def analyze_consumption(self, area: str) -> str:
            """Simulate energy consumption analysis"""
            return f"High energy consumption detected in {area}. Peak usage: 2-5 PM. Recommended actions: Implement load shifting."
    
    async def process_request(self, request: str) -> str:
        """Process energy-related requests"""
        # Use the energy plugin to analyze consumption
        energy_function = self.kernel.get_function("EnergyPlugin", "analyze_consumption")
        result = await self.kernel.invoke(energy_function, area="residential district")
        
        return f"Energy Analysis by {self.name}: {result}"

class CityCoordinator:
    """Orchestrates multiple city monitoring agents"""
    
    def __init__(self):
        self.agents = {
            "traffic": TrafficAgent(),
            "energy": EnergyAgent()
        }
    
    async def coordinate_monitoring(self, monitoring_request: str) -> Dict[str, str]:
        """Coordinate monitoring across multiple specialized agents"""
        results = {}
        
        # Process request with all relevant agents in parallel
        tasks = []
        for agent_name, agent in self.agents.items():
            tasks.append(agent.process_request(monitoring_request))
        
        # Gather all results
        agent_results = await asyncio.gather(*tasks)
        
        for (agent_name, _), result in zip(self.agents.items(), agent_results):
            results[agent_name] = result
        
        return results

# Demo execution
async def main():
    print("Smart City Infrastructure Monitoring Multi-Agent System Demo")
    print("============================================================")
    print("Using Semantic Kernel 1.36.2")
    print()
    
    coordinator = CityCoordinator()
    
    # Sample monitoring scenarios
    scenarios = [
        "Analyze downtown traffic patterns during morning rush hour",
        "Assess energy consumption peaks in residential areas"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"Scenario {i}: {scenario}")
        print("-" * 60)
        
        results = await coordinator.coordinate_monitoring(scenario)
        
        for agent_type, analysis in results.items():
            print(f"{agent_type.upper()} ANALYSIS:")
            print(analysis)
            print()
        
        print("=" * 60)
        print()

if __name__ == "__main__":
    asyncio.run(main())