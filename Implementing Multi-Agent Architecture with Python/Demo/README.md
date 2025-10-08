# 🏙️ Smart City Monitoring Demo (Semantic Kernel 1.36.2)

## 📖 Overview

This project demonstrates a **multi-agent smart city monitoring system** built using **Semantic Kernel 1.36.2** and **Azure OpenAI**.

The system simulates how different city specialists (Traffic, Energy, Safety) analyze urban issues using structured AI prompts. Each worker is modeled as an independent agent with its own area of expertise.

---

## 🚦 Workers (Specialized Agents)

The project defines a base class and three specialized agents:

### 🔹 Base Class: `Cityworker`

* Represents a generic worker with a **name**, **expertise**, and an **AI kernel** connection.
* Configures the Azure OpenAI service using environment variables.
* Defines an abstract `process_request()` method that subclasses must implement.

### 🔹 `Trafficworker`

* Expertise: Urban traffic flow and congestion management
* Generates a **traffic analysis** of the given scenario

### 🔹 `Energyworker`

* Expertise: City energy consumption and distribution
* Provides insights on **energy usage and patterns**

### 🔹 `Safetyworker`

* Expertise: Public safety and emergency response
* Performs a **safety risk assessment**

Each worker uses **KernelFunctionFromPrompt** to build prompts tailored to its expertise.

---

## ⚙️ How It Works

1. **Environment Setup**

   * Loads Azure OpenAI credentials from `.env`:

     ```env
     AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=your-deployment-name
     AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
     AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your-api-key
     ```

2. **Initialization**

   * Creates worker instances (`Trafficworker`, `Energyworker`, `Safetyworker`).
   * Each worker has its own AI kernel connected to Azure OpenAI.

3. **Scenario Simulation**

   * Defines demo scenarios:

     * Heavy traffic congestion
     * High downtown energy consumption
     * Public safety concerns in a park

4. **Parallel Processing**

   * Runs all workers **concurrently** using `asyncio.gather()`.
   * Each worker independently analyzes the scenario from its own perspective.

5. **Output**

   * Prints structured analysis results for each worker.
   * Handles errors gracefully and reports if any worker fails.

---

## 🛠️ Running the Demo

1. Install dependencies:

   ```bash
   pip install semantic-kernel==1.36.2 python-dotenv
   ```

2. Configure your `.env` file with Azure OpenAI credentials.

3. Run the script:

   ```bash
   python smart_city_demo.py
   ```

---

## 📊 Sample Output

```text
Smart City Monitoring Demo - Semantic Kernel 1.36.2
==================================================

Scenario 1: Heavy traffic congestion on Main Street
----------------------------------------
Traffic Manager:
🚦 Traffic Analysis:
[AI-generated traffic insights]

Energy Analyst:
⚡ Energy Analysis:
[AI-generated energy insights]

Safety Officer:
🚨 Safety Analysis:
[AI-generated safety insights]
```

---

## 🎯 Key Learning Outcomes

* **Multi-Agent Architecture**: Different workers specialize in distinct domains.
* **Prompt Engineering**: Tailored prompts create structured, domain-specific outputs.
* **Concurrency**: Workers process requests in parallel with async/await.
* **Semantic Kernel Integration**: Demonstrates `KernelFunctionFromPrompt` and Azure OpenAI usage.

---

## 🔮 Possible Extensions

* Add new workers (e.g., **EnvironmentWorker**, **HealthcareWorker**)
* Implement **intelligent coordination** to decide which workers should respond to each request
* Enhance prompts with **structured templates** for more detailed reports
* Integrate with real-time city data sources for live monitoring

---

✨ This project serves as a **starter template** for building intelligent, multi-agent monitoring systems with Semantic Kernel and Azure OpenAI.
