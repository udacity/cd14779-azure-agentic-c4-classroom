import asyncio
import os
from typing import Dict, List
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents import ChatHistory
from dotenv import load_dotenv

load_dotenv("../../.env")

# Modern KernelBaseModel for State Management
class Book(KernelBaseModel):
    """Model representing a book in the store using KernelBaseModel"""
    book_id: str
    title: str
    author: str
    genre: str
    price: float
    quantity: int
    is_bestseller: bool = False
    
    @kernel_function(
        name="check_availability",
        description="Check if the book is available in stock"
    )
    def check_availability(self) -> bool:
        """Check if book is available"""
        return self.quantity > 0
    
    @kernel_function(
        name="get_book_info",
        description="Get formatted book information"
    )
    def get_book_info(self) -> str:
        """Get formatted book information"""
        status = "🏆 BESTSELLER" if self.is_bestseller else "📚 Available"
        return f"{self.title} by {self.author} - ${self.price} ({self.genre}) - {status}"

class Customer(KernelBaseModel):
    """Model representing a customer using KernelBaseModel"""
    customer_id: str
    name: str
    email: str
    favorite_genres: List[str] = []
    total_spent: float = 0.0
    
    @kernel_function(
        name="check_vip_status",
        description="Check if customer is VIP based on spending"
    )
    def check_vip_status(self) -> bool:
        """Check if customer is VIP"""
        return self.total_spent > 500
    
    @kernel_function(
        name="get_customer_profile",
        description="Get formatted customer profile"
    )
    def get_customer_profile(self) -> str:
        """Get formatted customer profile"""
        vip_status = "⭐ VIP" if self.check_vip_status() else "👤 Regular"
        genres = ", ".join(self.favorite_genres) if self.favorite_genres else "No preferences"
        return f"{self.name} ({vip_status}) - Spent: ${self.total_spent:.2f} - Likes: {genres}"

class Order(KernelBaseModel):
    """Model representing a customer order using KernelBaseModel"""
    order_id: str
    customer_id: str
    book_ids: List[str]
    total_amount: float
    order_date: datetime
    status: str = "pending"
    
    @kernel_function(
        name="update_order_status",
        description="Update the order status with validation"
    )
    def update_order_status(self, new_status: str) -> bool:
        """Update order status with validation"""
        allowed_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        if new_status in allowed_statuses:
            self.status = new_status
            return True
        return False
    
    @kernel_function(
        name="get_order_summary",
        description="Get formatted order summary"
    )
    def get_order_summary(self) -> str:
        """Get formatted order summary"""
        return f"Order {self.order_id}: ${self.total_amount:.2f} - Status: {self.status}"

class StoreState(KernelBaseModel):
    """Central state management for the book store using KernelBaseModel"""
    books: Dict[str, Book] = {}
    customers: Dict[str, Customer] = {}
    orders: Dict[str, Order] = {}
    store_balance: float = 0.0
    daily_revenue: float = 0.0
    
    @kernel_function(
        name="add_book_to_inventory",
        description="Add or update book in inventory"
    )
    def add_book(self, book: Book) -> str:
        """Add or update book in inventory"""
        self.books[book.book_id] = book
        return f"✅ Added {book.title} to inventory"
    
    @kernel_function(
        name="remove_book_from_inventory",
        description="Remove quantity from book inventory"
    )
    def remove_book(self, book_id: str, quantity: int = 1) -> str:
        """Remove quantity from book inventory"""
        if book_id not in self.books:
            return f"❌ Book {book_id} not found in inventory"
        
        book = self.books[book_id]
        if book.quantity < quantity:
            return f"❌ Insufficient stock for {book.title}. Available: {book.quantity}"
        
        book.quantity -= quantity
        return f"✅ Removed {quantity} copy(ies) of {book.title}"
    
    @kernel_function(
        name="add_customer_to_database",
        description="Add or update customer in database"
    )
    def add_customer(self, customer: Customer) -> str:
        """Add or update customer"""
        self.customers[customer.customer_id] = customer
        return f"✅ Added customer {customer.name} to database"
    
    @kernel_function(
        name="create_new_order",
        description="Create a new customer order"
    )
    def add_order(self, order: Order) -> str:
        """Add a new order"""
        self.orders[order.order_id] = order
        return f"✅ Created order {order.order_id} for ${order.total_amount:.2f}"
    
    @kernel_function(
        name="record_sale_transaction",
        description="Record a sale and update store balance"
    )
    def record_sale(self, amount: float) -> str:
        """Record a sale and update store balance"""
        self.store_balance += amount
        self.daily_revenue += amount
        return f"✅ Recorded sale of ${amount:.2f}"
    
    @kernel_function(
        name="get_store_analytics",
        description="Get comprehensive store analytics"
    )
    def get_store_analytics(self) -> str:
        """Get comprehensive store analytics"""
        total_books = sum(book.quantity for book in self.books.values())
        total_value = sum(book.price * book.quantity for book in self.books.values())
        vip_customers = sum(1 for customer in self.customers.values() if customer.check_vip_status())
        
        return f"""
        📊 STORE ANALYTICS:
        • Store Balance: ${self.store_balance:.2f}
        • Today's Revenue: ${self.daily_revenue:.2f}
        • Total Book Copies: {total_books}
        • Book Types: {len(self.books)}
        • Inventory Value: ${total_value:.2f}
        • Customers: {len(self.customers)}
        • VIP Customers: {vip_customers}
        • Total Orders: {len(self.orders)}
        """

class StoreOperationsPlugin:
    """Plugin for store operations that can be properly registered with the kernel"""
    
    def __init__(self, store_state: StoreState):
        self.store_state = store_state
    
    @kernel_function(
        name="get_inventory_summary",
        description="Get current inventory summary"
    )
    def get_inventory_summary(self) -> str:
        """Get inventory summary"""
        total_books = sum(book.quantity for book in self.store_state.books.values())
        total_value = sum(book.price * book.quantity for book in self.store_state.books.values())
        
        return f"""
        📚 INVENTORY SUMMARY:
        • Total Books: {total_books}
        • Book Types: {len(self.store_state.books)}
        • Inventory Value: ${total_value:.2f}
        • Bestsellers: {sum(1 for book in self.store_state.books.values() if book.is_bestseller)}
        """
    
    @kernel_function(
        name="get_low_stock_books",
        description="Get books with low stock levels"
    )
    def get_low_stock_books(self) -> str:
        """Get low stock books"""
        low_stock = []
        for book in self.store_state.books.values():
            if book.quantity < 5:
                status = "🟥 CRITICAL" if book.quantity == 0 else "🟨 LOW"
                low_stock.append(f"{status} {book.title}: {book.quantity} left")
        
        if not low_stock:
            return "✅ All books have sufficient stock"
        return "\n".join(low_stock)
    
    @kernel_function(
        name="get_vip_customers_list",
        description="Get list of VIP customers"
    )
    def get_vip_customers_list(self) -> str:
        """Get VIP customers"""
        vip_customers = [customer for customer in self.store_state.customers.values() if customer.check_vip_status()]
        if not vip_customers:
            return "No VIP customers yet"
        
        vip_list = []
        for customer in vip_customers:
            vip_list.append(f"⭐ {customer.name}: ${customer.total_spent:.2f} spent")
        return "\n".join(vip_list)
    
    @kernel_function(
        name="get_bestsellers_list",
        description="Get current bestsellers"
    )
    def get_bestsellers_list(self) -> str:
        """Get bestsellers"""
        bestsellers = [book for book in self.store_state.books.values() if book.is_bestseller and book.quantity > 0]
        if not bestsellers:
            return "No bestsellers currently"
        
        bestseller_list = []
        for book in bestsellers:
            bestseller_list.append(f"🏆 {book.title} by {book.author} - ${book.price} ({book.quantity} in stock)")
        return "\n".join(bestseller_list)

class BookStoreAgentManager:
    """Modern book store system using Semantic Kernel 1.37.0 agent framework"""
    
    def __init__(self):
        # Shared kernel instance for optimal resource usage
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_bookstore_chat",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
        
        # Initialize shared store state
        self.store_state = StoreState()
        self._initialize_sample_data()
        
        # Initialize store operations plugin and add to kernel
        self.store_plugin = StoreOperationsPlugin(self.store_state)
        self.kernel.add_plugin(self.store_plugin, "StoreOperations")
        
        # Initialize specialized bookstore agents with modern framework
        self.agents = {
            "inventory": ChatCompletionAgent(
                kernel=self.kernel,
                name="Inventory_Manager",
                description="Specialist in book inventory management and stock control",
                instructions="""You are an inventory manager for a modern bookstore. Use available store data and inventory functions to manage stock.

                Available Functions:
                - get_inventory_summary: Get current inventory status
                - get_low_stock_books: Identify books needing restocking
                - get_bestsellers_list: See current popular books

                Always provide:
                - Current inventory assessment with data
                - Low stock alerts with specific titles
                - Restocking recommendations
                - Inventory optimization suggestions

                Use the store analytics for data-driven decisions and be proactive about inventory management."""
            ),
            "sales": ChatCompletionAgent(
                kernel=self.kernel,
                name="Sales_Manager", 
                description="Specialist in sales strategies and customer relationship management",
                instructions="""You are a sales manager for a bookstore. Analyze sales performance and customer data to drive revenue.

                Available Functions:
                - get_inventory_summary: Access current store metrics
                - get_vip_customers_list: See important customers
                - get_bestsellers_list: Identify popular books

                Always provide:
                - Sales performance analysis with metrics
                - Customer segmentation insights
                - Revenue optimization strategies
                - VIP customer engagement ideas

                Focus on data-driven sales strategies and customer satisfaction."""
            ),
            "recommendations": ChatCompletionAgent(
                kernel=self.kernel,
                name="Recommendation_Engine",
                description="Specialist in personalized book recommendations and customer matching",
                instructions="""You are a book recommendation expert. Use customer preferences and inventory data to suggest perfect matches.

                Available Functions:
                - get_inventory_summary: See available books
                - get_bestsellers_list: See popular choices
                - get_vip_customers_list: Understand customer preferences

                Always provide:
                - Personalized book recommendations based on preferences
                - Multiple options with reasoning
                - Cross-selling and up-selling suggestions
                - Genre exploration opportunities

                Be creative, personalized, and focus on customer reading enjoyment."""
            ),
            "coordinator": ChatCompletionAgent(
                kernel=self.kernel,
                name="Store_Coordinator",
                description="Intelligent coordinator for bookstore operations and agent collaboration",
                instructions="""You are the central coordinator for the bookstore multi-agent system. Route requests and ensure collaboration.

                Available Agents:
                - inventory: Stock management, restocking, inventory optimization
                - sales: Revenue growth, customer relationships, sales strategies  
                - recommendations: Book suggestions, customer matching, reading plans

                Always:
                1. Analyze the request and determine which specialist(s) should handle it
                2. Provide brief reasoning for your routing decision
                3. Suggest any inter-agent collaboration needed

                Respond in this format:
                Primary Agent: [inventory/sales/recommendations]
                Supporting Agents: [comma-separated list or none]
                Reasoning: [brief explanation of routing decision]"""
            )
        }
        
        self.runtime = InProcessRuntime()
        self.chat_history = ChatHistory()

    def _initialize_sample_data(self):
        """Initialize the store with sample data using kernel functions"""
        # Sample books
        sample_books = [
            Book(book_id="B001", title="The Great Gatsby", author="F. Scott Fitzgerald", 
                 genre="Fiction", price=12.99, quantity=15, is_bestseller=True),
            Book(book_id="B002", title="To Kill a Mockingbird", author="Harper Lee", 
                 genre="Fiction", price=14.99, quantity=8, is_bestseller=True),
            Book(book_id="B003", title="1984", author="George Orwell", 
                 genre="Fiction", price=10.99, quantity=12),
            Book(book_id="B004", title="The Lean Startup", author="Eric Ries", 
                 genre="Business", price=16.99, quantity=5),
            Book(book_id="B005", title="Sapiens", author="Yuval Noah Harari", 
                 genre="Non-Fiction", price=18.99, quantity=3),
            Book(book_id="B006", title="The Hobbit", author="J.R.R. Tolkien",
                 genre="Fantasy", price=13.99, quantity=0),  # Out of stock
        ]
        
        for book in sample_books:
            self.store_state.add_book(book)
        
        # Sample customers
        sample_customers = [
            Customer(customer_id="C001", name="Alice Johnson", email="alice@email.com", 
                    favorite_genres=["Fiction", "Mystery"], total_spent=245.50),
            Customer(customer_id="C002", name="Bob Smith", email="bob@email.com", 
                    favorite_genres=["Business", "Non-Fiction"], total_spent=650.00),
            Customer(customer_id="C003", name="Carol Davis", email="carol@email.com", 
                    favorite_genres=["Fiction", "Science"], total_spent=89.99),
            Customer(customer_id="C004", name="David Wilson", email="david@email.com",
                    favorite_genres=["Fantasy", "Fiction"], total_spent=1200.00),  # VIP
        ]
        
        for customer in sample_customers:
            self.store_state.add_customer(customer)

    async def coordinate_request(self, request: str) -> Dict:
        """Intelligent coordination of bookstore requests"""
        print(f"📨 Store Request: {request}")
        print("🔄 Analyzing and coordinating with specialists...")
        
        # Get coordination decision
        coordination_prompt = f"""
        STORE REQUEST: {request}
        
        Please coordinate this request among our specialized agents.
        """
        
        coordination_response = await self.agents["coordinator"].get_response(coordination_prompt)
        coordination_decision = self._parse_coordination_decision(str(coordination_response.content))
        
        print(f"✅ Coordination Decision:")
        print(f"   Primary Agent: {coordination_decision['primary_agent']}")
        print(f"   Supporting Agents: {coordination_decision['supporting_agents']}")
        print(f"   Reasoning: {coordination_decision['reasoning']}")
        
        return coordination_decision

    def _parse_coordination_decision(self, coordination_text: str) -> Dict:
        """Parse the coordination decision from AI response"""
        lines = [line.strip() for line in coordination_text.strip().split('\n') if line.strip()]
        
        decision = {
            "primary_agent": "inventory",
            "supporting_agents": [],
            "reasoning": "Default coordination",
            "raw_response": coordination_text
        }
        
        for line in lines:
            lower_line = line.lower()
            if lower_line.startswith('primary agent:'):
                agent = line.split(':', 1)[1].strip()
                if agent in self.agents:
                    decision["primary_agent"] = agent
            elif lower_line.startswith('supporting agents:'):
                agents_text = line.split(':', 1)[1].strip()
                if agents_text.lower() != 'none':
                    decision["supporting_agents"] = [agent.strip() for agent in agents_text.split(',')]
            elif lower_line.startswith('reasoning:'):
                decision["reasoning"] = line.split(':', 1)[1].strip()
        
        return decision

    async def process_with_agent(self, request: str, agent_name: str, context: Dict = None) -> str:
        """Process request with specified agent using modern Semantic Kernel"""
        print(f"🔧 Engaging {agent_name} specialist...")
        
        # Build enhanced context with store analytics
        store_context = self.store_state.get_store_analytics()
        
        # Add coordination context if available
        coordination_context = ""
        if context:
            coordination_context = f"\n\nCOORDINATION CONTEXT: {context.get('reasoning', 'General request')}"
        
        enhanced_request = f"""
        STORE REQUEST: {request}
        
        CURRENT STORE STATUS:
        {store_context}
        {coordination_context}
        
        Please provide your expert analysis and recommendations.
        """
        
        try:
            agent_response = await self.agents[agent_name].get_response(enhanced_request)
            return self._format_agent_response(agent_name, str(agent_response.content))
            
        except Exception as e:
            return f"❌ Error in {agent_name} processing: {str(e)}"

    def _format_agent_response(self, agent_name: str, content: str) -> str:
        """Format agent response with appropriate branding"""
        icons = {
            "inventory": "📚",
            "sales": "💰", 
            "recommendations": "🎯"
        }
        
        titles = {
            "inventory": "Inventory Management Analysis",
            "sales": "Sales Strategy Recommendations", 
            "recommendations": "Personalized Book Recommendations"
        }
        
        icon = icons.get(agent_name, "🏪")
        title = titles.get(agent_name, "Store Analysis")
        
        return f"{icon} **{title}**\n\n{content}"

    async def handle_store_request(self, request: str) -> Dict:
        """Complete processing of a store request with modern agent framework"""
        # Add to chat history for context
        self.chat_history.add_user_message(request)
        
        # Step 1: Coordinate the request
        coordination_decision = await self.coordinate_request(request)
        
        # Step 2: Process with primary agent
        primary_agent = coordination_decision["primary_agent"]
        if primary_agent in self.agents:
            specialist_response = await self.process_with_agent(
                request, 
                primary_agent,
                coordination_decision
            )
            
            # Add assistant response to history
            self.chat_history.add_assistant_message(specialist_response)
            
            return {
                "coordination_decision": coordination_decision,
                "specialist_response": specialist_response,
                "agent_name": primary_agent.replace('_', ' ').title(),
                "store_analytics": self.store_state.get_store_analytics(),
                "chat_history": len(self.chat_history.messages)
            }
        else:
            error_response = "❌ No suitable agent available for this request."
            self.chat_history.add_assistant_message(error_response)
            
            return {
                "coordination_decision": coordination_decision,
                "specialist_response": error_response,
                "agent_name": "Coordination System",
                "store_analytics": self.store_state.get_store_analytics(),
                "chat_history": len(self.chat_history.messages)
            }

    def display_result(self, result: Dict):
        """Display the processing result with modern formatting"""
        print(f"\n🎯 STORE REQUEST PROCESSING COMPLETE")
        print(f"Handled by: {result['agent_name']}")
        print(f"Supporting: {', '.join(result['coordination_decision']['supporting_agents']) or 'None'}")
        print(f"Session: {result.get('chat_history', 0)} messages")
        print("\n" + "=" * 70)
        print(f"{result['specialist_response']}")
        print("=" * 70)

    async def simulate_business_operation(self):
        """Simulate a business operation to demonstrate state changes"""
        print("\n🔄 SIMULATING BUSINESS OPERATION...")
        
        # Simulate a book sale
        if self.store_state.books and self.store_state.customers:
            customer = list(self.store_state.customers.values())[0]
            available_books = [book for book in self.store_state.books.values() if book.check_availability()]
            
            if available_books:
                book = available_books[0]
                
                # Create and process order
                order_id = f"ORD{len(self.store_state.orders) + 1:03d}"
                
                # Use store state methods for operations
                self.store_state.add_order(Order(
                    order_id=order_id,
                    customer_id=customer.customer_id,
                    book_ids=[book.book_id],
                    total_amount=book.price,
                    order_date=datetime.now()
                ))
                
                self.store_state.remove_book(book.book_id, 1)
                self.store_state.record_sale(book.price)
                
                # Update customer spending
                customer.total_spent += book.price
                
                print(f"✅ BUSINESS OPERATION: {customer.name} purchased '{book.title}' for ${book.price:.2f}")
                print(f"📦 Order {order_id} processed successfully")

async def main():
    """Modern bookstore multi-agent system demo"""
    print("🏪 MODERN BOOKSTORE MULTI-AGENT SYSTEM")
    print("State Management & Agent Collaboration Demo")
    print("Semantic Kernel 1.37.0 with Advanced Agent Framework")
    print("=" * 70)
    
    # Validate environment setup
    required_vars = [
        "AZURE_TEXTGENERATOR_DEPLOYMENT_NAME",
        "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", 
        "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return
    
    # Initialize modern bookstore system
    bookstore_system = BookStoreAgentManager()
    
    # Display initial state
    print("\n📊 INITIAL STORE STATE:")
    print(bookstore_system.store_state.get_store_analytics())
    
    # Enhanced demo scenarios
    store_scenarios = [
        "We're running low on Fiction books, what should we restock?",
        "Our sales have been slow this week, suggest some strategies to boost revenue",
        "A customer loves Business and Non-Fiction books, what would you recommend?",
        "Which books should we promote as bestsellers and do we have enough stock?",
        "How can we better engage our VIP customers and increase their spending?",
        "Analyze our current inventory and suggest optimization strategies",
    ]
    
    print("🚀 Starting multi-agent bookstore demonstrations...")
    print("Available Agents: Inventory Manager, Sales Manager, Recommendation Engine, Store Coordinator")
    print()
    
    # Process enhanced scenarios
    for i, scenario in enumerate(store_scenarios, 1):
        print(f"\n{'#' * 70}")
        print(f"STORE SCENARIO #{i}")
        print(f"{'#' * 70}")
        
        try:
            result = await bookstore_system.handle_store_request(scenario)
            bookstore_system.display_result(result)
            
            # Simulate business operation between scenarios
            if i < len(store_scenarios):
                await bookstore_system.simulate_business_operation()
            
            await asyncio.sleep(1)  # Brief pause for demo flow
            
        except Exception as e:
            print(f"❌ System error: {e}")
            continue
    
    # Display final state
    print(f"\n📈 FINAL STORE STATE:")
    print(bookstore_system.store_state.get_store_analytics())
    
    print(f"\n✅ Modern Bookstore AI System Demo Completed!")
    print(f"📊 Session Summary: {len(bookstore_system.chat_history.messages)} store interactions processed")
    print(f"🛠️  Features Used: Multi-Agent Coordination, State Management, Kernel Functions, Real-time Analytics")

if __name__ == "__main__":
    asyncio.run(main())