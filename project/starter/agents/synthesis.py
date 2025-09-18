from typing import Any, List
from models import SynthReport
from llm_utils import parse_json_with_retry
"""
Synthesis agent that combines results from all specialists into a cohesive response.
Students: This demonstrates the composite pattern.
"""

class SynthesisAgent:
    def __init__(self):
        print("[SynthesisAgent] Initialized - ready to create comprehensive reports")

    async def build_report(self, ctx: Any, findings: List[Any]):
        """
        Combine results from all agents into a final customer response.
        Students: Implement more sophisticated report generation here.
        """
        print(f"[SynthesisAgent] Synthesizing report for {ctx.customer_id}")
        
        # Mock synthesis - students replace with real aggregation logic
        risk_score = 0.0
        decisions = {}
        
        for finding in findings:
            if finding.get("agent") == "fraud" and finding["result"].get("suspicious"):
                risk_score += 0.6
                decisions["fraud_action"] = finding["result"].get("recommended_action")
            
            if finding.get("agent") == "loans":
                decisions["loan_eligibility"] = finding["result"].get("eligible")
                decisions["credit_score"] = finding["result"].get("credit_score")
        
        return {
            "report": {
                "summary": f"Comprehensive analysis for customer {ctx.customer_id}",
                "risk_score": min(1.0, risk_score),
                "decisions": decisions,
                "customer_id": ctx.customer_id
            }
        }