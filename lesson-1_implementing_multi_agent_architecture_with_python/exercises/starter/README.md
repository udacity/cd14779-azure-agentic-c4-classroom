# Smart City Multi-Agent System - Starter Code

## 🎯 Learning Exercise Overview

This starter code provides the foundation for building an advanced multi-agent smart city management system using **Semantic Kernel 1.37.0**. Your task is to complete the implementation by:

* **Creating Specialized Agents**: Implement all required AI agents with proper configurations
* **Adding Environment Manager**: Extend the system with environmental expertise
* **Implementing Sequential Collaboration**: Build a sophisticated workflow where agents build on each other's analyses

---

## 🏗️ System Architecture Framework

### Parallel Mode - Independent Analysis
![Parallel Mode](architecture_parallel.png)

### Sequential Mode - Context-Aware Chain
![Sequential Mode](architecture_sequential.png)

The starter code provides the basic structure:
- **SmartCityAgentManager** orchestrates agent interactions
- **Placeholder Agents** ready for your implementation
- **Shared Kernel Instance** for optimized resource usage
- **Dual Processing Framework**: Parallel analysis & sequential collaboration patterns

---

## 📋 Exercise Tasks

### 1. Agent Creation & Configuration

**TODO: Implement all agents in the `__init__` method:**

```python
self.agents = {
    "traffic": None,      # Create Traffic Manager agent
    "energy": None,       # Create Energy Analyst agent  
    "safety": None,       # Create Safety Officer agent
    "environment": None,  # Create Environment Manager agent
    "coordinator": None   # Create City Coordinator agent
}
```

**Each agent should include:**
- **Name**: Follow naming conventions (e.g., "Traffic_Manager")
- **Description**: Clear domain expertise description
- **Instructions**: Detailed role-specific guidance

### 2. Environment Manager Integration

**TODO: Add Environment Manager to parallel analysis:**

```python
tasks = {
    "🚦 Traffic": ...,
    "⚡ Energy": ...,
    "🚨 Safety": ...,
    "🌳 Environment": ...  # Add this line
}
```

### 3. Sequential Collaboration Implementation

**TODO: Complete the `run_sequential_collaboration` method:**

- **Step 1**: Traffic analysis
- **Step 2**: Energy analysis (using traffic context)
- **Step 3**: Safety analysis (using traffic + energy context)  
- **Step 4**: Environmental analysis (using all previous context)
- **Step 5**: Integrated summary generation

---

## 🔧 Technical Framework

### Semantic Kernel 1.37.0 Features

* **Modern Agent Framework**: Uses `ChatCompletionAgent` class
* **Azure OpenAI Foundry**: All agents use enterprise AI services
* **InProcessRuntime**: Proper runtime management for agent execution
* **Async/Await Patterns**: Efficient concurrent processing

### Error Handling Structure

* Pre-implemented exception handling in `_get_agent_response`
* Graceful degradation when individual agents fail
* Comprehensive error reporting

### Performance Optimizations

* **Shared Kernel**: Single instance for all agents
* **Parallel Processing**: `asyncio.gather()` for concurrent analysis
* **Resource Management**: Proper runtime lifecycle

---

## 🚀 Getting Started

### 1. Environment Setup

```bash
pip install semantic-kernel==1.37.0 python-dotenv
```

### 2. Azure OpenAI Configuration

Create `.env` file:

```env
AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=your-foundry-deployment
AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your-api-key
```

### 3. Run the Starter Code

```bash
python smart_city_starter.py
```

---

## 🎯 Expected Learning Outcomes

After completing this exercise, you will understand:

* **Modern Agent Patterns**: Creating and configuring `ChatCompletionAgent` instances
* **Multi-Agent Orchestration**: Coordinating multiple specialized AI agents
* **Context-Aware Processing**: Building sequential workflows with shared context
* **Production Best Practices**: Error handling, resource management, and performance optimization
* **System Extensibility**: Adding new domain experts to existing architecture

---

## 🔍 Exercise Instructions

1. **Review the TODOs**: Each TODO comment indicates a required implementation
2. **Start with Agent Creation**: Complete the agent initialization in `__init__`
3. **Test Parallel Analysis**: Verify all agents work in parallel mode
4. **Implement Sequential Flow**: Build the step-by-step collaboration
5. **Validate with Scenarios**: Use the provided test scenarios to verify functionality

---

## 📚 Learning Progression

This exercise builds progressively:

1. **Basic Agent Setup** → Understanding Semantic Kernel agent framework
2. **System Extension** → Adding new capabilities to existing architecture  
3. **Advanced Orchestration** → Implementing complex multi-agent workflows
4. **Production Patterns** → Error handling and performance optimization

---

## 🆘 Getting Help

If you get stuck:
1. Review the Semantic Kernel 1.37.0 documentation for `ChatCompletionAgent`
2. Check the error messages carefully - they often indicate the specific issue
3. Ensure your Azure OpenAI credentials are correctly configured
4. Verify all agents have proper names, descriptions, and instructions

---

## ✅ Success Criteria

Your implementation is complete when:
- All five agents are properly configured and functional
- Environment Manager participates in parallel analysis
- Sequential collaboration works end-to-end with all agents
- No TODO comments remain in the code
- All test scenarios execute successfully
---
