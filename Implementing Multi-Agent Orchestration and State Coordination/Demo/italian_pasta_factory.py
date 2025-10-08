import asyncio
import os
from typing import Dict, List
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
load_dotenv("../../.env")

# Pydantic Models for State Management
class PastaOrder(BaseModel):
    """Model representing a pasta order"""
    order_id: str = Field(..., description="Unique order identifier")
    customer_name: str = Field(..., description="Customer name")
    pasta_type: str = Field(..., description="Type of pasta")
    sauce: str = Field(..., description="Sauce type")
    status: str = Field(default="received", description="Order status")
    order_date: datetime = Field(default_factory=datetime.now)
    
    @field_validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['received', 'preparing', 'cooking', 'ready', 'served']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of {allowed_statuses}')
        return v

class KitchenResource(BaseModel):
    """Model representing kitchen resources"""
    resource_id: str = Field(..., description="Unique resource identifier")
    name: str = Field(..., description="Resource name")
    capacity: int = Field(..., gt=0, description="Maximum capacity")
    current_usage: int = Field(default=0, ge=0, description="Current usage")
    
    @property
    def available(self) -> bool:
        """Check if resource is available"""
        return self.current_usage < self.capacity

class PastaFactoryState(BaseModel):
    """Central state management for the pasta factory"""
    orders: Dict[str, PastaOrder] = Field(default_factory=dict, description="All orders")
    resources: Dict[str, KitchenResource] = Field(default_factory=dict, description="Kitchen resources")
    completed_orders: int = Field(default=0, description="Total completed orders")
    daily_special: str = Field(default="Spaghetti Carbonara", description="Today's special")
    
    def add_order(self, order: PastaOrder) -> None:
        """Add a new order"""
        self.orders[order.order_id] = order
    
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        if order_id not in self.orders:
            return False
        self.orders[order_id].status = status
        return True
    
    def allocate_resource(self, resource_id: str) -> bool:
        """Allocate a kitchen resource"""
        if resource_id not in self.resources:
            return False
        resource = self.resources[resource_id]
        if not resource.available:
            return False
        resource.current_usage += 1
        return True
    
    def release_resource(self, resource_id: str) -> bool:
        """Release a kitchen resource"""
        if resource_id not in self.resources:
            return False
        resource = self.resources[resource_id]
        resource.current_usage = max(0, resource.current_usage - 1)
        return True

class PastaAgent:
    """Base class for all pasta factory agents with shared state access"""
    
    def __init__(self, name: str, role: str, factory_state: PastaFactoryState):
        self.name = name
        self.role = role
        self.factory_state = factory_state
        self.kernel = Kernel()
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
    
    async def process_request(self, request: str) -> Dict:
        """Process factory request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

class OrderAgent(PastaAgent):
    """Agent specializing in order management"""
    
    def __init__(self, factory_state: PastaFactoryState):
        super().__init__("Order Manager", "Manage pasta orders and customer requests", factory_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle order-related requests"""
        
        prompt = """
        You are an order manager for an Italian pasta factory. Handle customer orders and coordinate the kitchen.

        REQUEST: {{$request}}

        CURRENT ORDERS STATUS:
        {{$orders_summary}}

        Please provide:
        1. Order status overview
        2. Priority recommendations
        3. Customer service suggestions

        Keep it practical and focused on Italian pasta preparation.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="order_management",
            plugin_name="orders",
            prompt=prompt
        )
        
        orders_summary = self._get_orders_summary()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            orders_summary=orders_summary
        )
        
        return {
            "agent": self.name,
            "analysis": str(result),
            "pending_orders": self._get_pending_orders(),
            "current_status": self._get_current_status()
        }
    
    def _get_orders_summary(self) -> str:
        """Generate orders summary"""
        total_orders = len(self.factory_state.orders)
        active_orders = len([o for o in self.factory_state.orders.values() if o.status != 'served'])
        
        summary = f"""
        Total Orders Today: {total_orders}
        Active Orders: {active_orders}
        Completed Orders: {self.factory_state.completed_orders}
        Daily Special: {self.factory_state.daily_special}
        """
        return summary
    
    def _get_pending_orders(self) -> List[Dict]:
        """Get pending orders that need attention"""
        pending = []
        for order in self.factory_state.orders.values():
            if order.status in ['received', 'preparing']:
                pending.append({
                    "order_id": order.order_id,
                    "customer": order.customer_name,
                    "pasta": order.pasta_type,
                    "status": order.status
                })
        return pending
    
    def _get_current_status(self) -> Dict:
        """Get current order status breakdown"""
        status_count = {}
        for order in self.factory_state.orders.values():
            status_count[order.status] = status_count.get(order.status, 0) + 1
        return status_count

class KitchenAgent(PastaAgent):
    """Agent specializing in kitchen resource management"""
    
    def __init__(self, factory_state: PastaFactoryState):
        super().__init__("Kitchen Manager", "Manage kitchen resources and cooking process", factory_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle kitchen-related requests"""
        
        prompt = """
        You are a kitchen manager for an Italian pasta factory. Coordinate cooking resources and resolve conflicts.

        REQUEST: {{$request}}

        KITCHEN STATUS:
        {{$kitchen_status}}

        Please provide:
        1. Resource allocation recommendations
        2. Conflict resolution strategies
        3. Cooking process optimizations

        Focus on efficient pasta preparation and resource management.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="kitchen_management",
            plugin_name="kitchen",
            prompt=prompt
        )
        
        kitchen_status = self._get_kitchen_status()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            kitchen_status=kitchen_status
        )
        
        return {
            "agent": self.name,
            "recommendations": str(result),
            "resource_usage": self._get_resource_usage(),
            "bottlenecks": self._get_bottlenecks()
        }
    
    def _get_kitchen_status(self) -> str:
        """Get current kitchen status"""
        available_resources = []
        busy_resources = []
        
        for resource in self.factory_state.resources.values():
            if resource.available:
                available_resources.append(f"{resource.name} ({resource.current_usage}/{resource.capacity})")
            else:
                busy_resources.append(f"{resource.name} (FULL: {resource.current_usage}/{resource.capacity})")
        
        return f"""
        Available Resources: {', '.join(available_resources) if available_resources else 'None'}
        Busy Resources: {', '.join(busy_resources) if busy_resources else 'None'}
        Total Resources: {len(self.factory_state.resources)}
        """
    
    def _get_resource_usage(self) -> Dict:
        """Calculate resource usage metrics"""
        usage = {}
        for resource_id, resource in self.factory_state.resources.items():
            usage[resource.name] = f"{resource.current_usage}/{resource.capacity}"
        return usage
    
    def _get_bottlenecks(self) -> List[str]:
        """Identify resource bottlenecks"""
        bottlenecks = []
        for resource in self.factory_state.resources.values():
            if resource.current_usage >= resource.capacity:
                bottlenecks.append(f"{resource.name} at full capacity")
        return bottlenecks

class QualityAgent(PastaAgent):
    """Agent specializing in quality control and recipe management"""
    
    def __init__(self, factory_state: PastaFactoryState):
        super().__init__("Quality Manager", "Ensure pasta quality and recipe standards", factory_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle quality-related requests"""
        
        prompt = """
        You are a quality manager for an Italian pasta factory. Maintain authentic Italian pasta standards.

        REQUEST: {{$request}}

        FACTORY OVERVIEW:
        {{$factory_overview}}

        Please provide:
        1. Quality assurance recommendations
        2. Traditional Italian cooking tips
        3. Recipe improvement suggestions

        Emphasize authentic Italian cooking techniques.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="quality_management",
            plugin_name="quality",
            prompt=prompt
        )
        
        factory_overview = self._get_factory_overview()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            factory_overview=factory_overview
        )
        
        return {
            "agent": self.name,
            "quality_advice": str(result),
            "popular_pastas": self._get_popular_pastas(),
            "completion_rate": self._get_completion_rate()
        }
    
    def _get_factory_overview(self) -> str:
        """Get factory overview"""
        pasta_types = set(order.pasta_type for order in self.factory_state.orders.values())
        sauce_types = set(order.sauce for order in self.factory_state.orders.values())
        
        return f"""
        Pasta Types in Production: {', '.join(pasta_types)}
        Sauce Varieties: {', '.join(sauce_types)}
        Total Production: {len(self.factory_state.orders)} orders
        Success Rate: {self._get_completion_rate():.1f}%
        """
    
    def _get_popular_pastas(self) -> List[str]:
        """Get most popular pasta types"""
        from collections import Counter
        pastas = [order.pasta_type for order in self.factory_state.orders.values()]
        return [pasta for pasta, count in Counter(pastas).most_common(3)]
    
    def _get_completion_rate(self) -> float:
        """Calculate order completion rate"""
        if not self.factory_state.orders:
            return 0.0
        served_orders = len([o for o in self.factory_state.orders.values() if o.status == 'served'])
        return (served_orders / len(self.factory_state.orders)) * 100

class PastaFactorySystem:
    """Main pasta factory system coordinating all agents"""
    
    def __init__(self):
        # Initialize shared factory state
        self.factory_state = PastaFactoryState()
        self._initialize_kitchen_resources()
        
        # Initialize specialized agents
        self.agents = {
            "orders": OrderAgent(self.factory_state),
            "kitchen": KitchenAgent(self.factory_state),
            "quality": QualityAgent(self.factory_state)
        }
    
    def _initialize_kitchen_resources(self):
        """Initialize the factory with kitchen resources"""
        resources = [
            KitchenResource(resource_id="R001", name="Pasta Maker", capacity=2),
            KitchenResource(resource_id="R002", name="Sauce Station", capacity=3),
            KitchenResource(resource_id="R003", name="Cooking Station", capacity=4),
            KitchenResource(resource_id="R004", name="Assembly Line", capacity=3)
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
        
        self.factory_state.add_order(order)
        return order_id
    
    def process_order(self, order_id: str) -> bool:
        """Process an order through the kitchen"""
        if order_id not in self.factory_state.orders:
            return False
        
        order = self.factory_state.orders[order_id]
        
        # Try to allocate resources
        if (self.factory_state.allocate_resource("R001") and  # Pasta Maker
            self.factory_state.allocate_resource("R002") and  # Sauce Station
            self.factory_state.allocate_resource("R003")):     # Cooking Station
            
            # Update order status through preparation stages
            self.factory_state.update_order_status(order_id, "preparing")
            self.factory_state.update_order_status(order_id, "cooking")
            self.factory_state.update_order_status(order_id, "ready")
            self.factory_state.update_order_status(order_id, "served")
            
            # Release resources
            self.factory_state.release_resource("R001")
            self.factory_state.release_resource("R002")
            self.factory_state.release_resource("R003")
            
            self.factory_state.completed_orders += 1
            return True
        
        return False
    
    async def run_demo(self):
        """Run the complete pasta factory demo"""
        print("🍝 ITALIAN PASTA FACTORY MULTI-AGENT SYSTEM")
        print("State Coordination Demo")
        print("=" * 50)
        
        # Display initial state
        self.display_factory_state()
        
        # Place some sample orders
        sample_orders = [
            {"customer_name": "Mario Rossi", "pasta_type": "Spaghetti", "sauce": "Carbonara"},
            {"customer_name": "Laura Bianchi", "pasta_type": "Fettuccine", "sauce": "Alfredo"},
            {"customer_name": "Giovanni Verdi", "pasta_type": "Penne", "sauce": "Arrabbiata"},
            {"customer_name": "Maria Romano", "pasta_type": "Linguine", "sauce": "Pesto"},
        ]
        
        order_ids = []
        for order in sample_orders:
            order_id = self.place_order(**order)
            order_ids.append(order_id)
            print(f"📝 Order placed: {order_id} - {order['pasta_type']} with {order['sauce']} for {order['customer_name']}")
        
        # Demo scenarios
        scenarios = [
            "Check current order status and prioritize cooking",
            "Manage kitchen resources and resolve any conflicts", 
            "Ensure authentic Italian quality for all pasta dishes",
            "What's our current production efficiency?",
            "How can we improve our pasta preparation process?"
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎯 SCENARIO {i}: {scenario}")
            print("-" * 50)
            
            await self.process_scenario(scenario)
            
            # Process some orders between scenarios to show state changes
            if i < len(scenarios) and order_ids:
                orders_to_process = order_ids[:min(2, len(order_ids))]
                for order_id in orders_to_process:
                    if self.process_order(order_id):
                        print(f"👨‍🍳 Processed order: {order_id}")
        
        print("\n🎉 DEMO COMPLETED!")
        self.display_final_state()
    
    async def process_scenario(self, scenario: str):
        """Process a scenario with all agents"""
        print("🤖 Consulting all specialists...")
        
        # Process with all agents in parallel
        tasks = []
        for agent_name, agent in self.agents.items():
            tasks.append(agent.process_request(scenario))
        
        results = await asyncio.gather(*tasks)
        
        # Display results
        for (agent_name, _), result in zip(self.agents.items(), results):
            print(f"\n{agent_name.upper()} AGENT:")
            response = result.get('analysis', result.get('recommendations', result.get('quality_advice', 'No response')))
            print(f"Response: {response}")
            
            # Show additional data if available
            if 'pending_orders' in result and result['pending_orders']:
                print("⏳ Pending Orders:", result['pending_orders'])
            if 'bottlenecks' in result and result['bottlenecks']:
                print("🚧 Bottlenecks:", result['bottlenecks'])
            if 'popular_pastas' in result and result['popular_pastas']:
                print("🏆 Popular Pastas:", result['popular_pastas'])
    
    def display_factory_state(self):
        """Display current factory state"""
        print("\n📊 CURRENT FACTORY STATE:")
        print(f"🍝 Daily Special: {self.factory_state.daily_special}")
        print(f"📦 Total Orders: {len(self.factory_state.orders)}")
        print(f"✅ Completed Orders: {self.factory_state.completed_orders}")
        print(f"🔧 Kitchen Resources: {len(self.factory_state.resources)}")
        
        # Resource status
        available = sum(1 for r in self.factory_state.resources.values() if r.available)
        print(f"🟢 Available Resources: {available}/{len(self.factory_state.resources)}")
    
    def display_final_state(self):
        """Display final state after demo"""
        print("\n📈 FINAL FACTORY STATE:")
        print(f"📦 Total Orders: {len(self.factory_state.orders)}")
        print(f"✅ Completed Orders: {self.factory_state.completed_orders}")
        
        # Order status breakdown
        status_count = {}
        for order in self.factory_state.orders.values():
            status_count[order.status] = status_count.get(order.status, 0) + 1
        
        print("📊 Order Status:")
        for status, count in status_count.items():
            print(f"  {status}: {count}")
        
        # Resource utilization
        print("🔧 Resource Utilization:")
        for resource in self.factory_state.resources.values():
            utilization = (resource.current_usage / resource.capacity) * 100
            print(f"  {resource.name}: {resource.current_usage}/{resource.capacity} ({utilization:.1f}%)")

async def main():
    # Check environment variables
    required_vars = ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing environment variables. Please check your .env file.")
        print(f"Missing: {missing_vars}")
        return
    
    # Create and run the pasta factory system
    pasta_factory = PastaFactorySystem()
    await pasta_factory.run_demo()

if __name__ == "__main__":
    asyncio.run(main())