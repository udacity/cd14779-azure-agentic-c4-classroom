# 🍽️ Restaurant Recommendation System - Exercise

## 🎯 Exercise Overview

Transform this starter code into a complete **multi-agent restaurant recommendation system**!
You’ll implement missing agents and orchestration patterns to create a smart dining advisor.

---

## 📋 Exercise Tasks

### Task 1: Improve Existing Agents

**File: `restaurant_starter.py`**

#### 1.1 Enhance `CuisineAgent` Prompt

Include:

* 2–3 recommended cuisine types
* Why each cuisine fits the request
* Popular dishes to try
* Dietary considerations

#### 1.2 Enhance `LocationAgent` Prompt

Include:

* Recommended neighborhoods/areas
* Atmosphere descriptions
* Transportation/parking tips
* Best times to visit

---

### Task 2: Implement `PriceRangeAgent`

**File: `restaurant_starter.py`**

Create a new class that handles:

* Price range estimates ($, $$, $$$)
* Value-for-money suggestions
* Cost-saving tips
* Typical meal prices

---

### Task 3: Complete `RestaurantOrchestrator`

**File: `restaurant_starter.py`**

#### 3.1 Add `PriceRangeAgent` to Orchestrator

Register the new agent in the `agents` dictionary.

#### 3.2 Complete Sequential Orchestration

Add `PriceRangeAgent` as **step 3** in the sequential workflow.

#### 3.3 Implement Parallel Orchestration

Run all agents simultaneously using `asyncio.gather`.

#### 3.4 Implement Conditional Orchestration

Select agents dynamically based on request content.

---

### Task 4: Test All Patterns

**File: `restaurant_starter.py`**

* Uncomment and test the **parallel** and **conditional** patterns in the main function.

---

## 🛠️ Setup Instructions

1. **Install Dependencies**

   ```bash
   pip install semantic-kernel==1.36.2 python-dotenv
   ```

2. **Configure Environment**
   Create a `.env` file with your Azure OpenAI credentials:

   ```env
   AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=your-deployment-name
   AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your-api-key
   ```

3. **Run Starter Code**

   ```bash
   python restaurant_starter.py
   ```

---

## 💡 Implementation Hints

**For Better Prompts:**

* Use clear, specific instructions
* Ask for structured information
* Include practical, actionable advice
* Consider different dining scenarios

**For `PriceRangeAgent`:**

* Model it after existing agents
* Focus on budget-friendly advice
* Include price ranges and typical costs

**For Parallel Orchestration:**

```python
tasks = [
    self.agents["cuisine"].process_request(request),
    self.agents["location"].process_request(request),
    self.agents["price"].process_request(request)
]
results = await asyncio.gather(*tasks)
```

**For Conditional Orchestration:**

* Analyze keywords in the request
* Use simple if–else logic
* Map keywords to relevant agents

---

## 🧪 Testing Your Solution

After completing all tasks, your system should:

* Provide **detailed recommendations** from all three agents
* Support all orchestration patterns:

  * **Sequential**: Cuisine → Location → Price
  * **Parallel**: All agents simultaneously
  * **Conditional**: Smart agent selection
* Handle multiple restaurant scenarios without errors

---

## 📚 Expected Output

```text
🎉 SEQUENTIAL ORCHESTRATION RESULTS
============================================================

🍽️ Cuisine Recommendations
1. Authentic Italian — Perfect for romantic occasions  
   - Must-try: Osso Buco, Tiramisu  
   - Great for special celebrations  

2. Modern Italian Fusion — Creative dishes in upscale setting  
   - Must-try: Truffle Pasta, Burrata  
   - Romantic ambiance with contemporary twist  

📍 Location Recommendations
• Downtown Fine Dining District  
  - Atmosphere: Intimate, candlelit  
  - Parking: Valet available  
  - Best time: 7–8 PM  

• Riverside Restaurants  
  - Atmosphere: Scenic, peaceful  
  - Best for special occasions  

💰 Price Range Recommendations
• Price Range: $$$ (Fine Dining)  
• Average Cost: $80–120 per person  
• Value Tips: Look for prix fixe menus, book early for specials  
• Typical Prices: Appetizers $15–20, Mains $30–45, Desserts $12–18  
```

---

## 🆘 Need Help?

* Review the **travel planning demo** for orchestration patterns
* Check the solution code for reference
* Test one agent at a time
* Start with simple prompts, then enhance

---

## 🎯 Success Criteria

✅ All three agents provide structured recommendations
✅ All orchestration patterns work correctly
✅ The system handles different restaurant scenarios
✅ Output is clear, detailed, and well-formatted

---

🚀 Good luck building your restaurant advisor!
