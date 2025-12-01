import asyncio
import os
import pyodbc
from contextlib import contextmanager
from typing import List, Dict, Optional
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents.runtime import InProcessRuntime
from dotenv import load_dotenv

load_dotenv()

class BankDataConnector:
    """Data connector for bank transactions from Azure SQL Server"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv("AZURE_SQL_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable not set")
        
        # Load initial data from database
        self.transactions_data = self._load_transaction_data()
    
    @contextmanager
    def get_db_connection(self):
        """Database connection helper for Azure SQL Server"""
        conn = pyodbc.connect(self.connection_string)
        try:
            yield conn
        finally:
            conn.close()

    def _load_transaction_data(self) -> Dict[str, List[Dict]]:
        """Load transaction data from Azure SQL database"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                data = {}
                
                # Query to get transaction data from Example_Transactions table
                cursor.execute("""
                    SELECT id, account_id, type, amount, 
                           date, status, description 
                    FROM Example_Transactions 
                    ORDER BY date DESC
                """)
                
                for row in cursor.fetchall():
                    id, account_id, type, amount, date, status, description = row
                    
                    if data.get(account_id) is None:
                        data[account_id] = {
                            "transactions": [{
                                "id": id,
                                "account_id": account_id,
                                "type": type,
                                "amount": float(amount),
                                "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                                "status": status,
                                "description": description or ""
                            }]
                        }
                    else:
                        data[account_id]['transactions'].append({
                            "id": id,
                            "account_id": account_id,
                            "type": type,
                            "amount": float(amount),
                            "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                            "status": status,
                            "description": description or ""
                        })
                
                print(f"✅ Loaded transactions for {len(data)} accounts from Example_Transactions table")
                return data
                
        except Exception as e:
            print(f"❌ Error loading transaction data: {e}")
            return {}
    
    def get_transactions(self, account_id: Optional[str] = None) -> List[Dict]:
        """Get transactions - optionally filtered by account"""
        try:
            if account_id:
                # Return transactions for specific account
                account_data = self.transactions_data.get(account_id, {})
                return account_data.get("transactions", [])
            else:
                # Return all transactions across all accounts
                all_transactions = []
                for account_data in self.transactions_data.values():
                    all_transactions.extend(account_data.get("transactions", []))
                return all_transactions
                
        except Exception as e:
            print(f"❌ Error getting transactions: {e}")
            return []
    
    def get_account_balance(self, account_id: str) -> float:
        """Calculate current balance for an account from database"""
        try:
            # Use the pre-loaded data for balance calculation
            account_transactions = self.get_transactions(account_id)
            balance = 0.0
            
            for transaction in account_transactions:
                if transaction["status"] == "completed":
                    if transaction["type"] in ["deposit", "credit"]:
                        balance += transaction["amount"]
                    else:  # withdrawal, transfer, debit
                        balance -= transaction["amount"]
            
            return balance
            
        except Exception as e:
            print(f"❌ Error calculating balance for account {account_id}: {e}")
            return 0.0
    
    def add_transaction(self, account_id: str, type: str, amount: float, 
                       description: str = "", status: str = "pending") -> bool:
        """Add a new transaction to the database"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insert new transaction record
                cursor.execute("""
                    INSERT INTO Example_Transactions 
                    (account_id, type, amount, date, status, description)
                    VALUES (?, ?, ?, GETDATE(), ?, ?)
                """, account_id, type, amount, status, description)
                
                conn.commit()
                print(f"✅ Added transaction for account {account_id}: {type} ${amount}")
                
                # Refresh the local data cache
                self.transactions_data = self._load_transaction_data()
                return True
                
        except Exception as e:
            print(f"❌ Error adding transaction: {e}")
            return False
    
    def get_accounts(self) -> List[str]:
        """Get list of all account IDs from the database"""
        try:
            return list(self.transactions_data.keys())
        except Exception as e:
            print(f"❌ Error getting account list: {e}")
            return ["ACC001", "ACC002", "ACC003"]  # Fallback
    
    def get_recent_transactions(self, account_id: str, limit: int = 5) -> List[Dict]:
        """Get recent transactions for an account"""
        try:
            all_transactions = self.get_transactions(account_id)
            # Sort by date descending and return limited results
            sorted_transactions = sorted(
                all_transactions, 
                key=lambda x: x["date"], 
                reverse=True
            )
            return sorted_transactions[:limit]
        except Exception as e:
            print(f"❌ Error getting recent transactions: {e}")
            return []

class BankAgentManager:
    """Complete banking agent system with intelligent routing and Azure SQL integration"""
    
    def __init__(self):
        # Shared kernel instance for optimal resource usage
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_banking_chat",
                deployment_name=os.environ["AZURE_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_DEPLOYMENT_KEY"]
            )
        )
        
        # Initialize data connector for Azure SQL database
        self.data_connector = BankDataConnector()
        
        # Initialize specialized banking agents with detailed instructions
        self.agents = {
            "account": ChatCompletionAgent(
                kernel=self.kernel,
                name="Account_Specialist",
                description="Specialist in account balances and transaction inquiries",
                instructions="""You are a bank account specialist. Help customers with account-related inquiries.

                Always provide:
                - Clear explanation of account status and balances
                - Recent transaction summaries with context
                - Answers to specific account questions
                - Next steps if action is needed

                Use transaction data from the database to provide accurate, data-driven responses.
                Be helpful, professional, and focus on security and accuracy."""
            ),
            "loan": ChatCompletionAgent(
                kernel=self.kernel,
                name="Loan_Specialist",
                description="Specialist in loan applications and financing",
                instructions="""You are a bank loan specialist. Assist customers with loan inquiries and applications.

                Always include:
                - Information about various loan options and products
                - Eligibility requirements and qualification criteria
                - Application process explanation with timelines
                - Interest rate information and payment calculations
                - Documentation requirements and next steps

                Provide clear, accurate information about loan products and processes."""
            ),
            "card": ChatCompletionAgent(
                kernel=self.kernel,
                name="Card_Specialist", 
                description="Specialist in credit and debit card services",
                instructions="""You are a bank card specialist. Handle card-related inquiries and issues.

                Always provide:
                - Card service information and features
                - Issue resolution steps for problems
                - Replacement and renewal processes
                - Security recommendations and fraud prevention
                - Activation and usage guidance

                Focus on quick resolution, security, and customer satisfaction."""
            ),
            "emergency": ChatCompletionAgent(
                kernel=self.kernel,
                name="Emergency_Specialist",
                description="Specialist in urgent banking issues and security concerns",
                instructions="""You are an emergency banking specialist. Handle urgent requests immediately.

                This is HIGH PRIORITY. Always provide:
                - Immediate action steps for urgent situations
                - Emergency contact information and procedures
                - Fraud prevention and security measures
                - Account protection steps and temporary holds
                - Clear timelines for resolution and follow-up

                Respond with URGENCY and provide clear emergency procedures.
                Focus on security, speed, and customer reassurance."""
            ),
            "router": ChatCompletionAgent(
                kernel=self.kernel,
                name="Routing_Agent",
                description="Intelligent router for banking request distribution",
                instructions="""You are an intelligent routing agent. Analyze banking requests and route to appropriate specialists.

                Analyze each request and determine:
                1. Which specialist should handle it (account/loan/card/emergency)
                2. The urgency level (Low/Medium/High/Emergency)
                3. Brief reasoning for your decision

                Specialist Responsibilities:
                - account: Account balances, transactions, account information, transfers
                - loan: Loan applications, mortgages, personal loans, interest rates, financing
                - card: Credit/debit card issues, lost cards, card applications, disputes
                - emergency: Fraud, stolen cards, urgent account issues, security breaches

                Urgency Guidelines:
                - Low: General inquiries, information requests, product questions
                - Medium: Service requests, application status, routine issues
                - High: Time-sensitive issues, payment problems, card declines
                - Emergency: Fraud, security breaches, lost/stolen cards, unauthorized transactions

                Respond in this exact format:
                Specialist: [account/loan/card/emergency]
                Urgency: [Low/Medium/High/Emergency]
                Reasoning: [brief explanation]"""
            )
        }
        
        self.runtime = InProcessRuntime()

    async def route_customer_request(self, customer_request: str) -> dict:
        """Intelligent routing of customer requests to appropriate specialists"""
        print(f"📥 Customer Request: {customer_request}")
        print("🔄 Analyzing request and determining routing...")
        
        # Use routing agent to analyze the request
        routing_prompt = f"CUSTOMER REQUEST: {customer_request}"
        
        routing_response = await self.agents["router"].get_response(routing_prompt)
        routing_content = str(routing_response.content)
        
        # Parse routing decision
        routing_decision = self._parse_routing_decision(routing_content)
        
        print(f"✅ Routing Decision:")
        print(f"   Specialist: {routing_decision['specialist']}")
        print(f"   Urgency: {routing_decision['urgency']}")
        print(f"   Reasoning: {routing_decision['reasoning']}")
        
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

    async def process_with_specialist(self, customer_request: str, specialist: str, urgency: str) -> str:
        """Process customer request with the appropriate specialist"""
        print(f"🔧 Connecting to {specialist} specialist...")
        
        # Get relevant transaction data for context
        accounts = self.data_connector.get_accounts()
        transaction_context = ""
        
        if specialist == "account":
            # Provide transaction data for account inquiries
            recent_transactions = []
            for account in accounts[:2]:  # Show data for first 2 accounts
                transactions = self.data_connector.get_recent_transactions(account, 3)
                balance = self.data_connector.get_account_balance(account)
                recent_transactions.append(f"Account {account} (Balance: ${balance:.2f}): {transactions}")
            
            transaction_context = f"\n\nACCOUNT DATA CONTEXT:\n" + "\n".join(recent_transactions)
        
        # Add urgency context for emergency situations
        urgency_context = ""
        if urgency in ["High", "Emergency"]:
            urgency_context = f"\n\n🚨 URGENCY: {urgency} - Requiring immediate attention"
        
        # Process request with specialist agent
        full_request = f"CUSTOMER REQUEST: {customer_request}{transaction_context}{urgency_context}"
        
        specialist_response = await self.agents[specialist].get_response(full_request)
        
        return f"🏦 **{specialist.capitalize()} Assistance**\n\n{specialist_response.content}"

    async def handle_customer_request(self, customer_request: str) -> dict:
        """Complete processing of a customer request"""
        # Step 1: Route the request
        routing_decision = await self.route_customer_request(customer_request)
        
        # Step 2: Process with appropriate specialist
        if routing_decision["specialist"] in self.agents:
            specialist_response = await self.process_with_specialist(
                customer_request, 
                routing_decision["specialist"],
                routing_decision["urgency"]
            )
            
            return {
                "routing_decision": routing_decision,
                "specialist_response": specialist_response,
                "specialist_name": routing_decision["specialist"].capitalize() + " Specialist"
            }
        else:
            return {
                "routing_decision": routing_decision,
                "specialist_response": "❌ No suitable specialist found for this request.",
                "specialist_name": "Unknown"
            }

    def display_result(self, result: dict):
        """Display the processing result"""
        print(f"\n🎯 REQUEST PROCESSING COMPLETE")
        print(f"Handled by: {result['specialist_name']}")
        print(f"Urgency: {result['routing_decision']['urgency']}")
        print("\n" + "=" * 60)
        print(f"{result['specialist_response']}")
        print("=" * 60)

async def main():
    """Main banking system demo"""
    print("🏦 BANKING MULTI-AGENT SYSTEM - COMPLETE SOLUTION")
    print("Intelligent Routing and Data Flow with Azure SQL")
    print("Semantic Kernel 1.37.0 with Modern Agent Framework")
    print("=" * 70)
    
    # Validate environment setup
    required_vars = [
        "AZURE_DEPLOYMENT_NAME",
        "AZURE_DEPLOYMENT_ENDPOINT", 
        "AZURE_DEPLOYMENT_KEY",
        "AZURE_SQL_CONNECTION_STRING"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return
    
    manager = BankAgentManager()
    
    # Sample customer requests covering different scenarios
    customer_requests = [
        "I want to check my account balance and recent transactions for ACC001",
        "I'm interested in applying for a home loan, what are the requirements and current rates?",
        "My credit card was stolen this morning, I need to report it immediately and get a replacement",
        "Can you help me with a personal loan for $10,000? What's the application process?",
        "I noticed a suspicious transaction of $300 on my account from yesterday that I don't recognize",
        "What's the process to get a new debit card and how long does it take?",
        "I need to transfer $500 to my savings account urgently",
        "What are your current mortgage interest rates for a 30-year fixed loan?"
    ]
    
    # Process customer requests
    for i, customer_request in enumerate(customer_requests[:4], 1):
        print(f"\n{'#' * 70}")
        print(f"CUSTOMER REQUEST #{i}")
        print(f"{'#' * 70}")
        
        try:
            result = await manager.handle_customer_request(customer_request)
            manager.display_result(result)
            
            # Brief pause between requests
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            continue
    
    print("\n✅ Banking system demo completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())