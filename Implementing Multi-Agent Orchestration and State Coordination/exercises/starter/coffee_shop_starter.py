import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
load_dotenv("../../../.env")

# TODO: Define Pydantic Models
# Create models for:
# - CoffeeOrder: order_id, customer_name, coffee_type, size, status
# - CoffeeResource: resource_id, name, capacity, current_usage  
# - CoffeeShopState: orders, resources, completed_orders

class CoffeeOrder(BaseModel):
    """Model representing a coffee order"""
    # TODO: Add fields: order_id, customer_name, coffee_type, size, status, order_date
    pass

class CoffeeResource(BaseModel):
    """Model representing coffee shop resources"""
    # TODO: Add fields: resource_id, name, capacity, current_usage
    pass

class CoffeeShopState(BaseModel):
    """Central state management for the coffee shop"""
    # TODO: Add fields: orders, resources, completed_orders
    pass

# TODO: Create Base Agent Class
class CoffeeAgent:
    """Base class for all coffee shop agents"""
    
    def __init__(self, name: str, role: str, shop_state: CoffeeShopState):
        self.name = name
        self.role = role
        self.shop_state = shop_state
        self.kernel = Kernel()
        
        # TODO: Initialize AzureChatCompletion service
        # Use environment variables for Azure configuration
    
    async def process_request(self, request: str) -> Dict:
        raise NotImplementedError("Subclasses must implement this method")

# TODO: Implement Specialized Agents
class OrderAgent(CoffeeAgent):
    """Agent specializing in order management"""
    
    def __init__(self, shop_state: CoffeeShopState):
        super().__init__("Order Manager", "Manage coffee orders", shop_state)
    
    async def process_request(self, request: str) -> Dict:
        # TODO: Implement order management logic
        # Use prompt templates to analyze orders
        pass
    
    def _get_orders_summary(self) -> str:
        # TODO: Generate orders summary
        pass

class BaristaAgent(CoffeeAgent):
    """Agent specializing in coffee preparation"""
    
    def __init__(self, shop_state: CoffeeShopState):
        super().__init__("Barista", "Prepare coffee drinks", shop_state)
    
    async def process_request(self, request: str) -> Dict:
        # TODO: Implement barista logic
        # Handle resource allocation and coffee preparation
        pass

class InventoryAgent(CoffeeAgent):
    """Agent specializing in inventory management"""
    
    def __init__(self, shop_state: CoffeeShopState):
        super().__init__("Inventory Manager", "Manage coffee supplies", shop_state)
    
    async def process_request(self, request: str) -> Dict:
        # TODO: Implement inventory management
        # Track coffee beans, milk, syrups, etc.
        pass

# TODO: Implement Main Coffee Shop System
class CoffeeShopSystem:
    """Main coffee shop system coordinating all agents"""
    
    def __init__(self):
        # TODO: Initialize shop state and agents
        self.shop_state = CoffeeShopState()
        self._initialize_resources()
        self.agents = {}  # Initialize agents here
    
    def _initialize_resources(self):
        """Initialize coffee shop resources"""
        # TODO: Create coffee machines, grinders, etc.
        pass
    
    def place_order(self, customer_name: str, coffee_type: str, size: str) -> str:
        """Place a new coffee order"""
        # TODO: Implement order placement
        pass
    
    async def process_scenario(self, scenario: str):
        """Process a scenario with all agents"""
        # TODO: Implement scenario processing
        pass
    
    def display_shop_state(self):
        """Display current shop state"""
        # TODO: Implement state display
        pass

# TODO: Implement the demo execution
async def main():
    """Main function to run the coffee shop demo"""
    # TODO: Create coffee shop system and run demo scenarios
    
    scenarios = [
        "Check current order status and prioritize preparation",
        "Manage coffee machine resources and resolve conflicts",
        "Check inventory levels and suggest restocking",
        "What's our current service efficiency?",
        "How can we improve our coffee preparation process?"
    ]
    
    # TODO: Process each scenario and show state changes

if __name__ == "__main__":
    asyncio.run(main())