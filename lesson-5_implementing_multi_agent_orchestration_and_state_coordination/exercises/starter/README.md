# ☕ Modern Coffee Shop Multi-Agent System - Exercise

## 🎯 Exercise Objective
Implement a modern multi-agent coffee shop system using **Semantic Kernel 1.37.0** that coordinates order processing, resource management, and inventory tracking through **intelligent agent orchestration** and **shared state management**.

---

## 🏗️ Modern System Architecture

![Architecture Diagram](architecture.png)

Target architecture for the Coffee Shop system you'll build featuring:
- **ModernCoffeeShopSystem** with shared kernel and CoffeeShopPlugin
- **Shop Coordinator** for intelligent request routing and agent collaboration
- **Three Specialist Agents**: Order Manager, Barista Manager, and Inventory Manager
- **CoffeeShopState (KernelBaseModel)** managing Orders, Resources, and Inventory
- Coordinator-based routing with bidirectional state access for real-time shop analytics

---

## 📋 Modern Requirements

### 1. Data Models (KernelBaseModel)
Complete the following models in `coffee_shop_starter.py` using **modern KernelBaseModel**:

**CoffeeOrder** (KernelBaseModel)
- `order_id`: string (unique identifier)
- `customer_name`: string
- `coffee_type`: string (espresso, latte, cappuccino, americano, flat_white)
- `size`: string (small, medium, large)
- `status`: string (received, preparing, brewing, ready, served)
- `order_date`: datetime
- **Kernel Functions**: `is_ready()`, `get_order_details()`

**CoffeeResource** (KernelBaseModel)
- `resource_id`: string
- `name`: string (espresso_machine, milk_steamer, grinder, brew_station)
- `capacity`: integer
- `current_usage`: integer
- **Kernel Functions**: `is_available()`, `get_resource_status()`

**CoffeeShopState** (KernelBaseModel)
- `orders`: Dict of CoffeeOrder
- `resources`: Dict of CoffeeResource
- `completed_orders`: integer
- `inventory`: Dict of supplies (coffee_beans, milk, sugar, cups, syrups)
- **Kernel Functions**: `add_order()`, `update_order_status()`, `allocate_resource()`, `release_resource()`, `get_shop_status()`, `get_order_metrics()`, `get_resource_capacity()`

### 2. Plugin Implementation
Complete the **CoffeeShopPlugin** with kernel functions:

**Required Kernel Functions:**
- `get_comprehensive_shop_status()`: Complete shop overview with metrics
- `get_inventory_status()`: Inventory analysis with alerts
- `process_coffee_order()`: Order processing workflow

### 3. Modern Agent Implementation
Complete four specialized agents using **ChatCompletionAgent** framework:

**Order Manager** (ChatCompletionAgent)
- Manages customer orders and workflow coordination
- Uses kernel functions for order analysis
- Provides order prioritization and customer service

**Barista Manager** (ChatCompletionAgent)
- Handles coffee preparation and equipment optimization
- Manages resource allocation and quality control
- Provides brewing techniques and efficiency improvements

**Inventory Manager** (ChatCompletionAgent)
- Tracks supplies and restocking strategies
- Uses kernel functions for inventory analysis
- Provides cost optimization and stock management

**Shop Coordinator** (ChatCompletionAgent)
- **Intelligent request routing** between specialists
- Analyzes requests and determines optimal agent assignment
- Suggests inter-agent collaboration for complex scenarios

### 4. Modern System Features
- **Multi-Agent Orchestration**: Intelligent coordination between four agents
- **Kernel Function Integration**: All operations exposed through kernel functions
- **Real-time Analytics**: Comprehensive shop metrics and status tracking
- **Plugin Architecture**: Modular and extensible system design
- **State Coordination**: Consistent shared state with KernelBaseModel validation

### 5. Enhanced Demo Scenarios
Implement 5 modern scenarios that demonstrate:
- **Intelligent Routing**: AI-powered request distribution
- **Resource Optimization**: Advanced capacity planning
- **Inventory Intelligence**: Smart restocking strategies
- **Performance Analytics**: Real-time efficiency tracking
- **Multi-Agent Collaboration**: Complex scenario coordination

## 🛠️ Modern Implementation Steps

### 1. **Complete KernelBaseModel Models** (20 minutes)
- Add all required fields with proper typing
- Implement kernel functions for state operations
- Add validation logic and status tracking

### 2. **Implement CoffeeShopPlugin** (15 minutes)
- Create kernel functions for shop operations
- Implement comprehensive analytics methods
- Add order processing workflow

### 3. **Configure Modern Kernel Setup** (10 minutes)
- Set up AzureChatCompletion service with environment variables
- Initialize shared kernel instance
- Register plugin with proper naming

### 4. **Build Modern ChatCompletionAgents** (25 minutes)
- Create four specialized agents with detailed instructions
- Configure kernel function access for each agent
- Implement coordinator agent for intelligent routing

### 5. **Implement Core System Methods** (20 minutes)
- Add order placement with kernel functions
- Implement coordination and request processing
- Create workflow simulation methods

### 6. **Complete Demo Execution** (10 minutes)
- Test all 5 enhanced scenarios
- Verify multi-agent coordination works
- Validate state consistency across all agents

## ✅ Modern Success Criteria

- All 4 agents properly respond to coordinated requests
- Kernel functions provide real-time analytics and operations
- Intelligent routing directs requests to optimal specialists
- Order processing successfully transitions through all stages
- State updates are immediately visible across all agents
- Shop coordinator provides logical routing decisions
- Comprehensive analytics show evolving shop performance

## 💡 Modern Tips

- **Start with KernelBaseModel**: Implement models before agents
- **Use Plugin Architecture**: Organize all kernel functions in CoffeeShopPlugin
- **Test Agent Isolation**: Verify each agent works independently first
- **Leverage Coordinator**: Use coordinator for complex request routing
- **Monitor State Changes**: Use comprehensive status methods for debugging
- **Follow Modern Patterns**: Reference pasta factory example for structure
- **Use Meaningful Naming**: Clear resource and agent names help debugging

## 🚀 Modern Getting Started

### 1. **Environment Setup**
```bash
# Install modern Semantic Kernel packages
pip install semantic-kernel==1.37.0 python-dotenv

# Ensure Azure OpenAI credentials in .env file
AZURE_DEPLOYMENT_NAME=your-deployment-name
AZURE_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT_KEY=your-api-key
```

### 2. **Implementation Order**
1. Complete KernelBaseModel classes with kernel functions
2. Implement CoffeeShopPlugin with kernel functions
3. Configure kernel and register plugin
4. Build ChatCompletionAgent instances
5. Implement coordination and workflow methods
6. Test with demo scenarios

### 3. **Run Your Implementation**
```bash
python coffee_shop_starter.py
```

---

## 🔧 Modern Technical Stack

- **Python 3.8+** with async/await support
- **Semantic Kernel 1.37.0** with modern agent framework
- **KernelBaseModel** for state management and validation
- **ChatCompletionAgent** for specialized AI agents
- **Plugin Architecture** for modular kernel functions
- **Azure OpenAI** for advanced LLM integration

---

## 🎯 Learning Outcomes

After completing this exercise, you'll understand:

- **Modern State Management**: KernelBaseModel with kernel function integration
- **Multi-Agent Orchestration**: Intelligent coordination between specialized agents
- **Plugin Architecture**: Organizing kernel functions for reusability
- **Real-time Analytics**: Comprehensive metrics and status tracking
- **AI-Powered Routing**: Intelligent request distribution using coordinator agent
- **Production Workflows**: Sequential order processing through multiple agents

**Good luck building your modern coffee shop! ☕**
