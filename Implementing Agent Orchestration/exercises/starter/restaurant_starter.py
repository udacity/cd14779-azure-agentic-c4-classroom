import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from dotenv import load_dotenv
load_dotenv("../../../.env")

class RestaurantAgent:
    """Base class for all restaurant specialist agents"""
    
    def __init__(self, name: str, specialty: str):
        self.name = name
        self.specialty = specialty
        self.kernel = Kernel()
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
    
    async def process_request(self, request: str) -> str:
        """Process restaurant request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

class CuisineAgent(RestaurantAgent):
    """Agent specializing in cuisine recommendations"""
    
    def __init__(self):
        super().__init__("Cuisine Expert", "Recommending cuisine types")
    
    async def process_request(self, request: str) -> str:
        """Recommend cuisine types based on preferences"""
        
        # TODO: Create a better prompt for cuisine recommendations
        # The prompt should ask for:
        # - 2-3 recommended cuisine types
        # - Why each cuisine fits the request
        # - Popular dishes to try
        # - Dietary considerations
        
        prompt = "You are a food expert. Suggest cuisines for this request: {{$request}}"
        
        function = KernelFunctionFromPrompt(
            function_name="cuisine_recommendations",
            plugin_name="cuisine",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🍽️ **Cuisine Recommendations**\n\n{result}"

class LocationAgent(RestaurantAgent):
    """Agent specializing in restaurant locations and areas"""
    
    def __init__(self):
        super().__init__("Location Expert", "Finding best dining areas")
    
    async def process_request(self, request: str) -> str:
        """Recommend dining locations and areas"""
        
        # TODO: Create a better prompt for location recommendations
        # The prompt should ask for:
        # - Recommended neighborhoods/areas
        # - Atmosphere descriptions
        # - Transportation/parking tips
        # - Best times to visit
        
        prompt = "You are a location expert. Suggest areas for dining: {{$request}}"
        
        function = KernelFunctionFromPrompt(
            function_name="location_recommendations",
            plugin_name="location",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"📍 **Location Recommendations**\n\n{result}"

# TODO: Implement the PriceRangeAgent class
# This agent should handle budget and price range recommendations
# class PriceRangeAgent(RestaurantAgent):
#     def __init__(self):
#         super().__init__("Price Expert", "Budget and price range advice")
    
#     async def process_request(self, request: str) -> str:
#         # TODO: Create a prompt for price range recommendations
#         # The prompt should ask for:
#         # - Price range estimates ($, $$, $$$)
#         # - Value-for-money suggestions
#         # - Cost-saving tips
#         # - Typical meal prices
#         pass

class RestaurantOrchestrator:
    """Orchestrates multiple restaurant recommendation agents"""
    
    def __init__(self):
        self.agents = {
            "cuisine": CuisineAgent(),
            "location": LocationAgent()
            # TODO: Add PriceRangeAgent to the agents dictionary
        }
    
    async def sequential_orchestration(self, request: str) -> dict:
        """SEQUENTIAL: Agents process in order"""
        print("🚀 Starting SEQUENTIAL Orchestration")
        print("Pattern: Cuisine → Location")
        print("-" * 50)
        
        results = {}
        
        # Step 1: Get cuisine recommendations first
        print("1. 🍽️ Consulting Cuisine Expert...")
        results["cuisine"] = await self.agents["cuisine"].process_request(request)
        
        # Step 2: Then get location recommendations
        print("2. 📍 Consulting Location Expert...")
        results["location"] = await self.agents["location"].process_request(request)
        
        # TODO: Add Step 3: Get price range recommendations
        # print("3. 💰 Consulting Price Expert...")
        # results["price"] = await self.agents["price"].process_request(request)
        
        return results
    
    async def parallel_orchestration(self, request: str) -> dict:
        """PARALLEL: All agents process simultaneously"""
        print("🚀 Starting PARALLEL Orchestration")
        print("Pattern: All experts work simultaneously")
        print("-" * 50)
        
        print("🔄 Launching all experts in parallel...")
        
        # TODO: Implement parallel orchestration
        # Steps:
        # 1. Create tasks for all agents (cuisine, location, price)
        # 2. Use asyncio.gather to run them simultaneously
        # 3. Return the results in a dictionary
        
        # Placeholder - replace this with actual implementation
        results = {
            "cuisine": "Parallel orchestration not implemented yet",
            "location": "Parallel orchestration not implemented yet"
        }
        
        return results
    
    # TODO: Implement conditional_orchestration method
    # async def conditional_orchestration(self, request: str) -> dict:
    #     """CONDITIONAL: Only use relevant agents based on request"""
    #     # Steps:
    #     # 1. Analyze the request to determine which agents are needed
    #     # 2. Only call the relevant agents
    #     # 3. Return results from only those agents
    #     pass

    def display_results(self, results: dict, pattern_name: str):
        """Display results in a clean format"""
        print(f"\n🎉 {pattern_name.upper()} ORCHESTRATION RESULTS")
        print("=" * 60)
        
        for agent_type, result in results.items():
            print(f"\n{result}")
            print("-" * 40)

async def main():
    print("🍴 RESTAURANT RECOMMENDATION EXERCISE - STARTER CODE")
    print("Multi-Agent Orchestration Patterns")
    print("=" * 50)
    print("Complete the TODOs to make this system work!")
    print()
    
    # Check environment
    required_vars = ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing environment variables. Please check your .env file.")
        return
    
    orchestrator = RestaurantOrchestrator()
    
    # Restaurant recommendation scenarios
    restaurant_requests = [
        "I want to celebrate my anniversary with a romantic dinner. We like Italian food and have a medium budget.",
        "Looking for a family-friendly restaurant that has options for kids and adults. Prefer casual dining.",
        "Business lunch meeting tomorrow. Need a quiet place with good food that's not too expensive."
    ]
    
    # Test with first request
    restaurant_request = restaurant_requests[0]
    
    print(f"📝 RESTAURANT REQUEST: {restaurant_request}")
    print("\n" + "=" * 50)
    
    # Test sequential orchestration (partially implemented)
    print(f"\n🔧 Testing SEQUENTIAL Pattern:")
    print("=" * 50)
    
    try:
        results = await orchestrator.sequential_orchestration(restaurant_request)
        orchestrator.display_results(results, "sequential")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # TODO: Uncomment and test parallel orchestration after implementing it
    # print(f"\n🔧 Testing PARALLEL Pattern:")
    # print("=" * 50)
    # results = await orchestrator.parallel_orchestration(restaurant_request)
    # orchestrator.display_results(results, "parallel")
    
    # TODO: Uncomment and test conditional orchestration after implementing it
    # print(f"\n🔧 Testing CONDITIONAL Pattern:")
    # print("=" * 50)
    # results = await orchestrator.conditional_orchestration(restaurant_request)
    # orchestrator.display_results(results, "conditional")

if __name__ == "__main__":
    asyncio.run(main())