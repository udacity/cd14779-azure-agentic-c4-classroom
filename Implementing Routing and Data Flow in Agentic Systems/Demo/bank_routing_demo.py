import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from dotenv import load_dotenv

load_dotenv()

class BankDataConnector:
    """Simple data connector for bank transactions (simulated)"""
    
    def __init__(self):
        # In a real scenario, this would connect to Azure SQL Server
        # For demo purposes, we'll use simulated data
        self.transactions = [
            {"id": 1, "account_id": "ACC001", "type": "deposit", "amount": 1000.00, "date": "2024-01-15", "status": "completed"},
            {"id": 2, "account_id": "ACC001", "type": "withdrawal", "amount": 250.50, "date": "2024-01-16", "status": "completed"},
            {"id": 3, "account_id": "ACC002", "type": "deposit", "amount": 500.00, "date": "2024-01-17", "status": "completed"},
            {"id": 4, "account_id": "ACC001", "type": "transfer", "amount": 100.00, "date": "2024-01-18", "status": "pending"},
            {"id": 5, "account_id": "ACC003", "type": "withdrawal", "amount": 50.00, "date": "2024-01-18", "status": "failed"},
        ]
    
    def get_transactions(self, account_id=None):
        """Get transactions - optionally filtered by account"""
        if account_id:
            return [t for t in self.transactions if t["account_id"] == account_id]
        return self.transactions
    
    def get_account_balance(self, account_id):
        """Calculate current balance for an account"""
        account_transactions = self.get_transactions(account_id)
        balance = 0.0
        
        for transaction in account_transactions:
            if transaction["status"] == "completed":
                if transaction["type"] == "deposit":
                    balance += transaction["amount"]
                else:  # withdrawal or transfer
                    balance -= transaction["amount"]
        
        return balance

class BankAgent:
    """Base class for all bank specialist agents"""
    
    def __init__(self, name: str, specialty: str):
        self.name = name
        self.specialty = specialty
        self.kernel = Kernel()
        self.data_connector = BankDataConnector()
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"]
            )
        )
    
    async def process_request(self, request: str) -> str:
        """Process bank request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

class AccountAgent(BankAgent):
    """Agent specializing in account inquiries and balance checks"""
    
    def __init__(self):
        super().__init__("Account Specialist", "Account balances and information")
    
    async def process_request(self, request: str) -> str:
        """Handle account-related inquiries"""
        
        prompt = """
        You are a bank account specialist. Help the customer with their account inquiry.

        CUSTOMER REQUEST: {{$request}}

        Available transaction data will be provided separately.

        Please provide:
        - Clear explanation of account status
        - Recent transaction summary if relevant
        - Answers to specific account questions
        - Next steps if action is needed

        Be helpful and professional.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="account_inquiry",
            plugin_name="account",
            prompt=prompt
        )
        
        # Get transaction data for context
        account_transactions = self.data_connector.get_transactions("ACC001")  # Default account for demo
        transaction_context = f"Recent transactions: {account_transactions}"
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            transaction_data=transaction_context
        )
        
        return f"🏦 **Account Assistance**\n\n{result}"

class LoanAgent(BankAgent):
    """Agent specializing in loan inquiries and applications"""
    
    def __init__(self):
        super().__init__("Loan Specialist", "Loan applications and information")
    
    async def process_request(self, request: str) -> str:
        """Handle loan-related inquiries"""
        
        prompt = """
        You are a bank loan specialist. Help the customer with their loan inquiry.

        CUSTOMER REQUEST: {{$request}}

        Please provide:
        - Information about loan options
        - Eligibility requirements
        - Application process explanation
        - Interest rate information if available
        - Next steps for application

        Be clear about requirements and helpful with next steps.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="loan_inquiry",
            plugin_name="loan",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"💰 **Loan Assistance**\n\n{result}"

class CardAgent(BankAgent):
    """Agent specializing in credit/debit card services"""
    
    def __init__(self):
        super().__init__("Card Specialist", "Credit and debit card services")
    
    async def process_request(self, request: str) -> str:
        """Handle card-related inquiries"""
        
        prompt = """
        You are a bank card specialist. Help the customer with their card inquiry.

        CUSTOMER REQUEST: {{$request}}

        Please provide:
        - Card service information
        - Issue resolution steps
        - Replacement process if needed
        - Security recommendations
        - Next steps for the customer

        Focus on quick resolution and security.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="card_inquiry",
            plugin_name="card",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"💳 **Card Assistance**\n\n{result}"

class EmergencyAgent(BankAgent):
    """Agent specializing in urgent banking issues"""
    
    def __init__(self):
        super().__init__("Emergency Specialist", "Urgent banking issues")
    
    async def process_request(self, request: str) -> str:
        """Handle urgent banking issues"""
        
        prompt = """
        You are an emergency banking specialist. Handle this urgent request immediately.

        URGENT REQUEST: {{$request}}

        This is HIGH PRIORITY. Please provide:
        - Immediate action steps
        - Emergency contact information
        - Fraud prevention measures
        - Account protection steps
        - Timeline for resolution

        Respond with URGENCY and provide clear emergency procedures.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="emergency_assistance",
            plugin_name="emergency",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🚨 **EMERGENCY ASSISTANCE**\n\n{result}"

class RoutingAgent:
    """Intelligent router that directs requests to appropriate specialists"""
    
    def __init__(self):
        self.specialists = {
            "account": AccountAgent(),
            "loan": LoanAgent(),
            "card": CardAgent(),
            "emergency": EmergencyAgent()
        }
        
        self.kernel = Kernel()
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"]
            )
        )
    
    async def route_request(self, customer_request: str) -> dict:
        """Analyze request and route to appropriate specialist"""
        
        routing_prompt = """
        Analyze this bank customer request and determine:
        1. Which specialist should handle it
        2. The urgency level (Low, Medium, High, Emergency)
        3. Brief reasoning for your decision

        CUSTOMER REQUEST: {{$request}}

        Available specialists:
        - account: Account balances, transactions, account information
        - loan: Loan applications, mortgage, personal loans, interest rates
        - card: Credit/debit card issues, lost cards, card applications
        - emergency: Fraud, stolen cards, urgent account issues, security concerns

        Urgency levels:
        - Low: General inquiries, information requests
        - Medium: Service requests, application status
        - High: Time-sensitive issues, payment problems
        - Emergency: Fraud, security breaches, lost/stolen cards

        Respond in this exact format:
        Specialist: [account/loan/card/emergency]
        Urgency: [Low/Medium/High/Emergency]
        Reasoning: [brief explanation]
        """
        
        routing_function = KernelFunctionFromPrompt(
            function_name="request_routing",
            plugin_name="router",
            prompt=routing_prompt
        )
        
        routing_result = await self.kernel.invoke(
            routing_function, 
            request=customer_request
        )
        
        # Parse the routing decision
        routing_text = str(routing_result)
        routing_decision = self._parse_routing_decision(routing_text)
        
        return routing_decision
    
    def _parse_routing_decision(self, routing_text: str) -> dict:
        """Parse the routing decision from the AI response"""
        lines = routing_text.strip().split('\n')
        decision = {
            "specialist": "account",  # default
            "urgency": "Medium",      # default
            "reasoning": "Unable to parse routing decision",
            "raw_response": routing_text
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('Specialist:'):
                decision["specialist"] = line.split(':')[1].strip().lower()
            elif line.startswith('Urgency:'):
                decision["urgency"] = line.split(':')[1].strip()
            elif line.startswith('Reasoning:'):
                decision["reasoning"] = line.split(':')[1].strip()
        
        return decision
    
    async def process_customer_request(self, customer_request: str) -> dict:
        """Complete routing and processing of customer request"""
        
        print(f"📥 Customer Request: {customer_request}")
        print("🔄 Analyzing request and determining routing...")
        
        # Step 1: Route the request
        routing_decision = await self.route_request(customer_request)
        
        print(f"✅ Routing Decision:")
        print(f"   Specialist: {routing_decision['specialist']}")
        print(f"   Urgency: {routing_decision['urgency']}")
        print(f"   Reasoning: {routing_decision['reasoning']}")
        
        # Step 2: Process with appropriate specialist
        specialist_key = routing_decision["specialist"]
        if specialist_key in self.specialists:
            print(f"🔧 Connecting to {self.specialists[specialist_key].name}...")
            specialist_result = await self.specialists[specialist_key].process_request(customer_request)
            
            return {
                "routing_decision": routing_decision,
                "specialist_response": specialist_result,
                "specialist_name": self.specialists[specialist_key].name
            }
        else:
            return {
                "routing_decision": routing_decision,
                "specialist_response": "❌ No suitable specialist found for this request.",
                "specialist_name": "Unknown"
            }

class BankOfficeSystem:
    """Main bank office system coordinating all agents"""
    
    def __init__(self):
        self.router = RoutingAgent()
    
    async def handle_customer_requests(self, requests: list):
        """Process multiple customer requests"""
        
        print("🏦 BANK OFFICE MULTI-AGENT SYSTEM")
        print("Intelligent Routing and Data Flow Demo")
        print("=" * 60)
        
        for i, request in enumerate(requests, 1):
            print(f"\n{'#' * 60}")
            print(f"CUSTOMER REQUEST #{i}")
            print(f"{'#' * 60}")
            
            try:
                result = await self.router.process_customer_request(request)
                self.display_result(result)
                
                # Small pause between requests
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing request: {e}")
                continue

    def display_result(self, result: dict):
        """Display the processing result"""
        print(f"\n🎯 REQUEST PROCESSING COMPLETE")
        print(f"Handled by: {result['specialist_name']}")
        print(f"Urgency: {result['routing_decision']['urgency']}")
        print("\n" + "=" * 50)
        print(f"{result['specialist_response']}")
        print("=" * 50)

async def main():
    bank_system = BankOfficeSystem()
    
    # Sample customer requests
    customer_requests = [
        "I want to check my account balance and recent transactions",
        "I'm interested in applying for a home loan, what are the requirements?",
        "My credit card was stolen this morning, I need to report it immediately",
        "Can you help me with a personal loan for $10,000?",
        "I noticed a suspicious transaction on my account from yesterday",
        "What's the process to get a new debit card?",
        "I need to transfer money to another account urgently",
        "What are your current mortgage interest rates?"
    ]
    
    # Process all customer requests
    await bank_system.handle_customer_requests(customer_requests)

if __name__ == "__main__":
    asyncio.run(main())