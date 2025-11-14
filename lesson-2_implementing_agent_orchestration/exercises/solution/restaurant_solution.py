import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents.runtime import InProcessRuntime
from dotenv import load_dotenv

load_dotenv("../../../.env")

class RestaurantAgentManager:
    """Complete restaurant recommendation system with modern Semantic Kernel 1.37.0"""
    
    def __init__(self):
        # Shared kernel instance for optimal resource usage
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_restaurant_chat",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
        
        # Initialize specialized restaurant agents with detailed instructions
        self.agents = {
            "cuisine": ChatCompletionAgent(
                kernel=self.kernel,
                name="Cuisine_Expert",
                description="Specialist in cuisine recommendations and food types",
                instructions="""You are an expert in cuisine and food types. 
                Recommend specific cuisines and dishes based on dining preferences.
                
                Always provide:
                - 2-3 recommended cuisine types that fit the request
                - Brief explanation why each cuisine is appropriate
                - 2-3 popular dishes to try from each cuisine
                - Dietary considerations and alternatives
                
                Focus on matching cuisines to the occasion, preferences, and dietary needs."""
            ),
            "location": ChatCompletionAgent(
                kernel=self.kernel,
                name="Location_Expert",
                description="Specialist in dining locations and neighborhood recommendations",
                instructions="""You are an expert in dining locations and neighborhoods.
                Recommend the best areas and locations for restaurant experiences.
                
                Always include:
                - 2-3 recommended neighborhoods or dining districts
                - Atmosphere and vibe descriptions for each area
                - Transportation, parking, and accessibility advice
                - Best times to visit and crowd levels
                
                Focus on locations that match the dining occasion and preferences."""
            ),
            "price": ChatCompletionAgent(
                kernel=self.kernel,
                name="Price_Expert",
                description="Specialist in budget and price range recommendations",
                instructions="""You are an expert in restaurant pricing and budget planning.
                Provide comprehensive budget guidance and cost expectations.
                
                Always include:
                - Recommended price ranges ($, $$, $$$) with explanations
                - Estimated cost per person for different dining experiences
                - Value-for-money recommendations and hidden gems
                - Cost-saving strategies and timing tips
                
                Focus on helping diners make informed financial decisions."""
            ),
            "coordinator": ChatCompletionAgent(
                kernel=self.kernel,
                name="Restaurant_Coordinator",
                description="Coordinates and synthesizes all restaurant recommendations",
                instructions="""You are a restaurant coordinator that synthesizes inputs from all specialists.
                Create comprehensive, integrated dining recommendations with clear guidance.
                
                Always provide:
                - Consolidated restaurant recommendations with specific suggestions
                - Budget breakdown and cost optimization strategies
                - Location and timing coordination
                - Final recommendations and reservation tips
                
                Create practical, enjoyable, and well-organized dining plans."""
            )
        }
        
        self.runtime = InProcessRuntime()

    async def sequential_orchestration(self, request: str) -> dict:
        """SEQUENTIAL: Context-aware chain where each agent builds on previous work"""
        print("🚀 Starting SEQUENTIAL Orchestration")
        print("Pattern: Cuisine → Location → Price → Coordinator")
        print("-" * 60)
        
        self.runtime.start()
        
        try:
            results = {}
            
            # Step 1: Cuisine recommendations (foundation)
            print("1. 🍽️ Consulting Cuisine Expert...")
            cuisine_response = await self.agents["cuisine"].get_response(request)
            cuisine_content = str(cuisine_response.content)
            results["cuisine"] = f"🍽️ **Cuisine Recommendations**\n\n{cuisine_content}"
            print(f"   ✓ Cuisine analysis complete: {len(cuisine_content)} characters")
            
            # Step 2: Location recommendations (using cuisine context)
            print("2. 📍 Consulting Location Expert...")
            location_prompt = f"""Original Request: {request}

Cuisine Analysis:
{cuisine_content}

Provide location recommendations that work well with these cuisine types."""
            
            location_response = await self.agents["location"].get_response(location_prompt)
            location_content = str(location_response.content)
            results["location"] = f"📍 **Location Recommendations**\n\n{location_content}"
            print(f"   ✓ Location analysis complete: {len(location_content)} characters")
            
            # Step 3: Price recommendations (using cuisine + location context)
            print("3. 💰 Consulting Price Expert...")
            price_prompt = f"""Original Request: {request}

Cuisine Analysis:
{cuisine_content}

Location Analysis:
{location_content}

Provide price range recommendations that fit these cuisine and location choices."""
            
            price_response = await self.agents["price"].get_response(price_prompt)
            price_content = str(price_response.content)
            results["price"] = f"💰 **Price Recommendations**\n\n{price_content}"
            print(f"   ✓ Price analysis complete: {len(price_content)} characters")
            
            # Step 4: Integrated coordination
            print("4. 📋 Generating Integrated Recommendation...")
            coordinator_prompt = f"""Create a comprehensive restaurant recommendation based on all specialist inputs:

ORIGINAL REQUEST: {request}

CUISINE ANALYSIS:
{cuisine_content}

LOCATION ANALYSIS:
{location_content}

PRICE ANALYSIS:
{price_content}

Synthesize this into a cohesive dining plan with specific restaurant suggestions, budget summary, and reservation advice."""
            
            coordinator_response = await self.agents["coordinator"].get_response(coordinator_prompt)
            coordinator_content = str(coordinator_response.content)
            results["coordinator"] = f"📋 **Integrated Restaurant Plan**\n\n{coordinator_content}"
            print(f"   ✓ Integrated plan complete: {len(coordinator_content)} characters")
            
            return results
            
        except Exception as e:
            print(f"❌ Sequential orchestration error: {e}")
            raise
        finally:
            await self.runtime.stop_when_idle()

    async def parallel_orchestration(self, request: str) -> dict:
        """PARALLEL: All agents work simultaneously for efficiency"""
        print("🚀 Starting PARALLEL Orchestration")
        print("Pattern: All experts work simultaneously")
        print("-" * 60)
        
        print("🔄 Launching all restaurant experts in parallel...")
        
        # Create tasks for all agents
        tasks = {
            "cuisine": self._get_agent_response(self.agents["cuisine"], request, "🍽️ Cuisine"),
            "location": self._get_agent_response(self.agents["location"], request, "📍 Location"),
            "price": self._get_agent_response(self.agents["price"], request, "💰 Price")
        }
        
        # Execute all agents simultaneously
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Process results
        formatted_results = {}
        for (agent_name, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                formatted_results[agent_name] = f"❌ Error: {result}"
            else:
                formatted_results[agent_name] = result
        
        print("✅ All parallel analyses completed!")
        return formatted_results

    async def conditional_orchestration(self, request: str) -> dict:
        """CONDITIONAL: Smart agent selection based on request analysis"""
        print("🚀 Starting CONDITIONAL Orchestration")
        print("Pattern: Intelligent agent selection based on request content")
        print("-" * 60)
        
        # Enhanced keyword-based conditional logic
        request_lower = request.lower()
        results = {}
        
        # Smart routing based on request content patterns
        needs_cuisine = any(phrase in request_lower for phrase in [
            'food', 'cuisine', 'italian', 'mexican', 'asian', 'type of food',
            'kind of restaurant', 'what to eat', 'dish', 'menu'
        ])
        
        needs_location = any(phrase in request_lower for phrase in [
            'where', 'location', 'area', 'neighborhood', 'place', 'part of town',
            'district', 'near', 'close to', 'in the'
        ])
        
        needs_price = any(phrase in request_lower for phrase in [
            'price', 'budget', 'cost', 'cheap', 'expensive', 'affordable',
            '$', 'money', 'how much', 'costly', 'inexpensive'
        ])
        
        print(f"🤖 Smart Routing: Cuisine={needs_cuisine}, Location={needs_location}, Price={needs_price}")
        
        # Execute only needed agents in parallel
        tasks = []
        agent_mapping = {}
        
        if needs_cuisine:
            task = self._get_agent_response(self.agents["cuisine"], request, "🍽️ Cuisine")
            tasks.append(task)
            agent_mapping[task] = "cuisine"
        
        if needs_location:
            task = self._get_agent_response(self.agents["location"], request, "📍 Location")
            tasks.append(task)
            agent_mapping[task] = "location"
        
        if needs_price:
            task = self._get_agent_response(self.agents["price"], request, "💰 Price")
            tasks.append(task)
            agent_mapping[task] = "price"
        
        if tasks:
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for task, result in zip(tasks, agent_results):
                agent_name = agent_mapping[task]
                if isinstance(result, Exception):
                    results[agent_name] = f"❌ Error: {result}"
                else:
                    results[agent_name] = result
        else:
            print("ℹ️  No specific agents needed - providing general restaurant advice")
            general_response = await self.agents["cuisine"].get_response(request)
            results["general"] = f"🍴 **Restaurant Advice**\n\n{general_response.content}"
        
        return results

    async def _get_agent_response(self, agent: ChatCompletionAgent, request: str, role: str = "") -> str:
        """Helper method to get agent response with proper formatting"""
        try:
            response = await agent.get_response(request)
            if role:
                emoji = role.split()[0]
                return f"{emoji} **{role.split(' ', 1)[1]} Recommendations**\n\n{response.content}"
            return str(response.content)
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def display_results(self, results: dict, pattern_name: str):
        """Display results in a clean, organized format"""
        print(f"\n🎉 {pattern_name.upper()} ORCHESTRATION COMPLETE")
        print("=" * 70)
        
        for agent_type, result in results.items():
            print(f"\n{result}")
            print("─" * 50)

async def main():
    """Main demo function showcasing all orchestration patterns"""
    print("🍴 RESTAURANT RECOMMENDATION SYSTEM - COMPLETE SOLUTION")
    print("Modern Multi-Agent Orchestration with Semantic Kernel 1.37.0")
    print("=" * 70)
    
    # Validate environment setup
    required_vars = [
        "AZURE_TEXTGENERATOR_DEPLOYMENT_NAME",
        "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", 
        "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return
    
    manager = RestaurantAgentManager()
    
    # Restaurant recommendation scenarios
    restaurant_scenarios = [
        "I want to celebrate my anniversary with a romantic dinner. We like Italian food and have a medium budget.",
        "Looking for a family-friendly restaurant that has options for kids and adults. Prefer casual dining.",
        "Business lunch meeting tomorrow. Need a quiet place with good food that's not too expensive.",
        "Where can I find authentic Mexican food in the downtown area? Budget is flexible."
    ]
    
    # Test each orchestration pattern
    for i, restaurant_request in enumerate(restaurant_scenarios[:2], 1):
        print(f"\n📝 SCENARIO {i}: {restaurant_request}")
        print("=" * 70)
        
        orchestration_patterns = [
            ("SEQUENTIAL", manager.sequential_orchestration),
            ("PARALLEL", manager.parallel_orchestration),
            ("CONDITIONAL", manager.conditional_orchestration)
        ]
        
        for pattern_name, pattern_function in orchestration_patterns:
            print(f"\n🔧 Testing {pattern_name} Pattern:")
            print("=" * 70)
            
            try:
                results = await pattern_function(restaurant_request)
                manager.display_results(results, pattern_name)
                
                # Brief pause between patterns for readability
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Pattern execution failed: {e}")
                continue
    
    print("\n✅ Demo completed! All restaurant orchestration patterns tested successfully.")

if __name__ == "__main__":
    asyncio.run(main())