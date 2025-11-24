import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents.runtime import InProcessRuntime
from dotenv import load_dotenv

load_dotenv("../../../.env")

class RestaurantAgentManager:
    """Modern restaurant recommendation manager using Semantic Kernel 1.37.0"""
    
    def __init__(self):
        # TODO: Create a shared kernel instance for all agents
        # This will optimize resource usage and improve performance
        self.kernel = Kernel()
        
        # TODO: Add Azure OpenAI service to the shared kernel
        # Use the environment variables for configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_restaurant_chat",
                deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_DEPLOYMENT_KEY"]
            )
        )
        
        # TODO: Initialize specialized restaurant agents using ChatCompletionAgent
        # Each agent should have a name, description, and detailed instructions
        self.agents = {
            "cuisine": None,     # TODO: Create Cuisine Expert agent
            "location": None,    # TODO: Create Location Expert agent
            "price": None,       # TODO: Create Price Range Expert agent
            "coordinator": None  # TODO: Create Restaurant Coordinator agent
        }
        
        # TODO: Initialize the runtime for agent execution
        self.runtime = InProcessRuntime()

    async def sequential_orchestration(self, request: str) -> dict:
        """SEQUENTIAL: Agents process in order with context sharing"""
        print("🚀 Starting SEQUENTIAL Orchestration")
        print("Pattern: Cuisine → Location → Price → Coordinator")
        print("-" * 60)
        
        # TODO: Implement sequential orchestration
        # Steps should be:
        # 1. Start runtime
        # 2. Cuisine agent analyzes first
        # 3. Location agent builds on cuisine analysis
        # 4. Price agent integrates cuisine and location context
        # 5. Coordinator creates integrated recommendation
        # 6. Stop runtime
        
        if not all([self.agents["cuisine"], self.agents["location"], self.agents["price"]]):
            print("❌ Not all agents are initialized. Complete the TODOs first!")
            return {}
        
        self.runtime.start()
        
        try:
            # Step 1: Cuisine analysis
            print("1. 🍽️ Consulting Cuisine Expert...")
            # TODO: Get cuisine analysis and display results
            
            # Step 2: Location analysis (with cuisine context)
            print("2. 📍 Consulting Location Expert...")
            # TODO: Get location analysis using cuisine context
            
            # Step 3: Price analysis (with cuisine and location context)
            print("3. 💰 Consulting Price Expert...")
            # TODO: Get price analysis using both cuisine and location context
            
            # Step 4: Generate integrated summary
            print("4. 📋 Generating Integrated Recommendation...")
            # TODO: Create comprehensive restaurant recommendation
            
            print("🎯 Sequential Collaboration Completed!")
            return {}  # TODO: Return actual results
            
        except Exception as e:
            print(f"❌ Sequential orchestration error: {e}")
            return {}
        finally:
            await self.runtime.stop_when_idle()

    async def parallel_orchestration(self, request: str) -> dict:
        """PARALLEL: All agents process simultaneously for efficiency"""
        print("🚀 Starting PARALLEL Orchestration")
        print("Pattern: All experts work simultaneously")
        print("-" * 60)
        
        print("🔄 Launching all restaurant experts in parallel...")
        
        # TODO: Implement parallel orchestration
        # Steps:
        # 1. Create tasks for all agents (cuisine, location, price)
        # 2. Use asyncio.gather to run them simultaneously
        # 3. Return the results in a dictionary
        
        if not all([self.agents["cuisine"], self.agents["location"], self.agents["price"]]):
            print("❌ Not all agents are initialized. Complete the TODOs first!")
            return {}
        
        tasks = {
            "🍽️ Cuisine": self._get_agent_response(self.agents["cuisine"], request),
            "📍 Location": self._get_agent_response(self.agents["location"], request),
            "💰 Price": self._get_agent_response(self.agents["price"], request)
        }
        
        # TODO: Execute all analyses in parallel and return results
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # TODO: Process and format the results
        formatted_results = {}
        for (role, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                formatted_results[role.split()[1].lower()] = f"❌ Error: {result}"
            else:
                formatted_results[role.split()[1].lower()] = result
        
        return formatted_results

    async def conditional_orchestration(self, request: str) -> dict:
        """CONDITIONAL: Smart agent selection based on request analysis"""
        print("🚀 Starting CONDITIONAL Orchestration")
        print("Pattern: Intelligent agent selection based on request content")
        print("-" * 60)
        
        # TODO: Implement conditional orchestration
        # Steps:
        # 1. Analyze the request to determine which agents are needed
        # 2. Use keyword matching or AI analysis to decide
        # 3. Only call the relevant agents
        # 4. Return results from only those agents
        
        if not all([self.agents["cuisine"], self.agents["location"], self.agents["price"]]):
            print("❌ Not all agents are initialized. Complete the TODOs first!")
            return {}
        
        # TODO: Analyze request to determine needed agents
        request_lower = request.lower()
        results = {}
        
        # TODO: Implement smart routing logic
        needs_cuisine = False  # TODO: Set based on request analysis
        needs_location = False  # TODO: Set based on request analysis  
        needs_price = False  # TODO: Set based on request analysis
        
        print(f"🤖 Smart Analysis: Cuisine={needs_cuisine}, Location={needs_location}, Price={needs_price}")
        
        # TODO: Execute only needed agents
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
        
        # TODO: Execute tasks and process results
        if tasks:
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)
            # TODO: Process results...
        else:
            print("ℹ️  No specific agents needed - providing general restaurant advice")
        
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
    """Main exercise function"""
    print("🍴 RESTAURANT RECOMMENDATION SYSTEM - STUDENT EXERCISE")
    print("Modern Multi-Agent Orchestration with Semantic Kernel 1.37.0")
    print("=" * 70)
    print("Complete the TODOs to build your restaurant recommendation system!")
    print()
    
    # Validate environment setup
    required_vars = [
        "AZURE_DEPLOYMENT_NAME",
        "AZURE_DEPLOYMENT_ENDPOINT", 
        "AZURE_DEPLOYMENT_KEY"
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
    
    # TODO: Uncomment when agents are implemented
    # for i, scenario in enumerate(restaurant_scenarios[:2], 1):
    #     print(f"\n📝 Scenario {i}: {scenario}")
    #     print("=" * 70)
    #     await manager.run_parallel_analysis(scenario)
    
    # Test orchestration patterns
    restaurant_request = restaurant_scenarios[0]
    
    print(f"📝 RESTAURANT REQUEST: {restaurant_request}")
    print("\n" + "=" * 70)
    
    # Test sequential orchestration (partially implemented)
    print(f"\n🔧 Testing SEQUENTIAL Pattern:")
    print("=" * 70)
    
    try:
        results = await manager.sequential_orchestration(restaurant_request)
        manager.display_results(results, "sequential")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎓 Exercise Instructions:")
    print("1. Create all agents in the __init__ method with proper configurations")
    print("2. Implement sequential orchestration with context sharing")
    print("3. Complete parallel orchestration using asyncio.gather()")
    print("4. Build conditional orchestration with intelligent agent selection")
    print("5. Test with the provided restaurant scenarios")

if __name__ == "__main__":
    asyncio.run(main())