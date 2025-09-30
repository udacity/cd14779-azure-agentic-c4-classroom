import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from dotenv import load_dotenv
load_dotenv()

class Cityworker:
    def __init__(self, name: str, expertise: str):
        self.name = name
        self.expertise = expertise
        self.kernel = Kernel()
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"]
            )
        )
    
    async def process_request(self, request: str) -> str:
        raise NotImplementedError("Subclasses must implement this method")

class Trafficworker(Cityworker):
    def __init__(self):
        super().__init__("Traffic Manager", "Urban traffic flow and congestion management")
    
    async def process_request(self, request: str) -> str:
        # TODO: Create a more detailed prompt for traffic analysis
        # The prompt should ask for:
        # - Current traffic conditions
        # - Root cause analysis
        # - Immediate actions
        # - Long-term solutions
        # - Impact assessment
        prompt = "You are a traffic expert. Analyze this traffic situation: {{$request}}"
        
        function = KernelFunctionFromPrompt(
            function_name="traffic_analysis",
            plugin_name="traffic",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🚦 Traffic Analysis by {self.name}:\n{result}"

class Energyworker(Cityworker):
    def __init__(self):
        super().__init__("Energy Analyst", "City energy consumption and distribution")
    
    async def process_request(self, request: str) -> str:
        # TODO: Create a more detailed prompt for energy analysis
        # The prompt should ask for:
        # - Current energy usage patterns
        # - Efficiency opportunities
        # - Cost-saving measures
        # - Sustainability improvements
        # - Implementation timeline
        prompt = "You are an energy expert. Analyze this energy situation: {{$request}}"
        
        function = KernelFunctionFromPrompt(
            function_name="energy_analysis",
            plugin_name="energy",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"⚡ Energy Analysis by {self.name}:\n{result}"

class Safetyworker(Cityworker):
    def __init__(self):
        super().__init__("Safety Officer", "Public safety and emergency response")
    
    async def process_request(self, request: str) -> str:
        # TODO: Create a more detailed prompt for safety analysis
        # The prompt should ask for:
        # - Risk assessment
        # - Immediate safety concerns
        # - Preventive measures
        # - Emergency response plans
        # - Community safety recommendations
        prompt = "You are a safety expert. Analyze this safety situation: {{$request}}"
        
        function = KernelFunctionFromPrompt(
            function_name="safety_analysis",
            plugin_name="safety",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🚨 Safety Analysis by {self.name}:\n{result}"

# TODO: Implement the EnvironmentWorker class
# This worker should handle environmental and sustainability issues
# class EnvironmentWorker(Cityworker):
#     def __init__(self):
#         super().__init__("Environment Specialist", "Environmental monitoring and sustainability")
    
#     async def process_request(self, request: str) -> str:
#         # TODO: Create a detailed prompt for environmental analysis
#         # The prompt should ask for:
#         # - Environmental impact assessment
#         # - Sustainability recommendations
#         # - Pollution control measures
#         # - Green infrastructure suggestions
#         # - Compliance with environmental regulations
#         pass

class CityCoordinator:
    def __init__(self):
        self.workers = {
            "traffic": Trafficworker(),
            "energy": Energyworker(),
            "safety": Safetyworker()
            # TODO: Add EnvironmentWorker to the workers dictionary
        }
    
    async def coordinate_monitoring(self, monitoring_request: str) -> dict:
        """Coordinate monitoring across all workers"""
        results = {}
        
        tasks = [worker.process_request(monitoring_request) for worker in self.workers.values()]
        worker_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (worker_name, worker), result in zip(self.workers.items(), worker_results):
            if isinstance(result, Exception):
                results[worker_name] = f"❌ Error: {result}"
            else:
                results[worker_name] = result
        
        return results
    
    # TODO: Implement this method to analyze which workers are relevant for a request
    # async def analyze_relevance(self, request: str) -> dict:
    #     """Use LLM to determine which workers are most relevant for the request"""
    #     # This should return a dictionary with relevance scores for each worker
    #     pass
    
    # TODO: Implement this method to only use relevant workers
    # async def coordinate_smart_monitoring(self, monitoring_request: str) -> dict:
    #     """Only use relevant workers based on request analysis"""
    #     # Steps:
    #     # 1. Analyze which workers are relevant
    #     # 2. Only invoke relevant workers
    #     # 3. Return results from relevant workers only
    #     pass

async def main():
    print("Smart City Monitoring System - Starter Code")
    print("=" * 50)
    print("This is the basic version. Complete the TODOs to enhance the system!")
    print()
    
    coordinator = CityCoordinator()
    
    scenarios = [
        "Heavy traffic congestion on Main Street during rush hour with average speeds below 10 mph",
        "Energy consumption peaks in downtown offices between 2-5 PM, 40% above normal levels",
        "Safety concerns in Central Park after dark due to poor lighting and limited security patrols",
        # TODO: Add an environmental scenario
        # "High air pollution levels reported in industrial district exceeding safety standards"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"Scenario {i}: {scenario}")
        print("-" * 60)
        
        results = await coordinator.coordinate_monitoring(scenario)
        
        for worker_type, analysis in results.items():
            print(f"\n{analysis}")
            print("-" * 40)
        
        print("\n" + "=" * 60)
        print()

if __name__ == "__main__":
    asyncio.run(main())