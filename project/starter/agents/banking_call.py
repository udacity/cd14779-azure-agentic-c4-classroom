"""
Entry point agent that receives customer calls and routes to coordinator.
This demonstrates the facade pattern - a simple interface to a complex system.
"""
from typing import Any
from .coordinator import CoordinatorAgent

class BankingCallAgent:
    def __init__(self, coordinator: CoordinatorAgent):
        self.coordinator = coordinator

    async def receive_call(self, ctx: Any):
        """
        Main entry point for customer interactions.
        Students: This is where you'd add authentication, logging, or input validation.
        """
        print(f"[BankingCallAgent] Received call for customer {ctx.customer_id}")
        print(f"[BankingCallAgent] Query: '{ctx.payload.get('query', '')}'")
        
        # Delegate to coordinator for complex routing logic
        result = await self.coordinator.handle(ctx)
        
        print(f"[BankingCallAgent] Call completed for {ctx.customer_id}")
        return result