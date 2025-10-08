# Smart City Monitoring System - Exercise Starter

## 🎯 Learning Objectives

This exercise will help you practice:

* Extending multi-agent AI systems
* Creating structured prompts for LLMs
* Implementing new specialized workers
* Adding intelligent coordination logic
* Working with **Semantic Kernel 1.36.2**

---

## 📋 Exercise Tasks

Complete the following **TODOs** in the starter code:

### 1. Enhanced Prompt Engineering

**File: `smart_city_starter.py`**

Improve the prompts for existing workers to provide more structured and comprehensive analysis:

* **TrafficWorker**: Current conditions, root cause analysis, immediate actions, long-term solutions, impact assessment
* **EnergyWorker**: Current patterns, efficiency opportunities, cost-saving measures, sustainability improvements, implementation timeline
* **SafetyWorker**: Risk assessment, immediate concerns, preventive measures, emergency response, community recommendations

---

### 2. Implement Environment Worker

**File: `smart_city_starter.py`**

Create a new `EnvironmentWorker` class that handles:

* Environmental impact assessment
* Sustainability recommendations
* Pollution control measures
* Green infrastructure suggestions
* Regulatory compliance

---

### 3. Add Environment Worker to Coordinator

**File: `smart_city_starter.py`**

Register the new `EnvironmentWorker` in the `CityCoordinator`'s workers dictionary.

---

### 4. Implement Smart Coordination

**File: `smart_city_starter.py`**

Add two new methods to `CityCoordinator`:

* `analyze_relevance()`: Use LLM to determine which workers are relevant for a given request
* `coordinate_smart_monitoring()`: Invoke only the relevant workers based on the analysis

---

### 5. Add Environmental Scenario

**File: `smart_city_starter.py`**

Add an environmental scenario to the demo scenarios list.

---

## 🛠️ Setup Instructions

1. **Environment Setup**

   ```bash
   pip install semantic-kernel==1.36.2 python-dotenv
   ```

2. **Azure OpenAI Configuration**
   Create a `.env` file with your credentials:

   ```bash
   AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=your-deployment-name
   AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your-api-key
   ```

3. **Run the Starter Code**

   ```bash
   python smart_city_starter.py
   ```

---

## 💡 Implementation Hints

**For Enhanced Prompts**

* Use clear section headers (e.g., 🚦, 🔍, 🚨)
* Ask for specific types of information in each section
* Include practical, actionable recommendations
* Consider both short-term and long-term solutions

**For Environment Worker**

* Model it after the existing workers
* Focus on environmental sustainability metrics
* Include both monitoring and improvement recommendations

**For Smart Coordination**

* Create a prompt that analyzes request content
* Define clear criteria for relevance scoring
* Consider threshold-based worker selection

---

## 🧪 Testing Your Solution

After completing all tasks, your enhanced system should:

* Provide more detailed, structured analysis from each worker
* Include environmental analysis for relevant scenarios
* Show relevance analysis before processing requests
* Handle all demo scenarios without errors

---

## 📚 Learning Resources

* [Semantic Kernel Documentation](https://learn.microsoft.com/semantic-kernel)
* [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
* [Prompt Engineering Guide](https://learn.microsoft.com/azure/ai-services/openai/concepts/prompt-engineering)

---

## 🆘 Need Help?

If you get stuck:

* Check the solution code for reference
* Review the **Semantic Kernel 1.36.2 API** documentation
* Look at the existing worker implementations as examples
* Test your prompts directly in **Azure OpenAI Studio** first

---

✨ Good luck! 🚀
