import json
from typing import Any,List, Dict
from models import LoanResult
from llm_utils import parse_json_with_retry

"""
Loan evaluation agent specialized in credit assessment.
Students: This demonstrates specialized domain expertise.
"""
from typing import Any

class LoansAgent:
    def __init__(self):
        # In real implementation, this would have credit scoring models
        print("[LoansAgent] Initialized - ready to evaluate loan applications")

    async def check(self, ctx: Any):
        """
        Evaluate loan eligibility based on customer data.
        Students: Implement real credit scoring algorithms here.
        """
        print(f"[LoansAgent] Evaluating loan eligibility for {ctx.customer_id}")
        
        # Mock loan evaluation - students replace with real logic
        income = ctx.payload.get("income", 0)
        transactions = ctx.payload.get("transactions", [])
        
        # Simple rule: income > 3000 and no very large debits
        eligible = income > 3000
        credit_score = min(850, int(income / 10) + 600)  # Mock score
        
        return {
            "agent": "loans",
            "result": {
                "credit_score": credit_score,
                "eligible": eligible,
                "rationale": "Sufficient income and good transaction history" if eligible else "Income below threshold",
                "recommended_action": "Approve with standard terms" if eligible else "Request additional income verification",
                "required_documents": ["id_proof", "income_proof"] if eligible else ["id_proof", "income_proof", "bank_statements"]
            }
        }