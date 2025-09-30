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
        prompt = "You are a traffic expert. Analyze this traffic situation: {{$request}}"
        function = KernelFunctionFromPrompt(
            function_name="traffic_analysis",
            plugin_name="traffic",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🚦 Traffic Analysis:\n{result}"

class Energyworker(Cityworker):
    def __init__(self):
        super().__init__("Energy Analyst", "City energy consumption and distribution")
    
    async def process_request(self, request: str) -> str:
        prompt = "You are an energy expert. Analyze this energy situation: {{$request}}"
        function = KernelFunctionFromPrompt(
            function_name="energy_analysis",
            plugin_name="energy",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"⚡ Energy Analysis:\n{result}"

class Safetyworker(Cityworker):
    def __init__(self):
        super().__init__("Safety Officer", "Public safety and emergency response")
    
    async def process_request(self, request: str) -> str:
        prompt = "You are a safety expert. Analyze this safety situation: {{$request}}"
        function = KernelFunctionFromPrompt(
            function_name="safety_analysis",
            plugin_name="safety",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🚨 Safety Analysis:\n{result}"

async def main():
    print("Smart City Monitoring Demo - Semantic Kernel 1.36.2")
    print("=" * 50)
    
    workers = {
        "traffic": Trafficworker(),
        "energy": Energyworker(),
        "safety": Safetyworker()
    }
    
    scenarios = [
        "Heavy traffic congestion on Main Street",
        "High energy consumption in downtown area",
        "Safety concerns in Central Park"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {scenario}")
        print("-" * 40)
        
        tasks = [worker.process_request(scenario) for worker in workers.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (name, worker), result in zip(workers.items(), results):
            if isinstance(result, Exception):
                print(f"{worker.name}: Error - {result}")
            else:
                print(f"{worker.name}:\n{result}\n")

if __name__ == "__main__":
    asyncio.run(main())