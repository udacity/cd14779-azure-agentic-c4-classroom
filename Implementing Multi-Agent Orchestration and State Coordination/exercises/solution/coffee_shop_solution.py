import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
load_dotenv()

# Pydantic Models
class CoffeeOrder(BaseModel):
    """Model representing a coffee order"""
    order_id: str = Field(..., description="Unique order identifier")
    customer_name: str = Field(..., description="Customer name")
    coffee_type: str = Field(..., description="Type of coffee")
    size: str = Field(..., description="Coffee size")
    status: str = Field(default="received", description="Order status")
    order_date: datetime = Field(default_factory=datetime.now)
    
    @field_validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['received', 'preparing', 'brewing', 'ready', 'served']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of {allowed_statuses}')
        return v

class CoffeeResource(BaseModel):
    """Model representing coffee shop resources"""
    resource_id: str = Field(..., description="Unique resource identifier")
    name: str = Field(..., description="Resource name")
    capacity: int = Field(..., gt=0, description="Maximum capacity")
    current_usage: int = Field(default=0, ge=0, description="Current usage")
    
    @property
    def available(self) -> bool:
        """Check if resource is available"""
        return self.current_usage < self.capacity

class CoffeeShopState(BaseModel):
    """Central state management for the coffee shop"""
    orders: Dict[str, CoffeeOrder] = Field(default_factory=dict, description="All orders")
    resources: Dict[str, CoffeeResource] = Field(default_factory=dict, description="Coffee resources")
    completed_orders: int = Field(default=0, description="Total completed orders")
    inventory: Dict[str, int] = Field(default_factory=dict, description="Inventory supplies")
    
    def add_order(self, order: CoffeeOrder) -> None:
        """Add a new order"""
        self.orders[order.order_id] = order
    
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        if order_id not in self.orders:
            return False
        self.orders[order_id].status = status
        return True
    
    def allocate_resource(self, resource_id: str) -> bool:
        """Allocate a coffee resource"""
        if resource_id not in self.resources:
            return False
        resource = self.resources[resource_id]
        if not resource.available:
            return False
        resource.current_usage += 1
        return True
    
    def release_resource(self, resource_id: str) -> bool:
        """Release a coffee resource"""
        if resource_id not in self.resources:
            return False
        resource = self.resources[resource_id]
        resource.current_usage = max(0, resource.current_usage - 1)
        return True

# Base Agent Class
class CoffeeAgent:
    """Base class for all coffee shop agents"""
    
    def __init__(self, name: str, role: str, shop_state: CoffeeShopState):
        self.name = name
        self.role = role
        self.shop_state = shop_state
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
        raise NotImplementedError("Subclasses must implement this method")

# Specialized Agents
class OrderAgent(CoffeeAgent):
    """Agent specializing in order management"""
    
    def __init__(self, shop_state: CoffeeShopState):
        super().__init__("Order Manager", "Manage coffee orders and customer requests", shop_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle order-related requests"""
        
        prompt = """
        You are an order manager for a busy coffee shop. Coordinate orders and ensure customer satisfaction.

        REQUEST: {{$request}}

        CURRENT ORDERS STATUS:
        {{$orders_summary}}

        Please provide:
        1. Order prioritization recommendations
        2. Customer service suggestions
        3. Efficiency improvements

        Focus on practical coffee shop operations.
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
        total_orders = len(self.shop_state.orders)
        active_orders = len([o for o in self.shop_state.orders.values() if o.status != 'served'])
        
        summary = f"""
        Total Orders Today: {total_orders}
        Active Orders: {active_orders}
        Completed Orders: {self.shop_state.completed_orders}
        """
        return summary
    
    def _get_pending_orders(self) -> List[Dict]:
        """Get pending orders that need attention"""
        pending = []
        for order in self.shop_state.orders.values():
            if order.status in ['received', 'preparing']:
                pending.append({
                    "order_id": order.order_id,
                    "customer": order.customer_name,
                    "coffee": order.coffee_type,
                    "size": order.size,
                    "status": order.status
                })
        return pending
    
    def _get_current_status(self) -> Dict:
        """Get current order status breakdown"""
        status_count = {}
        for order in self.shop_state.orders.values():
            status_count[order.status] = status_count.get(order.status, 0) + 1
        return status_count

class BaristaAgent(CoffeeAgent):
    """Agent specializing in coffee preparation"""
    
    def __init__(self, shop_state: CoffeeShopState):
        super().__init__("Barista", "Prepare coffee drinks and manage equipment", shop_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle coffee preparation requests"""
        
        prompt = """
        You are a skilled barista in a coffee shop. Manage coffee preparation and equipment usage.

        REQUEST: {{$request}}

        EQUIPMENT STATUS:
        {{$equipment_status}}

        Please provide:
        1. Coffee preparation strategies
        2. Equipment usage recommendations
        3. Conflict resolution for busy equipment

        Focus on efficient coffee making techniques.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="barista_management",
            plugin_name="barista",
            prompt=prompt
        )
        
        equipment_status = self._get_equipment_status()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            equipment_status=equipment_status
        )
        
        return {
            "agent": self.name,
            "recommendations": str(result),
            "resource_usage": self._get_resource_usage(),
            "bottlenecks": self._get_bottlenecks()
        }
    
    def _get_equipment_status(self) -> str:
        """Get current equipment status"""
        available_resources = []
        busy_resources = []
        
        for resource in self.shop_state.resources.values():
            if resource.available:
                available_resources.append(f"{resource.name} ({resource.current_usage}/{resource.capacity})")
            else:
                busy_resources.append(f"{resource.name} (FULL: {resource.current_usage}/{resource.capacity})")
        
        return f"""
        Available Equipment: {', '.join(available_resources) if available_resources else 'None'}
        Busy Equipment: {', '.join(busy_resources) if busy_resources else 'None'}
        """
    
    def _get_resource_usage(self) -> Dict:
        """Calculate resource usage metrics"""
        usage = {}
        for resource_id, resource in self.shop_state.resources.items():
            usage[resource.name] = f"{resource.current_usage}/{resource.capacity}"
        return usage
    
    def _get_bottlenecks(self) -> List[str]:
        """Identify equipment bottlenecks"""
        bottlenecks = []
        for resource in self.shop_state.resources.values():
            if resource.current_usage >= resource.capacity:
                bottlenecks.append(f"{resource.name} at full capacity")
        return bottlenecks

class InventoryAgent(CoffeeAgent):
    """Agent specializing in inventory management"""
    
    def __init__(self, shop_state: CoffeeShopState):
        super().__init__("Inventory Manager", "Manage coffee supplies and inventory", shop_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle inventory-related requests"""
        
        prompt = """
        You are an inventory manager for a coffee shop. Track supplies and ensure we never run out.

        REQUEST: {{$request}}

        CURRENT INVENTORY:
        {{$inventory_status}}

        Please provide:
        1. Inventory restocking recommendations
        2. Supply usage analysis
        3. Cost optimization suggestions

        Focus on maintaining adequate stock levels.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="inventory_management",
            plugin_name="inventory",
            prompt=prompt
        )
        
        inventory_status = self._get_inventory_status()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            inventory_status=inventory_status
        )
        
        return {
            "agent": self.name,
            "inventory_advice": str(result),
            "low_stock": self._get_low_stock_items(),
            "popular_coffees": self._get_popular_coffees()
        }
    
    def _get_inventory_status(self) -> str:
        """Get current inventory status"""
        return f"""
        Coffee Beans: {self.shop_state.inventory.get('coffee_beans', 0)} units
        Milk: {self.shop_state.inventory.get('milk', 0)} units
        Sugar: {self.shop_state.inventory.get('sugar', 0)} units
        Cups: {self.shop_state.inventory.get('cups', 0)} units
        """
    
    def _get_low_stock_items(self) -> List[str]:
        """Get items with low stock"""
        low_stock = []
        for item, quantity in self.shop_state.inventory.items():
            if quantity < 10:  # Low stock threshold
                low_stock.append(f"{item}: {quantity} remaining")
        return low_stock
    
    def _get_popular_coffees(self) -> List[str]:
        """Get most popular coffee types"""
        from collections import Counter
        coffees = [order.coffee_type for order in self.shop_state.orders.values()]
        return [coffee for coffee, count in Counter(coffees).most_common(3)]

# Main Coffee Shop System
class CoffeeShopSystem:
    """Main coffee shop system coordinating all agents"""
    
    def __init__(self):
        self.shop_state = CoffeeShopState()
        self._initialize_resources()
        self._initialize_inventory()
        
        self.agents = {
            "orders": OrderAgent(self.shop_state),
            "barista": BaristaAgent(self.shop_state),
            "inventory": InventoryAgent(self.shop_state)
        }
    
    def _initialize_resources(self):
        """Initialize coffee shop resources"""
        resources = [
            CoffeeResource(resource_id="espresso_machine_1", name="Espresso Machine 1", capacity=2),
            CoffeeResource(resource_id="espresso_machine_2", name="Espresso Machine 2", capacity=2),
            CoffeeResource(resource_id="milk_steamer", name="Milk Steamer", capacity=3),
            CoffeeResource(resource_id="coffee_grinder", name="Coffee Grinder", capacity=2),
        ]
        
        for resource in resources:
            self.shop_state.resources[resource.resource_id] = resource
    
    def _initialize_inventory(self):
        """Initialize inventory supplies"""
        self.shop_state.inventory = {
            "coffee_beans": 50,
            "milk": 30,
            "sugar": 20,
            "cups": 100
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
        
        self.shop_state.add_order(order)
        return order_id
    
    def process_order(self, order_id: str) -> bool:
        """Process a coffee order"""
        if order_id not in self.shop_state.orders:
            return False
        
        order = self.shop_state.orders[order_id]
        
        # Don't process already served orders
        if order.status == 'served':
            return False
        
        # Try to allocate resources for preparation
        if (self.shop_state.allocate_resource("espresso_machine_1") and
            self.shop_state.allocate_resource("coffee_grinder")):
            
            # Update order status through preparation stages
            self.shop_state.update_order_status(order_id, "preparing")
            self.shop_state.update_order_status(order_id, "brewing")
            
            # For milk-based drinks, need milk steamer
            if order.coffee_type in ['latte', 'cappuccino']:
                if not self.shop_state.allocate_resource("milk_steamer"):
                    # Release other resources if milk steamer not available
                    self.shop_state.release_resource("espresso_machine_1")
                    self.shop_state.release_resource("coffee_grinder")
                    return False
            
            self.shop_state.update_order_status(order_id, "ready")
            self.shop_state.update_order_status(order_id, "served")
            
            # Release resources
            self.shop_state.release_resource("espresso_machine_1")
            self.shop_state.release_resource("coffee_grinder")
            if order.coffee_type in ['latte', 'cappuccino']:
                self.shop_state.release_resource("milk_steamer")
            
            # Update inventory
            self.shop_state.inventory["coffee_beans"] -= 1
            self.shop_state.inventory["cups"] -= 1
            if order.coffee_type in ['latte', 'cappuccino']:
                self.shop_state.inventory["milk"] -= 1
            
            self.shop_state.completed_orders += 1
            return True
        
        return False
    
    async def run_demo(self):
        """Run the complete coffee shop demo"""
        print("☕ COFFEE SHOP MULTI-AGENT SYSTEM")
        print("State Coordination Exercise Solution")
        print("=" * 50)
        
        # Display initial state
        self.display_shop_state()
        
        # Place some sample orders
        sample_orders = [
            {"customer_name": "Alice", "coffee_type": "latte", "size": "medium"},
            {"customer_name": "Bob", "coffee_type": "espresso", "size": "small"},
            {"customer_name": "Charlie", "coffee_type": "cappuccino", "size": "large"},
            {"customer_name": "Diana", "coffee_type": "americano", "size": "medium"},
        ]
        
        order_ids = []
        for order in sample_orders:
            order_id = self.place_order(**order)
            order_ids.append(order_id)
            print(f"📝 Order placed: {order_id} - {order['coffee_type']} for {order['customer_name']}")
        
        # Demo scenarios
        scenarios = [
            "Check current order status and prioritize preparation",
            "Manage coffee machine resources and resolve conflicts", 
            "Check inventory levels and suggest restocking",
            "What's our current service efficiency?",
            "How can we improve our coffee preparation process?"
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎯 SCENARIO {i}: {scenario}")
            print("-" * 50)
            
            await self.process_scenario(scenario)
            
            # Process some orders between scenarios to show state changes
            if i < len(scenarios) and order_ids:
                unprocessed_orders = [oid for oid in order_ids 
                                    if self.shop_state.orders[oid].status != 'served']
                orders_to_process = unprocessed_orders[:min(2, len(unprocessed_orders))]
                
                for order_id in orders_to_process:
                    if self.process_order(order_id):
                        print(f"👨‍🍳 Processed order: {order_id}")
                    else:
                        print(f"⏳ Could not process order {order_id} - resources busy")
        
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
            response = result.get('analysis', result.get('recommendations', result.get('inventory_advice', 'No response')))
            print(f"Response: {response}")
            
            # Show additional data if available
            if 'pending_orders' in result and result['pending_orders']:
                print("⏳ Pending Orders:", result['pending_orders'])
            if 'bottlenecks' in result and result['bottlenecks']:
                print("🚧 Bottlenecks:", result['bottlenecks'])
            if 'low_stock' in result and result['low_stock']:
                print("📉 Low Stock:", result['low_stock'])
    
    def display_shop_state(self):
        """Display current shop state"""
        print("\n📊 CURRENT SHOP STATE:")
        print(f"📦 Total Orders: {len(self.shop_state.orders)}")
        print(f"✅ Completed Orders: {self.shop_state.completed_orders}")
        print(f"🔧 Coffee Resources: {len(self.shop_state.resources)}")
        
        # Resource status
        available = sum(1 for r in self.shop_state.resources.values() if r.available)
        print(f"🟢 Available Resources: {available}/{len(self.shop_state.resources)}")
        print(f"📦 Inventory: {self.shop_state.inventory}")
    
    def display_final_state(self):
        """Display final state after demo"""
        print("\n📈 FINAL SHOP STATE:")
        print(f"📦 Total Orders: {len(self.shop_state.orders)}")
        print(f"✅ Completed Orders: {self.shop_state.completed_orders}")
        
        # Order status breakdown
        status_count = {}
        for order in self.shop_state.orders.values():
            status_count[order.status] = status_count.get(order.status, 0) + 1
        
        print("📊 Order Status:", status_count)
        
        # Resource utilization
        print("🔧 Resource Utilization:")
        for resource in self.shop_state.resources.values():
            utilization = (resource.current_usage / resource.capacity) * 100
            print(f"  {resource.name}: {resource.current_usage}/{resource.capacity} ({utilization:.1f}%)")
        
        print(f"📦 Final Inventory: {self.shop_state.inventory}")

async def main():
    # Check environment variables
    required_vars = ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing environment variables. Please check your .env file.")
        print(f"Missing: {missing_vars}")
        return
    
    # Create and run the coffee shop system
    coffee_shop = CoffeeShopSystem()
    await coffee_shop.run_demo()

if __name__ == "__main__":
    asyncio.run(main())