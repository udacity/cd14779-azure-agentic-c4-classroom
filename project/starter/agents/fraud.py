import json
from typing import Any,List, Dict
from models import FraudResult
from llm_utils import parse_json_with_retry
"""
Fraud detection agent specialized in identifying suspicious activities.
Students: This demonstrates the single responsibility principle.
"""

class FraudAgent:
    def __init__(self):
        # In real implementation, this would have ML models or rule engines
        print("[FraudAgent] Initialized - ready to detect suspicious activity")

    async def check(self, ctx: Any):
        """
        Analyze transactions for fraud patterns.
        Students: Implement real fraud detection algorithms here.
        """
        print(f"[FraudAgent] Analyzing transactions for {ctx.customer_id}")
        
        # Mock fraud analysis - students replace with real logic
        transactions = ctx.payload.get("transactions", [])
        income = ctx.payload.get("income", 0)
        
        # Simple rule: large transactions relative to income are suspicious
        suspicious = any(tx['amount'] > income * 0.5 for tx in transactions)
        
        return {
            "agent": "fraud",
            "result": {
                "suspicious": suspicious,
                "rationale": "Large transaction detected relative to income" if suspicious else "No obvious fraud patterns",
                "evidence": {"large_transactions": [tx for tx in transactions if tx['amount'] > 1000]},
                "recommended_action": "Freeze account and contact customer" if suspicious else "Monitor normally"
            }
        }