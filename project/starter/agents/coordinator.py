import asyncio
import json
import pyodbc
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from shared_state import SharedState
from llm_utils import parse_json_with_retry

"""
Orchestrator agent that routes requests to specialized workers.
This demonstrates the mediator pattern - coordinating multiple components.
"""

class DataConnector:
    """
    Mock data access layer. In real implementation, this would connect to databases.
    Students: Replace this with actual SQL queries or API calls.
    """
    def __init__(self,datastore: Optional[Dict[str, Any]] = None,connection_string: Optional[str] = None):
        # Mock customer data for educational purposes
        self.datastore =datastore or {}
        self.connection_string = connection_string

    async def fetch_income(self, customer_id: str) -> Optional[float]:
        """Mock income fetch - students: implement real database query here"""
        await asyncio.sleep(0.1)  # Simulate network delay
        return self.datastore.get(customer_id, {}).get("income")

    async def fetch_transactions(self, customer_id: str) -> List[Dict]:
        """Mock transactions fetch - students: implement real database query here"""
        await asyncio.sleep(0.1)  # Simulate network delay
        return self.datastore.get(customer_id, {}).get("transactions", [])

class CoordinatorAgent:
    """
    Central coordinator that understands customer intent and routes to appropriate agents.
    Students: This is where you'd add more sophisticated routing logic.
    """
    def __init__(self, workers: Dict[str, Any], data_connector: Optional[DataConnector] = None):
        self.workers = workers
        self.data_connector = data_connector or DataConnector()
        self.activated_agents = []  # Track which agents were used

    async def handle(self, ctx: Any):
        """
        Main coordination logic. Analyzes query and routes to appropriate agents.
        Students: This demonstrates the strategy pattern - choosing algorithms at runtime.
        """
        print(f"[Coordinator] Analyzing query for customer {ctx.customer_id}")
        
        # Simple intent detection - students can enhance this with ML/NLP
        query = ctx.payload.get("query", "").lower()
        tasks = self._detect_intent(query)
        
        # Get customer data (mock implementation)
        income = await self.get_income(ctx.customer_id)
        transactions = await self.get_transactions(ctx.customer_id)
        
        # Prepare context for specialized agents
        enriched_payload = {
            "query": query,
            "tasks": tasks,
            "income": income,
            "transactions": transactions,
            "customer_id": ctx.customer_id
        }
        
        ctx.payload = enriched_payload
        print(f"[Coordinator] Routing to agents: {tasks}")

        # Execute agents concurrently - demonstrates async programming
        results = []
        self.activated_agents = []
        
        for task in tasks:
            if task in self.workers:
                self.activated_agents.append(task)
                worker = self.workers[task]
                
                # Call appropriate method based on agent type
                if hasattr(worker, 'check'):
                    result = await worker.check(ctx)
                else:
                    result = await worker.assist(ctx)
                
                results.append(result)
        
        # Synthesize final response
        if "synthesis" in self.workers:
            final_result = await self.workers["synthesis"].build_report(ctx, results)
        else:
            final_result = {"results": results}
        
        return final_result

    def _detect_intent(self, query: str) -> List[str]:
        """Simple rule-based intent detection - students can replace with ML model"""
        tasks = []
        
        if any(word in query for word in ["fraud", "suspicious", "unauthorized", "stolen"]):
            tasks.append("fraud")
        
        if any(word in query for word in ["loan", "borrow", "credit", "mortgage"]):
            tasks.append("loans")
        
        if any(word in query for word in ["help", "support", "question", "how to"]):
            tasks.append("support")
        
        return tasks if tasks else ["support"]  # Default to support

    async def get_income(self, customer_id: str) -> Optional[float]:
        """Get customer income with caching example"""
        # Students: Implement real caching mechanism here
        return await self.data_connector.fetch_income(customer_id)

    async def get_transactions(self, customer_id: str) -> List[Dict]:
        """Get customer transactions"""
        return await self.data_connector.fetch_transactions(customer_id)