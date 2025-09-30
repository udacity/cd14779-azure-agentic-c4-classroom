import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from dotenv import load_dotenv

load_dotenv()

class RestaurantAgent:
    """Base class for all restaurant specialist agents"""
    
    def __init__(self, name: str, specialty: str):
        self.name = name
        self.specialty = specialty
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
        """Process restaurant request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

class CuisineAgent(RestaurantAgent):
    """Agent specializing in cuisine recommendations"""
    
    def __init__(self):
        super().__init__("Cuisine Expert", "Recommending cuisine types")
    
    async def process_request(self, request: str) -> str:
        """Recommend cuisine types based on preferences"""
        
        prompt = """
        You are a food and cuisine expert. Analyze this dining request and provide specific cuisine recommendations.

        REQUEST: {{$request}}

        Please provide:
        - 2-3 recommended cuisine types that fit the request
        - Brief explanation why each cuisine is a good fit
        - 2-3 popular dishes to try from each cuisine
        - Any dietary considerations or alternatives

        Focus on cuisines that match the occasion, preferences, and dietary needs.
        """
        
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
        
        prompt = """
        You are a dining location expert. Analyze this request and recommend the best areas for restaurants.

        REQUEST: {{$request}}

        Please provide:
        - 2-3 recommended neighborhoods or dining areas
        - Description of the atmosphere in each area
        - Transportation and parking advice
        - Best times to visit each area
        - Any area-specific considerations

        Focus on areas that match the dining occasion and preferences.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="location_recommendations",
            plugin_name="location",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"📍 **Location Recommendations**\n\n{result}"

class PriceRangeAgent(RestaurantAgent):
    """Agent specializing in budget and price range recommendations"""
    
    def __init__(self):
        super().__init__("Price Expert", "Budget and price range advice")
    
    async def process_request(self, request: str) -> str:
        """Provide price range and budget recommendations"""
        
        prompt = """
        You are a restaurant pricing expert. Analyze this request and provide budget guidance.

        REQUEST: {{$request}}

        Please provide:
        - Recommended price range ($, $$, $$$)
        - Estimated cost per person
        - Value-for-money suggestions
        - Cost-saving tips and strategies
        - Typical price ranges for different menu items

        Focus on helping diners make informed budget decisions.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="price_recommendations",
            plugin_name="price",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"💰 **Price Range Recommendations**\n\n{result}"

class RestaurantOrchestrator:
    """Orchestrates multiple restaurant recommendation agents"""
    
    def __init__(self):
        self.agents = {
            "cuisine": CuisineAgent(),
            "location": LocationAgent(),
            "price": PriceRangeAgent()
        }
    
    async def sequential_orchestration(self, request: str) -> dict:
        """SEQUENTIAL: Agents process in order"""
        print("🚀 Starting SEQUENTIAL Orchestration")
        print("Pattern: Cuisine → Location → Price")
        print("-" * 50)
        
        results = {}
        
        # Step 1: Get cuisine recommendations first
        print("1. 🍽️ Consulting Cuisine Expert...")
        results["cuisine"] = await self.agents["cuisine"].process_request(request)
        
        # Step 2: Then get location recommendations
        print("2. 📍 Consulting Location Expert...")
        results["location"] = await self.agents["location"].process_request(request)
        
        # Step 3: Finally get price range recommendations
        print("3. 💰 Consulting Price Expert...")
        results["price"] = await self.agents["price"].process_request(request)
        
        return results
    
    async def parallel_orchestration(self, request: str) -> dict:
        """PARALLEL: All agents process simultaneously"""
        print("🚀 Starting PARALLEL Orchestration")
        print("Pattern: All experts work simultaneously")
        print("-" * 50)
        
        print("🔄 Launching all experts in parallel...")
        
        # Execute all agents at the same time
        tasks = [
            self.agents["cuisine"].process_request(request),
            self.agents["location"].process_request(request),
            self.agents["price"].process_request(request)
        ]
        
        cuisine_result, location_result, price_result = await asyncio.gather(*tasks)
        
        return {
            "cuisine": cuisine_result,
            "location": location_result,
            "price": price_result
        }
    
    async def conditional_orchestration(self, request: str) -> dict:
        """CONDITIONAL: Only use relevant agents based on request"""
        print("🚀 Starting CONDITIONAL Orchestration")
        print("Pattern: Smart agent selection based on request")
        print("-" * 50)
        
        # Simple rule-based conditional logic
        request_lower = request.lower()
        results = {}
        
        # Determine which agents are needed based on keywords
        needs_cuisine = any(word in request_lower for word in ['food', 'cuisine', 'italian', 'mexican', 'asian', 'type', 'kind'])
        needs_location = any(word in request_lower for word in ['where', 'location', 'area', 'neighborhood', 'place'])
        needs_price = any(word in request_lower for word in ['price', 'budget', 'cost', 'cheap', 'expensive', '$', 'money'])
        
        print(f"🤖 Smart Analysis: Cuisine={needs_cuisine}, Location={needs_location}, Price={needs_price}")
        
        # Only call needed agents
        if needs_cuisine:
            print("🍽️ Consulting Cuisine Expert...")
            results["cuisine"] = await self.agents["cuisine"].process_request(request)
        
        if needs_location:
            print("📍 Consulting Location Expert...")
            results["location"] = await self.agents["location"].process_request(request)
        
        if needs_price:
            print("💰 Consulting Price Expert...")
            results["price"] = await self.agents["price"].process_request(request)
        
        return results

    def display_results(self, results: dict, pattern_name: str):
        """Display results in a clean format"""
        print(f"\n🎉 {pattern_name.upper()} ORCHESTRATION RESULTS")
        print("=" * 60)
        
        for agent_type, result in results.items():
            print(f"\n{result}")
            print("-" * 40)

async def main():
    print("🍴 RESTAURANT RECOMMENDATION SYSTEM - COMPLETE SOLUTION")
    print("Multi-Agent Orchestration Patterns")
    print("=" * 50)
    
    # Check environment
    required_vars = ["AZURE_OPENAI_DEPLOYMENT_NAME", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing environment variables. Please check your .env file.")
        return
    
    orchestrator = RestaurantOrchestrator()
    
    # Restaurant recommendation scenarios
    restaurant_requests = [
        "I want to celebrate my anniversary with a romantic dinner. We like Italian food and have a medium budget.",
        "Looking for a family-friendly restaurant that has options for kids and adults. Prefer casual dining.",
        "Business lunch meeting tomorrow. Need a quiet place with good food that's not too expensive.",
        "Where can I find the best sushi in town? Price is not an issue."
    ]
    
    # Test all patterns with different requests
    for i, restaurant_request in enumerate(restaurant_requests[:2], 1):
        print(f"\n📝 SCENARIO {i}: {restaurant_request}")
        print("=" * 70)
        
        # Test all orchestration patterns
        patterns = [
            ("SEQUENTIAL", orchestrator.sequential_orchestration),
            ("PARALLEL", orchestrator.parallel_orchestration),
            ("CONDITIONAL", orchestrator.conditional_orchestration)
        ]
        
        for pattern_name, pattern_function in patterns:
            print(f"\n🔧 Testing {pattern_name} Pattern:")
            print("-" * 50)
            
            try:
                results = await pattern_function(restaurant_request)
                orchestrator.display_results(results, pattern_name)
                
                # Small pause between patterns
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

if __name__ == "__main__":
    asyncio.run(main())