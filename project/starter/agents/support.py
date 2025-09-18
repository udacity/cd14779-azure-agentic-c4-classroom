import json
from typing import Any,List, Dict
from llm_utils import parse_json_with_retry

"""
Customer support agent specialized in general assistance and guidance.
Students: This demonstrates customer service automation.
"""

class SupportAgent:
    def __init__(self):
        # In real implementation, this would have knowledge base access
        print("[SupportAgent] Initialized - ready to assist customers")

    async def assist(self, ctx: Any):
        """
        Provide general customer support and guidance.
        Students: Integrate with real knowledge bases or helpdesk systems.
        """
        print(f"[SupportAgent] Assisting customer {ctx.customer_id}")
        
        # Mock support response - students replace with real logic
        query = ctx.payload.get("query", "").lower()
        
        if "password" in query:
            steps = ["reset_password", "verify_identity"]
        elif "contact" in query:
            steps = ["contact_human_support"]
        else:
            steps = ["provide_information", "escalate_issue"]
        
        return {
            "agent": "support",
            "result": {
                "suggested_steps": steps,
                "follow_up_actions": ["schedule_callback" if "contact" in query else ""],
                "required_documents": {}
            }
        }