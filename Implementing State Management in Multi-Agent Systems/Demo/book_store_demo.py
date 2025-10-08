import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
load_dotenv("../../.env")

# Pydantic Models for State Management
class Book(BaseModel):
    """Model representing a book in the store"""
    book_id: str = Field(..., description="Unique book identifier")
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    genre: str = Field(..., description="Book genre")
    price: float = Field(..., gt=0, description="Book price in USD")
    quantity: int = Field(..., ge=0, description="Available quantity")
    is_bestseller: bool = Field(default=False, description="Is this a bestseller?")
    
    @field_validator('genre')
    def validate_genre(cls, v):
        common_genres = ['Fiction', 'Non-Fiction', 'Science', 'Technology', 'Business', 'Biography']
        if v not in common_genres:
            print(f"⚠️  Warning: '{v}' is not a common genre")
        return v

class Customer(BaseModel):
    """Model representing a customer"""
    customer_id: str = Field(..., description="Unique customer identifier")
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email")
    favorite_genres: List[str] = Field(default_factory=list, description="Customer's favorite genres")
    total_spent: float = Field(default=0.0, ge=0, description="Total amount spent")
    
    @property
    def is_vip(self) -> bool:
        """Check if customer is VIP based on spending"""
        return self.total_spent > 500

class Order(BaseModel):
    """Model representing a customer order"""
    order_id: str = Field(..., description="Unique order identifier")
    customer_id: str = Field(..., description="Customer who placed the order")
    book_ids: List[str] = Field(..., description="Books in the order")
    total_amount: float = Field(..., ge=0, description="Order total amount")
    order_date: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="pending", description="Order status")
    
    @field_validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of {allowed_statuses}')
        return v

class StoreState(BaseModel):
    """Central state management for the book store"""
    books: Dict[str, Book] = Field(default_factory=dict, description="Book inventory")
    customers: Dict[str, Customer] = Field(default_factory=dict, description="Customer database")
    orders: Dict[str, Order] = Field(default_factory=dict, description="All orders")
    store_balance: float = Field(default=0.0, description="Store's total balance")
    daily_revenue: float = Field(default=0.0, description="Today's revenue")
    
    def add_book(self, book: Book) -> None:
        """Add or update book in inventory"""
        self.books[book.book_id] = book
    
    def remove_book(self, book_id: str, quantity: int = 1) -> bool:
        """Remove quantity from book inventory"""
        if book_id not in self.books:
            return False
        
        book = self.books[book_id]
        if book.quantity < quantity:
            return False
        
        book.quantity -= quantity
        return True
    
    def add_customer(self, customer: Customer) -> None:
        """Add or update customer"""
        self.customers[customer.customer_id] = customer
    
    def add_order(self, order: Order) -> None:
        """Add a new order"""
        self.orders[order.order_id] = order
    
    def record_sale(self, amount: float) -> None:
        """Record a sale and update store balance"""
        self.store_balance += amount
        self.daily_revenue += amount

class StoreAgent:
    """Base class for all store agents with shared state access"""
    
    def __init__(self, name: str, role: str, store_state: StoreState):
        self.name = name
        self.role = role
        self.store_state = store_state
        self.kernel = Kernel()
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
    
    async def process_request(self, request: str) -> Dict:
        """Process store request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

class InventoryAgent(StoreAgent):
    """Agent specializing in book inventory management"""
    
    def __init__(self, store_state: StoreState):
        super().__init__("Inventory Manager", "Manage book inventory and stock", store_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle inventory-related requests"""
        
        prompt = """
        You are an inventory manager for a book store. Analyze the current inventory situation.

        REQUEST: {{$request}}

        CURRENT INVENTORY:
        {{$inventory_summary}}

        Please provide:
        1. Current inventory status
        2. Books that need restocking
        3. Recommendations for inventory management

        Keep it simple and practical.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="inventory_analysis",
            plugin_name="inventory",
            prompt=prompt
        )
        
        inventory_summary = self._get_inventory_summary()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            inventory_summary=inventory_summary
        )
        
        return {
            "agent": self.name,
            "analysis": str(result),
            "low_stock_books": self._get_low_stock_books(),
            "total_books": len(self.store_state.books)
        }
    
    def _get_inventory_summary(self) -> str:
        """Generate inventory summary"""
        total_books = sum(book.quantity for book in self.store_state.books.values())
        total_value = sum(book.price * book.quantity for book in self.store_state.books.values())
        
        summary = f"""
        Total Books: {total_books}
        Total Value: ${total_value:.2f}
        Book Types: {len(self.store_state.books)}
        Bestsellers: {sum(1 for book in self.store_state.books.values() if book.is_bestseller)}
        """
        return summary
    
    def _get_low_stock_books(self) -> List[Dict]:
        """Get books with low stock"""
        low_stock = []
        for book in self.store_state.books.values():
            if book.quantity < 5:  # Low stock threshold
                low_stock.append({
                    "title": book.title,
                    "current_stock": book.quantity,
                    "status": "CRITICAL" if book.quantity == 0 else "LOW"
                })
        return low_stock

class SalesAgent(StoreAgent):
    """Agent specializing in sales and customer service"""
    
    def __init__(self, store_state: StoreState):
        super().__init__("Sales Manager", "Handle sales and customer relationships", store_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle sales-related requests"""
        
        prompt = """
        You are a sales manager for a book store. Help with sales strategies and customer service.

        REQUEST: {{$request}}

        STORE STATUS:
        {{$store_status}}

        Please provide:
        1. Sales recommendations
        2. Customer service suggestions
        3. Ideas to increase revenue

        Focus on practical, actionable advice.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="sales_analysis",
            plugin_name="sales",
            prompt=prompt
        )
        
        store_status = self._get_store_status()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            store_status=store_status
        )
        
        return {
            "agent": self.name,
            "recommendations": str(result),
            "sales_metrics": self._get_sales_metrics(),
            "vip_customers": self._get_vip_customers()
        }
    
    def _get_store_status(self) -> str:
        """Get current store status"""
        return f"""
        Store Balance: ${self.store_state.store_balance:.2f}
        Today's Revenue: ${self.store_state.daily_revenue:.2f}
        Total Customers: {len(self.store_state.customers)}
        Total Orders: {len(self.store_state.orders)}
        """
    
    def _get_sales_metrics(self) -> Dict:
        """Calculate sales metrics"""
        total_orders = len(self.store_state.orders)
        completed_orders = len([o for o in self.store_state.orders.values() if o.status == 'delivered'])
        
        return {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "completion_rate": (completed_orders / total_orders * 100) if total_orders > 0 else 0
        }
    
    def _get_vip_customers(self) -> List[str]:
        """Get VIP customer names"""
        return [customer.name for customer in self.store_state.customers.values() if customer.is_vip]

class RecommendationAgent(StoreAgent):
    """Agent specializing in book recommendations"""
    
    def __init__(self, store_state: StoreState):
        super().__init__("Recommendation Engine", "Provide book recommendations", store_state)
    
    async def process_request(self, request: str) -> Dict:
        """Handle recommendation requests"""
        
        prompt = """
        You are a book recommendation expert. Suggest books based on customer preferences.

        REQUEST: {{$request}}

        AVAILABLE BOOKS:
        {{$available_books}}

        Please provide:
        1. Personalized book recommendations
        2. Reasons for each recommendation
        3. Alternative suggestions

        Be helpful and specific.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="book_recommendations",
            plugin_name="recommendations",
            prompt=prompt
        )
        
        available_books = self._get_available_books()
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            available_books=available_books
        )
        
        return {
            "agent": self.name,
            "recommendations": str(result),
            "bestsellers": self._get_bestsellers(),
            "popular_genres": self._get_popular_genres()
        }
    
    def _get_available_books(self) -> str:
        """Get list of available books"""
        books_list = []
        for book in self.store_state.books.values():
            if book.quantity > 0:
                books_list.append(f"- {book.title} by {book.author} (${book.price}) - {book.genre}")
        
        return "\n".join(books_list) if books_list else "No books currently available"
    
    def _get_bestsellers(self) -> List[str]:
        """Get current bestsellers"""
        return [book.title for book in self.store_state.books.values() if book.is_bestseller and book.quantity > 0]
    
    def _get_popular_genres(self) -> List[str]:
        """Get popular genres from inventory"""
        from collections import Counter
        genres = [book.genre for book in self.store_state.books.values()]
        return [genre for genre, count in Counter(genres).most_common(3)]

class BookStoreSystem:
    """Main book store system coordinating all agents"""
    
    def __init__(self):
        # Initialize shared store state
        self.store_state = StoreState()
        self._initialize_sample_data()
        
        # Initialize specialized agents
        self.agents = {
            "inventory": InventoryAgent(self.store_state),
            "sales": SalesAgent(self.store_state),
            "recommendations": RecommendationAgent(self.store_state)
        }
    
    def _initialize_sample_data(self):
        """Initialize the store with sample data"""
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
        ]
        
        for customer in sample_customers:
            self.store_state.add_customer(customer)
    
    async def run_demo(self):
        """Run the complete book store demo"""
        print("📚 BOOK STORE MULTI-AGENT SYSTEM")
        print("State Management Demo")
        print("=" * 50)
        
        # Display initial state
        self.display_store_state()
        
        # Demo scenarios
        scenarios = [
            "Check current inventory status and suggest restocking",
            "Analyze sales performance and suggest improvements", 
            "Recommend books for a customer who likes Fiction",
            "What are our current bestsellers and should we order more?",
            "How can we better serve our VIP customers?"
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎯 SCENARIO {i}: {scenario}")
            print("-" * 50)
            
            await self.process_scenario(scenario)
            
            # Simulate a purchase between scenarios to show state changes
            if i < len(scenarios):
                self.simulate_purchase()
        
        print("\n🎉 DEMO COMPLETED!")
        self.display_final_state()
    
    async def process_scenario(self, scenario: str):
        """Process a scenario with all agents"""
        print("🤖 Consulting all specialists...")
        
        # Process with all agents in parallel
        tasks = []
        for agent_name, agent in self.agents.items():
            tasks.append(agent.process_request(scenario))
        
        results = await asyncio.gather(*tasks)
        
        # Display results
        for (agent_name, _), result in zip(self.agents.items(), results):
            print(f"\n{agent_name.upper()} AGENT:")
            print(f"Analysis: {result.get('analysis', result.get('recommendations', 'No response'))}")
            
            # Show additional data if available
            if 'low_stock_books' in result and result['low_stock_books']:
                print("📉 Low Stock Books:", result['low_stock_books'])
            if 'vip_customers' in result and result['vip_customers']:
                print("⭐ VIP Customers:", result['vip_customers'])
            if 'bestsellers' in result and result['bestsellers']:
                print("🏆 Bestsellers:", result['bestsellers'])
    
    def display_store_state(self):
        """Display current store state"""
        print("\n📊 CURRENT STORE STATE:")
        print(f"💰 Store Balance: ${self.store_state.store_balance:.2f}")
        print(f"📈 Today's Revenue: ${self.store_state.daily_revenue:.2f}")
        print(f"📚 Books in Inventory: {len(self.store_state.books)} types")
        print(f"👥 Registered Customers: {len(self.store_state.customers)}")
        print(f"📦 Total Orders: {len(self.store_state.orders)}")
        
        # VIP customers
        vip_count = sum(1 for customer in self.store_state.customers.values() if customer.is_vip)
        print(f"⭐ VIP Customers: {vip_count}")
    
    def simulate_purchase(self):
        """Simulate a book purchase to demonstrate state updates"""
        print("\n🛒 SIMULATING A BOOK PURCHASE...")
        
        # Find a customer and available book
        if not self.store_state.customers or not self.store_state.books:
            print("❌ No customers or books available for purchase simulation")
            return
        
        customer = list(self.store_state.customers.values())[0]
        available_books = [book for book in self.store_state.books.values() if book.quantity > 0]
        
        if not available_books:
            print("❌ No books available for purchase")
            return
        
        book = available_books[0]
        
        # Create order
        order_id = f"ORD{len(self.store_state.orders) + 1:03d}"
        order = Order(
            order_id=order_id,
            customer_id=customer.customer_id,
            book_ids=[book.book_id],
            total_amount=book.price,
            status="delivered"
        )
        
        # Update state
        self.store_state.add_order(order)
        self.store_state.remove_book(book.book_id, 1)
        self.store_state.record_sale(book.price)
        
        # Update customer spending
        customer.total_spent += book.price
        
        print(f"✅ {customer.name} purchased '{book.title}' for ${book.price:.2f}")
        print(f"📦 Order {order_id} completed successfully")
    
    def display_final_state(self):
        """Display final state after demo"""
        print("\n📈 FINAL STORE STATE:")
        print(f"💰 Store Balance: ${self.store_state.store_balance:.2f}")
        print(f"📈 Today's Revenue: ${self.store_state.daily_revenue:.2f}")
        print(f"📚 Books in Inventory: {len(self.store_state.books)} types")
        print(f"👥 Registered Customers: {len(self.store_state.customers)}")
        print(f"📦 Total Orders: {len(self.store_state.orders)}")
        
        # Show some statistics
        total_books = sum(book.quantity for book in self.store_state.books.values())
        print(f"📖 Total Book Copies: {total_books}")
        
        vip_customers = [c for c in self.store_state.customers.values() if c.is_vip]
        print(f"⭐ VIP Customers: {len(vip_customers)}")

async def main():
    # Check environment variables
    required_vars = ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing environment variables. Please check your .env file.")
        print(f"Missing: {missing_vars}")
        return
    
    # Create and run the book store system
    book_store = BookStoreSystem()
    await book_store.run_demo()

if __name__ == "__main__":
    asyncio.run(main())