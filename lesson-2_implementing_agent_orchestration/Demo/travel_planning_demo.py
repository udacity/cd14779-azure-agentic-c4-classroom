import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents.runtime import InProcessRuntime
from dotenv import load_dotenv

load_dotenv("../../.env")

class TravelAgentManager:
    """Modern travel agent manager using Semantic Kernel 1.37.0 agent framework"""
    
    def __init__(self):
        # Single shared kernel instance for optimal resource usage
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_travel_chat",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
        
        # Initialize specialized travel agents with detailed instructions
        self.agents = {
            "destination": ChatCompletionAgent(
                kernel=self.kernel,
                name="Destination_Expert",
                description="Specialist in travel destination recommendations",
                instructions="""You are an expert travel destination specialist. 
                Recommend 2-3 perfect destinations based on travel preferences.
                
                Always provide:
                - Top 2-3 destination recommendations with brief explanations
                - Best time to visit and seasonal considerations
                - Budget level (Budget/Mid-range/Luxury) and cost expectations
                - Key attractions and activities
                - Travel style suitability (adventure, relaxation, cultural, etc.)
                
                Be specific, practical, and personalized to the user's request."""
            ),
            "flights": ChatCompletionAgent(
                kernel=self.kernel,
                name="Flight_Expert", 
                description="Specialist in flight options and travel logistics",
                instructions="""You are an expert flight and travel logistics specialist.
                Provide comprehensive flight advice and travel arrangements.
                
                Always include:
                - Best airlines and routes for the journey
                - Estimated flight durations and layover options
                - Price ranges and booking timing advice
                - Travel documentation and visa considerations
                - Airport tips and security advice
                
                Focus on practical, money-saving, and time-efficient options."""
            ),
            "accommodation": ChatCompletionAgent(
                kernel=self.kernel,
                name="Accommodation_Expert",
                description="Specialist in accommodation and lodging options",
                instructions="""You are an expert accommodation and lodging specialist.
                Provide detailed accommodation recommendations and booking advice.
                
                Always include:
                - Recommended accommodation types (hotel, rental, resort, etc.)
                - Best neighborhoods and locations for the traveler's needs
                - Price ranges and value-for-money recommendations
                - Amenities and facility considerations
                - Booking strategies and cancellation policies
                
                Focus on comfort, location, and overall travel experience."""
            ),
            "activities": ChatCompletionAgent(
                kernel=self.kernel,
                name="Activities_Expert",
                description="Specialist in tours, activities, and experiences",
                instructions="""You are an expert activities and experiences specialist.
                Recommend tours, activities, and local experiences.
                
                Always include:
                - Must-do activities and hidden gems
                - Tour operators and booking recommendations
                - Timing and duration suggestions
                - Cost ranges and budget options
                - Local culture and etiquette tips
                
                Focus on creating memorable, authentic travel experiences."""
            ),
            "coordinator": ChatCompletionAgent(
                kernel=self.kernel,
                name="Travel_Coordinator",
                description="Coordinates and synthesizes all travel recommendations",
                instructions="""You are a travel coordinator that synthesizes inputs from all specialists.
                Create comprehensive, integrated travel plans with clear itineraries.
                
                Always provide:
                - Consolidated daily itinerary suggestions
                - Budget breakdown and cost optimization
                - Timing and logistics coordination
                - Contingency plans and alternatives
                - Final recommendations and next steps
                
                Create practical, enjoyable, and well-organized travel plans."""
            )
        }
        
        self.runtime = InProcessRuntime()

    async def sequential_orchestration(self, travel_request: str) -> dict:
        """SEQUENTIAL: Context-aware chain where each agent builds on previous work"""
        print("🚀 Starting SEQUENTIAL Orchestration")
        print("Pattern: Destination → Flights → Accommodation → Activities → Coordinator")
        print("-" * 60)
        
        self.runtime.start()
        
        try:
            results = {}
            
            # Step 1: Destination recommendations (foundation)
            print("1. 🗺️ Consulting Destination Expert...")
            dest_response = await self.agents["destination"].get_response(travel_request)
            dest_content = str(dest_response.content)
            results["destination"] = f"🗺️ **Destination Recommendations**\n\n{dest_content}"
            print(f"   ✓ Destination analysis complete: {len(dest_content)} characters")
            
            # Step 2: Flight options (using destination context)
            print("2. ✈️ Consulting Flight Expert...")
            flight_prompt = f"""Original Request: {travel_request}

Destination Analysis:
{dest_content}

Provide flight recommendations considering these destinations."""
            
            flight_response = await self.agents["flights"].get_response(flight_prompt)
            flight_content = str(flight_response.content)
            results["flights"] = f"✈️ **Flight Recommendations**\n\n{flight_content}"
            print(f"   ✓ Flight analysis complete: {len(flight_content)} characters")
            
            # Step 3: Accommodation (using destination + flight context)
            print("3. 🏨 Consulting Accommodation Expert...")
            accom_prompt = f"""Original Request: {travel_request}

Destination Analysis:
{dest_content}

Flight Analysis:
{flight_content}

Provide accommodation recommendations that work with these destinations and travel plans."""
            
            accom_response = await self.agents["accommodation"].get_response(accom_prompt)
            accom_content = str(accom_response.content)
            results["accommodation"] = f"🏨 **Accommodation Recommendations**\n\n{accom_content}"
            print(f"   ✓ Accommodation analysis complete: {len(accom_content)} characters")
            
            # Step 4: Activities (using all previous context)
            print("4. 🎭 Consulting Activities Expert...")
            activities_prompt = f"""Original Request: {travel_request}

Destination Analysis:
{dest_content}

Flight & Travel Context:
{flight_content}

Accommodation Context:
{accom_content}

Provide activity and experience recommendations that complement the overall travel plan."""
            
            activities_response = await self.agents["activities"].get_response(activities_prompt)
            activities_content = str(activities_response.content)
            results["activities"] = f"🎭 **Activity Recommendations**\n\n{activities_content}"
            print(f"   ✓ Activities analysis complete: {len(activities_content)} characters")
            
            # Step 5: Integrated coordination
            print("5. 📋 Generating Integrated Travel Plan...")
            coordinator_prompt = f"""Create a comprehensive travel plan based on all specialist inputs:

ORIGINAL REQUEST: {travel_request}

DESTINATION ANALYSIS:
{dest_content}

FLIGHT ANALYSIS:
{flight_content}

ACCOMMODATION ANALYSIS:
{accom_content}

ACTIVITIES ANALYSIS:
{activities_content}

Synthesize this into a cohesive travel itinerary with clear recommendations, budget summary, and next steps."""
            
            coordinator_response = await self.agents["coordinator"].get_response(coordinator_prompt)
            coordinator_content = str(coordinator_response.content)
            results["coordinator"] = f"📋 **Integrated Travel Plan**\n\n{coordinator_content}"
            print(f"   ✓ Integrated plan complete: {len(coordinator_content)} characters")
            
            return results
            
        except Exception as e:
            print(f"❌ Sequential orchestration error: {e}")
            raise
        finally:
            await self.runtime.stop_when_idle()

    async def parallel_orchestration(self, travel_request: str) -> dict:
        """PARALLEL: All agents work simultaneously for efficiency"""
        print("🚀 Starting PARALLEL Orchestration")
        print("Pattern: All experts work simultaneously")
        print("-" * 60)
        
        print("🔄 Launching all travel experts in parallel...")
        
        # Create tasks for all agents
        tasks = {
            "destination": self._get_agent_response(self.agents["destination"], travel_request, "🗺️ Destination"),
            "flights": self._get_agent_response(self.agents["flights"], travel_request, "✈️ Flights"),
            "accommodation": self._get_agent_response(self.agents["accommodation"], travel_request, "🏨 Accommodation"),
            "activities": self._get_agent_response(self.agents["activities"], travel_request, "🎭 Activities")
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

    async def conditional_orchestration(self, travel_request: str) -> dict:
        """CONDITIONAL: Smart agent selection based on request analysis"""
        print("🚀 Starting CONDITIONAL Orchestration")
        print("Pattern: Intelligent agent selection based on request content")
        print("-" * 60)
        
        # Use AI to analyze which agents are needed
        analysis_prompt = f"""Analyze this travel request and determine which specialists are needed:

REQUEST: {travel_request}

Available specialists:
- destination: For "where to go", destination recommendations, place suggestions
- flights: For "how to get there", flights, transportation, travel logistics  
- accommodation: For "where to stay", hotels, lodging, accommodation
- activities: For "what to do", tours, experiences, activities

For each specialist, provide:
- Needed: Yes/No
- Reason: Brief explanation
- Priority: High/Medium/Low

Respond in a structured format."""
        
        self.runtime.start()
        
        try:
            # Analyze request to determine needed agents
            print("🔍 Analyzing request to determine needed specialists...")
            analysis_response = await self.agents["destination"].get_response(analysis_prompt)
            analysis_content = str(analysis_response.content)
            print(f"Request Analysis:\n{analysis_content}\n")
            
            # Smart routing based on common patterns (enhanced from simple keyword matching)
            request_lower = travel_request.lower()
            results = {}
            
            # Destination agent: Needed for planning new trips
            needs_destination = any(phrase in request_lower for phrase in [
                'where should', 'recommend destination', 'place to visit', 'where to go',
                'planning trip', 'vacation ideas', 'travel destination'
            ]) or ('where' in request_lower and 'go' in request_lower)
            
            # Flights agent: Needed when transportation is mentioned
            needs_flights = any(phrase in request_lower for phrase in [
                'flight', 'fly', 'airline', 'how to get', 'travel to', 'getting there',
                'transportation', 'airport'
            ])
            
            # Accommodation agent: Needed when lodging is mentioned
            needs_accommodation = any(phrase in request_lower for phrase in [
                'hotel', 'stay', 'accommodation', 'lodging', 'where to stay',
                'place to stay', 'resort'
            ])
            
            # Activities agent: Needed for experiences and tours
            needs_activities = any(phrase in request_lower for phrase in [
                'things to do', 'activities', 'tours', 'experiences', 'sightseeing',
                'what to do', 'attractions'
            ])
            
            print(f"🤖 Smart Routing: Destination={needs_destination}, Flights={needs_flights}, "
                  f"Accommodation={needs_accommodation}, Activities={needs_activities}")
            
            # Execute only needed agents in parallel
            tasks = []
            agent_mapping = {}
            
            if needs_destination:
                task = self._get_agent_response(self.agents["destination"], travel_request, "🗺️ Destination")
                tasks.append(task)
                agent_mapping[task] = "destination"
            
            if needs_flights:
                task = self._get_agent_response(self.agents["flights"], travel_request, "✈️ Flights")
                tasks.append(task)
                agent_mapping[task] = "flights"
            
            if needs_accommodation:
                task = self._get_agent_response(self.agents["accommodation"], travel_request, "🏨 Accommodation")
                tasks.append(task)
                agent_mapping[task] = "accommodation"
            
            if needs_activities:
                task = self._get_agent_response(self.agents["activities"], travel_request, "🎭 Activities")
                tasks.append(task)
                agent_mapping[task] = "activities"
            
            if tasks:
                agent_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for task, result in zip(tasks, agent_results):
                    agent_name = agent_mapping[task]
                    if isinstance(result, Exception):
                        results[agent_name] = f"❌ Error: {result}"
                    else:
                        results[agent_name] = result
            else:
                print("ℹ️  No specific agents needed - providing general travel advice")
                general_response = await self.agents["destination"].get_response(travel_request)
                results["general"] = f"🌍 **Travel Advice**\n\n{general_response.content}"
            
            return results
            
        except Exception as e:
            print(f"❌ Conditional orchestration error: {e}")
            raise
        finally:
            await self.runtime.stop_when_idle()

    async def _get_agent_response(self, agent: ChatCompletionAgent, request: str, role: str) -> str:
        """Helper method to get agent response with proper formatting"""
        try:
            response = await agent.get_response(request)
            emoji = role.split()[0]  # Get the emoji from role
            return f"{emoji} **{role.split(' ', 1)[1]} Recommendations**\n\n{response.content}"
        except Exception as e:
            return f"❌ {role} Error: {str(e)}"

    def display_results(self, results: dict, pattern_name: str):
        """Display results in a clean, organized format"""
        print(f"\n🎉 {pattern_name.upper()} ORCHESTRATION COMPLETE")
        print("=" * 70)
        
        for agent_type, result in results.items():
            print(f"\n{result}")
            print("─" * 50)

async def main():
    """Main demo function showcasing all orchestration patterns"""
    print("🌍 TRAVEL AGENT ORCHESTRATION DEMO")
    print("Semantic Kernel 1.37.0 - Modern Multi-Agent Patterns")
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
    
    manager = TravelAgentManager()
    
    # Diverse travel scenarios to test different patterns
    travel_scenarios = [
        "I want to plan a 2-week cultural trip to Europe this summer. Interested in history, art, and local cuisine. Budget is mid-range.",
        "Business trip to Tokyo for 5 days. Need efficient flights and a comfortable hotel near the business district. Will have 2 free evenings for sightseeing."
    ]
    
    orchestration_patterns = [
        ("SEQUENTIAL", manager.sequential_orchestration),
        ("PARALLEL", manager.parallel_orchestration), 
        ("CONDITIONAL", manager.conditional_orchestration)
    ]
    
    # Test each orchestration pattern
    for i, travel_request in enumerate(travel_scenarios[:2], 1):  # Test with first 2 scenarios
        print(f"\n📝 SCENARIO {i}: {travel_request}")
        print("=" * 70)
        
        for pattern_name, pattern_function in orchestration_patterns:
            print(f"\n🔧 Testing {pattern_name} Pattern:")
            print("=" * 70)
            
            try:
                results = await pattern_function(travel_request)
                manager.display_results(results, pattern_name)
                
                # Brief pause between patterns for readability
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Pattern execution failed: {e}")
                continue
    
    print("\n✅ Demo completed! All orchestration patterns tested successfully.")

if __name__ == "__main__":
    asyncio.run(main())