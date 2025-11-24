import asyncio
import os
from typing import Dict
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents import ChatHistory
from dotenv import load_dotenv

load_dotenv("../.env")

# Modern KernelBaseModel for State Management
class PastaOrder(KernelBaseModel):
    """Model representing a pasta order using KernelBaseModel"""
    order_id: str
    customer_name: str
    pasta_type: str
    sauce: str
    status: str = "received"
    order_date: datetime = datetime.now()
    
    def is_ready(self) -> bool:
        """Check if order is ready"""
        return self.status == 'ready'
    
    def get_order_details(self) -> str:
        """Get formatted order information"""
        status_icons = {
            'received': '📥',
            'preparing': '👨‍🍳', 
            'cooking': '🍳',
            'ready': '✅',
            'served': '🍝'
        }
        icon = status_icons.get(self.status, '📦')
        return f"{icon} Order {self.order_id}: {self.pasta_type} with {self.sauce} for {self.customer_name} - Status: {self.status}"

class KitchenResource(KernelBaseModel):
    """Model representing kitchen resources using KernelBaseModel"""
    resource_id: str
    name: str
    capacity: int
    current_usage: int = 0
    
    def is_available(self) -> bool:
        """Check if resource is available"""
        return self.current_usage < self.capacity
    
    def get_resource_status(self) -> str:
        """Get formatted resource status"""
        status = "🟢 Available" if self.is_available() else "🔴 Busy"
        return f"{self.name}: {self.current_usage}/{self.capacity} - {status}"

class PastaFactoryState(KernelBaseModel):
    """Central state management for the pasta factory using KernelBaseModel"""
    orders: Dict[str, PastaOrder] = {}
    resources: Dict[str, KitchenResource] = {}
    completed_orders: int = 0
    daily_special: str = "Spaghetti Carbonara"
    
    def add_order(self, order: PastaOrder) -> str:
        """Add a new order"""
        self.orders[order.order_id] = order
        return f"✅ Added order {order.order_id} for {order.customer_name}"
    
    def update_order_status(self, order_id: str, status: str) -> str:
        """Update order status"""
        if order_id in self.orders:
            self.orders[order_id].status = status
            return f"✅ Updated order {order_id} to {status}"
        return f"❌ Order {order_id} not found"
    
    def allocate_resource(self, resource_id: str) -> str:
        """Allocate a kitchen resource"""
        if resource_id in self.resources and self.resources[resource_id].is_available():
            self.resources[resource_id].current_usage += 1
            return f"✅ Allocated {self.resources[resource_id].name}"
        return f"❌ Resource {resource_id} not available"
    
    def release_resource(self, resource_id: str) -> str:
        """Release a kitchen resource"""
        if resource_id in self.resources:
            self.resources[resource_id].current_usage = max(0, self.resources[resource_id].current_usage - 1)
            return f"✅ Released {self.resources[resource_id].name}"
        return f"❌ Resource {resource_id} not found"
    
    def get_factory_status(self) -> str:
        """Get comprehensive factory status"""
        total_orders = len(self.orders)
        active_orders = len([o for o in self.orders.values() if o.status != 'served'])
        
        available_resources = len([r for r in self.resources.values() if r.is_available()])
        total_resources = len(self.resources)
        
        return f"""
        🍝 PASTA FACTORY STATUS:
        • Orders: {total_orders} total ({active_orders} active, {self.completed_orders} completed)
        • Resources: {available_resources}/{total_resources} available
        • Daily Special: {self.daily_special}
        • Efficiency: {(self.completed_orders/max(1, total_orders))*100:.1f}%
        """
    
    def get_order_metrics(self) -> str:
        """Get order metrics and statistics"""
        status_count = {}
        pasta_types = {}
        
        for order in self.orders.values():
            status_count[order.status] = status_count.get(order.status, 0) + 1
            pasta_types[order.pasta_type] = pasta_types.get(order.pasta_type, 0) + 1
        
        metrics = "📊 ORDER METRICS:\n"
        metrics += "Status Distribution:\n"
        for status, count in status_count.items():
            icon = '📥' if status == 'received' else '👨‍🍳' if status == 'preparing' else '🍳' if status == 'cooking' else '✅' if status == 'ready' else '🍝'
            metrics += f"  {icon} {status}: {count} orders\n"
        
        metrics += "\nPopular Pasta Types:\n"
        for pasta, count in sorted(pasta_types.items(), key=lambda x: x[1], reverse=True)[:3]:
            metrics += f"  🍝 {pasta}: {count} orders\n"
        
        return metrics
    
    def get_kitchen_capacity(self) -> str:
        """Get kitchen capacity analysis"""
        capacity = "👨‍🍳 KITCHEN CAPACITY:\n"
        
        for resource in self.resources.values():
            utilization = (resource.current_usage / resource.capacity) * 100
            status = "🟢 Good" if utilization < 70 else "🟡 Moderate" if utilization < 90 else "🔴 Critical"
            capacity += f"• {resource.name}: {resource.current_usage}/{resource.capacity} ({utilization:.1f}%) - {status}\n"
        
        available_count = len([r for r in self.resources.values() if r.is_available()])
        capacity += f"\n📈 Available Stations: {available_count}/{len(self.resources)}"
        
        return capacity

class PastaFactoryPlugin:
    """Plugin for pasta factory operations with kernel functions"""
    
    def __init__(self, factory_state: PastaFactoryState):
        self.factory_state = factory_state
    
    @kernel_function(
        name="get_comprehensive_factory_status",
        description="Get complete factory status with all metrics"
    )
    def get_comprehensive_status(self) -> str:
        """Get comprehensive factory status"""
        status = self.factory_state.get_factory_status()
        metrics = self.factory_state.get_order_metrics()
        capacity = self.factory_state.get_kitchen_capacity()
        
        return f"{status}\n{metrics}\n{capacity}"
    
    @kernel_function(
        name="get_factory_status",
        description="Get factory status overview"
    )
    def get_factory_status(self) -> str:
        """Get factory status"""
        return self.factory_state.get_factory_status()
    
    @kernel_function(
        name="get_order_metrics",
        description="Get order metrics and statistics"
    )
    def get_order_metrics(self) -> str:
        """Get order metrics"""
        return self.factory_state.get_order_metrics()
    
    @kernel_function(
        name="get_kitchen_capacity",
        description="Get kitchen resource capacity analysis"
    )
    def get_kitchen_capacity(self) -> str:
        """Get kitchen capacity"""
        return self.factory_state.get_kitchen_capacity()
    
    @kernel_function(
        name="update_order_status",
        description="Update order status with validation"
    )
    def update_order_status(self, order_id: str, status: str) -> str:
        """Update order status"""
        return self.factory_state.update_order_status(order_id, status)
    
    @kernel_function(
        name="allocate_kitchen_resource",
        description="Allocate a kitchen resource for cooking"
    )
    def allocate_resource(self, resource_id: str) -> str:
        """Allocate a kitchen resource"""
        return self.factory_state.allocate_resource(resource_id)
    
    @kernel_function(
        name="release_kitchen_resource", 
        description="Release a kitchen resource after use"
    )
    def release_resource(self, resource_id: str) -> str:
        """Release a kitchen resource"""
        return self.factory_state.release_resource(resource_id)
    
    @kernel_function(
        name="process_pasta_order",
        description="Process a pasta order through the kitchen workflow"
    )
    def process_order(self, order_id: str) -> str:
        """Process an order through the kitchen workflow"""
        if order_id not in self.factory_state.orders:
            return f"❌ Order {order_id} not found"
        
        order = self.factory_state.orders[order_id]
        steps = []
        
        # Step 1: Allocate resources and start preparation
        if (self.factory_state.allocate_resource("R001") and  # Pasta Maker
            self.factory_state.allocate_resource("R002")):    # Sauce Station
            
            self.factory_state.update_order_status(order_id, "preparing")
            steps.append("✅ Started pasta preparation")
            
            # Step 2: Move to cooking
            if self.factory_state.allocate_resource("R003"):  # Cooking Station
                self.factory_state.update_order_status(order_id, "cooking")
                steps.append("✅ Started cooking")
                
                # Step 3: Mark as ready
                self.factory_state.update_order_status(order_id, "ready")
                steps.append("✅ Order ready for serving")
                
                # Step 4: Serve and release resources
                self.factory_state.update_order_status(order_id, "served")
                self.factory_state.release_resource("R001")
                self.factory_state.release_resource("R002") 
                self.factory_state.release_resource("R003")
                self.factory_state.completed_orders += 1
                steps.append("✅ Order served and resources released")
            else:
                steps.append("❌ Cooking station not available")
        else:
            steps.append("❌ Preparation resources not available")
        
        return f"👨‍🍳 Processing {order_id}:\n" + "\n".join(steps)

class ModernPastaFactorySystem:
    """Modern pasta factory system using Semantic Kernel 1.37.0 multi-agent framework"""
    
    def __init__(self):
        # Shared kernel instance
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_pasta_chat",
                deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_DEPLOYMENT_KEY"]
            )
        )
        
        # Initialize shared factory state
        self.factory_state = PastaFactoryState()
        self._initialize_kitchen_resources()
        
        # Initialize pasta factory plugin and register with kernel
        self.pasta_plugin = PastaFactoryPlugin(self.factory_state)
        self.kernel.add_plugin(self.pasta_plugin, "PastaFactory")
        
        # Initialize specialized pasta agents with modern framework
        self.agents = {
            "orders": ChatCompletionAgent(
                kernel=self.kernel,
                name="Order_Manager",
                description="Specialist in order management and customer service",
                instructions="""You are an order manager for an authentic Italian pasta factory. Handle customer orders and coordinate the kitchen workflow.

                Available Functions from PastaFactory Plugin:
                - get_comprehensive_factory_status: Access complete factory overview
                - get_factory_status: Get factory overview
                - get_order_metrics: View order statistics and distribution
                - process_pasta_order: Manage order processing workflow
                - update_order_status: Update order status

                Always provide:
                - Current order status and priority assessment
                - Customer service recommendations
                - Order workflow optimization suggestions
                - Authentic Italian pasta preparation insights

                Use factory data for accurate analysis and focus on customer satisfaction."""
            ),
            "kitchen": ChatCompletionAgent(
                kernel=self.kernel,
                name="Kitchen_Manager", 
                description="Specialist in kitchen resource management and cooking coordination",
                instructions="""You are a kitchen manager for an Italian pasta factory. Optimize resource allocation and cooking processes.

                Available Functions from PastaFactory Plugin:
                - get_kitchen_capacity: Access resource utilization metrics
                - get_comprehensive_factory_status: Complete factory overview
                - get_factory_status: View overall factory status
                - allocate_kitchen_resource: Manage resource allocation
                - release_kitchen_resource: Release resources after use

                Always provide:
                - Kitchen resource optimization recommendations
                - Bottleneck identification and resolution strategies
                - Cooking process efficiency improvements
                - Traditional Italian cooking technique guidance

                Focus on efficient resource management and authentic preparation."""
            ),
            "quality": ChatCompletionAgent(
                kernel=self.kernel,
                name="Quality_Manager",
                description="Specialist in authentic Italian quality standards and recipe excellence",
                instructions="""You are a quality manager maintaining authentic Italian pasta standards.

                Available Functions from PastaFactory Plugin:
                - get_comprehensive_factory_status: Access production overview
                - get_factory_status: Monitor production quality metrics
                - get_order_metrics: Analyze order patterns and preferences

                Always provide:
                - Quality assurance recommendations
                - Authentic Italian cooking technique validation
                - Recipe improvement suggestions
                - Traditional standards compliance guidance

                Emphasize authentic Italian quality and culinary excellence."""
            ),
            "coordinator": ChatCompletionAgent(
                kernel=self.kernel,
                name="Factory_Coordinator",
                description="Intelligent coordinator for pasta factory multi-agent collaboration",
                instructions="""You are the central coordinator for the pasta factory multi-agent system.

                Available Agents:
                - orders: Order management, customer service, workflow coordination
                - kitchen: Resource allocation, cooking optimization, bottleneck resolution  
                - quality: Quality assurance, authentic standards, recipe excellence

                Always:
                1. Analyze the request and determine which specialist(s) should handle it
                2. Provide brief reasoning for your routing decision
                3. Suggest any inter-agent collaboration needed for complex pasta preparation

                Respond in this exact format:
                Primary Agent: [orders/kitchen/quality]
                Supporting Agents: [comma-separated list or none]
                Reasoning: [brief explanation of routing decision]"""
            )
        }
        
        # Initialize modern orchestration runtime
        self.runtime = InProcessRuntime()
        self.chat_history = ChatHistory()

    def _initialize_kitchen_resources(self):
        """Initialize the factory with kitchen resources"""
        resources = [
            KitchenResource(resource_id="R001", name="Pasta Maker", capacity=2),
            KitchenResource(resource_id="R002", name="Sauce Station", capacity=3),
            KitchenResource(resource_id="R003", name="Cooking Station", capacity=4),
            KitchenResource(resource_id="R004", name="Assembly Line", capacity=3),
            KitchenResource(resource_id="R005", name="Quality Check", capacity=2)
        ]
        
        for resource in resources:
            self.factory_state.resources[resource.resource_id] = resource

    def place_order(self, customer_name: str, pasta_type: str, sauce: str) -> str:
        """Place a new pasta order"""
        order_id = f"ORD{len(self.factory_state.orders) + 1:03d}"
        order = PastaOrder(
            order_id=order_id,
            customer_name=customer_name,
            pasta_type=pasta_type,
            sauce=sauce
        )
        
        result = self.factory_state.add_order(order)
        print(f"📝 {result}")
        return order_id

    async def coordinate_request(self, request: str) -> Dict:
        """Intelligent coordination of factory requests using coordinator agent"""
        print(f"📨 Factory Request: {request}")
        print("🔄 Analyzing and coordinating with specialists...")
        
        coordination_prompt = f"FACTORY REQUEST: {request}"
        
        coordination_response = await self.agents["coordinator"].get_response(coordination_prompt)
        coordination_decision = self._parse_coordination_decision(str(coordination_response.content))
        
        print(f"✅ Coordination Decision:")
        print(f"   Primary Agent: {coordination_decision['primary_agent']}")
        print(f"   Supporting Agents: {coordination_decision['supporting_agents']}")
        print(f"   Reasoning: {coordination_decision['reasoning']}")
        
        return coordination_decision

    def _parse_coordination_decision(self, coordination_text: str) -> Dict:
        """Parse the coordination decision from AI response"""
        lines = [line.strip() for line in coordination_text.strip().split('\n') if line.strip()]
        
        decision = {
            "primary_agent": "orders",
            "supporting_agents": [],
            "reasoning": "Default coordination",
            "raw_response": coordination_text
        }
        
        for line in lines:
            lower_line = line.lower()
            if lower_line.startswith('primary agent:'):
                agent = line.split(':', 1)[1].strip()
                if agent in self.agents:
                    decision["primary_agent"] = agent
            elif lower_line.startswith('supporting agents:'):
                agents_text = line.split(':', 1)[1].strip()
                if agents_text.lower() != 'none':
                    decision["supporting_agents"] = [agent.strip() for agent in agents_text.split(',')]
            elif lower_line.startswith('reasoning:'):
                decision["reasoning"] = line.split(':', 1)[1].strip()
        
        return decision

    async def process_with_agent(self, request: str, agent_name: str, context: Dict = None) -> str:
        """Process request with specified agent using modern Semantic Kernel"""
        print(f"🔧 Engaging {agent_name} specialist...")
        
        # Build enhanced context with factory analytics
        factory_status = self.factory_state.get_factory_status()
        order_metrics = self.factory_state.get_order_metrics()
        kitchen_capacity = self.factory_state.get_kitchen_capacity()
        
        # Add coordination context if available
        coordination_context = ""
        if context:
            coordination_context = f"\n\nCOORDINATION CONTEXT: {context.get('reasoning', 'General request')}"
        
        enhanced_request = f"""
        FACTORY REQUEST: {request}
        
        CURRENT FACTORY STATUS:
        {factory_status}
        
        ORDER METRICS:
        {order_metrics}
        
        KITCHEN CAPACITY:
        {kitchen_capacity}
        {coordination_context}
        
        Please provide your expert analysis and recommendations based on the available data.
        """
        
        try:
            agent_response = await self.agents[agent_name].get_response(enhanced_request)
            return self._format_agent_response(agent_name, str(agent_response.content))
            
        except Exception as e:
            return f"❌ Error in {agent_name} processing: {str(e)}"

    def _format_agent_response(self, agent_name: str, content: str) -> str:
        """Format agent response with appropriate branding"""
        icons = {
            "orders": "📝",
            "kitchen": "👨‍🍳", 
            "quality": "⭐"
        }
        
        titles = {
            "orders": "Order Management Analysis",
            "kitchen": "Kitchen Optimization Recommendations", 
            "quality": "Quality Assurance Insights"
        }
        
        icon = icons.get(agent_name, "🍝")
        title = titles.get(agent_name, "Factory Analysis")
        
        return f"{icon} **{title}**\n\n{content}"

    async def process_manual_workflow(self, order_id: str) -> str:
        """Process order through manual workflow simulation"""
        print(f"🔄 Starting manual workflow for {order_id}...")
        
        workflow_steps = []
        
        try:
            # Step 1: Order Agent analyzes the order
            order_analysis = await self.agents["orders"].get_response(
                f"Analyze order {order_id} and provide preparation instructions"
            )
            workflow_steps.append(f"📝 Order Analysis: Order {order_id} analysis completed")
            
            # Step 2: Kitchen Agent allocates resources
            kitchen_plan = await self.agents["kitchen"].get_response(
                f"Allocate resources and plan cooking for order {order_id}"
            )
            workflow_steps.append(f"👨‍🍳 Kitchen Plan: Resource allocation planned")
            
            # Step 3: Quality Agent ensures standards
            quality_check = await self.agents["quality"].get_response(
                f"Ensure quality standards for order {order_id}"
            )
            workflow_steps.append(f"⭐ Quality Check: Quality standards verified")
            
            # Process the order using direct method calls (not kernel functions)
            process_result = self._process_order_directly(order_id)
            
            workflow_summary = "🎉 Manual Workflow Completed!\n\n" + "\n".join(workflow_steps) + f"\n\n{process_result}"
            return workflow_summary
            
        except Exception as e:
            # Fallback: Just process the order without agent analysis
            process_result = self._process_order_directly(order_id)
            return f"🔄 Basic Processing Completed (Agent analysis skipped due to error):\n\n{process_result}"

    def _process_order_directly(self, order_id: str) -> str:
        """Process order directly without kernel function calls"""
        if order_id not in self.factory_state.orders:
            return f"❌ Order {order_id} not found"
        
        order = self.factory_state.orders[order_id]
        steps = []
        
        # Step 1: Allocate resources and start preparation
        if (self.factory_state.allocate_resource("R001") and  # Pasta Maker
            self.factory_state.allocate_resource("R002")):    # Sauce Station
            
            self.factory_state.update_order_status(order_id, "preparing")
            steps.append("✅ Started pasta preparation")
            
            # Step 2: Move to cooking
            if self.factory_state.allocate_resource("R003"):  # Cooking Station
                self.factory_state.update_order_status(order_id, "cooking")
                steps.append("✅ Started cooking")
                
                # Step 3: Mark as ready
                self.factory_state.update_order_status(order_id, "ready")
                steps.append("✅ Order ready for serving")
                
                # Step 4: Serve and release resources
                self.factory_state.update_order_status(order_id, "served")
                self.factory_state.release_resource("R001")
                self.factory_state.release_resource("R002") 
                self.factory_state.release_resource("R003")
                self.factory_state.completed_orders += 1
                steps.append("✅ Order served and resources released")
            else:
                steps.append("❌ Cooking station not available")
        else:
            steps.append("❌ Preparation resources not available")
        
        return f"👨‍🍳 Processing {order_id}:\n" + "\n".join(steps)

    async def handle_factory_request(self, request: str) -> Dict:
        """Complete processing of a factory request with modern agent framework"""
        # Add to chat history for context
        self.chat_history.add_user_message(request)
        
        # Step 1: Coordinate the request
        coordination_decision = await self.coordinate_request(request)
        
        # Step 2: Process with primary agent
        primary_agent = coordination_decision["primary_agent"]
        if primary_agent in self.agents:
            try:
                specialist_response = await self.process_with_agent(
                    request, 
                    primary_agent,
                    coordination_decision
                )
            except Exception as e:
                specialist_response = f"❌ Error processing with {primary_agent}: {str(e)}"
            
            # Add assistant response to history
            self.chat_history.add_assistant_message(specialist_response)
            
            return {
                "coordination_decision": coordination_decision,
                "specialist_response": specialist_response,
                "agent_name": primary_agent.replace('_', ' ').title(),
                "factory_status": self.factory_state.get_factory_status(),
                "chat_history": len(self.chat_history.messages)
            }
        else:
            error_response = "❌ No suitable agent available for this request."
            self.chat_history.add_assistant_message(error_response)
            
            return {
                "coordination_decision": coordination_decision,
                "specialist_response": error_response,
                "agent_name": "Coordination System",
                "factory_status": self.factory_state.get_factory_status(),
                "chat_history": len(self.chat_history.messages)
            }

    def display_result(self, result: Dict):
        """Display the processing result with modern formatting"""
        print(f"\n🎯 FACTORY REQUEST PROCESSING COMPLETE")
        print(f"Handled by: {result['agent_name']}")
        print(f"Supporting: {', '.join(result['coordination_decision']['supporting_agents']) or 'None'}")
        print(f"Session: {result.get('chat_history', 0)} messages")
        print("\n" + "=" * 70)
        print(f"{result['specialist_response']}")
        print("=" * 70)

    async def simulate_factory_operation(self):
        """Simulate a factory operation to demonstrate state changes"""
        print("\n🔄 SIMULATING FACTORY OPERATION...")
        
        # Find orders that can be processed
        processable_orders = [
            order for order in self.factory_state.orders.values() 
            if order.status in ['received', 'preparing']
        ]
        
        if processable_orders:
            order = processable_orders[0]
            old_status = order.status
            
            # Use manual workflow
            result = await self.process_manual_workflow(order.order_id)
            print(f"👨‍🍳 Processed '{order.pasta_type}' order (was {old_status})")
            
            # Show updated status
            new_status = self.factory_state.orders[order.order_id].status
            print(f"📈 Status changed: {old_status} → {new_status}")
        else:
            print("ℹ️  No orders available for processing simulation")

    async def run_demo(self):
        """Run the complete modern pasta factory demo"""
        print("🍝 MODERN PASTA FACTORY MULTI-AGENT SYSTEM")
        print("Semantic Kernel 1.37.0 with Advanced Agent Framework")
        print("=" * 70)
        
        # Display initial state
        print("\n📊 INITIAL FACTORY STATE:")
        print(self.factory_state.get_factory_status())
        
        # Place sample orders
        sample_orders = [
            {"customer_name": "Mario Rossi", "pasta_type": "Spaghetti", "sauce": "Carbonara"},
            {"customer_name": "Laura Bianchi", "pasta_type": "Fettuccine", "sauce": "Alfredo"},
            {"customer_name": "Giovanni Verdi", "pasta_type": "Penne", "sauce": "Arrabbiata"},
            {"customer_name": "Maria Romano", "pasta_type": "Linguine", "sauce": "Pesto"},
            {"customer_name": "Antonio Costa", "pasta_type": "Ravioli", "sauce": "Marinara"}
        ]
        
        order_ids = []
        print("\n📝 PLACING SAMPLE ORDERS:")
        for order in sample_orders:
            order_id = self.place_order(**order)
            order_ids.append(order_id)
        
        # Demo scenarios
        factory_scenarios = [
            "We have multiple orders waiting. What's the current status and how should we prioritize?",
            "The kitchen is getting busy. How can we optimize resource allocation?",
            "Ensure all pasta dishes meet authentic Italian quality standards.",
            "We're expecting a large dinner rush. How should we prepare?",
            "Analyze our current production efficiency and suggest improvements."
        ]
        
        print("🚀 Starting multi-agent pasta factory demonstrations...")
        print("Available Agents: Order Manager, Kitchen Manager, Quality Manager, Factory Coordinator")
        print()
        
        # Process scenarios
        for i, scenario in enumerate(factory_scenarios, 1):
            print(f"\n{'#' * 70}")
            print(f"FACTORY SCENARIO #{i}")
            print(f"{'#' * 70}")
            
            try:
                result = await self.handle_factory_request(scenario)
                self.display_result(result)
                
                # Simulate factory operation between scenarios
                if i < len(factory_scenarios) and order_ids:
                    await self.simulate_factory_operation()
                
                await asyncio.sleep(1)  # Brief pause for demo flow
                
            except Exception as e:
                print(f"❌ System error: {e}")
                continue
        
        # Display final state
        print(f"\n📈 FINAL FACTORY STATE:")
        print(self.factory_state.get_factory_status())
        
        print(f"\n✅ Modern Pasta Factory Demo Completed!")
        print(f"📊 Session Summary: {len(self.chat_history.messages)} factory interactions processed")

async def main():
    """Main demo execution"""
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
    
    # Initialize and run modern pasta factory system
    pasta_factory = ModernPastaFactorySystem()
    await pasta_factory.run_demo()

if __name__ == "__main__":
    asyncio.run(main())