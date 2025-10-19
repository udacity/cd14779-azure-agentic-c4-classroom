import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from dotenv import load_dotenv

load_dotenv("../../.env")

class TravelAgent:
    """Base class for all travel specialist agents"""
    
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
        """Process travel request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

class DestinationAgent(TravelAgent):
    """Agent specializing in destination recommendations"""
    
    def __init__(self):
        super().__init__("Destination Expert", "Finding perfect travel destinations")
    
    async def process_request(self, request: str) -> str:
        """Recommend destinations based on travel preferences"""
        
        prompt = """
        You are a travel destination expert. Recommend 2-3 destinations for this trip:

        TRAVEL REQUEST: {{$request}}

        Provide a concise response with:
        - Top 2-3 destination recommendations
        - Brief reason why each destination fits
        - Best time to visit
        - Budget level (Budget/Mid-range/Luxury)

        Keep it clear and practical.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="destination_recommendations",
            plugin_name="destination",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🗺️ **Destination Recommendations**\n\n{result}"

class FlightAgent(TravelAgent):
    """Agent specializing in flight research"""
    
    def __init__(self):
        super().__init__("Flight Expert", "Finding best flight options")
    
    async def process_request(self, request: str) -> str:
        """Research flight options"""
        
        prompt = """
        You are a flight booking expert. Provide flight advice for this trip:

        TRAVEL REQUEST: {{$request}}

        Provide a concise response with:
        - Best airlines for this route
        - Estimated flight duration
        - Price range estimate
        - 2-3 booking tips

        Focus on practical, actionable advice.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="flight_advice",
            plugin_name="flight",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"✈️ **Flight Recommendations**\n\n{result}"

class AccommodationAgent(TravelAgent):
    """Agent specializing in accommodation research"""
    
    def __init__(self):
        super().__init__("Accommodation Expert", "Finding great places to stay")
    
    async def process_request(self, request: str) -> str:
        """Research accommodation options"""
        
        prompt = """
        You are an accommodation expert. Provide lodging advice for this trip:

        TRAVEL REQUEST: {{$request}}

        Provide a concise response with:
        - Recommended accommodation types (hotel/vacation rental/etc.)
        - Best areas to stay
        - Price range per night
        - 2-3 booking tips

        Focus on location and value.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="accommodation_advice",
            plugin_name="accommodation",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🏨 **Accommodation Recommendations**\n\n{result}"

class TravelOrchestrator:
    """Orchestrates multiple travel agents using different patterns"""
    
    def __init__(self):
        self.agents = {
            "destination": DestinationAgent(),
            "flights": FlightAgent(),
            "accommodation": AccommodationAgent()
        }
    
    async def sequential_orchestration(self, travel_request: str) -> dict:
        """SEQUENTIAL: Agents process in order"""
        print("🚀 Starting SEQUENTIAL Orchestration")
        print("Pattern: Destination → Flights → Accommodation")
        print("-" * 50)
        
        results = {}
        
        # Step 1: Get destinations first
        print("1. 🗺️ Consulting Destination Expert...")
        results["destination"] = await self.agents["destination"].process_request(travel_request)
        
        # Step 2: Then get flights based on likely destinations
        print("2. ✈️ Consulting Flight Expert...")
        results["flights"] = await self.agents["flights"].process_request(travel_request)
        
        # Step 3: Finally get accommodation
        print("3. 🏨 Consulting Accommodation Expert...")
        results["accommodation"] = await self.agents["accommodation"].process_request(travel_request)
        
        return results
    
    async def parallel_orchestration(self, travel_request: str) -> dict:
        """PARALLEL: All agents process simultaneously"""
        print("🚀 Starting PARALLEL Orchestration")
        print("Pattern: All experts work simultaneously")
        print("-" * 50)
        
        print("🔄 Launching all experts in parallel...")
        
        # Execute all agents at the same time
        tasks = [
            self.agents["destination"].process_request(travel_request),
            self.agents["flights"].process_request(travel_request),
            self.agents["accommodation"].process_request(travel_request)
        ]
        
        destination_result, flights_result, accommodation_result = await asyncio.gather(*tasks)
        
        return {
            "destination": destination_result,
            "flights": flights_result,
            "accommodation": accommodation_result
        }
    
    async def conditional_orchestration(self, travel_request: str) -> dict:
        """CONDITIONAL: Only use relevant agents based on request"""
        print("🚀 Starting CONDITIONAL Orchestration")
        print("Pattern: Smart agent selection based on request")
        print("-" * 50)
        
        # Simple rule-based conditional logic
        request_lower = travel_request.lower()
        results = {}
        
        # Determine which agents are needed
        needs_destination = any(word in request_lower for word in ['where', 'destination', 'place', 'location', 'go'])
        needs_flights = any(word in request_lower for word in ['flight', 'fly', 'airline', 'travel to'])
        needs_accommodation = any(word in request_lower for word in ['stay', 'hotel', 'accommodation', 'lodging'])
        
        print(f"🤖 Smart Analysis: Destination={needs_destination}, Flights={needs_flights}, Accommodation={needs_accommodation}")
        
        # Only call needed agents
        if needs_destination:
            print("🗺️ Consulting Destination Expert...")
            results["destination"] = await self.agents["destination"].process_request(travel_request)
        
        if needs_flights:
            print("✈️ Consulting Flight Expert...")
            results["flights"] = await self.agents["flights"].process_request(travel_request)
        
        if needs_accommodation:
            print("🏨 Consulting Accommodation Expert...")
            results["accommodation"] = await self.agents["accommodation"].process_request(travel_request)
        
        return results

    def display_results(self, results: dict, pattern_name: str):
        """Display results in a clean format"""
        print(f"\n🎉 {pattern_name.upper()} ORCHESTRATION RESULTS")
        print("=" * 60)
        
        for agent_type, result in results.items():
            print(f"\n{result}")
            print("-" * 40)

async def main():
    print("🌍 SIMPLIFIED TRAVEL PLANNING DEMO")
    print("Multi-Agent Orchestration Patterns")
    print("=" * 50)
    
    # Check environment
    required_vars = ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing environment variables. Please check your .env file.")
        return
    
    orchestrator = TravelOrchestrator()
    
    # Simple travel scenarios
    travel_requests = [
        "I want to go to Europe for 2 weeks in summer. Budget is medium. I like history and culture.",
        "Need a beach vacation for 7 days. Flying from New York. All-inclusive resort preferred.",
        "Business trip to Tokyo for 5 days. Need flights and hotel near city center."
    ]
    
    orchestration_patterns = [
        ("SEQUENTIAL", orchestrator.sequential_orchestration),
        ("PARALLEL", orchestrator.parallel_orchestration),
        ("CONDITIONAL", orchestrator.conditional_orchestration)
    ]
    
    # Test each orchestration pattern with the first request
    travel_request = travel_requests[0]
    
    print(f"📝 TRAVEL REQUEST: {travel_request}")
    print("\n" + "=" * 50)
    
    for pattern_name, pattern_function in orchestration_patterns:
        print(f"\n🔧 Testing {pattern_name} Pattern:")
        print("=" * 50)
        
        try:
            results = await pattern_function(travel_request)
            orchestrator.display_results(results, pattern_name)
            
            # Small pause between patterns
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(main())