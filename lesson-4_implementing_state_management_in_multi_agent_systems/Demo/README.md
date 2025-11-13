# 📘 Book Store Multi-Agent System - State Management Demo

## 🎯 Learning Objectives

This demo teaches you how to:

* Implement shared state management in multi-agent systems
* Use **Pydantic** models for data validation and state representation
* Coordinate multiple specialized agents with a common state
* Handle state updates and maintain consistency across agents
* Build context-aware AI systems

---


## 🏗️ System Architecture

![Architecture Diagram](architecture.png)

Book store system with three agents (Inventory, Sales, Recommendation) sharing state through Pydantic models for coordinated inventory and customer management.

---

## 🏗️ System Architecture

### 🧩 Shared State Management

The system uses a central `StoreState` class that manages:

* **Book Inventory** – Available books with quantities and prices
* **Customer Database** – Customer information and preferences
* **Order History** – All customer orders and their statuses
* **Financial Data** – Store balance and daily revenue

---

### 🤖 Three Specialist Agents

1. **📚 Inventory Agent** – Manages book stock and inventory levels
2. **💰 Sales Agent** – Handles sales strategies and customer relationships
3. **🎯 Recommendation Agent** – Provides personalized book suggestions

---

### 🧱 Pydantic Models for Data Integrity

```python
class Book(BaseModel):
    book_id: str
    title: str
    author: str
    genre: str
    price: float
    quantity: int
    is_bestseller: bool
```

---

## 🚀 Running the Demo

### 1️⃣ Prerequisites

```bash
pip install semantic-kernel==1.36.2 python-dotenv pydantic
```

### 2️⃣ Environment Setup

Create a `.env` file:

```env
AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=your-deployment-name
AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your-api-key
```

### 3️⃣ Run the Demo

```bash
python book_store_demo.py
```

---

## 📊 Demo Workflow

### Step 1: System Initialization

* Creates shared store state with sample data
* Initializes three specialized agents
* Sets up inventory, customers, and financial data

### Step 2: State Display

Shows initial store state:

```
📊 CURRENT STORE STATE:
💰 Store Balance: $0.00
📈 Today's Revenue: $0.00
📚 Books in Inventory: 5 types
👥 Registered Customers: 3
📦 Total Orders: 0
⭐ VIP Customers: 1
```

### Step 3: Scenario Processing

The system processes multiple scenarios:

* **Inventory Management:** “Check current inventory status”
* **Sales Analysis:** “Analyze sales performance”
* **Customer Recommendations:** “Recommend books for Fiction lovers”
* **Business Strategy:** “How to serve VIP customers better”

### Step 4: State Updates

Between scenarios, the system simulates purchases to demonstrate:

* Order creation and tracking
* Inventory updates
* Customer spending updates
* Revenue calculations

### Step 5: Final State Display

Shows how the state evolved during the demo.

---

## 🔧 Key Features

### 🧠 Shared State Management

* All agents access the same `StoreState` instance
* State updates are immediately visible to all agents
* Consistent data across the entire system

### ✅ Pydantic Data Validation

* Automatic data type validation
* Custom validators for business rules
* Property methods for computed fields

### 👥 Agent Specialization

* Each agent has a specific domain expertise
* Agents provide context-aware responses
* Enables collaborative problem-solving

---

## 🎪 Sample Output

```
🎯 SCENARIO 1: Check current inventory status and suggest restocking

🤖 Consulting all specialists...

INVENTORY AGENT:
Analysis: Current inventory has 5 book types with 43 total copies...
📉 Low Stock Books: [{'title': 'Sapiens', 'current_stock': 3, 'status': 'LOW'}]

SALES AGENT:
Analysis: Store has good inventory diversity with 3 bestsellers...
⭐ VIP Customers: ['Bob Smith']

RECOMMENDATION AGENT:
Analysis: Based on current inventory, I recommend focusing on Fiction...
🏆 Bestsellers: ['The Great Gatsby', 'To Kill a Mockingbird']
```

---

## 💡 Learning Points

### 🧩 State Management Patterns

* **Centralized State:** Single source of truth for all agents
* **Immutable Updates:** Pydantic ensures data consistency
* **Observable Changes:** Agents instantly see state updates

### ⚙️ Multi-Agent Coordination

* **Parallel Processing:** Agents can work simultaneously
* **Shared Context:** Common state enables collaboration
* **Specialized Expertise:** Each agent focuses on its domain

### 🌍 Real-World Applications

* E-commerce systems
* Inventory management
* Customer relationship management
* Business intelligence systems

---

## 🔄 Extension Ideas

* **Add Persistence:** Save state to a database between sessions
* **Real-time Updates:** Web interface showing live state changes
* **More Agents:** Add shipping, marketing, or finance agents
* **Advanced Analytics:** Machine learning for predictions
* **API Integration:** Connect to real book databases

---

## 🛠️ Technical Stack

* **Python 3.8+** – Core programming language
* **Semantic Kernel** – AI orchestration framework
* **Azure OpenAI** – LLM integration for intelligent agents
* **Pydantic** – Data validation and settings management
* **Asyncio** – Concurrent agent processing

