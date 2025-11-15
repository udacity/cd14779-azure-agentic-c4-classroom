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

load_dotenv("../../../.env")

# Modern KernelBaseModel for State Management
class CoffeeOrder(KernelBaseModel):
    """Model representing a coffee order using KernelBaseModel"""
    order_id: str
    customer_name: str
    coffee_type: str
    size: str
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
            'brewing': '☕',
            'ready': '✅',
            'served': '🎯'
        }
        icon = status_icons.get(self.status, '📦')
        return f"{icon} Order {self.order_id}: {self.coffee_type} ({self.size}) for {self.customer_name} - Status: {self.status}"

class CoffeeResource(KernelBaseModel):
    """Model representing coffee shop resources using KernelBaseModel"""
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

class CoffeeShopState(KernelBaseModel):
    """Central state management for the coffee shop using KernelBaseModel"""
    orders: Dict[str, CoffeeOrder] = {}
    resources: Dict[str, CoffeeResource] = {}
    completed_orders: int = 0
    inventory: Dict[str, int] = {}
    
    def add_order(self, order: CoffeeOrder) -> str:
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
        """Allocate a coffee resource"""
        if resource_id in self.resources and self.resources[resource_id].is_available():
            self.resources[resource_id].current_usage += 1
            return f"✅ Allocated {self.resources[resource_id].name}"
        return f"❌ Resource {resource_id} not available"
    
    def release_resource(self, resource_id: str) -> str:
        """Release a coffee resource"""
        if resource_id in self.resources:
            self.resources[resource_id].current_usage = max(0, self.resources[resource_id].current_usage - 1)
            return f"✅ Released {self.resources[resource_id].name}"
        return f"❌ Resource {resource_id} not found"
    
    def get_shop_status(self) -> str:
        """Get comprehensive shop status"""
        total_orders = len(self.orders)
        active_orders = len([o for o in self.orders.values() if o.status != 'served'])
        
        available_resources = len([r for r in self.resources.values() if r.is_available()])
        total_resources = len(self.resources)
        
        return f"""
        ☕ COFFEE SHOP STATUS:
        • Orders: {total_orders} total ({active_orders} active, {self.completed_orders} completed)
        • Resources: {available_resources}/{total_resources} available
        • Efficiency: {(self.completed_orders/max(1, total_orders))*100:.1f}%
        """
    
    def get_order_metrics(self) -> str:
        """Get order metrics and statistics"""
        status_count = {}
        coffee_types = {}
        
        for order in self.orders.values():
            status_count[order.status] = status_count.get(order.status, 0) + 1
            coffee_types[order.coffee_type] = coffee_types.get(order.coffee_type, 0) + 1
        
        metrics = "📊 ORDER METRICS:\n"
        metrics += "Status Distribution:\n"
        for status, count in status_count.items():
            icon = '📥' if status == 'received' else '👨‍🍳' if status == 'preparing' else '☕' if status == 'brewing' else '✅' if status == 'ready' else '🎯'
            metrics += f"  {icon} {status}: {count} orders\n"
        
        metrics += "\nPopular Coffee Types:\n"
        for coffee, count in sorted(coffee_types.items(), key=lambda x: x[1], reverse=True)[:3]:
            metrics += f"  ☕ {coffee}: {count} orders\n"
        
        return metrics
    
    def get_resource_capacity(self) -> str:
        """Get resource capacity analysis"""
        capacity = "🔧 RESOURCE CAPACITY:\n"
        
        for resource in self.resources.values():
            utilization = (resource.current_usage / resource.capacity) * 100
            status = "🟢 Good" if utilization < 70 else "🟡 Moderate" if utilization < 90 else "🔴 Critical"
            capacity += f"• {resource.name}: {resource.current_usage}/{resource.capacity} ({utilization:.1f}%) - {status}\n"
        
        available_count = len([r for r in self.resources.values() if r.is_available()])
        capacity += f"\n📈 Available Equipment: {available_count}/{len(self.resources)}"
        
        return capacity

class CoffeeShopPlugin:
    """Plugin for coffee shop operations with kernel functions"""
    
    def __init__(self, shop_state: CoffeeShopState):
        self.shop_state = shop_state
    
    @kernel_function(
        name="get_comprehensive_shop_status",
        description="Get complete coffee shop status with all metrics"
    )
    def get_comprehensive_status(self) -> str:
        """Get comprehensive shop status"""
        status = self.shop_state.get_shop_status()
        metrics = self.shop_state.get_order_metrics()
        capacity = self.shop_state.get_resource_capacity()
        
        return f"{status}\n{metrics}\n{capacity}"
    
    @kernel_function(
        name="get_inventory_status",
        description="Get inventory status and analysis"
    )
    def get_inventory_status(self) -> str:
        """Get inventory status"""
        inventory = "📦 INVENTORY STATUS:\n"
        for item, quantity in self.shop_state.inventory.items():
            status = "🟢 Good" if quantity > 15 else "🟡 Low" if quantity > 5 else "🔴 Critical"
            inventory += f"• {item.replace('_', ' ').title()}: {quantity} units - {status}\n"
        
        low_stock = [item for item, qty in self.shop_state.inventory.items() if qty < 10]
        if low_stock:
            inventory += f"\n🚨 Low Stock Alert: {', '.join(low_stock)}"
        
        return inventory
    
    @kernel_function(
        name="process_coffee_order",
        description="Process a coffee order through the preparation workflow"
    )
    def process_order(self, order_id: str) -> str:
        """Process an order through the coffee preparation workflow"""
        if order_id not in self.shop_state.orders:
            return f"❌ Order {order_id} not found"
        
        order = self.shop_state.orders[order_id]
        steps = []
        
        # Step 1: Allocate resources for preparation
        if (self.shop_state.allocate_resource("espresso_machine_1") and
            self.shop_state.allocate_resource("coffee_grinder")):
            
            self.shop_state.update_order_status(order_id, "preparing")
            steps.append("✅ Started coffee preparation")
            
            # Step 2: Brew coffee
            self.shop_state.update_order_status(order_id, "brewing")
            steps.append("✅ Started brewing")
            
            # Step 3: For milk-based drinks, steam milk
            if order.coffee_type in ['latte', 'cappuccino', 'flat_white']:
                if self.shop_state.allocate_resource("milk_steamer"):
                    steps.append("✅ Steamed milk for drink")
                else:
                    steps.append("❌ Milk steamer not available")
            
            # Step 4: Mark as ready and serve
            self.shop_state.update_order_status(order_id, "ready")
            self.shop_state.update_order_status(order_id, "served")
            
            # Release resources
            self.shop_state.release_resource("espresso_machine_1")
            self.shop_state.release_resource("coffee_grinder")
            if order.coffee_type in ['latte', 'cappuccino', 'flat_white']:
                self.shop_state.release_resource("milk_steamer")
            
            # Update inventory
            self.shop_state.inventory["coffee_beans"] = max(0, self.shop_state.inventory.get("coffee_beans", 0) - 1)
            self.shop_state.inventory["cups"] = max(0, self.shop_state.inventory.get("cups", 0) - 1)
            if order.coffee_type in ['latte', 'cappuccino', 'flat_white']:
                self.shop_state.inventory["milk"] = max(0, self.shop_state.inventory.get("milk", 0) - 1)
            
            self.shop_state.completed_orders += 1
            steps.append("✅ Order served and resources released")
        else:
            steps.append("❌ Preparation resources not available")
        
        return f"👨‍🍳 Processing {order_id}:\n" + "\n".join(steps)

class ModernCoffeeShopSystem:
    """Modern coffee shop system using Semantic Kernel 1.37.0 multi-agent framework"""
    
    def __init__(self):
        # Shared kernel instance
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_coffee_chat",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
        
        # Initialize shared shop state
        self.shop_state = CoffeeShopState()
        self._initialize_resources()
        self._initialize_inventory()
        
        # Initialize coffee shop plugin and register with kernel
        self.coffee_plugin = CoffeeShopPlugin(self.shop_state)
        self.kernel.add_plugin(self.coffee_plugin, "CoffeeShop")
        
        # Initialize specialized coffee agents with modern framework
        self.agents = {
            "orders": ChatCompletionAgent(
                kernel=self.kernel,
                name="Order_Manager",
                description="Specialist in order management and customer service",
                instructions="""You are an order manager for a busy coffee shop. Coordinate orders and ensure customer satisfaction.

                Available Functions from CoffeeShop Plugin:
                - get_comprehensive_shop_status: Access complete shop overview
                - get_inventory_status: View inventory levels
                - process_coffee_order: Manage order processing workflow

                Always provide:
                - Current order status and priority assessment
                - Customer service recommendations  
                - Order workflow optimization suggestions
                - Coffee preparation insights

                Use shop data for accurate analysis and focus on customer satisfaction."""
            ),
            "barista": ChatCompletionAgent(
                kernel=self.kernel,
                name="Barista_Manager", 
                description="Specialist in coffee preparation and equipment management",
                instructions="""You are a skilled barista managing coffee preparation and equipment.

                Available Functions from CoffeeShop Plugin:
                - get_comprehensive_shop_status: Access shop overview
                - process_coffee_order: Handle order processing
                - get_inventory_status: Check ingredient availability

                Always provide:
                - Equipment optimization recommendations
                - Coffee preparation techniques
                - Resource allocation strategies
                - Quality control measures

                Focus on efficient coffee preparation and equipment management."""
            ),
            "inventory": ChatCompletionAgent(
                kernel=self.kernel,
                name="Inventory_Manager",
                description="Specialist in inventory management and supply chain",
                instructions="""You are an inventory manager ensuring adequate supplies.

                Available Functions from CoffeeShop Plugin:
                - get_inventory_status: Access current inventory levels
                - get_comprehensive_shop_status: View overall shop status

                Always provide:
                - Inventory restocking recommendations
                - Supply usage analysis
                - Cost optimization suggestions
                - Stock level management

                Focus on maintaining optimal inventory levels."""
            ),
            "coordinator": ChatCompletionAgent(
                kernel=self.kernel,
                name="Shop_Coordinator",
                description="Intelligent coordinator for coffee shop multi-agent collaboration",
                instructions="""You are the central coordinator for the coffee shop multi-agent system.

                Available Agents:
                - orders: Order management, customer service, workflow coordination
                - barista: Coffee preparation, equipment management, quality control
                - inventory: Supply management, restocking, cost optimization

                Always:
                1. Analyze the request and determine which specialist(s) should handle it
                2. Provide brief reasoning for your routing decision
                3. Suggest any inter-agent collaboration needed

                Respond in this exact format:
                Primary Agent: [orders/barista/inventory]
                Supporting Agents: [comma-separated list or none]
                Reasoning: [brief explanation of routing decision]"""
            )
        }
        
        # Initialize modern orchestration runtime
        self.runtime = InProcessRuntime()
        self.chat_history = ChatHistory()

    def _initialize_resources(self):
        """Initialize coffee shop resources"""
        resources = [
            CoffeeResource(resource_id="espresso_machine_1", name="Espresso Machine 1", capacity=2),
            CoffeeResource(resource_id="espresso_machine_2", name="Espresso Machine 2", capacity=2),
            CoffeeResource(resource_id="milk_steamer", name="Milk Steamer", capacity=3),
            CoffeeResource(resource_id="coffee_grinder", name="Coffee Grinder", capacity=2),
            CoffeeResource(resource_id="brew_station", name="Brew Station", capacity=4)
        ]
        
        for resource in resources:
            self.shop_state.resources[resource.resource_id] = resource

    def _initialize_inventory(self):
        """Initialize inventory supplies"""
        self.shop_state.inventory = {
            "coffee_beans": 45,
            "milk": 25,
            "sugar": 30,
            "cups": 80,
            "syrups": 15
        }

    def place_order(self, customer_name: str, coffee_type: str, size: str) -> str:
        """Place a new coffee order"""
        order_id = f"ORD{len(self.shop_state.orders) + 1:03d}"
        order = CoffeeOrder(
            order_id=order_id,
            customer_name=customer_name,
            coffee_type=coffee_type,
            size=size
        )
        
        result = self.shop_state.add_order(order)
        print(f"📝 {result}")
        return order_id

    async def coordinate_request(self, request: str) -> Dict:
        """Intelligent coordination of shop requests using coordinator agent"""
        print(f"📨 Shop Request: {request}")
        print("🔄 Analyzing and coordinating with specialists...")
        
        coordination_prompt = f"SHOP REQUEST: {request}"
        
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
        
        # Build enhanced context with shop analytics
        shop_status = self.shop_state.get_shop_status()
        order_metrics = self.shop_state.get_order_metrics()
        resource_capacity = self.shop_state.get_resource_capacity()
        inventory_status = self.coffee_plugin.get_inventory_status()
        
        # Add coordination context if available
        coordination_context = ""
        if context:
            coordination_context = f"\n\nCOORDINATION CONTEXT: {context.get('reasoning', 'General request')}"
        
        enhanced_request = f"""
        SHOP REQUEST: {request}
        
        CURRENT SHOP STATUS:
        {shop_status}
        
        ORDER METRICS:
        {order_metrics}
        
        RESOURCE CAPACITY:
        {resource_capacity}
        
        INVENTORY STATUS:
        {inventory_status}
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
            "barista": "👨‍🍳", 
            "inventory": "📦"
        }
        
        titles = {
            "orders": "Order Management Analysis",
            "barista": "Barista Recommendations", 
            "inventory": "Inventory Management Insights"
        }
        
        icon = icons.get(agent_name, "☕")
        title = titles.get(agent_name, "Shop Analysis")
        
        return f"{icon} **{title}**\n\n{content}"

    async def process_workflow(self, order_id: str) -> str:
        """Process order through manual workflow simulation"""
        print(f"🔄 Starting workflow for {order_id}...")
        
        workflow_steps = []
        
        try:
            # Step 1: Order Agent analyzes the order
            order_analysis = await self.agents["orders"].get_response(
                f"Analyze order {order_id} and provide preparation instructions"
            )
            workflow_steps.append(f"📝 Order Analysis: Order {order_id} analysis completed")
            
            # Step 2: Barista Agent prepares coffee
            barista_plan = await self.agents["barista"].get_response(
                f"Plan coffee preparation for order {order_id}"
            )
            workflow_steps.append(f"👨‍🍳 Barista Plan: Preparation strategy defined")
            
            # Step 3: Inventory Agent checks supplies
            inventory_check = await self.agents["inventory"].get_response(
                f"Verify inventory for order {order_id}"
            )
            workflow_steps.append(f"📦 Inventory Check: Supplies verified")
            
            # Process the order using direct method calls
            process_result = self.coffee_plugin.process_order(order_id)
            
            workflow_summary = "🎉 Workflow Completed!\n\n" + "\n".join(workflow_steps) + f"\n\n{process_result}"
            return workflow_summary
            
        except Exception as e:
            # Fallback: Just process the order without agent analysis
            process_result = self.coffee_plugin.process_order(order_id)
            return f"🔄 Basic Processing Completed:\n\n{process_result}"

    async def handle_shop_request(self, request: str) -> Dict:
        """Complete processing of a shop request with modern agent framework"""
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
                "shop_status": self.shop_state.get_shop_status(),
                "chat_history": len(self.chat_history.messages)
            }
        else:
            error_response = "❌ No suitable agent available for this request."
            self.chat_history.add_assistant_message(error_response)
            
            return {
                "coordination_decision": coordination_decision,
                "specialist_response": error_response,
                "agent_name": "Coordination System",
                "shop_status": self.shop_state.get_shop_status(),
                "chat_history": len(self.chat_history.messages)
            }

    def display_result(self, result: Dict):
        """Display the processing result with modern formatting"""
        print(f"\n🎯 SHOP REQUEST PROCESSING COMPLETE")
        print(f"Handled by: {result['agent_name']}")
        print(f"Supporting: {', '.join(result['coordination_decision']['supporting_agents']) or 'None'}")
        print(f"Session: {result.get('chat_history', 0)} messages")
        print("\n" + "=" * 70)
        print(f"{result['specialist_response']}")
        print("=" * 70)

    async def simulate_shop_operation(self):
        """Simulate a shop operation to demonstrate state changes"""
        print("\n🔄 SIMULATING SHOP OPERATION...")
        
        # Find orders that can be processed
        processable_orders = [
            order for order in self.shop_state.orders.values() 
            if order.status in ['received', 'preparing']
        ]
        
        if processable_orders:
            order = processable_orders[0]
            old_status = order.status
            
            # Use workflow processing
            result = await self.process_workflow(order.order_id)
            print(f"👨‍🍳 Processed '{order.coffee_type}' order (was {old_status})")
            
            # Show updated status
            new_status = self.shop_state.orders[order.order_id].status
            print(f"📈 Status changed: {old_status} → {new_status}")
        else:
            print("ℹ️  No orders available for processing simulation")

    async def run_demo(self):
        """Run the complete modern coffee shop demo"""
        print("☕ MODERN COFFEE SHOP MULTI-AGENT SYSTEM")
        print("Semantic Kernel 1.37.0 with Advanced Agent Framework")
        print("=" * 70)
        
        # Display initial state
        print("\n📊 INITIAL SHOP STATE:")
        print(self.shop_state.get_shop_status())
        
        # Place sample orders
        sample_orders = [
            {"customer_name": "Alice Chen", "coffee_type": "latte", "size": "medium"},
            {"customer_name": "Bob Rodriguez", "coffee_type": "espresso", "size": "small"},
            {"customer_name": "Carol Williams", "coffee_type": "cappuccino", "size": "large"},
            {"customer_name": "David Kim", "coffee_type": "americano", "size": "medium"},
            {"customer_name": "Eva Martinez", "coffee_type": "flat_white", "size": "small"}
        ]
        
        order_ids = []
        print("\n📝 PLACING SAMPLE ORDERS:")
        for order in sample_orders:
            order_id = self.place_order(**order)
            order_ids.append(order_id)
        
        # Demo scenarios
        shop_scenarios = [
            "We have multiple orders waiting. What's the current status and how should we prioritize?",
            "The coffee machines are getting busy. How can we optimize resource allocation?",
            "Check our inventory levels and suggest restocking strategies.",
            "We're expecting a morning rush. How should we prepare?",
            "Analyze our current service efficiency and suggest improvements."
        ]
        
        print("🚀 Starting multi-agent coffee shop demonstrations...")
        print("Available Agents: Order Manager, Barista Manager, Inventory Manager, Shop Coordinator")
        print()
        
        # Process scenarios
        for i, scenario in enumerate(shop_scenarios, 1):
            print(f"\n{'#' * 70}")
            print(f"SHOP SCENARIO #{i}")
            print(f"{'#' * 70}")
            
            try:
                result = await self.handle_shop_request(scenario)
                self.display_result(result)
                
                # Simulate shop operation between scenarios
                if i < len(shop_scenarios) and order_ids:
                    await self.simulate_shop_operation()
                
                await asyncio.sleep(1)  # Brief pause for demo flow
                
            except Exception as e:
                print(f"❌ System error: {e}")
                continue
        
        # Display final state
        print(f"\n📈 FINAL SHOP STATE:")
        print(self.shop_state.get_shop_status())
        
        print(f"\n✅ Modern Coffee Shop Demo Completed!")
        print(f"📊 Session Summary: {len(self.chat_history.messages)} shop interactions processed")
        print(f"🛠️  Features Used: Multi-Agent Coordination, KernelBaseModel, Plugin Architecture, Real-time Analytics")

async def main():
    """Main demo execution"""
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
    
    # Initialize and run modern coffee shop system
    coffee_shop = ModernCoffeeShopSystem()
    await coffee_shop.run_demo()

if __name__ == "__main__":
    asyncio.run(main())